#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Edwin H. Sutanudjaja, Rens van Beek, Niko Wanders, Yoshihide Wada, 
# Joyce H. C. Bosmans, Niels Drost, Ruud J. van der Ent, Inge E. M. de Graaf, Jannis M. Hoch, 
# Kor de Jong, Derek Karssenberg, Patricia López López, Stefanie Peßenteiner, Oliver Schmitz, 
# Menno W. Straatsma, Ekkamol Vannametee, Dominik Wisser, and Marc F. P. Bierkens
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import pcraster as pcr

sys.path.append("..")
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)


class ThermoelectricWaterDemand(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # make the iniItems for the entire class
        self.iniItems = iniItems
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # get the file information for thermoelectric water demand (unit: m/day)
        self.thermoelectricWaterDemandOption = False
        if iniItems.waterDemandOptions['includeThermoelectricWaterDemand']  == "True":
            self.thermoelectricWaterDemandOption = True  
            logger.info("Thermoelectric water demand is included in the calculation.")
        else:
            logger.info("Thermoelectric water demand is NOT included in the calculation.")
        
        if self.thermoelectricWaterDemandOption:
            self.thermoelectricWaterDemandFile = \
                vos.getFullPath(\
                    inputPath        = iniItems.waterDemandOptions['thermoelectricWaterDemandFile'], \
                    absolutePath     = self.inputDir, \
                    completeFileName = False)



    def update(self, currTimeStep, routing = None, read_file = True):
        
        if read_file:
            self.read_thermoelectric_water_demand_from_files(currTimeStep)
        else:
            self.calculate_thermoelectric_water_demand_for_date(currTimeStep, routing)



    def read_thermoelectric_water_demand_from_files(self, currTimeStep):
        # read thermoelectric water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.thermoelectricWaterDemandOption:
                self.thermoelectricGrossDemand = \
                    pcr.max(0.0, \
                            pcr.cover( \
                                      vos.netcdf2PCRobjClone( \
                                          ncFile           = self.thermoelectricWaterDemandFile, \
                                          varName          = 'thermoelectricGrossDemand', \
                                          dateInput        = currTimeStep.fulldate, \
                                          useDoy           = 'monthly',\
                                          cloneMapFileName = self.cloneMap), \
                                      0.0))
                
                self.thermoelectricNettoDemand = \
                    pcr.max(0.0, \
                            pcr.cover( \
                                      vos.netcdf2PCRobjClone( \
                                          ncFile           = self.thermoelectricWaterDemandFile, \
                                          varName          = 'thermoelectricNettoDemand', \
                                          dateInput        = currTimeStep.fulldate, \
                                          useDoy           = 'monthly', \
                                          cloneMapFileName = self.cloneMap), \
                                      0.0))
                
            else:
                self.thermoelectricGrossDemand = pcr.spatial(pcr.scalar(0.0))
                self.thermoelectricNettoDemand = pcr.spatial(pcr.scalar(0.0))
                logger.debug("Thermoelectric water demand is NOT included.")
            
            # gross and netto industrial water demand in m/day
            self.thermoelectricGrossDemand = pcr.cover(self.thermoelectricGrossDemand, 0.0)
            self.thermoelectricNettoDemand = pcr.cover(self.thermoelectricNettoDemand, 0.0)
            self.thermoelectricNettoDemand = pcr.min(self.thermoelectricGrossDemand, self.thermoelectricNettoDemand)  
            
            # return flow fraction
            self.thermoelectricReturnFlowFraction = pcr.max(0.0, 1.0 - vos.getValDivZero(self.thermoelectricNettoDemand, self.thermoelectricGrossDemand))



    def calculate_thermoelectric_water_demand_for_date(self, currTimeStep, routing):
        
        # read in power plant data for the current date
        if currTimeStep.doy == 1:
            self.readPowerplantData(currTimeStep, routing)
        
        # calculate the thermoelectric water demand for the date
        self.calculatePowerplantDemands(currTimeStep, routing)



    def readPowerplantData(self, currTimeStep, routing):
        
        logger.info("reading in (annual) powerplant data")
        
        # freshwater plants (with a water temperature dependency)
        self.powerplants_fw_capacity =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'capacity',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_ntotal =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'ntotal',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_nelec =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'nelec',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_alpha =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'alpha',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_beta =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'beta',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_omega =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'omega',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_EZ =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'EZ',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_gamma =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'gamma',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_lambda =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'lambda',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fw_ratio =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwNC,'con_ratio',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        self.powerplants_fw_ratio = pcr.cover(self.powerplants_fw_ratio, 0.)
        
        # freshwater plants (without a water temperature dependency)
        self.powerplants_fwfixed_capacity =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwfixedNC,'capacity',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fwfixed_q =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwfixedNC,'withdrawals',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_fwfixed_ratio =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_fwfixedNC,'con_ratio',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        self.powerplants_fwfixed_ratio = pcr.cover(self.powerplants_fwfixed_ratio, 0.)
        
        # seawater plants
        self.powerplants_sw_capacity =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_swNC,'capacity',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_sw_q =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_swNC,'withdrawals',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        
        self.powerplants_sw_ratio =  vos.netcdf2PCRobjClone(\
                                             routing.powerplants_swNC,'con_ratio',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)
        self.powerplants_sw_ratio = pcr.cover(self.powerplants_sw_ratio, 0.)
        
        # Poweplant demand factors
        self.dTlmax = pcr.scalar(7.)
        self.Tlmax =  vos.netcdf2PCRobjClone(\
                                             routing.TlmaxNC,'waterTemperature',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None)



    def calculatePowerplantDemands(self, currTimeStep, routing):
        
        logger.info("Dynamically estimating (daily) powerplant gross water demands")
        
        # freshwater plants (with a water temperature dependency)
        # (units: m3/s)
        ###demands considering only dTlmax
        self.powerplants_fw_qmin = self.powerplants_fw_capacity * 1e6 * ((1-self.powerplants_fw_ntotal)/ self.powerplants_fw_nelec) * (((1-self.powerplants_fw_alpha) * (1-self.powerplants_fw_beta) * self.powerplants_fw_omega * self.powerplants_fw_EZ)/ (routing.densityWater * routing.specificHeatWater * self.dTlmax)) #minimum demands (i.e. only considering deltaTlmax)
        
        ###demands considering simulated river water temperature
        self.min_Tlmax_dTlmax = pcr.max(pcr.min(self.Tlmax - routing.waterTemp, self.dTlmax),1.) #calculate min of Tlmax (max allowed temperature) - triver (water temperature). Returns minimum value of 1 (i.e. water can always be warmed by 1K as a minimum).
        
        self.powerplants_fw_q  = self.powerplants_fw_capacity * 1e6 * ((1-self.powerplants_fw_ntotal)/ self.powerplants_fw_nelec) * (((1-self.powerplants_fw_alpha) * (1-self.powerplants_fw_beta) * self.powerplants_fw_omega * self.powerplants_fw_EZ)/ (routing.densityWater * routing.specificHeatWater * self.min_Tlmax_dTlmax))
        self.powerplants_fw_rf = self.powerplants_fw_q * (1 - self.powerplants_fw_ratio) #power return flows (m3 s-1)
        
        # freshwater plants (without a water temperature dependency)
        # (units:m3/s)
        self.powerplants_fwfixed_q  = self.powerplants_fwfixed_q #freshwater demands for power prescribed by Lohrmann et al., (2019)
        self.powerplants_fwfixed_rf = self.powerplants_fwfixed_q * (1 - self.powerplants_fwfixed_ratio) #power return flows (to freshwater) prescribed by Lohrmann et al., (2019)
        
        # seawater plants
        # (units:m3/s)
        self.powerplants_sw_q  = self.powerplants_sw_q #seawater demands for power prescribed by Lohrmann et al., (2019)
        self.powerplants_sw_rf = self.powerplants_sw_q * (1 - self.powerplants_sw_ratio) #power return flows (to seawater) prescribed by Lohrmann et al., (2019)
        
        
        # gross and netto thermoelectric water demand
        # (unis: m/day)
        self.thermoelectricGrossDemand = pcr.cover((self.powerplants_fw_q + self.powerplants_fwfixed_q) * 86400 / routing.cellArea, \
                                                   0.0)
        self.thermoelectricNettoDemand = self.thermoelectricGrossDemand - \
                                         pcr.cover((self.powerplants_fw_rf + self.powerplants_fwfixed_rf) * 86400 / routing.cellArea, \
                                                   0.0)
        self.thermoelectricNettoDemand = pcr.min(self.thermoelectricGrossDemand, self.thermoelectricNettoDemand)
        
        # return flow fraction
        self.thermoelectricReturnFlowFraction = pcr.max(0.0, \
                                                        1.0 - vos.getValDivZero(self.thermoelectricNettoDemand, self.thermoelectricGrossDemand))
