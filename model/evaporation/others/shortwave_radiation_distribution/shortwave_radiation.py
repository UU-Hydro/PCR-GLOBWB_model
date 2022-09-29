#!/usr/bin/env python
#  -*- coding: utf-8 -*-

###############################################################################
# shortwave_radiation.py:                                                     #
# global shortwave radiation: class instance that allows for the computation  #
# of spatial distributed fields of the incoming radiation per day             #
###############################################################################

"""

shortwave_radiation.py:                                                     #
global shortwave radiation: class instance that allows for the computation  #
of spatial distributed fields of the incoming radiation per day             #

"""

###########
# Modules #
###########
#-standard modules
import os
import sys
import math
import datetime

import pcraster as pcr

from calendar import isleap
from copy import deepcopy

########
# TODO #
########
critical_improvements= str.join('\n\t',\
             ( \
              '', \
              ))

development= str.join('\n\t',\
             ( \
              '', \
              'add a class to compute subdaily radiation and the angle', \
              'as well as a class to compute the topographic shading for regional models.'
              '', \
              ))

print ('\nDevelopmens for main module:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

####################
# global variables #
####################

# set the global option to radians
pcr.setglobaloption('radians')

# type set to identify None (compatible with pytyon 2.x)
NoneType = type(None)

# and set pi
pi = math.pi

#############
# functions #
#############

# conversions to and from radians
def deg2rad(a):
    
    return a * pi / 180.0

def rad2deg(a):
    
    return a * 180.0 / pi

# julian day and relative julian day

def get_julian_day_number(date):

    '''

get_julian_day_number: returns the julian day number in the year.

    Input:
    ======
    date:               date in datetime date or datetime format.
    
    Output:
    =======
    julian_day:         integer number of julian day in the present year

'''

    # recast as date
    if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
        d = datetime.date(date.year, date.month, date.day)
    else:
        message_str = 'ERROR: date needs to have datetime date or datetime format.'
        sys.exit(message_str)

    # get the difference
    d0 = datetime.date(d.year, 1, 1)
    td = (d - d0)

    # and return the number
    julian_day = int(td.days)
    return julian_day

# atmospheric pressure correction
def get_patm_cor(z):

    '''

get_patm_cor: function that returns the correction for the atmospheric pressure \
as a function of the surface elevation, z [m]. Returns atm_corr [-].

'''

    return (1.0 - 2.2569e-5 * z) ** 5.2553

# transmittance
def get_tau_o(latitude, tau_o_min = 0.774):

    '''

get_tau_o: function that returns the transmittance of clean, dry air \
as a function of the latitude, using the approximation proposed by Winslow et \
al. (2001) on the basis of the data by List (1971).

    Input:
    ======
    latitude:           latitude of the cell in radians;
    tau_o_min:          minimum allowable value of the transmittance tau_o
                        (optional), which by default is set to 0.774 [-]
                        that corresponds with a latitude of 80 degrees (1.40
                        rad).
    
    Output:
    =======
    tau_o:              transmittance of clean, dry air [-].

'''

    # set the constants, so tau_o = a - c * phi ** b
    a = 0.947
    b = 2.220
    c = 8.263e-02

    # get tau_o
    tau_o = pcr.max(tau_o_min, \
                    a - c * pcr.abs(latitude) ** b)
    
    # return tau_o
    return tau_o

def get_tau_a():

    '''
get_tau_a: returns the transmittance affected by atmospheric
aerosols and ozone; currently not defined and returns a global value of 1.

'''

    return pcr.spatial(pcr.scalar(1))

def get_tau_v(temp_annual):

    '''

get_tau_v: function that returns the transmittance as affected by atmospheric 
water vapour, using the approximation proposed by Winslow et al. (2001).

    Input:
    ======
    temp_annual:        average annual temperature in degC.
    
    Output:
    =======
    tau_v:              transmittance as affected by atmospheric water vapour
                        [-].

'''

    # set the constants, so tau_v = a - c * (t_a + d) ** b
    a = 0.9636
    b = 1.8232
    c = 9.092e-5
    d = 30.0


    # get tau_v
    tau_v = a - c * pcr.max(0.0, temp_annual + d) ** b
    
    # return tau_v
    return tau_v

# parameter beta to correct for the influence of the relative humidity
def compute_beta(temp_annual, delta_temp_mean):

    '''

compute_beta: parameter of the Bristow-Campbell relation that scales the \
extraterrestrial shortwave radiation to the shortwave radiation at the surface \
as a function of the relative humidity (as estimated between the saturated \
vapour pressure at the minimum temperature as an approximation of the dew point \
 and that at the maximum temperature).

The value of the parameter beta was determined empirically by Winslow et al. \
(2001) and fitted to have a lower value of 1.041 (assuming the relative \
humidity is always less than 0.96 x 100%):

    beta = max(1.041, 23.753 * delta_temp_mean / (temp_mean + 273.15))


    Input:
    ======
    temp_annual:        long-term annual mean temperature.
    delta_temp_mean:    long-term annual mean value of the diurnal difference
                        between Tmax and Tmin;
                        Both temperature fields are supposed to be scalar
                        PCRaster maps.

    Output:
    =======
    beta:               parameter that scales the influence of the relative
                        humidity on the shortwave radiation that reaches the
                        surface [-].

beta increases linearly with the temperature difference but the limit of 1.041 \
is exceeded earlier for colder mean temperatures and the increase is steeper.

'''

    # return beta
    return pcr.max(1.041, 23.753 * delta_temp_mean / (temp_annual + 273.15))

#day length correction for relative humidity
def compute_day_length_correction(day_length):
    
    '''

compute_day_length_correction: function that compute the correction for shift \
between the incoming shortwave radiation during the daylight period (equal to \
the day length, over which Rs is accumulated) and the moment the relative \
humidity is at its lowest or the temperature is at its maximum (R@Tmax).
The correction is adopted and modified after Winslow et al. (2001).

The day length is entered in hours and converted internally to 2 * pi for \
a duration of 24 hours. The radiation distribution over the day is linearized \
and centred on 12 AM (noon), when the radiation is the maximum
The function assumes that the maximum temperature is \
reached at 3 PM (day length of 0.5 * pi). If the day length is equal to shorter \
than 6 hours (Rs occurring before or at 3 PM), the correction is limited to 1, \
if this falls later, more incoming shortwave radiation is received as the \
duration over the radiation comes in through an atmosphere with less relative \
humidity and thus can reach the surface more uninterrupted, increases.


The correction factor rs_rtmax_cor then is computed from:

    Rs/R@Tmax = (1 - 0.25 * (D - 0.5 * pi) ** 2 / D ** 2) ** -1
    
where D is the day length scaled to 2 * pi radians for 24 hours and D cannot \
be smaller than 0.5 * pi (equivalent to Tmax at 3 PM, so Rs/R@Tmax = 1).

    Input:
    ======
    day_length:         the length of the day in sunshine hours per cell,
                        entered as a PCRaster spatial scalar map.

    Output:
    =======
    ratio_rs_rtmax:     the correction factor, being the ratio Rs/R@Tmax,
                        which cannot be smaller than unity or larger than 1.164
                        if day_length = 24 hours.

'''

    # convert the daylength to radians; cast as a scalar PCRaster map
    # to return a map for sure
    dl_rad = pcr.max(6.0, pcr.scalar(day_length)) * 2 * pi / 24

    # compute the ratio
    ratio_rs_rtmax = (1 - 0.25 * (dl_rad - 0.5 * pi) ** 2 / dl_rad ** 2) ** -1

    # return the ratio
    return ratio_rs_rtmax

# saturated vapour pressure
def compute_sat_pressure(air_temp):
    
    '''
compute_sat_pressure: function to compute the saturated vapour pressure from \
the air temperature.

    Input:
    ======
    air_temp            :   air temperature in [degC].
    
    Output:
    =======
    esat                :   saturated vapour pressur in [Pa].

The solution is based on Tetens' (1930) relation and distinguishes between \
air temperatures below and above freezing using the relation by Murray (1967).

'''
    # References
    # Tetens, O. 1930. Über einige meteorologische Begriffe. Z. Geophys 6: 207-309.
    # Murray, F.W. 1967. On the computation of saturation vapour pressure. J. Applied Meteorology 6: 203-204.

    # set the constants as a tuple where the first entry belongs to an air temperature
    # below freezing, the second entry to an air temperature above freezing:
    # e_sat = p * exp((a * air_temp + b) / (air_temp + c))

    # function was developed for air temperature in [K],
    # so scale the temperature accordingly
    air_temp = deepcopy(air_temp) + 273.15

    # set the pressure term in [Pa]
    p = 610.78
    # set the offset of the temperature ratio: 
    # for air temperature below freezing, the offset c is 265.5, above freezing
    # it is 237.3 in case the temperature is given in degrees centigrade,
    # the factor a is 21.875 and 17.27 and the offset b is zero in both cases.
    # in case the air temperature is given in K, the following values are used:
    a = (21.875, 17.27)
    b = (-5975.2, -4717.3)
    c = (-7.65, -35.85)
    
    # get the saturated vapour pressure [Pa] depending on the data type
    esat = p * pcr.ifthenelse(air_temp < 273.15, \
           pcr.exp((a[0] * air_temp + b[0]) / (air_temp + c[0])), \
           pcr.exp((a[1] * air_temp + b[1]) / (air_temp + c[1])))

    # return the saturated vapour pressure
    return esat


def estimate_relative_humidity(t, tdew):

    '''

estimate_relative_humidity: function that approximates the relative humidity \
on a day or at a particular time as the ratio between the saturated vapour \
pressure at the dewpoint temperature and the temperature at a later moment in \
time or over the day.

    Input:
    ======
    t:                  air temperature [degC]; can be the average over the day
                        or an instantaneous moment in time (e.g., tmax);
    tdew:               dewpoint temperature [degC], which can be approximated
                        as the minimum temperature except for arid areas where
                        the dew point is typically 2-3 degrees centigrade lower
                        than the minimum air temperature;
                        Both temperature fields are supposed to be scalar
                        PCRaster maps or compatible with this.

    Output:
    =======
    relhum:             relative humidity [-]; ratio of esat(tdew) / esat(t).

'''

    return pcr.min(1.0, compute_sat_pressure(pcr.spatial(pcr.scalar(tdew))) /\
                   compute_sat_pressure(pcr.spatial(pcr.scalar(t))))


# solar geometry
def compute_solar_declination(day_angle):

    '''

compute_solar_declination: function that computes the solar declination \
as a function of the day angle in radians.

    Input:
    ======
    day_angle:          day angle [radians] that expresses the position of the
                        julian day within the year.

    Output:
    =======
    solar_declination:  solar declination relative to the equator [radians].

 '''

    # compute the solar declination [radians]
    solar_declination = 0.006918 - 0.399912 * pcr.cos(day_angle) + \
                        0.070257 * pcr.sin(day_angle) - 0.006758 * pcr.cos(2*day_angle) + \
                        0.000907 * pcr.sin(2 * day_angle) - 0.002697 * pcr.cos(3 * day_angle) + \
                        0.00148 * pcr.sin(3 * day_angle)

    # return the solar declination
    return solar_declination

def compute_eccentricity(day_angle):

    '''

compute_eccentricty: function that computes the eccentricity of the earth's \
orbit around the sun as a function of the day angle in radians.

    Input:
    ======
    day_angle:          day angle [radians] that expresses the position of the
                        julian day within the year.

    Output:
    =======
    eccentricity:       eccentricity (ro / r) ** 2 [-].

 '''

    # compute the eccentricity [-]
    eccentricity =  1.00011 + 0.034221 * pcr.cos(day_angle) + \
                    0.00128 * pcr.sin(day_angle) + 0.000719 * pcr.cos(2 * day_angle) + \
                    0.000077 * pcr.sin(2 * day_angle)
    
    # return eccentricity
    return eccentricity

def compute_day_length(latitude, solar_declination):

    '''

compute_day_length: function that computes the day length in hours.

    Input:
    ======
    latitude:           PCRaster field of the latitude of all cells in
                        radians;
    solar_declination:  solar declination relative to the equator [radians].


    Output:
    =======
    day_length:         day length [hours].

 '''

    # compute the day length
    tanterm = pcr.tan(latitude) * pcr.tan(solar_declination)
    day_length = 2 * pcr.ifthenelse( \
                 pcr.abs(tanterm) < 1.00, \
                 pcr.scalar(pcr.acos(-tanterm)) / 0.2618, \
                 pcr.ifthenelse(solar_declination < 0, pcr.scalar(0), 12))

    # return the day length
    return day_length

def compute_solar_geometry(latitude, day_angle):

    '''

compute_solar_geometry: function that computes the solar declination and the \
eccentricity as a function of the latitude and day angle in radians.

    Input:
    ======
    latitude:           PCRaster field of the latitude of all cells in
                        radians;
    day_angle:          day angle [radians] that expresses the position of the
                        julian day within the year.

    Output:
    =======
    solar_declination:  solar declination relative to the equator [radians];
    eccentricity:       eccentricity (ro / r) ** 2 [-].

 '''

    # get the solar declination [rad]
    solar_declination = compute_solar_declination(day_angle)
    
    # get the eccentricity
    eccentricity = compute_eccentricity(day_angle)

    # return the solar declination and eccentricity
    return solar_declination, eccentricity

def compute_radsw_ext(latitude, solar_declination, \
                      eccentricity, day_length, solar_constant = 118.1):

    '''

compute_radsw_ext: function that computes the extraterrestrial radiation \
as a function of the latitude and day angle in radians, in the units of the \
solar_constant specified.

    Input:
    ======
    latitude:           PCRaster field of the latitude of all cells in
                        radians;
    solar_declination:  solar declination relative to the equator [radians];
    eccentricity:       eccentricity (ro / r) ** 2 [-];
    day_length:         day length [hours];
    solar_constant:     incoming shortwave radiation from solar radiation,
                        projected perpendicularly to surface if the earth,
                        optional input, default value is 118.1 (MJ/m2/day;
                        equivalent to 341 W/m2).

    Output:
    =======
    radsw_ext:         extraterrestrial shortwave radiation in units of the
                        solar constant specified.

  '''

    # compute the extraterrestrial shortwave radiation
    radsw_ext = 2.0 / 24.0 * solar_constant * eccentricity * \
                (pcr.cos(solar_declination) * pcr.cos(latitude) * \
                 pcr.sin(0.5 * 0.2618 * day_length) / 0.2618 + \
                 0.5 * pcr.sin(solar_declination) * pcr.sin(latitude) * \
                 day_length)

    # return the extraterrestrial shortwave radiation
    return radsw_ext

###########
# classes #
###########

##########################################
# start of the shortwave_radiation class #
##########################################

class shortwave_radiation(object):

    """

shortwave_radiation: class that updates on a daily timestep the incoming \
shortwave radiation in the form of spatial PCRaster maps holding the following \
variables:
    - extraterrestrial radiation;
    - actual radiation at the earth's surface.

These quantities are computed on the basis of the following information:
    - latitude;
    - surface elevation.
    - julian day number within the year;
    - climate variables: precipitation and maximum and minimum temperature on
      a daily basis and mean annual temperature.

The modification from extraterrestrial radiation to cloud-free shortwave \
radiation and to the actual shortwave radiation contains in total three static \
transmissivity components for cloud-free skies and two conceptualized factors \
to represent the course in humidity over the day, that are all available in \
the class.

Units of the output depend on the units of the solar constant, which by default \
is defined in [MJ/m2/day].

The computation of the extraterrestrial radiation is based on Dingman's \
Physical Geography (2015), the conversion to surface shortwave radiation \
on the VP-RAD model by Winslow et al. (2001):

    Dingman, S. L. (2015). Physical hydrology. Waveland press.

    Winslow, J. C., Hunt Jr, E. R., & Piper, S. C. (2001).
    A globally applicable model of daily solar irradiance estimated from air 
    temperature and precipitation data. Ecological Modelling, 143(3), 227-243.
    doi.org/10.1016/S0304-3800(01)00341-6

"""

    def __init__(self, \
                 latitude, \
                 elevation, \
                 temp_annual, \
                 delta_temp_mean, \
                 solar_constant = 118.1):
        
        '''

shortwave_radiation.__init__(): function to inintialize this instance of the \
class shortwave radiation.

    Input:
    ======
    latitude:           PCRaster field of the latitude of all cells in
                        radians;
    elevation:          PCRaster field of the surface elevation (DEM)
                        in metres;
    temp_annual:        long-term annual mean temperature.
    delta_temp_mean:    long-term annual mean value of the diurnal difference
                        between Tmax and Tmin;
                        Temperature fields are supposed to be scalar
                        PCRaster maps;
    solar_constant:     incoming shortwave radiation from solar radiation,
                        projected perpendicularly to surface if the earth,
                        optional input, default value is 118.1 (MJ/m2/day;
                        equivalent to 341 W/m2).

    Output:
    =======
    None:               returns None.

Shortwave radiation computed in this class has the same unit as the solar
constant (default MJ/m2/day).

'''

        # init object
        object.__init__(self)

        # reduction of the transmittance [-] affected by water vapour in the
        # atmospheric column on a wet day (Winslow et al., 2001), that is
        # characterized by precipitation exceeeding the threshold specified
        # (defined as 1 mm waterslice per day, in units of metres).
        self.tau_v_red  = 0.13
        self.prec_limit = 1.0e-3
        
        # set the fraction of the extraterrestrial shortwave radiation
        # that would be received as diffuse radiation in case of full cloudiness
        # at the earth's surface (Winslow et al., 2001 based on List, 1971)
        self.max_red_radsw_ext = 0.10

        # set the solar constant
        self.solar_constant = solar_constant

        # set the latitude in radians
        self.latitude = latitude

        # set the solar constant
        self.solar_constant = solar_constant

        # initialize the variables:
        # extraterrestrial shortwave radiation
        # actual shortwave radiation
        self.radsw_ext = pcr.spatial(pcr.scalar(0))
        self.radsw_act = pcr.spatial(pcr.scalar(0))

        # initialize the other parameters; this is grouped in a function
        # that can be called outside the __init__ function, so all variables are
        # set internally.
        self.tau_o    = pcr.spatial(pcr.scalar(1))
        self.tau_a    = pcr.spatial(pcr.scalar(1))
        self.tau_v    = pcr.spatial(pcr.scalar(1))
        self.tau_cf   = pcr.spatial(pcr.scalar(1))
        self.patm_cor = pcr.spatial(pcr.scalar(1))
        self.beta     =  pcr.spatial(pcr.scalar(1))
        self.parameter_initialization(latitude, elevation, temp_annual, \
                                      delta_temp_mean)

        # returns None
        return None

    def parameter_initialization(self, latitude, elevation, temp_annual, \
                                 delta_temp_mean):

        '''

parameter_initialization: function that sets internally the parameters \
required to compute the shortwave radiation at the earth surface.

    Input:
    ======
    elevation:          PCRaster field of the surface elevation (DEM)
                        in metres;
    temp_annual:        average annual temperature in degC.

    Output:
    =======
    tau_o, 
    tau_a,
    tau_v:              transmittance [-] of the air column for 
                        clean, dry air, as affected by atmospheric
                        aerosols and ozone, and as affected by atmospheric
                        water vapour;
                        where P/Po is the correction for atmospheric pressure [-];
    patm_cor:           correction for atmospheric pressure [-],
                        relative to the reference value at sea-level and
                        based on the elevation, z [m];
    beta:               parameter that scales the influence of the relative
                        humidity on the shortwave radiation that reaches the
                        surface [-].

All variables are also set internally

'''
        # initialize all variables
        # correction for atmospheric pressure
        patm_cor = get_patm_cor(elevation)
        # components of the transmissivity
        tau_o  = get_tau_o(latitude)
        tau_a  = get_tau_a()
        tau_v  = get_tau_v(temp_annual)
        beta   = compute_beta(temp_annual, delta_temp_mean)

        # set the internal variables
        self.tau_o = tau_o
        self.tau_a = tau_a
        self.tau_v = tau_v
        self.patm_cor = patm_cor
        self.beta = beta

        # return the values
        return tau_o, tau_a, tau_v, patm_cor, beta

    def update(self, date, prec_daily, temp_min_daily, temp_max_daily):

        '''

update: function that updates the extraterrestrial radiation and the actual \
shortwave radiation at the earth's surface on a particular day given the \
precipitation, minimum and maximum daily temperature.

    Input:
    ======
    date:               date of the year, in datetime date or datetime format;
    prec_daily:         daily precipitation [m waterslice per day];
    temp_min_daily:     daily minimum temperature [degC];
    temp_max_daily:     daily maximum temperature [degC];
                        precipitation and temperature are supposed to be
                        spatial scalar PCRaster fields or compatible with this.

    Output:
    =======
    None:               returns None.

'''

        # get the julian day and the number of days
        julian_day = get_julian_day_number(date)
        number_days = 365
        if isleap(date.year):
            number_days = 366
        # get the day angle [rad]
        day_angle = float(julian_day - 1) / number_days * 2 * pi

        # get the solar geometry (declination, eccentricity) and the day length
        solar_declination, eccentricity = compute_solar_geometry(self.latitude, \
                                                                 day_angle)
        day_length = compute_day_length(self.latitude, solar_declination)

        # # compute the extraterrestrial radiation
        self.radsw_ext = compute_radsw_ext(self.latitude, solar_declination, \
                                           eccentricity, day_length, \
                                           self.solar_constant)

        # decide whether the day classifies as a wet day on the basis of the
        # daily precipitation amount
        wet_day = prec_daily > self.prec_limit 

        # estimate the relative humidity using the minimum daily temperature
        # as the dewpoint temperature
        rel_hum = estimate_relative_humidity(temp_max_daily, temp_min_daily)

        # get the transmittance
        # tau_cf:             transmittance [-] for a cloud-free atmospheric column,
        #                     which is computed as
        #                                 tau_cf = (tau_o * tau_a * tau_v)**(P/Po)
        # with tau_v modified in case of a wet day
        self.tau_cf = (self.tau_o * self.tau_a * \
                       pcr.max(0, self.tau_v - pcr.scalar(wet_day) * self.tau_v_red)) \
                       **self.patm_cor

        # get the day length correction
        day_length_correction = compute_day_length_correction(day_length)

        # finally, compute the reduction of the extraterrestrial radiation to
        # obtain the actual shortwave radiation received at the surface
        red_radsw_ext = pcr.max(self.max_red_radsw_ext, \
                                self.tau_cf * day_length_correction * \
                                pcr.max(0.0, 1.0 - self.beta * rel_hum))

 
        # and update the incoming, actual shortwave radiation at the earth's
        # surface
        self.radsw_act = red_radsw_ext * self.radsw_ext

        # returns None
        return None

########################################
# end of the shortwave_radiation class #
########################################

########
# main #
########

def main():

    # initialization
    # set the input directory
    # and the input files
    inputpath = 'data'
    clonefilename = os.path.join(inputpath, 'Global_CloneMap_30min.map')
    demfilename   = os.path.join(inputpath, 'gtopo30min.map')
    precfilename  = os.path.join(inputpath, 'prec_day0120.map')
    tempfilename  = os.path.join(inputpath, 'temp_day0120.map')
    temp_annual_filename = \
                    os.path.join(inputpath, 'temp_annual.map')
    delta_temp_mean_filename = \
                    os.path.join(inputpath, 'delta_temp_mean.map')
    delta_temp_daily_filename = \
                    os.path.join(inputpath, 'delta_temp_daily.map')

    # set the date
    date = datetime.datetime(1979, 4, 30)

    # start
    # set the clone and read in the input maps
    pcr.setclone(clonefilename)
    landmask = pcr.readmap(clonefilename)

    # read in the DEM and the precipitation and temperature file
    dem = pcr.ifthen(landmask, pcr.readmap(demfilename))
    prec_daily  = pcr.ifthen(landmask, pcr.readmap(precfilename))
    temp_daily  = pcr.ifthen(landmask, pcr.readmap(tempfilename))
    temp_annual = pcr.ifthen(landmask, pcr.readmap(temp_annual_filename))
    delta_temp_mean = pcr.ifthen(landmask, pcr.readmap(delta_temp_mean_filename))
    delta_temp_daily = pcr.ifthen(landmask, pcr.readmap(delta_temp_daily_filename))
    temp_min_daily = temp_daily - 0.5 * delta_temp_daily
    temp_max_daily = temp_daily + 0.5 * delta_temp_daily


    # set the latitude in radians
    latitude = deg2rad(pcr.ycoordinate(landmask))

    # initialize the shortwave_radiation class
    sw_rad = shortwave_radiation(latitude, dem, temp_annual, delta_temp_mean)

    # update the shortwave radiation for the specified date
    sw_rad.update(date, prec_daily, temp_min_daily, temp_max_daily)

    # finally, show the values
    pcr.aguila(sw_rad.radsw_ext, sw_rad.radsw_act, sw_rad.radsw_act / sw_rad.radsw_ext)

if __name__ == "__main__":

    # call main and exit
    main()
    sys.exit('all done')