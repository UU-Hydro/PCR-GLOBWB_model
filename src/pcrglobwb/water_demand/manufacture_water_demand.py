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


class ManufactureWaterDemand(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # make the iniItems for the entire class
        self.iniItems = iniItems
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # get the file information for manufacture water demand (unit: m/day)
        self.manufactureWaterDemandOption = False
        if iniItems.waterDemandOptions['includeManufactureWaterDemand']  == "True":
            self.manufactureWaterDemandOption = True  
            logger.info("Manufacture water demand is included in the calculation.")
        else:
            logger.info("Manufacture water demand is NOT included in the calculation.")
        
        if self.manufactureWaterDemandOption:
            self.manufactureWaterDemandFile = \
                vos.getFullPath(\
                    inputPath        = iniItems.waterDemandOptions['manufactureWaterDemandFile'], \
                    absolutePath     = self.inputDir, \
                    completeFileName = False)



    def update(self, currTimeStep, read_file = True):

        # get the gross and netto demand values (as well as return flow fraction), either by reading input files or calculating them
        if read_file:
            self.read_manufacture_water_demand_from_files(currTimeStep)
        else:
            self.calculate_manufacture_water_demand_for_date(currTimeStep)



    def read_manufacture_water_demand_from_files(self, currTimeStep):
        # read manufacture water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.manufactureWaterDemandOption:
                self.manufactureGrossDemand = \
                    pcr.max(0.0, \
                            pcr.cover( \
                                      vos.netcdf2PCRobjClone( \
                                          ncFile           = self.manufactureWaterDemandFile, \
                                          varName          = 'manufactureGrossDemand', \
                                          dateInput        = currTimeStep.fulldate, \
                                          useDoy           = 'monthly',\
                                          cloneMapFileName = self.cloneMap), \
                                      0.0))
                
                self.manufactureNettoDemand = \
                    pcr.max(0.0, \
                            pcr.cover( \
                                      vos.netcdf2PCRobjClone( \
                                          ncFile           = self.manufactureWaterDemandFile, \
                                          varName          = 'manufactureNettoDemand', \
                                          dateInput        = currTimeStep.fulldate, \
                                          useDoy           = 'monthly', \
                                          cloneMapFileName = self.cloneMap), \
                                      0.0))
                
            else:
                self.manufactureGrossDemand = pcr.spatial(pcr.scalar(0.0))
                self.manufactureNettoDemand = pcr.spatial(pcr.scalar(0.0))
                logger.debug("Manufacture water demand is NOT included.")
            
            # gross and netto industrial water demand in m/day
            self.manufactureGrossDemand = pcr.cover(self.manufactureGrossDemand, 0.0)
            self.manufactureNettoDemand = pcr.cover(self.manufactureNettoDemand, 0.0)
            self.manufactureNettoDemand = pcr.min(self.manufactureGrossDemand, self.manufactureNettoDemand)  

            # return flow fraction
            self.manufactureReturnFlowFraction = pcr.max(0.0, 1.0 - vos.getValDivZero(self.manufactureNettoDemand, self.manufactureGrossDemand))


    def calculate_manufacture_water_demand_for_date(self, currTimeStep):
        # TODO: We may want to calculate manufacture water demand on the fly (read_file = False)
        pass
