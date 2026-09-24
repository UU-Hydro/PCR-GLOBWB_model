import os
import sys

import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

import logging
logger = logging.getLogger(__name__)


class IndustryWaterDemand(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # make the iniItems for the entire class
        self.iniItems = iniItems
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # get the file information for industry water demand (unit: m/day)
        self.industryWaterDemandOption = False
        if iniItems.waterDemandOptions['includeIndustryWaterDemand']  == "True":
            self.industryWaterDemandOption = True  
            logger.info("Industry water demand is included in the calculation.")
        else:
            logger.info("Industry water demand is NOT included in the calculation.")
        
        if self.industryWaterDemandOption:
            self.industryWaterDemandFile = \
                vos.getFullPath(\
                    inputPath        = iniItems.waterDemandOptions['industryWaterDemandFile'], \
                    absolutePath     = self.inputDir, \
                    completeFileName = False)



    def update(self, currTimeStep, read_file = True):

        # get the gross and netto demand values (as well as return flow fraction), either by reading input files or calculating them
        if read_file:
            self.read_industry_water_demand_from_files(currTimeStep)
        else:
            self.calculate_industry_water_demand_for_date(currTimeStep)



    def read_industry_water_demand_from_files(self, currTimeStep):
        # read industry water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.industryWaterDemandOption:
                
                # reading from a netcdf file
                if self.industryWaterDemandFile.endswith(vos.netcdf_suffixes):  
                    self.industryGrossDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.netcdf2PCRobjClone( \
                                              ncFile           = self.industryWaterDemandFile, \
                                              varName          = 'industryGrossDemand', \
                                              dateInput        = currTimeStep.fulldate, \
                                              useDoy           = 'monthly',\
                                              cloneMapFileName = self.cloneMap), \
                                          0.0))
                    
                    self.industryNettoDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.netcdf2PCRobjClone( \
                                              ncFile           = self.industryWaterDemandFile, \
                                              varName          = 'industryNettoDemand', \
                                              dateInput        = currTimeStep.fulldate, \
                                              useDoy           = 'monthly', \
                                              cloneMapFileName = self.cloneMap), \
                                          0.0))
                
                # reading from pcraster maps
                else:
                    grossFileName = self.industryWaterDemandFile + "w" + str(currTimeStep.year) + ".map"
                    self.industryGrossDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.readPCRmapClone( 
                                              v                = grossFileName, \
                                              cloneMapFileName = self.cloneMap, \
                                              tmpDir           = self.tmpDir), \
                                          0.0))
                    
                    nettoFileName = self.industryWaterDemandFile + "n" + str(currTimeStep.year) + ".map"
                    self.industryNettoDemand = \
                        pcr.max(0.0, \
                                pcr.cover( \
                                          vos.readPCRmapClone( \
                                              v                = nettoFileName, \
                                              cloneMapFileName = self.cloneMap, \
                                              tmpDir           = self.tmpDir), \
                                          0.0))
            else:
                self.industryGrossDemand = pcr.spatial(pcr.scalar(0.0))
                self.industryNettoDemand = pcr.spatial(pcr.scalar(0.0))
                logger.debug("Industry water demand is NOT included.")
            
            # gross and netto industrial water demand in m/day
            self.industryGrossDemand = pcr.cover(self.industryGrossDemand, 0.0)
            self.industryNettoDemand = pcr.cover(self.industryNettoDemand, 0.0)
            self.industryNettoDemand = pcr.min(self.industryGrossDemand, self.industryNettoDemand)  

            # return flow fraction
            self.industryReturnFlowFraction = pcr.max(0.0, 1.0 - vos.getValDivZero(self.industryNettoDemand, self.industryGrossDemand))



    def calculate_industrial_water_demand_for_date(self, currTimeStep):
        # TODO: We may want to calculate industry water demand on the fly (read_file = False)
        pass
