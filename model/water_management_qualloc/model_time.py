#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
 
"""

###########
# Modules #
###########
import sys
import datetime
import calendar
import logging

import numpy as np

from math  import pi, cos, tan, acos
from copy import deepcopy

logger = logging.getLogger(__name__)

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
              'make time increment variable', \
              '', \
              ))

print ('\nDevelopmens for time class:')

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

# functions #

def get_weights_from_dates(dates):
    
    # returns the weights of the spaced time increments of dates over the total
    # length; input is a sequence of dates (list, numpy array) and the weights
    # are stored as a dictionary with the date as key for transparency
    
    # get the type of the list
    seq_type = type(dates)
    
    # cast the dates as a new sequence
    d = deepcopy(dates)
    
    if seq_type == list:
        d = np.array(d)
    
    # collapse the dates and sort
    d = d.ravel()
    d.sort()
    
    # create the weights
    w = np.zeros(d.size)
    
    # add a final date
    d = np.append(d, datetime.datetime(d[0].year + 1, d[0].month, d[0].day))
    
    # iterate over the weighs to get the date difference
    delta_d = d[-1] - d[0]
    for ix in range(w.size):
        
        w[ix] = (d[ix + 1] - d[ix]) / delta_d
       
    # cast the weights to the desired type and return
    if seq_type == list:
        w = w.tolist()
      
    # return the weights
    return dict((d[ix], w[ix]) for ix in range(len(w)))

def get_julian_daynumber(date):
    
    # returns the integer julian day number for a date provieded in daytime format

    return int((date - datetime.datetime(date.year, 1, 1)).days)

def match_date_by_julian_number(date, dates, within_same_month = True):

    '''
    Output:
    =======
match_date_by_julian_number: function that allows for date substitution in the water management \
module.

    Input:
    ======
    date:                   date provided;
    dates:                  array of available dates to which the provided
                            dates should be matched;
    date_selection_method:  date selection method, default value is 'exact';
                            can be 'exact', 'before', or 'after'.

    Output:
    =======
    date_index:             date index matching the sought date to the av-
                            ailable dates;
    matched_date:           the date in the available dates that matches the
                            date index;
    message_str:            message string on the date selction for subsequent
                            logging.

'''

    # initialize the message string
    message_str = ''

    # get the julian day number and month for the date
    julian_day  = get_julian_daynumber(date)
    month       = date.month
    year        = date.year

    # make sure dates are an array
    if isinstance(dates, list):
        dates = np.array(dates)

    # get the julian day number and month for the dates
    julian_days = np.zeros(dates.shape, dtype = int)
    months      = np.zeros(dates.shape, dtype = int)
    years       = np.zeros(dates.shape, dtype = int)
    ix = 0
    for sdate in dates:
        julian_days[ix] = get_julian_daynumber(sdate)
        months[ix]      = sdate.month
        years[ix]       = sdate.month
        ix = ix + 1

    # set the range of indices
    ixs       = np.arange(dates.size, dtype = int)
    ixs.shape = dates.shape

    # compute the deviations
    devs = np.abs(julian_days - julian_day)

    # set the mask
    if within_same_month and np.any(months == month):
        mask = months == month
    else:
        mask = months != 13
        if within_same_month:
            message_str = '; Warning: month %d is not present in the provided dates' % month

    if year in years:
        mask = mask & (years == year)

    # halt if the mask returns a zero selection
    if np.size(devs[mask]) > 0:

        # get the minimum deviation
        devs    = devs[mask]
        ixs     = ixs[mask]

        # get the minimimum deviation and date index
        min_dev    = devs.min()
        date_index = int(ixs[devs == min_dev][0])

    # get the matched date
    matched_date = dates[date_index]
    # create the output message string
    message_str = str.join('',\
                           ('date %s is matched with %s in the available dates' % \
                            (date, matched_date), \
                            message_str))

    # return the date index, matched date and message string
    return date_index, matched_date, message_str

#-class objects are organized as follows: __init__, __repr__ & __str__ methods
# read and reports, initializations, functions with child, and childless functions

#-file with class definitions for the CALEROS landscape dynamics model
#///start of file with class definitions///

class model_time(object):
  #-definition of the class object handling the timers for the Caleros landscape model
  # this model initializes and updates the continuous timer and julian day number

    def __init__(self, startyear, endyear, time_increment, \
                 time_step_length = 1.00, \
                 ):

        # initialize the object
        object.__init__(self)

        # set seconds per day
        self.seconds_per_day = 86400
        
        #-start year is the year in which the simulation starts
        self.time_step_length = time_step_length
        self.startyear = startyear
        self.endyear   = endyear
        self.time_increment = time_increment
        self.startdate = datetime.datetime(self.startyear,  1,  1)
        self.enddate   = datetime.datetime(self.endyear,   12, 31)
        self.date      = self.startdate

        # get the length of the simulation
        if self.time_increment == 'daily':
            self.number_time_steps = int(((self.enddate - self.date).days) / \
                                      self.time_step_length) + 1
        elif self.time_increment == 'monthly':
            self.number_time_steps = int((endyear - startyear) + 1) * 12
        else:
            sys.exit('%s cannot be used' % self.time_increment)

        #-report flags
        self.report_flags = {}.fromkeys(['daily', 'monthly', 'yearly'], False)

        # special markers, set all as False
        self.last_day_of_month  = False
        self.last_day_of_year   = False
        self.last_time_step     = False

    def __repr__(self):
        #-default report on class
        return 'this is an instance of the Caleros time class object with date %s' % \
                self.__str__

    def __str__(self):
        #-report on timers
        return self.date

    def update(self, increment):
        # update the date by incrementing it by one time step at the time
        if self.time_increment == 'daily':
            # set the time step length in days
            self.time_step_length =  1
            self.date = self.startdate + \
                        datetime.timedelta(days = (increment - 1) * self.time_step_length)
        elif self.time_increment == 'monthly':
            # get the year and month for the new date
            year  = self.startdate.year + (increment - 1) // 12
            if increment % 12 == 0:
                month = 12
            else:
                month = increment % 12
            # set the date and increment
            self.date = datetime.datetime(year, month, 1)
            # set the time step length in days
            self.time_step_length =  calendar.monthrange(year, month)[1]
        else:
            sys.exit('%s cannot be used' % self.time_increment)

        # get the year, month and day
        self.year = self.date.year
        month     = self.date.month
        day       = self.date.day

        # get the julian day
        self.julianday = get_julian_daynumber(self.date)

        # set the special markers
        # for daily time increments
        if self.time_increment == 'daily':
            self.report_flags['daily'] = True
            number_days = calendar.monthrange(self.year, month)[1]
            self.report_flags['monthly'] = day == number_days
            if self.report_flags['monthly'] and month == 12:
                self.last_day_of_year = True
            else:
                self.last_day_of_year = False
        elif self.time_increment == 'monthly':
            self.report_flags['daily'] = False
            self.report_flags['monthly'] = True
            self.last_day_of_year = month == 12
        else:
            # should not get here, but all disabled anyway
            self.report_flags = {}.fromkeys(['daily', 'monthly', 'yearly'], False)
        # set the last day of the year
        self.report_flags['yearly'] = self.last_day_of_year

        # last time step
        self.last_time_step     = increment == self.number_time_steps

        # log the date
        message_str = 'processing %s' % self.date
        logger.info(message_str)

    # def get_day_length(self, julianday, year, latitude):
    #     #-returns day length on the basis of latitude, julian day number and number of days in year
    #     # all data in radians
    #     yearlength = 365
    #     if calendar.isleap(year):
    #         yearlength = 366
    #     decl = -23.45 * pi / 180.0 * cos(2 * pi * (julianday + 10) / yearlength)
    #     return 24.0 / pi * acos(-tan(decl) * tan(latitude * pi / 180.0))

#/end of timer class/