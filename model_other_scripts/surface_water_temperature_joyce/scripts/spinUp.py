#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import math
import logging

import pcraster as pcr

import virtualOS as vos

class SpinUp(object):

    def __init__(self, iniItems):
        object.__init__(self)
        
        self.noSpinUps      = None

        # How many soil layers (excluding groundwater):
        self.numberOfLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])

        self.setupConvergence(iniItems) 

    def setupConvergence(self,iniItems):

        self.noSpinUps         =   int(iniItems.globalOptions['maxSpinUpsInYears'])

        self.minConvForTotlSto = float(iniItems.globalOptions['minConvForTotlSto'])
        self.minConvForSoilSto = float(iniItems.globalOptions['minConvForSoilSto'])
        self.minConvForGwatSto = float(iniItems.globalOptions['minConvForGwatSto'])
        self.minConvForChanSto = float(iniItems.globalOptions['minConvForChanSto'])

        # TODO: including the convergence of ResvSto (reservoir storage)
        # self.minConvForResvSto = float(iniItems.globalOptions['minConvForResvSto'])
        
        self.iniLandSurface = {}
        # landCover types included in the simulation: 
        self.coverTypes = ["forest","grassland"]
        #
        if iniItems.landSurfaceOptions['includeIrrigation'] == "True":\
           self.coverTypes += ["irrPaddy","irrNonPaddy"] 
        for coverType in self.coverTypes:
            self.iniLandSurface[coverType] = None
        
        self.endStateDir = iniItems.endStateDir     

    def getIniStates(self,model):

        if self.numberOfLayers == 2: 
            
            self.iniSoilSto = max(1E-20,\
                              vos.getMapVolume(\
                              model.landSurface.topWaterLayer +\
                              model.landSurface.storUpp +\
                              model.landSurface.storLow +\
                              model.groundwater.storGroundwater,
                              model.routing.cellArea))            # unit: m3

        if self.numberOfLayers == 3: 
            
            self.iniSoilSto = max(1E-20,\
                              vos.getMapVolume(\
                              model.landSurface.topWaterLayer +\
                              model.landSurface.storUpp000005 +\
                              model.landSurface.storUpp005030 +\
                              model.landSurface.storLow030150 +\
                              model.groundwater.storGroundwater,
                              model.routing.cellArea))            # unit: m3


        self.iniGwatSto = max(1E-20,\
                          vos.getMapVolume(\
                          model.groundwater.storGroundwater,
                          model.routing.cellArea))                # unit: m3
        self.iniChanSto = max(1E-20,\
                          vos.getMapVolume(\
                          model.routing.channelStorage,1))
                                                                  # unit: m3
        self.iniTotlSto = max(1E-20,\
                          self.iniSoilSto + self.iniChanSto +\
                          vos.getMapVolume(\
                          model.landSurface.interceptStor +\
                          model.landSurface.snowFreeWater +\
                          model.landSurface.snowCoverSWE,
                          model.routing.cellArea))                # unit: m3

    def soilStorageVolume(self, state, cellAreaMap):

        if self.numberOfLayers == 2:\
        return vos.getMapVolume(\
                     state['landSurface']['topWaterLayer'] + state['landSurface']['storUpp'] +\
                                                           + state['landSurface']['storLow'] +\
                     state['groundwater']['storGroundwater'], cellAreaMap) # unit: m3

        if self.numberOfLayers == 3:\
        return vos.getMapVolume(\
                     state['landSurface']['topWaterLayer'] + state['landSurface']['storUpp000005'] +\
                     state['landSurface']['storUpp005030'] + state['landSurface']['storLow030150'] +\
                     state['groundwater']['storGroundwater'], cellAreaMap) # unit: m3
        
        
    def groundwaterStorageVolume(self, state, cellAreaMap):
        return vos.getMapVolume(state['groundwater']['storGroundwater'], cellAreaMap) # unit: m3
    
    def channelStorageVolume(self, state, cellAreaMap):
        return vos.getMapVolume(state['routing']['channelStorage'], cellAreaMap) # unit: m3
    
    def totalStorageVolume(self, state, cellAreaMap):
        return self.soilStorageVolume(state, cellAreaMap) + self.groundwaterStorageVolume(state, cellAreaMap) +\
            vos.getMapVolume(\
                     state['landSurface']['interceptStor'] +\
                     state['landSurface']['snowFreeWater'] +\
                     state['landSurface']['snowCoverSWE'],
                     cellAreaMap)             # unit: m3


    def checkConvergence(self,beginState, endState, spinUpRun, cellAreaMap):
        
        #calculate convergence of soil storage
        
        beginSoilSto = max(1E-20,self.soilStorageVolume(beginState, cellAreaMap))
        endSoilSto = self.soilStorageVolume(endState, cellAreaMap)
        
        convSoilSto = math.fabs(100*(endSoilSto-beginSoilSto)/beginSoilSto)
                    
        logging.getLogger('spinup').info('Delta SoilStorage = %.2f percent ; SpinUp No. %i of %i' \
                    %(convSoilSto, spinUpRun, self.noSpinUps)) 
        
        #calculate convergence of ground water storage
        
        beginGwatSto = max(1E-20,self.groundwaterStorageVolume(beginState, cellAreaMap))
        endGwatSto = self.groundwaterStorageVolume(endState, cellAreaMap)
        
        convGwatSto =  math.fabs(100*(endGwatSto-beginGwatSto)/beginGwatSto)
        
        logging.getLogger('spinup').info('Delta GwatStorage = %.2f percent' %(convGwatSto))
        
        #calculate convergence of channel storage
        
        beginChanSto = max(1E-20,self.channelStorageVolume(beginState, cellAreaMap))
        endChanSto = self.channelStorageVolume(endState, cellAreaMap)
          
        convChanSto = math.fabs(100*(endChanSto-beginChanSto)/beginChanSto)
        
        logging.getLogger('spinup').info('Delta ChanStorage = %.2f percent' \
                    %(convChanSto))

        #calculate convergence of total water storage

        beginTotlSto = max(1E-20,self.totalStorageVolume(beginState, cellAreaMap))
        endTotlSto = self.totalStorageVolume(endState, cellAreaMap)

        convTotlSto = math.fabs(100*(endTotlSto-beginTotlSto)/beginTotlSto)
         
        logging.getLogger('spinup').info('Delta TotlStorage = %.2f percent' \
                    %(convTotlSto))
        
        return convSoilSto <= self.minConvForSoilSto and  convGwatSto <= self.minConvForGwatSto\
           and convChanSto <= self.minConvForChanSto and convTotlSto <= self.minConvForTotlSto 
