#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Ludovicus P. H. (Rens) van Beek, Edwin H. Sutanudjaja, Yoshihide Wada,
# Joyce H. C. Bosmans, Niels Drost, Inge E. M. de Graaf, Kor de Jong, Patricia Lopez Lopez,
# Stefanie Pessenteiner, Oliver Schmitz, Menno W. Straatsma, Niko Wanders, Dominik Wisser,
# and Marc F. P. Bierkens,
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
import math
import gc

import pcraster as pcr

import virtualOS as vos
import groundwater_MODFLOW

import logging
logger = logging.getLogger(__name__)

'''
Created on May 20, 2015

@author: Edwin H. Sutanudjaja
'''
class ModflowCoupling(object):
    
    def __init__(self, configuration, currTimeStep):
        self._configuration = configuration
        self._modelTime = currTimeStep
        
        pcr.setclone(configuration.cloneMap)

        # read the ldd map
        #~ self.lddMap = vos.netcdf2PCRobjCloneWithoutTime(configuration.modflowParameterOptions['channelNC'], 'lddMap',\
                                                        #~ configuration.cloneMap)
        if 'routingOptions' not in configuration.allSections: 
            configuration.routingOptions = {}
            configuration.routingOptions['lddMap'] = configuration.modflowParameterOptions['lddMap']
        self.lddMap = vos.readPCRmapClone(\
                  configuration.routingOptions['lddMap'],
                  configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'],True)
        # ensure ldd map is correct, and actually of type "ldd"
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
 
        # defining the landmask map
        if configuration.globalOptions['landmask'] != "None":
            self.landmask = vos.readPCRmapClone(\
            configuration.globalOptions['landmask'],
            configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'])
        else:
            self.landmask = pcr.defined(self.lddMap)
        
        # preparing the sub-model(s)         - Currently, there is only one sub-model. 
        self.createSubmodels()
         
    @property
    def configuration(self):
        return self._configuration
         
    def createSubmodels(self):

        # initializing sub modules
        self.modflow = groundwater_MODFLOW.GroundwaterModflow(self.configuration,\
                                                              self.landmask)
        
    def dumpState(self, outputDirectory, timeStamp = "Default"):

        state = self.getState()
        
        groundWaterState = state['groundwater']
        
        # time stamp used as part of the file name:
        if timeStamp == "Default": timeStamp = str(self._modelTime.fulldate) 
        
        for variable, map in groundWaterState.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             timeStamp+".map",\
             outputDirectory)

        for variable, map in groundWaterState.iteritems():
            vos.writePCRmapToDir(\
             pcr.ifthen(self.landmask, map),\
             str(variable)+"_"+
             timeStamp+".masked.map",\
             outputDirectory)

    def dumpGroundwaterDepth(self, outputDirectory, timeStamp = "Default"):

        depth = self.getGroundwaterDepth()
        
        groundWaterDepth = depth['groundwater_depth']
        
        # time stamp used as part of the file name:
        if timeStamp == "Default": timeStamp = str(self._modelTime.fulldate) 
        
        for variable, map in groundWaterDepth.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             timeStamp+".map",\
             outputDirectory)

        for variable, map in groundWaterDepth.iteritems():
            vos.writePCRmapToDir(\
             pcr.ifthen(self.landmask, map),\
             str(variable)+"_"+
             timeStamp+".masked.map",\
             outputDirectory)

    def dumpVariableValuesForPCRGLOBWB(self, outputDirectory, timeStamp = "Default"):

        variables = self.modflow.getVariableValuesForPCRGLOBWB()
        
        # time stamp used as part of the file name:
        if timeStamp == "Default": timeStamp = str(self._modelTime.fulldate) 
        
        for variable, map in variables.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             timeStamp+".map",\
             outputDirectory)

        # for a transient run with the coupled PCR-GLOBWB-MODFLOW, make an empty file to indicate that modflow files are ready
        if self._configuration.online_coupling_between_pcrglobwb_and_modflow and \
           self._configuration.steady_state_only == False:
            filename = outputDirectory+"/modflow_files_for_"+str(self._modelTime.fulldate)+"_are_ready.txt"
            if os.path.exists(filename): os.remove(filename)
            open(filename, "w").close()    

    def getState(self):
        result = {}
        result['groundwater'] = self.modflow.getState()
        
        return result
        
    def getGroundwaterDepth(self):
        result = {}
        result['groundwater_depth'] = self.modflow.getGroundwaterDepth()
        
        return result

    def update(self):
        
        msg  = "" + "\n\n"
        logger.info(msg)
        logger.info("Updating model for time %s", self._modelTime)
        msg  = "" + "\n\n"
        logger.info(msg)
        
        self.modflow.update(self._modelTime)

        # save/dump states at the end of the month or at the end of model simulation
        if self._modelTime.isLastDayOfMonth() or self._modelTime.isLastTimeStep():

            logger.info("Save or dump states to pcraster maps for time %s to the directory %s", self._modelTime, self._configuration.endStateDir)
            self.dumpState(self._configuration.endStateDir)

            logger.info("Save/dump some variables for PCR-GLOBWB simulation to pcraster maps to the directory %s", self._configuration.endStateDir)
            self.dumpVariableValuesForPCRGLOBWB(self._configuration.mapsDir)

    def get_initial_heads(self):
        logger.info("Get initial head values (based on a steady-state simulation or a pre-defined pcraster map.")
        
        self.modflow.get_initial_heads()

        # save/dump states used as the initial conditions 
        logger.info("Save/dump states of the initial conitions used to pcraster maps to the directory %s", self._configuration.endStateDir)
        self.dumpState(outputDirectory = self._configuration.endStateDir,\
                             timeStamp = self._configuration.globalOptions['startTime']+".ini")
                             

        # save/dump groundwater depth 
        logger.info("Save/dump groundwater depth maps to the directory %s", self._configuration.endStateDir)
        self.dumpGroundwaterDepth(outputDirectory = self._configuration.endStateDir,\
                                  timeStamp = self._configuration.globalOptions['startTime']+".ini")

        # save/dump some initial variables for PCR-GLOBWB
        if self._configuration.steady_state_only or self._configuration.modflowTransientInputOptions['usingPredefinedInitialHead'] == "False":
            logger.info("Save/dump some variables for PCR-GLOBWB simulation to pcraster maps to the directory %s", self._configuration.endStateDir)
            self.dumpVariableValuesForPCRGLOBWB(outputDirectory = self._configuration.mapsDir,\
                                                      timeStamp = self._configuration.globalOptions['startTime']+".ini")


