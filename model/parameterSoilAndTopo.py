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

import pcraster as pcr
import virtualOS as vos

class SoilAndTopoParameters(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)

        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # How many soil layers (excluding groundwater):
        self.numberOfLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])

    def read(self, iniItems, optionDict = None):
        
        self.readTopo(iniItems, optionDict)
        self.readSoil(iniItems, optionDict)

    def readTopo(self, iniItems, optionDict):

        # a dictionary/section of options that will be used
        if optionDict == None: optionDict = iniItems.landSurfaceOptions

        # maps of elevation attributes: 
        topoParams = ['tanslope','slopeLength','orographyBeta']
        if optionDict['topographyNC'] == str(None):
            for var in topoParams:
                input = iniItems.landSurfaceOptions[str(var)]
                vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                self.tmpDir,self.inputDir)
                if var != "slopeLength": vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
        else:
            topoPropertiesNC = vos.getFullPath(\
                               optionDict['topographyNC'],
                                                self.inputDir)
            for var in topoParams:
                vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(\
                                    topoPropertiesNC,var, \
                                    cloneMapFileName = self.cloneMap)
                if var != "slopeLength": vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        #~ self.tanslope = pcr.max(self.tanslope, 0.00001)              # In principle, tanslope can be zero. Zero tanslope will provide zero TCL (no interflow)

        # covering slopeLength with its maximum value 
        self.slopeLength = pcr.cover(self.slopeLength, pcr.mapmaximum(self.slopeLength))
        
        # maps of relative elevation above flood plains 
        dzRel = ['dzRel0001','dzRel0005',
                 'dzRel0010','dzRel0020','dzRel0030','dzRel0040','dzRel0050',
                 'dzRel0060','dzRel0070','dzRel0080','dzRel0090','dzRel0100']
        if optionDict['topographyNC'] == str(None):
            for i in range(0, len(dzRel)):
                var = dzRel[i]
                input = optionDict[str(var)]
                vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                self.tmpDir,self.inputDir)
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                if i > 0: vars(self)[var] = pcr.max(vars(self)[var], vars(self)[dzRel[i-1]])
        else:
            for i in range(0, len(dzRel)):
                var = dzRel[i]
                vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(\
                                    topoPropertiesNC,var, \
                                    cloneMapFileName = self.cloneMap)
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                if i > 0: vars(self)[var] = pcr.max(vars(self)[var], vars(self)[dzRel[i-1]])

    def readSoilMapOfFAO(self, iniItems, optionDict = None):

        # a dictionary/section of options that will be used
        if optionDict == None: optionDict = iniItems.landSurfaceOptions
        
        # soil variable names given either in the ini or netCDF file:
        soilParameters = ['airEntryValue1','airEntryValue2',       
                          'poreSizeBeta1','poreSizeBeta2',        
                          'resVolWC1','resVolWC2',            
                          'satVolWC1','satVolWC2',
                          'KSat1','KSat2',
                          'percolationImp']
        if optionDict['soilPropertiesNC'] == str(None):
            for var in soilParameters:
                input = optionDict[str(var)]
                vars(self)[var] = \
                               vos.readPCRmapClone(input,self.cloneMap,\
                                             self.tmpDir,self.inputDir)
                vars(self)[var] = pcr.scalar(vars(self)[var])

                if input == "percolationImp": vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                
                # extrapolation 
                # - TODO: Make a general extrapolation option as a function in the virtualOS.py 
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 0.75))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        else:
            soilPropertiesNC = vos.getFullPath(\
                               optionDict['soilPropertiesNC'],
                                                self.inputDir)
            for var in soilParameters:
                vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(\
                                    soilPropertiesNC,var, \
                                    cloneMapFileName = self.cloneMap)

                if var == "percolationImp": vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

                # extrapolation 
                # - TODO: Make a general extrapolation option as a function in the virtualOS.py 
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 0.75))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))
                vars(self)[var] = pcr.cover(vars(self)[var],
                                  pcr.windowaverage(vars(self)[var], 1.00))

                vars(self)[var] = pcr.cover(vars(self)[var], 0.01)
            
        # make sure that resVolWC1 <= satVolWC1
        self.resVolWC1 = pcr.min(self.resVolWC1, self.satVolWC1)
        self.resVolWC2 = pcr.min(self.resVolWC2, self.satVolWC2)
        
        if self.numberOfLayers == 2:
            self.satVolMoistContUpp = self.satVolWC1                         # saturated volumetric moisture content (m3.m-3)
            self.satVolMoistContLow = self.satVolWC2
            self.resVolMoistContUpp = self.resVolWC1                         # residual volumetric moisture content (m3.m-3)
            self.resVolMoistContLow = self.resVolWC2
            self.airEntryValueUpp   = self.airEntryValue1                    # air entry value (m) according to soil water retention curve of Clapp & Hornberger (1978)
            self.airEntryValueLow   = self.airEntryValue2
            self.poreSizeBetaUpp    = self.poreSizeBeta1                     # pore size distribution parameter according to Clapp & Hornberger (1978) 
            self.poreSizeBetaLow    = self.poreSizeBeta2
            self.kSatUpp            = self.KSat1                             # saturated hydraulic conductivity (m.day-1) 
            self.kSatLow            = self.KSat2

        if self.numberOfLayers == 3:
            self.satVolMoistContUpp000005 = self.satVolWC1     
            self.satVolMoistContUpp005030 = self.satVolWC1     
            self.satVolMoistContLow030150 = self.satVolWC2
            self.resVolMoistContUpp000005 = self.resVolWC1     
            self.resVolMoistContUpp005030 = self.resVolWC1     
            self.resVolMoistContLow030150 = self.resVolWC2
            self.airEntryValueUpp000005   = self.airEntryValue1
            self.airEntryValueUpp005030   = self.airEntryValue1
            self.airEntryValueLow030150   = self.airEntryValue2
            self.poreSizeBetaUpp000005    = self.poreSizeBeta1 
            self.poreSizeBetaUpp005030    = self.poreSizeBeta1 
            self.poreSizeBetaLow030150    = self.poreSizeBeta2
            self.kSatUpp000005            = self.KSat1         
            self.kSatUpp005030            = self.KSat1         
            self.kSatLow030150            = self.KSat2

        self.percolationImp = pcr.cover(self.percolationImp, 0.0)            # fractional area where percolation to groundwater store is impeded (dimensionless)

        # soil thickness and storage variable names 
        # as given either in the ini or netCDF file:
        soilStorages = ['firstStorDepth',      'secondStorDepth',      
                        'soilWaterStorageCap1','soilWaterStorageCap2'] 
        if optionDict['soilPropertiesNC'] == str(None):
            for var in soilStorages:
                input = optionDict[str(var)]
                temp = str(var)+'Inp'
                vars(self)[temp] = vos.readPCRmapClone(input,\
                                            self.cloneMap,
                                            self.tmpDir,self.inputDir)

                # extrapolation 
                # - TODO: Make a general extrapolation option as a function in the virtualOS.py 
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 0.75))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp], 0.0)

        else:
            soilPropertiesNC = vos.getFullPath(\
                               optionDict['soilPropertiesNC'],
                                                self.inputDir)
            for var in soilStorages:
                temp = str(var)+'Inp'
                vars(self)[temp] = vos.netcdf2PCRobjCloneWithoutTime(\
                                     soilPropertiesNC,var, \
                                     cloneMapFileName = self.cloneMap)
                # extrapolation 
                # - TODO: Make a general extrapolation option as a function in the virtualOS.py 
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 0.75))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp],
                                   pcr.windowaverage(vars(self)[temp], 1.05))
                vars(self)[temp] = pcr.cover(vars(self)[temp], 0.0)

        # layer thickness
        if self.numberOfLayers == 2:
            self.thickUpp = (0.30/0.30)*self.firstStorDepthInp
            self.thickLow = (1.20/1.20)*self.secondStorDepthInp
        if self.numberOfLayers == 3:
            self.thickUpp000005 = (0.05/0.30)*self.firstStorDepthInp
            self.thickUpp005030 = (0.25/0.30)*self.firstStorDepthInp
            self.thickLow030150 = (1.20/1.20)*self.secondStorDepthInp

        # soil storage
        if self.numberOfLayers == 2:
            #~ self.storCapUpp = (0.30/0.30)*self.soilWaterStorageCap1Inp
            #~ self.storCapLow = (1.20/1.20)*self.soilWaterStorageCap2Inp                     # 22 Feb 2014: We can calculate this based on thickness and porosity. 
            self.storCapUpp = self.thickUpp * \
                             (self.satVolMoistContUpp - self.resVolMoistContUpp)
            self.storCapLow = self.thickLow * \
                             (self.satVolMoistContLow - self.resVolMoistContLow)
            self.rootZoneWaterStorageCap = self.storCapUpp + \
                                           self.storCapLow                                    # This is called as WMAX in the original pcrcalc script. 
        if self.numberOfLayers == 3:
            self.storCapUpp000005 = self.thickUpp000005 * \
                             (self.satVolMoistContUpp000005 - self.resVolMoistContUpp000005)
            self.storCapUpp005030 = self.thickUpp005030 * \
                             (self.satVolMoistContUpp005030 - self.resVolMoistContUpp005030)
            self.storCapLow030150 = self.thickLow030150 * \
                             (self.satVolMoistContLow030150 - self.resVolMoistContLow030150)
            self.rootZoneWaterStorageCap = self.storCapUpp000005 + \
                                           self.storCapUpp005030 + \
                                           self.storCapLow030150

    def readSoil(self, iniItems, optionDict = None):

        # a dictionary/section of options that will be used
        if optionDict == None: optionDict = iniItems.landSurfaceOptions

        # default values of soil parameters that are constant/uniform for the entire domain:
        self.clappAddCoeff   = pcr.scalar(3.0)        # dimensionless
        self.matricSuctionFC = pcr.scalar(1.0)        # unit: m
        #~ self.matricSuction50 = pcr.scalar(10./3.)  # unit: m
        self.matricSuction50 = pcr.scalar(3.33)       # unit: m
        self.matricSuctionWP = pcr.scalar(156.0)      # unit: m
        self.maxGWCapRise    = pcr.scalar(5.0)        # unit: m
        #  
        # values defined in the ini/configuration file:
        soilParameterConstants = ['clappAddCoeff',        
                                  'matricSuctionFC',      
                                  'matricSuction50',      
                                  'matricSuctionWP',      
                                  'maxGWCapRise']
        for var in soilParameterConstants:
            if var in list(iniItems.landSurfaceOptions.keys()):
                input = iniItems.landSurfaceOptions[str(var)]
                vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,\
                                                            self.tmpDir,self.inputDir)
        
        # read soil parameter based on the FAO soil map:
        self.readSoilMapOfFAO(iniItems, optionDict)                                 
       
        # assign Campbell's (1974) beta coefficient, as well as degree 
        # of saturation at field capacity and corresponding unsaturated hydraulic conductivity
        #
        if self.numberOfLayers == 2:

            self.campbellBetaUpp = self.poreSizeBetaUpp*2.0 + \
                                      self.clappAddCoeff                       # Campbell's (1974) coefficient ; Rens's line: BCB = 2*BCH + BCH_ADD
            self.campbellBetaLow = self.poreSizeBetaLow*2.0 + \
                                      self.clappAddCoeff                

            self.effSatAtFieldCapUpp = \
                     (self.matricSuctionFC / self.airEntryValueUpp)**\
                                        (-1.0/ self.poreSizeBetaUpp )          # saturation degree at field capacity       : THEFF_FC = (PSI_FC/PSI_A)**(-1/BCH)
            self.effSatAtFieldCapUpp = pcr.cover(self.effSatAtFieldCapUpp, 1.0)
            
            self.effSatAtFieldCapLow = \
                     (self.matricSuctionFC / self.airEntryValueLow)**\
                                        (-1.0/ self.poreSizeBetaLow )
            self.effSatAtFieldCapLow = pcr.cover(self.effSatAtFieldCapLow, 1.0)

            self.kUnsatAtFieldCapUpp = pcr.max(0., \
             (self.effSatAtFieldCapUpp ** self.campbellBetaUpp) * self.kSatUpp)  # unsaturated conductivity at field capacity: KTHEFF_FC = max(0,THEFF_FC[TYPE]**BCB*KS1)
            self.kUnsatAtFieldCapLow = pcr.max(0., \
             (self.effSatAtFieldCapLow ** self.campbellBetaLow) * self.kSatLow)
        #
        if self.numberOfLayers == 3:

            self.campbellBetaUpp000005 = self.poreSizeBetaUpp000005*2.0 + \
                                            self.clappAddCoeff
            self.campbellBetaUpp005030 = self.poreSizeBetaUpp005030*2.0 + \
                                            self.clappAddCoeff                
            self.campbellBetaLow030150 = self.poreSizeBetaLow030150*2.0 + \
                                            self.clappAddCoeff                

            self.effSatAtFieldCapUpp000005 = \
                     (self.matricSuctionFC / self.airEntryValueUpp000005)**\
                                        (-1.0/ self.poreSizeBetaUpp000005)
            self.effSatAtFieldCapUpp005030 = \
                     (self.matricSuctionFC / self.airEntryValueUpp005030)**\
                                        (-1.0/ self.poreSizeBetaUpp005030)
            self.effSatAtFieldCapLow030150 = \
                     (self.matricSuctionFC / self.airEntryValueLow030150)**\
                                        (-1.0/ self.poreSizeBetaLow030150)

            self.kUnsatAtFieldCapUpp000005 = pcr.max(0., \
             (self.effSatAtFieldCapUpp000005 ** self.campbellBetaUpp000005) * self.kSatUpp000005)
            self.kUnsatAtFieldCapUpp005030 = pcr.max(0., \
             (self.effSatAtFieldCapUpp005030 ** self.campbellBetaUpp005030) * self.kSatUpp005030)
            self.kUnsatAtFieldCapLow030150 = pcr.max(0., \
             (self.effSatAtFieldCapLow030150 ** self.campbellBetaLow030150) * self.kSatLow030150)

        # calculate degree of saturation at which transpiration is halved (50) 
        # and at wilting point
        #
        if self.numberOfLayers == 2:
            self.effSatAt50Upp = (self.matricSuction50/self.airEntryValueUpp)**\
                                                    (-1.0/self.poreSizeBetaUpp)
            self.effSatAt50Upp = pcr.cover(self.effSatAt50Upp, 1.0)                                        
            self.effSatAt50Low = (self.matricSuction50/self.airEntryValueLow)**\
                                                    (-1.0/self.poreSizeBetaLow)
            self.effSatAt50Low = pcr.cover(self.effSatAt50Low, 1.0)                                        
            self.effSatAtWiltPointUpp = pcr.cover(\
                                 (self.matricSuctionWP/self.airEntryValueUpp)**\
                                                    (-1.0/self.poreSizeBetaUpp), 1.0)
            self.effSatAtWiltPointLow = pcr.cover(\
                                 (self.matricSuctionWP/self.airEntryValueLow)**\
                                                    (-1.0/self.poreSizeBetaLow), 1.0)
        if self.numberOfLayers == 3:
            self.effSatAt50Upp000005 = (self.matricSuction50/self.airEntryValueUpp000005)**\
                                                          (-1.0/self.poreSizeBetaUpp000005)
            self.effSatAt50Upp005030 = (self.matricSuction50/self.airEntryValueUpp005030)**\
                                                          (-1.0/self.poreSizeBetaUpp005030)
            self.effSatAt50Low030150 = (self.matricSuction50/self.airEntryValueLow030150)**\
                                                          (-1.0/self.poreSizeBetaLow030150)
            self.effSatAtWiltPointUpp000005 = \
                                       (self.matricSuctionWP/self.airEntryValueUpp000005)**\
                                                          (-1.0/self.poreSizeBetaUpp000005)
            self.effSatAtWiltPointUpp005030 = \
                                       (self.matricSuctionWP/self.airEntryValueUpp005030)**\
                                                          (-1.0/self.poreSizeBetaUpp005030)
            self.effSatAtWiltPointLow030150 = \
                                       (self.matricSuctionWP/self.airEntryValueLow030150)**\
                                                          (-1.0/self.poreSizeBetaLow030150)

        # calculate interflow parameter (TCL): 
        #
        if self.numberOfLayers == 2:
            self.interflowConcTime = (self.kSatLow * self.tanslope*2.0) / \
                     (self.slopeLength * (1.- self.effSatAtFieldCapLow) * \
                    (self.satVolMoistContLow - self.resVolMoistContLow))    # TCL = Duration*(2*KS2*TANSLOPE)/(LSLOPE*(1-THEFF2_FC)*(THETASAT2-THETARES2))
        #
        if self.numberOfLayers == 3:
            self.interflowConcTime = (self.kSatLow030150 * self.tanslope*2.0) / \
                     (self.slopeLength * (1.-self.effSatAtFieldCapLow030150) * \
             (self.satVolMoistContLow030150 - self.resVolMoistContLow030150))
        
        self.interflowConcTime = pcr.max(0.0, pcr.cover(self.interflowConcTime, 0.0))     
