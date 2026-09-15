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
# TODO: FIX THIS, at this moment there is a link to virtualOS.py to the upper folder.
# ~ from .. import virtualOS as vos

from . import domestic_water_demand
from . import industry_water_demand
from . import livestock_water_demand
from . import manufacture_water_demand
from . import thermoelectric_water_demand
from . import irrigation_water_demand

import logging
logger = logging.getLogger(__name__)

class WaterDemand(object):

    def __init__(self, iniItems, landmask, landCoverTypeNames, landCoverObjects):
        object.__init__(self)
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # evaluate if sectors are consistent: Industry, Manufacturing and Thermoelectric
        if iniItems.waterDemandOptions['includeIndustryWaterDemand'] == "True" and \
           iniItems.waterDemandOptions['includeManufactureWaterDemand'] == "True" and \
           iniItems.waterDemandOptions['includeThermoelectricWaterDemand'] == "True":
            
            msg  = '\nIndustry, Manufacturing and Thermoelectric water use sectors are included in the calculations.\n'
            msg += 'Industrial demands already account for Manufacturing and Thermoelectric, thus water demands will be double counted.\n'
            msg += 'Set either "includeIndustryWaterDemand" to "False" or\n'
            msg += '           "includeManufactureWaterDemand" and "includeThermoelectricWaterDemand" to "False".'
            logger.warning(msg)
            sys.exit()
        
        # initiate non-irrigation sectoral water demand objects
        self.water_demand_domestic       = domestic_water_demand.DomesticWaterDemand(iniItems, self.landmask)
        self.water_demand_industry       = industry_water_demand.IndustryWaterDemand(iniItems, self.landmask)
        self.water_demand_livestock      = livestock_water_demand.LivestockWaterDemand(iniItems, self.landmask)
        self.water_demand_manufacture    = manufacture_water_demand.ManufactureWaterDemand(iniItems, self.landmask)
        self.water_demand_thermoelectric = thermoelectric_water_demand.ThermoelectricWaterDemand(iniItems, self.landmask)
        
        # initiate irrigation sectoral water demand objects
        # - for every irrigation land cover type
        self.water_demand_irrigation = {}
        self.coverTypes = landCoverTypeNames
        for coverType in self.coverTypes: 
            # - note loop will only be done for the land cover types that start with "irr" (irrigation)
            if coverType.startswith("irr"): self.water_demand_irrigation[coverType] = irrigation_water_demand.IrrigationWaterDemand(iniItems, coverType+str("Options"), self.landmask, landCoverObjects[coverType])


    def update(self, meteo, landSurface, groundwater, routing, currTimeStep):
        
        # get non irrigation demand (m)
        # - the content of this is based on the landSurface.py
        self.water_demand_domestic.update(currTimeStep)
        self.water_demand_industry.update(currTimeStep)
        self.water_demand_livestock.update(currTimeStep)
        self.water_demand_manufacture.update(currTimeStep)
        
        if routing.quality:
            self.water_demand_thermoelectric.update(currTimeStep, routing=routing, read_file=False)
        else:
            self.water_demand_thermoelectric.update(currTimeStep)
        
        # get irrigation demand (m)
        # - for every irrigation land cover type
        for coverType in self.coverTypes: 
            # - note loop will only be done for the land cover types that start with "irr" (irrigation)
            if coverType.startswith("irr"):
                # - the following will return irrGrossDemand in m per day
                self.water_demand_irrigation[coverType].update(meteo, landSurface, groundwater, routing, currTimeStep)
        
        # get irrigation demand in volume (m3)
        self.total_vol_irrigation_demand = pcr.scalar(0.0)
        for coverType in self.coverTypes: 
            if coverType.startswith("irr"):
                self.total_vol_irrigation_demand = self.total_vol_irrigation_demand + \
                                                   self.water_demand_irrigation[coverType].irrGrossDemand * routing.cellArea
