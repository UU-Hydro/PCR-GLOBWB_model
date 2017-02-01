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
import glob
import shutil
import math

import pcraster as pcr

import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

class SpinUp(object):

    def __init__(self, iniItems):
        object.__init__(self)

        self.noSpinUps      = None

        # How many soil layers (excluding groundwater):
        self.numberOfLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])

        # option to save the netcdf files of the latest cycle of spin up runs:
        self.spinUpOutputDir = None
        if 'spinUpOutputDir' in iniItems.globalOptions.keys():
            self.outNCDir = str(iniItems.outNCDir)
            if iniItems.globalOptions['spinUpOutputDir'] not in ["None", "False"]:
                self.spinUpOutputDir = vos.getFullPath(iniItems.globalOptions['spinUpOutputDir'], self.outNCDir)
            if iniItems.globalOptions['spinUpOutputDir'] == "True":
                self.spinUpOutputDir = self.outNCDir + "/spin-up/"

        # setting up the convergence parameters
        self.setupConvergence(iniItems)

    def setupConvergence(self,iniItems):

        self.noSpinUps         =   int(iniItems.globalOptions['maxSpinUpsInYears'])

        self.minConvForTotlSto = float(iniItems.globalOptions['minConvForTotlSto'])
        self.minConvForSoilSto = float(iniItems.globalOptions['minConvForSoilSto'])
        self.minConvForGwatSto = float(iniItems.globalOptions['minConvForGwatSto'])
        self.minConvForChanSto = float(iniItems.globalOptions['minConvForChanSto'])

        # TODO: including the convergence of ResvSto (reservoir storage)
        # self.minConvForResvSto = float(iniItems.globalOptions['minConvForResvSto'])

        # directory for storing end states (format: pcraster maps)
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


    def checkConvergence(self, beginState, endState, spinUpRun, cellAreaMap):

        # calculate convergence of soil storage

        beginSoilSto = max(1E-20,self.soilStorageVolume(beginState, cellAreaMap))
        endSoilSto = self.soilStorageVolume(endState, cellAreaMap)

        convSoilSto = math.fabs(100*(endSoilSto-beginSoilSto)/beginSoilSto)

        logger.info('Delta SoilStorage = %.2f percent ; SpinUp No. %i of %i' \
                    %(convSoilSto, spinUpRun, self.noSpinUps))

        # calculate convergence of ground water storage

        beginGwatSto = max(1E-20,self.groundwaterStorageVolume(beginState, cellAreaMap))
        endGwatSto = self.groundwaterStorageVolume(endState, cellAreaMap)

        convGwatSto =  math.fabs(100*(endGwatSto-beginGwatSto)/beginGwatSto)

        logger.info('Delta GwatStorage = %.2f percent' %(convGwatSto))

        # calculate convergence of channel storage

        beginChanSto = max(1E-20,self.channelStorageVolume(beginState, cellAreaMap))
        endChanSto = self.channelStorageVolume(endState, cellAreaMap)

        convChanSto = math.fabs(100*(endChanSto-beginChanSto)/beginChanSto)

        logger.info('Delta ChanStorage = %.2f percent' \
                    %(convChanSto))

        # calculate convergence of total water storage

        beginTotlSto = max(1E-20,self.totalStorageVolume(beginState, cellAreaMap))
        endTotlSto = self.totalStorageVolume(endState, cellAreaMap)

        convTotlSto = math.fabs(100*(endTotlSto-beginTotlSto)/beginTotlSto)

        logger.info('Delta TotlStorage = %.2f percent' \
                    %(convTotlSto))

        if self.spinUpOutputDir != None:
            logger.info('Move all netcdf files resulted from the spin-up run to the spin-up directory: '+self.spinUpOutputDir)

            # cleaning up the spin-up directory:
            if os.path.exists(self.spinUpOutputDir): shutil.rmtree(self.spinUpOutputDir)
            os.makedirs(self.spinUpOutputDir)

            # move files
            for filename in glob.glob(os.path.join(self.outNCDir, '*.nc')):
                shutil.move(filename, self.spinUpOutputDir)

        return convSoilSto <= self.minConvForSoilSto and  convGwatSto <= self.minConvForGwatSto\
           and convChanSto <= self.minConvForChanSto and convTotlSto <= self.minConvForTotlSto
