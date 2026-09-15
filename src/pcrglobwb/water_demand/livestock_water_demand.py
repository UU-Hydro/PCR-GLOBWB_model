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

import virtualOS as vos

import logging
logger = logging.getLogger(__name__)


class LivestockWaterDemand(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # make the iniItems for the entire class
        self.iniItems = iniItems
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # get the file information for livestock water demand (unit: m/day)
        self.livestockWaterDemandOption = False
        if iniItems.waterDemandOptions['includeLivestockWaterDemand']  == "True":
            self.livestockWaterDemandOption = True
            logger.info("Livestock water demand is included in the calculation.")
        else:
            logger.info("Livestock water demand is NOT included in the calculation.")
        
        if self.livestockWaterDemandOption:
            self.livestockWaterDemandFile = \
                vos.getFullPath( \
                    inputPath        = iniItems.waterDemandOptions['livestockWaterDemandFile'], \
                    absolutePath     = self.inputDir, \
                    completeFileName = False)



    def update(self, currTimeStep, read_file = True):

        # get the gross and netto demand values (as well as return flow fraction), either by reading input files or calculating them
        if read_file:
            self.read_livestock_water_demand_from_files(currTimeStep)
        else:
            self.calculate_livestock_water_demand_for_date(currTimeStep)




    def read_livestock_water_demand_from_files(self, currTimeStep):
        # read livestock water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.livestockWaterDemandOption:
                
                # reading from a netcdf file
                if self.livestockWaterDemandFile.endswith(vos.netcdf_suffixes):  
                    self.livestockGrossDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.netcdf2PCRobjClone( \
                                              ncFile           = self.livestockWaterDemandFile, \
                                              varName          = 'livestockGrossDemand', \
                                              dateInput        = currTimeStep.fulldate, \
                                              useDoy           = 'monthly',\
                                              cloneMapFileName = self.cloneMap), \
                                          0.0))
                    
                    self.livestockNettoDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.netcdf2PCRobjClone( \
                                              ncFile           = self.livestockWaterDemandFile, \
                                              varName          = 'livestockNettoDemand', \
                                              dateInput        = currTimeStep.fulldate, \
                                              useDoy           = 'monthly', \
                                              cloneMapFileName = self.cloneMap), \
                                          0.0))
                
                # reading from pcraster maps
                else:
                    string_month = str(currTimeStep.month).zfill(2)
                    
                    grossFileName = self.livestockWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
                    self.livestockGrossDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.readPCRmapClone( 
                                              v                = grossFileName, \
                                              cloneMapFileName = self.cloneMap, \
                                              tmpDir           = self.tmpDir), \
                                          0.0))
                    
                    nettoFileName = self.livestockWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
                    self.livestockNettoDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.readPCRmapClone( \
                                              v                = nettoFileName, \
                                              cloneMapFileName = self.cloneMap, \
                                              tmpDir           = self.tmpDir), \
                                          0.0))
            else:
                self.livestockGrossDemand = pcr.spatial(pcr.scalar(0.0))
                self.livestockNettoDemand = pcr.spatial(pcr.scalar(0.0))
                logger.debug("Livestock water demand is NOT included.")
            
            # gross and netto livestock water demand in m/day
            self.livestockGrossDemand = pcr.cover(self.livestockGrossDemand, 0.0)
            self.livestockNettoDemand = pcr.cover(self.livestockNettoDemand, 0.0)
            self.livestockNettoDemand = pcr.min(self.livestockGrossDemand, self.livestockNettoDemand)

            # return flow fraction
            self.livestockReturnFlowFraction = pcr.max(0.0, 1.0 - vos.getValDivZero(self.livestockNettoDemand, self.livestockGrossDemand))


    def calculate_livestock_water_demand_for_date(self, currTimeStep):
        # TODO: We may want to calculate livestock water demand on the fly (read_file = False)
        pass
