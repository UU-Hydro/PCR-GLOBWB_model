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
import types

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)


import virtualOS as vos

class WaterBodies(object):

    def __init__(self, iniItems, landmask, onlyNaturalWaterBodies = False):
        object.__init__(self)

        # clone map file names, temporary directory and global/absolute path of input directory
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
                
        # option to perform a run with only natural lakes (without reservoirs)
        self.onlyNaturalWaterBodies = onlyNaturalWaterBodies
        if self.onlyNaturalWaterBodies:
            logger.info("Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes.")
            self.onlyNaturalWaterBodies  = True
            self.dateForNaturalCondition = "1900-01-01"                  # The run for a natural condition should access only this date.   
        
        # netcdf file name for water bodies:
        self.useNetCDF = True
        self.ncFileInp = vos.getFullPath(iniItems.modflowParameterOptions['waterBodyInputNC'], self.inputDir)

        # minimum width (m) used in the weir formula  # TODO: define minWeirWidth based on the GLWD, GRanD database and/or bankfull discharge formula 
        self.minWeirWidth = 10.

    def getParameterFiles(self,date_given,cellArea,ldd):

        # parameters for Water Bodies: fracWat              
        #                              waterBodyIds
        #                              waterBodyOut
        #                              waterBodyArea 
        #                              waterBodyTyp
        #                              waterBodyCap
        
        # cell surface area (m2) and ldd
        self.cellArea = cellArea
        ldd = pcr.ifthen(self.landmask, ldd)
        
        # date and year used for accessing/extracting water body information
        date_used = date_given
        if self.onlyNaturalWaterBodies == True: date_used = self.dateForNaturalCondition
        year_used = date_used[0:4] 
        
        # fracWat = fraction of surface water bodies (dimensionless)
        self.fracWat = pcr.scalar(0.0)
        
        if self.useNetCDF:
            self.fracWat = vos.netcdf2PCRobjClone(self.ncFileInp,'fracWaterInp', \
                           date_used, useDoy = 'yearly',\
                           cloneMapFileName = self.cloneMap)
        self.fracWat = pcr.cover(self.fracWat, 0.0)
        self.fracWat = pcr.max(0.0,self.fracWat)
        self.fracWat = pcr.min(1.0,self.fracWat)
        
        self.waterBodyIds  = pcr.nominal(0)    # waterBody ids
        self.waterBodyOut  = pcr.boolean(0)    # waterBody outlets
        self.waterBodyArea = pcr.scalar(0.)    # waterBody surface areas

        # water body ids
        if self.useNetCDF:
            self.waterBodyIds = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyIds', \
                                date_used, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
        self.waterBodyIds = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            pcr.nominal(self.waterBodyIds))    

        # water body outlets (correcting outlet positions)
        wbCatchment = pcr.catchmenttotal(pcr.scalar(1),ldd)
        self.waterBodyOut = pcr.ifthen(wbCatchment ==\
                            pcr.areamaximum(wbCatchment, \
                            self.waterBodyIds),\
                            self.waterBodyIds) # = outlet ids           # This may give more than two outlets, particularly if there are more than one cells that have largest upstream areas      
        # - make sure that there is only one outlet for each water body 
        self.waterBodyOut = pcr.ifthen(\
                            pcr.areaorder(pcr.scalar(self.waterBodyOut), \
                            self.waterBodyOut) == 1., self.waterBodyOut)
        self.waterBodyOut = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            self.waterBodyOut)
        
        # TODO: Please also consider endorheic lakes!                    

        # correcting water body ids
        self.waterBodyIds = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            pcr.subcatchment(ldd,self.waterBodyOut))
        
        # boolean map for water body outlets:   
        self.waterBodyOut = pcr.ifthen(\
                            pcr.scalar(self.waterBodyOut) > 0.,\
                            pcr.boolean(1))

        # reservoir surface area (m2):
        if self.useNetCDF:
            resSfArea = 1000. * 1000. * \
                        vos.netcdf2PCRobjClone(self.ncFileInp,'resSfAreaInp', \
                        date_used, useDoy = 'yearly',\
                        cloneMapFileName = self.cloneMap)
        resSfArea = pcr.areaaverage(resSfArea,self.waterBodyIds)                        
        resSfArea = pcr.cover(resSfArea,0.)                        

        # water body surface area (m2): (lakes and reservoirs)
        self.waterBodyArea = pcr.max(pcr.areatotal(\
                             pcr.cover(\
                             self.fracWat*self.cellArea, 0.0), self.waterBodyIds),
                             pcr.areaaverage(\
                             pcr.cover(resSfArea, 0.0) ,       self.waterBodyIds))
        self.waterBodyArea = pcr.ifthen(self.waterBodyArea > 0.,\
                             self.waterBodyArea)
                                
        # correcting water body ids and outlets (exclude all water bodies with surfaceArea = 0)
        self.waterBodyIds = pcr.ifthen(self.waterBodyArea > 0.,
                            self.waterBodyIds)               
        self.waterBodyOut = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyOut)

        # water body types:
        # - 2 = reservoirs (regulated discharge)
        # - 1 = lakes (weirFormula)
        # - 0 = non lakes or reservoirs (e.g. wetland)
        self.waterBodyTyp = pcr.nominal(0)
        
        if self.useNetCDF:
            self.waterBodyTyp = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyTyp', \
                                date_used, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)

        # excluding wetlands (waterBodyTyp = 0) in all functions related to lakes/reservoirs 
        #
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyTyp) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.areamajority(self.waterBodyTyp,\
                                             self.waterBodyIds)     # choose only one type: either lake or reservoir                  
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyTyp) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyTyp)

        # correcting lakes and reservoirs ids and outlets
        self.waterBodyIds = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0,
                                                  self.waterBodyIds)               
        self.waterBodyOut = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0,
                                                  self.waterBodyOut)

        # reservoir maximum capacity (m3):
        self.resMaxCap = pcr.scalar(0.0)
        self.waterBodyCap = pcr.scalar(0.0)

        if self.useNetCDF:
            self.resMaxCap = 1000. * 1000. * \
                             vos.netcdf2PCRobjClone(self.ncFileInp,'resMaxCapInp', \
                             date_used, useDoy = 'yearly',\
                             cloneMapFileName = self.cloneMap)
        self.resMaxCap = pcr.ifthen(self.resMaxCap > 0,\
                                    self.resMaxCap)
        self.resMaxCap = pcr.areaaverage(self.resMaxCap,\
                                         self.waterBodyIds)
                                         
        # water body capacity (m3): (lakes and reservoirs)
        self.waterBodyCap = pcr.cover(self.resMaxCap,0.0)               # Note: Most of lakes have capacities > 0.
        self.waterBodyCap = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyCap)
                                               
        # correcting water body types:                                  # Reservoirs that have zero capacities will be assumed as lakes.
        self.waterBodyTyp = \
                 pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                       self.waterBodyTyp) 
        self.waterBodyTyp = pcr.ifthenelse(self.waterBodyCap > 0.,\
                                           self.waterBodyTyp,\
                 pcr.ifthenelse(pcr.scalar(self.waterBodyTyp) == 2,\
                                           pcr.nominal(1),\
                                           self.waterBodyTyp)) 

        # final corrections:
        self.waterBodyTyp = pcr.ifthen(self.waterBodyArea > 0.,\
                                       self.waterBodyTyp)                     # make sure that all lakes and/or reservoirs have surface areas
        self.waterBodyTyp = \
                 pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                       self.waterBodyTyp)                     # make sure that only types 1 and 2 will be considered in lake/reservoir functions
        self.waterBodyIds = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                            self.waterBodyIds)                                # make sure that all lakes and/or reservoirs have ids
        self.waterBodyOut = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.,\
                                                  self.waterBodyOut)          # make sure that all lakes and/or reservoirs have outlets
        
        
        # for a natural run (self.onlyNaturalWaterBodies == True) 
        # which uses only the year 1900, assume all reservoirs are lakes
        if self.onlyNaturalWaterBodies == True and date_used == self.dateForNaturalCondition:
            logger.info("Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes.")
            self.waterBodyTyp = \
             pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                        pcr.nominal(1))                         
        
        # check that all lakes and/or reservoirs have types, ids, surface areas and outlets:
        test = pcr.defined(self.waterBodyTyp) & pcr.defined(self.waterBodyArea) &\
               pcr.defined(self.waterBodyIds) & pcr.boolean(pcr.areamaximum(pcr.scalar(self.waterBodyOut), self.waterBodyIds))
        a,b,c = vos.getMinMaxMean(pcr.cover(pcr.scalar(test), 1.0) - pcr.scalar(1.0))
        threshold = 1e-3
        if abs(a) > threshold or abs(b) > threshold:
            logger.warning("Missing information in some lakes and/or reservoirs.")

        # cropping only in the landmask region:
        self.fracWat           = pcr.ifthen(self.landmask, self.fracWat         )
        self.waterBodyIds      = pcr.ifthen(self.landmask, self.waterBodyIds    ) 
        self.waterBodyOut      = pcr.ifthen(self.landmask, self.waterBodyOut    )
        self.waterBodyArea     = pcr.ifthen(self.landmask, self.waterBodyArea   )
        self.waterBodyTyp      = pcr.ifthen(self.landmask, self.waterBodyTyp    )  
        self.waterBodyCap      = pcr.ifthen(self.landmask, self.waterBodyCap    )
