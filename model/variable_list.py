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

'''
List of variables.

Created on July 7, 2014

@author: Edwin H. Sutanudjaja

eartH2Observe variables added
@editors: Ruud van der Ent, Rens van Beek

'''

netcdf_short_name = {}
netcdf_unit       = {}
netcdf_monthly_total_unit = {} 
netcdf_yearly_total_unit  = {}
netcdf_standard_name= {}
netcdf_long_name  = {}
description       = {}
comment           = {}
latex_symbol      = {}
pcr_short_name = {}     

# actualET
pcrglobwb_variable_name = 'actualET'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "eact"

# precipitation
pcrglobwb_variable_name = 'precipitation'
netcdf_short_name[pcrglobwb_variable_name] = 'precipitation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "pr"

# temperature
pcrglobwb_variable_name = 'temperature'
netcdf_short_name[pcrglobwb_variable_name] = 'temperature'
netcdf_unit[pcrglobwb_variable_name]       = 'degrees Celcius'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'mean_air_temperature'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "ta"

# referencePotET
pcrglobwb_variable_name = 'referencePotET'
netcdf_short_name[pcrglobwb_variable_name] = 'reference_potential_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "e0p"

# totalLandSurfacePotET
pcrglobwb_variable_name = 'totalLandSurfacePotET'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_potential_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'total_potential_evaporation_and_transpiration_at_land_surface'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Not including water bodies. Values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# totLandSurfaceActuaET
pcrglobwb_variable_name = 'totLandSurfaceActuaET'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_actual_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'total_actual_evaporation_and_transpiration_at_land_surface'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Not including water bodies. Values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# fractionLandSurfaceET
pcrglobwb_variable_name = 'fractionLandSurfaceET'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_evaporation_fraction'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'ratio_between_actual_and_potential_values_of_evaporation_and_transpiration_at_land_surface'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Not including water bodies.'
latex_symbol[pcrglobwb_variable_name]      = None

# interceptStor
pcrglobwb_variable_name = 'interceptStor'
netcdf_short_name[pcrglobwb_variable_name] = 'interception_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "intstor"

# snowCoverSWE 
pcrglobwb_variable_name = 'snowCoverSWE'
netcdf_short_name[pcrglobwb_variable_name] = 'snow_water_equivalent'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'snow_cover_in_water_equivalent_amount'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "snowcov"

# snowFreeWater
pcrglobwb_variable_name = 'snowFreeWater'
netcdf_short_name[pcrglobwb_variable_name] = 'snow_free_water'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'liquid_water_within_snowpack'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "snowliq"

# topWaterLayer
pcrglobwb_variable_name = 'topWaterLayer'
netcdf_short_name[pcrglobwb_variable_name] = 'top_water_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'water_layer_storage_above_soil'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storUppTotal 
pcrglobwb_variable_name = 'storUppTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'upper_soil_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'upper_soil_storage'       # first 30 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "sUpp"

# storUpp000005 
pcrglobwb_variable_name = 'storUpp000005'
netcdf_short_name[pcrglobwb_variable_name] = 'upper_soil_storage_5cm'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'upper_soil_storage_5cm'       # first 5 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storUpp005030 
pcrglobwb_variable_name = 'storUpp005030'
netcdf_short_name[pcrglobwb_variable_name] = 'upper_soil_storage_5_30cm'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'upper_soil_storage_5_30cm'       # from 5 to 30 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storLow030150 
pcrglobwb_variable_name = 'storLow030150'
netcdf_short_name[pcrglobwb_variable_name] = 'lower_soil_storage_30_150cm'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'lower_soil_storage_30_150cm'       # from 30 to 150 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storLowTotal 
pcrglobwb_variable_name = 'storLowTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'lower_soil_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'lower_soil_storage'       # next 30-150 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "sLow"

# interceptEvap       
pcrglobwb_variable_name = 'interceptEvap'
netcdf_short_name[pcrglobwb_variable_name] = 'interception_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'evaporation_from_interception_storage'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "int_evap"

# actSnowFreeWaterEvap
pcrglobwb_variable_name = 'actSnowFreeWaterEvap'
netcdf_short_name[pcrglobwb_variable_name] = 'snow_free_water_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'evaporation_from_liquid_water_within_snowpack'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "scf_evap"

# topWaterLayerEvap   
pcrglobwb_variable_name = 'topWaterLayerEvap'
netcdf_short_name[pcrglobwb_variable_name] = 'top_water_layer_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'evaporation_from_water_layer_storage_above_soil'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# actBareSoilEvap     
pcrglobwb_variable_name = 'actBareSoilEvap'
netcdf_short_name[pcrglobwb_variable_name] = 'bare_soil_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'actual_soil_evaporation'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "esact"

# actTranspiTotal     
pcrglobwb_variable_name = 'actTranspiTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'total_transpiration'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'total_plant_transpiration_from_entire_soil_storages'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "tact"

# actTranspiUppTotal
pcrglobwb_variable_name = 'actTranspiUppTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'upper_soil_transpiration'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'total_plant_transpiration_from_upper_soil_storage(s)'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "tactUpp"

# actTranspiLowTotal
pcrglobwb_variable_name = 'actTranspiLowTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'lower_soil_transpiration'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'total_plant_transpiration_from_lower_soil_storage'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "tactLow"

# directRunoff                    
pcrglobwb_variable_name = 'directRunoff'
netcdf_short_name[pcrglobwb_variable_name] = 'direct_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "qDr"

# interflowTotal                  
pcrglobwb_variable_name = 'interflowTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'interflow'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "qSf"

# baseflow                  
pcrglobwb_variable_name = 'baseflow'
netcdf_short_name[pcrglobwb_variable_name] = 'baseflow'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "qBf"

# infiltration                    
pcrglobwb_variable_name = 'infiltration'
netcdf_short_name[pcrglobwb_variable_name] = 'infiltration'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "infl"

# gwRecharge                      
pcrglobwb_variable_name = 'gwRecharge'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_recharge'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "negative values indicating (net) capillary rise from groundater store"
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "rch"

# gwNetCapRise                      
pcrglobwb_variable_name = 'gwNetCapRise'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_capillary_rise'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "values (positive) indicating (net) capillary rise from groundater store; only positive values given to the field."
latex_symbol[pcrglobwb_variable_name]      = None

# irrGrossDemand                  
pcrglobwb_variable_name = 'irrGrossDemand'
netcdf_short_name[pcrglobwb_variable_name] = 'irrigation_gross_demand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "not including water consumption for livestock"
latex_symbol[pcrglobwb_variable_name]      = None

# irrGrossDemandVolume                  
pcrglobwb_variable_name = 'irrGrossDemandVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'irrigation_gross_demand_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "not including water consumption for livestock"
latex_symbol[pcrglobwb_variable_name]      = None

# nonIrrGrossDemand                  
pcrglobwb_variable_name = 'nonIrrGrossDemand'
netcdf_short_name[pcrglobwb_variable_name] = 'non_irrigation_gross_demand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# nonIrrGrossDemandVolume                  
pcrglobwb_variable_name = 'nonIrrGrossDemandVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'non_irrigation_gross_demand_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalGrossDemand                  
pcrglobwb_variable_name = 'totalGrossDemand'
netcdf_short_name[pcrglobwb_variable_name] = 'total_gross_demand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalGrossDemandVolume                  
pcrglobwb_variable_name = 'totalGrossDemandVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'total_gross_demand_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# satDegUpp                       
pcrglobwb_variable_name = 'satDegUpp'
netcdf_short_name[pcrglobwb_variable_name] = 'upper_soil_saturation_degree'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# satDegLow                       
pcrglobwb_variable_name = 'satDegLow'
netcdf_short_name[pcrglobwb_variable_name] = 'lower_soil_saturation_degree'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storGroundwater                 
pcrglobwb_variable_name = 'storGroundwater'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'non_fossil_groundwater_storage'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "sGw"

# storGroundwaterFossil                 
pcrglobwb_variable_name = 'storGroundwaterFossil'
netcdf_short_name[pcrglobwb_variable_name] = 'fossil_groundwater_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# storGroundwaterTotal                 
pcrglobwb_variable_name = 'storGroundwaterTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'total_groundwater_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Non fossil and fossil groundwater storage.'
latex_symbol[pcrglobwb_variable_name]      = None

# surfaceWaterAbstraction         
pcrglobwb_variable_name = 'surfaceWaterAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'surface_water_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# surfaceWaterAbstractionVolume
pcrglobwb_variable_name = 'surfaceWaterAbstractionVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'surface_water_abstraction_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# nonFossilGroundwaterAbstraction 
pcrglobwb_variable_name = 'nonFossilGroundwaterAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'non_fossil_groundwater_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# fossilGroundwaterAbstraction     
pcrglobwb_variable_name = 'fossilGroundwaterAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'fossil_groundwater_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalGroundwaterAbstraction
pcrglobwb_variable_name = 'totalGroundwaterAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'total_groundwater_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Non fossil and fossil groundwater abstraction.'
latex_symbol[pcrglobwb_variable_name]      = None

# totalGroundwaterAbstractionVolume
pcrglobwb_variable_name = 'totalGroundwaterAbstractionVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'total_groundwater_abstraction_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Non fossil and fossil groundwater abstraction.'
latex_symbol[pcrglobwb_variable_name]      = None

# desalinationAbstraction
pcrglobwb_variable_name = 'desalinationAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'desalination_source_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# desalinationAbstractionVolume
pcrglobwb_variable_name = 'desalinationAbstractionVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'desalination_source_abstraction_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalAbstraction
pcrglobwb_variable_name = 'totalAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'total_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = "Total abstraction from all water sources: surface water, non fossil groundwater and other water sources (e.g. fossil groundwater, desalinisation)."
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# fracSurfaceWaterAllocation
pcrglobwb_variable_name = 'fracSurfaceWaterAllocation'
netcdf_short_name[pcrglobwb_variable_name] = 'fraction_of_surface_water_allocation'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Values equal to 1 indicate either 100% allocation (from surface water) or zero water demand."
latex_symbol[pcrglobwb_variable_name]      = None

# fracNonFossilGroundwaterAllocation
pcrglobwb_variable_name = 'fracNonFossilGroundwaterAllocation'
netcdf_short_name[pcrglobwb_variable_name] = 'fraction_of_non_fossil_groundwater_allocation'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Values equal to 0 indicate either zero allocation or zero water demand."
latex_symbol[pcrglobwb_variable_name]      = None

# fracOtherWaterSourceAllocation
pcrglobwb_variable_name = 'fracOtherWaterSourceAllocation'
netcdf_short_name[pcrglobwb_variable_name] = 'fraction_of_other_water_source_allocation'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Values equal to 0 indicate either zero allocation or zero water demand."
latex_symbol[pcrglobwb_variable_name]      = None

# fracDesalinatedWaterAllocation
pcrglobwb_variable_name = 'fracDesalinatedWaterAllocation'
netcdf_short_name[pcrglobwb_variable_name] = 'fraction_of_desalinated_water_allocation'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Values equal to 0 indicate either zero allocation or zero water demand."
latex_symbol[pcrglobwb_variable_name]      = None

# totalFracWaterSourceAllocation
pcrglobwb_variable_name = 'totalFracWaterSourceAllocation'
netcdf_short_name[pcrglobwb_variable_name] = 'total_fraction_water_allocation'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "All values must be equal to 1. Otherwise, water balance errors."
latex_symbol[pcrglobwb_variable_name]      = None

# waterBodyActEvaporation
pcrglobwb_variable_name = 'waterBodyActEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'water_body_actual_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only over surface water body fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# waterBodyPotEvaporation
pcrglobwb_variable_name = 'waterBodyPotEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'water_body_potential_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only over surface water body fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# fractionWaterBodyEvaporation
pcrglobwb_variable_name = 'fractionWaterBodyEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'water_body_evaporation_fraction'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'ratio_between_actual_and_potential_values_of_evaporation_and_transpiration_at_surface_water_bodies'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalEvaporation
pcrglobwb_variable_name = 'totalEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'total_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Including from water bodies.'
latex_symbol[pcrglobwb_variable_name]      = None

# fractionTotalEvaporation
pcrglobwb_variable_name = 'fractionTotalEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'total_evaporation_fraction'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'ratio_between_actual_and_potential_values_of_total_evaporation'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Including from water bodies.'
latex_symbol[pcrglobwb_variable_name]      = None

# runoff
pcrglobwb_variable_name = 'runoff'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "direct_runoff + interflow + baseflow, but not including local runoff from water bodies."
latex_symbol[pcrglobwb_variable_name]      = None
pcr_short_name[pcrglobwb_variable_name]    = "qLoc"

# accuRunoff
pcrglobwb_variable_name = 'accuRunoff'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_land_surface_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "direct_runoff + interflow + baseflow, but not including local runoff from water bodies."
latex_symbol[pcrglobwb_variable_name]      = None

# accuDirectRunoff
pcrglobwb_variable_name = 'accuDirectRunoff'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_land_surface_direct_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuInterflowTotal
pcrglobwb_variable_name = 'accuInterflowTotal'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_land_surface_total_interflow'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuBaseflow
pcrglobwb_variable_name = 'accuBaseflow'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_land_surface_baseflow'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuNetGroundwaterDischarge
pcrglobwb_variable_name = 'accuNetGroundwaterDischarge'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_net_groundwater_discharge'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'accumulated_net_groundwater_discharge_along_the_drainage_network'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Positive values indicating fluxes leaving groundwater bodies. Including (negative) surface water infiltration to groundwater."
latex_symbol[pcrglobwb_variable_name]      = None

# accuSurfaceWaterAbstraction
pcrglobwb_variable_name = 'accuSurfaceWaterAbstraction'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_surface_water_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuWaterBodyActEvaporation
pcrglobwb_variable_name = 'accuWaterBodyActEvaporation'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_water_body_actual_evaporation'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuNonIrrReturnFlow                  
pcrglobwb_variable_name = 'accuNonIrrReturnFlow'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_return_flow_from_non_irrigation_demand_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuStorGroundwaterTotalVolume
pcrglobwb_variable_name = 'accuStorGroundwaterTotalVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_total_groundwater_storage_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Total groundwater storage volume.'
latex_symbol[pcrglobwb_variable_name]      = None

# discharge
pcrglobwb_variable_name = 'discharge'
netcdf_short_name[pcrglobwb_variable_name] = 'discharge'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalRunoff
pcrglobwb_variable_name = 'totalRunoff'
netcdf_short_name[pcrglobwb_variable_name] = 'total_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Including local changes at water bodies."
latex_symbol[pcrglobwb_variable_name]      = None

# local_water_body_flux
pcrglobwb_variable_name = 'local_water_body_flux'
netcdf_short_name[pcrglobwb_variable_name] = 'local_water_body_flux'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# accuTotalRunoff
pcrglobwb_variable_name = 'accuTotalRunoff'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_total_surface_runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Including runoff from water bodies."
latex_symbol[pcrglobwb_variable_name]      = None

# net_liquid_water_to_soil
pcrglobwb_variable_name = 'net_liquid_water_to_soil'
netcdf_short_name[pcrglobwb_variable_name] = 'net_liquid_water_to_soil'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# totalActiveStorageThickness
pcrglobwb_variable_name = 'totalActiveStorageThickness'
netcdf_short_name[pcrglobwb_variable_name] = 'total_thickness_of_active_water_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Not including fossil groundwater."
latex_symbol[pcrglobwb_variable_name]      = None

# totalWaterStorageThickness
pcrglobwb_variable_name = 'totalWaterStorageThickness'
netcdf_short_name[pcrglobwb_variable_name] = 'total_thickness_of_water_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Including fossil groundwater."
latex_symbol[pcrglobwb_variable_name]      = None

# totalWaterStorageVolume
pcrglobwb_variable_name = 'totalWaterStorageVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'total_volume_of_water_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Including fossil groundwater."
latex_symbol[pcrglobwb_variable_name]      = None

# surfaceWaterStorage
pcrglobwb_variable_name = 'surfaceWaterStorage'
netcdf_short_name[pcrglobwb_variable_name] = 'surface_water_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Negative values may be reported, due to excessive demands.'
latex_symbol[pcrglobwb_variable_name]      = None

# waterBodyStorage 
pcrglobwb_variable_name = 'waterBodyStorage'
netcdf_short_name[pcrglobwb_variable_name] = 'lake_and_reservoir_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'The values given are for every lake and reservoir ids (not per cells) and after lake/reservoir releases/outflows.'
latex_symbol[pcrglobwb_variable_name]      = None

# channelStorage 
pcrglobwb_variable_name = 'channelStorage'
netcdf_short_name[pcrglobwb_variable_name] = 'channel_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# snowMelt
pcrglobwb_variable_name = 'snowMelt'
netcdf_short_name[pcrglobwb_variable_name] = 'snow_melt'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# satDegUppSurface                       
pcrglobwb_variable_name = 'satDegUppSurface'
netcdf_short_name[pcrglobwb_variable_name] = 'near_surface_soil_saturation_degree'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'This variable can only be reported if 3 layer soil model is used.'
latex_symbol[pcrglobwb_variable_name]      = None

# storUppSurface 
pcrglobwb_variable_name = 'storUppSurface'
netcdf_short_name[pcrglobwb_variable_name] = 'near_surface_soil_storage'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None                       # first 5 cm of soil
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'This variable can only be reported if 3 layer soil model is used.'
latex_symbol[pcrglobwb_variable_name]      = None

# nonIrrWaterConsumption                  
pcrglobwb_variable_name = 'nonIrrWaterConsumption'
netcdf_short_name[pcrglobwb_variable_name] = 'consumptive_water_use_for_non_irrigation_demand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# nonIrrReturnFlow                  
pcrglobwb_variable_name = 'nonIrrReturnFlow'
netcdf_short_name[pcrglobwb_variable_name] = 'return_flow_from_non_irrigation_demand_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# irrWaterConsumption                  
pcrglobwb_variable_name = 'irrWaterConsumption'
netcdf_short_name[pcrglobwb_variable_name] = 'consumptive_water_use_for_irrigation_demand'
netcdf_unit[pcrglobwb_variable_name]       = None
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# irrReturnFlow                  
pcrglobwb_variable_name = 'irrReturnFlow'
netcdf_short_name[pcrglobwb_variable_name] = 'return_flow_from_irrigation_demand_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = None
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# land_surface_water_balance                  
pcrglobwb_variable_name = 'land_surface_water_balance'
netcdf_short_name[pcrglobwb_variable_name] = 'land_surface_water_balance'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Excluding surface water bodies.'
latex_symbol[pcrglobwb_variable_name]      = None

# fraction_of_surface_water
pcrglobwb_variable_name = 'dynamicFracWat'
netcdf_short_name[pcrglobwb_variable_name] = 'fraction_of_surface_water'
netcdf_unit[pcrglobwb_variable_name]       = '1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Fraction of surface water over the cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# totalPotentialMaximumGrossDemand
pcrglobwb_variable_name = 'totalPotentialMaximumGrossDemand'
netcdf_short_name[pcrglobwb_variable_name] = 'totalPotentialMaximumGrossDemand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "NOT considering water availability, pumping capacity, etc."
latex_symbol[pcrglobwb_variable_name]      = None

# totalPotentialMaximumIrrGrossDemand
pcrglobwb_variable_name = 'totalPotentialMaximumIrrGrossDemand'
netcdf_short_name[pcrglobwb_variable_name] = 'totalPotentialMaximumIrrGrossDemand'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "NOT considering water availability, pumping capacity, etc."
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterAbsReturnFlow
pcrglobwb_variable_name = 'groundwaterAbsReturnFlow'
netcdf_short_name[pcrglobwb_variable_name] = 'return_flow_from_groundwater_abstraction'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'return_flow_from_groundwater_abstraction'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# surfaceWaterInf
pcrglobwb_variable_name = 'surfaceWaterInf'
netcdf_short_name[pcrglobwb_variable_name] = 'surface_water_infiltration'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'surface_water_infiltration_to_groundwater'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# netGroundwaterDischarge
pcrglobwb_variable_name = 'netGroundwaterDischarge'
netcdf_short_name[pcrglobwb_variable_name] = 'net_groundwater_discharge'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = 'net_groundwater_discharge'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Positive values indicating fluxes leaving groundwater bodies. Including (negative) surface water infiltration to groundwater."
latex_symbol[pcrglobwb_variable_name]      = None

# irrigationTranspiration
pcrglobwb_variable_name = 'irrigationTranspiration'
netcdf_short_name[pcrglobwb_variable_name] = 'transpiration_from_irrigation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# floodDepth
pcrglobwb_variable_name = 'floodDepth'
netcdf_short_name[pcrglobwb_variable_name] = 'flood_innundation_depth'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flood innundation depth above the channel flood plain. Not including flood overtopping reservoirs and lakes.'
latex_symbol[pcrglobwb_variable_name]      = None

# floodVolume
pcrglobwb_variable_name = 'floodVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'flood_innundation_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flood innundation volume above the channel storage capacity. Not including flood overtopping reservoirs and lakes.'
latex_symbol[pcrglobwb_variable_name]      = None

# surfaceWaterLevel
pcrglobwb_variable_name = 'surfaceWaterLevel'
netcdf_short_name[pcrglobwb_variable_name] = 'surface_water_level'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Estimate of surface/river water levels within surface water bodies (above channel bottom elevations).'
latex_symbol[pcrglobwb_variable_name]      = None

# irrPaddyWaterWithdrawal
pcrglobwb_variable_name = 'irrPaddyWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'paddy_irrigation_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# irrNonPaddyWaterWithdrawal
pcrglobwb_variable_name = 'irrNonPaddyWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'non_paddy_irrigation_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# irrigationWaterWithdrawal 
pcrglobwb_variable_name = 'irrigationWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'irrigation_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# domesticWaterWithdrawal   
pcrglobwb_variable_name = 'domesticWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'domestic_water_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# industryWaterWithdrawal
pcrglobwb_variable_name = 'industryWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'industry_water_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# livestockWaterWithdrawal  
pcrglobwb_variable_name = 'livestockWaterWithdrawal'
netcdf_short_name[pcrglobwb_variable_name] = 'livestock_water_withdrawal'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area.'
latex_symbol[pcrglobwb_variable_name]      = None

# domesticWaterWithdrawalVolume
pcrglobwb_variable_name = 'domesticWaterWithdrawalVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# industryWaterWithdrawalVolume
pcrglobwb_variable_name = 'industryWaterWithdrawalVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# livestockWaterWithdrawalVolume
pcrglobwb_variable_name = 'livestockWaterWithdrawalVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# irrigationWaterWithdrawalVolume
pcrglobwb_variable_name = 'irrigationWaterWithdrawalVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# domesticWaterConsumptionVolume
pcrglobwb_variable_name = 'domesticWaterConsumptionVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# industryWaterConsumptionVolume
pcrglobwb_variable_name = 'industryWaterConsumptionVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# livestockWaterConsumptionVolume
pcrglobwb_variable_name = 'livestockWaterConsumptionVolume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# precipitation_at_irrigation
pcrglobwb_variable_name = 'precipitation_at_irrigation'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# evaporation_from_irrigation
pcrglobwb_variable_name = 'evaporation_from_irrigation'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# netLqWaterToSoil_at_irrigation
pcrglobwb_variable_name = 'netLqWaterToSoil_at_irrigation'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# transpiration_from_irrigation
pcrglobwb_variable_name = 'transpiration_from_irrigation'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# precipitation_at_irrigation_volume
pcrglobwb_variable_name = 'precipitation_at_irrigation_volume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# evaporation_from_irrigation_volume
pcrglobwb_variable_name = 'evaporation_from_irrigation_volume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# netLqWaterToSoil_at_irrigation_volume
pcrglobwb_variable_name = 'netLqWaterToSoil_at_irrigation_volume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# transpiration_from_irrigation_volume
pcrglobwb_variable_name = 'transpiration_from_irrigation_volume'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm3.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm3.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# lake_and_reservoir_inflow (m3/s)
pcrglobwb_variable_name = 'lake_and_reservoir_inflow'
netcdf_short_name[pcrglobwb_variable_name] = pcrglobwb_variable_name
netcdf_unit[pcrglobwb_variable_name]       = 'm3.s'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None



#############################################################################################################
# MODFLOW variable lists (below)
#############################################################################################################

# groundwaterHeadLayer1                      
pcrglobwb_variable_name = 'groundwaterHeadLayer1'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_head_for_layer_1'
netcdf_unit[pcrglobwb_variable_name]       = 'm.'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterHeadLayer2                      
pcrglobwb_variable_name = 'groundwaterHeadLayer2'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_head_for_layer_2'
netcdf_unit[pcrglobwb_variable_name]       = 'm.'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterDepthLayer1                      
pcrglobwb_variable_name = 'groundwaterDepthLayer1'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_depth_for_layer_1'
netcdf_unit[pcrglobwb_variable_name]       = 'm.'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterDepthLayer2                      
pcrglobwb_variable_name = 'groundwaterDepthLayer2'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_depth_for_layer_2'
netcdf_unit[pcrglobwb_variable_name]       = 'm.'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterHead                      
pcrglobwb_variable_name = 'groundwaterHead'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_head_for_top_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm.'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterDepth                      
pcrglobwb_variable_name = 'groundwaterDepth'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_depth_for_top_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# relativeGroundwaterHead
pcrglobwb_variable_name = 'relativeGroundwaterHead'
netcdf_short_name[pcrglobwb_variable_name] = 'relativeGroundwaterHead'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterVolumeEstimate
pcrglobwb_variable_name = 'groundwaterVolumeEstimate'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_volume_estimate'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Note that the calculated values are until a certain aquifer/layer bottom elevation. Please check the assumption. Values can be negative."
latex_symbol[pcrglobwb_variable_name]      = None

# accuGroundwaterVolumeEstimate
pcrglobwb_variable_name = 'accuGroundwaterVolumeEstimate'
netcdf_short_name[pcrglobwb_variable_name] = 'accumulated_total_groundwater_storage_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = 'accumulated_total_groundwater_storage_volume_based_on_modflow'
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Total groundwater storage volume (based on MODFLOW).'
latex_symbol[pcrglobwb_variable_name]      = None

# groundwaterThicknessEstimate
pcrglobwb_variable_name = 'groundwaterThicknessEstimate'
netcdf_short_name[pcrglobwb_variable_name] = 'groundwater_thickness_estimate'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Note that the calculated values are until a certain aquifer/layer bottom elevation. Please check the assumption. Values can be negative."
latex_symbol[pcrglobwb_variable_name]      = None

# top_uppermost_layer (for two layer model)  
pcrglobwb_variable_name = 'top_uppermost_layer'
netcdf_short_name[pcrglobwb_variable_name] = 'top_elevation_of_uppermost_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Zero elevation values indicate mean sea level."
latex_symbol[pcrglobwb_variable_name]      = None

# bottom_uppermost_layer (for two layer model)
pcrglobwb_variable_name = 'bottom_uppermost_layer'
netcdf_short_name[pcrglobwb_variable_name] = 'bottom_elevation_of_uppermost_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Zero elevation values indicate mean sea level. This elevation is also the top_elevation_of_lowermost_layer."
latex_symbol[pcrglobwb_variable_name]      = None

# bottom_lowermost_layer (for two layer model)
pcrglobwb_variable_name = 'bottom_lowermost_layer'
netcdf_short_name[pcrglobwb_variable_name] = 'bottom_elevation_of_lowermost_layer'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Zero elevation values indicate mean sea level."
latex_symbol[pcrglobwb_variable_name]      = None

# test variable
pcrglobwb_variable_name = 'test'
netcdf_short_name[pcrglobwb_variable_name] = 'test'
netcdf_unit[pcrglobwb_variable_name]       = 'undefined'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None


#############################################################################################################
# eartH2Observe
#############################################################################################################
# RvB 23/02/2017 : start of edits 
# eartH2Observe variables added
#%% E2O - EartH2Oserve variables

#%% Water balance components

# Precip
pcrglobwb_variable_name = 'Precip'
netcdf_short_name[pcrglobwb_variable_name] = 'Precip'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'precipitation_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'total precipitation'
description[pcrglobwb_variable_name]       = 'Average of total precipitation (Rainf+Snowf), positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# Evap
pcrglobwb_variable_name = 'Evap'
netcdf_short_name[pcrglobwb_variable_name] = 'Evap'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'water_evaporation_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'total evatranpiration'
description[pcrglobwb_variable_name]       = 'Sum of all evaporation sources, averaged over a grid cell, positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# Runoff
pcrglobwb_variable_name = 'Runoff'
netcdf_short_name[pcrglobwb_variable_name] = 'Runoff'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'runoff_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'Total runoff'
description[pcrglobwb_variable_name]       = 'Average total liquid water draining from land'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# Qs
pcrglobwb_variable_name = 'Qs'
netcdf_short_name[pcrglobwb_variable_name] = 'Qs'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'surface_runoff_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'surface runoff'
description[pcrglobwb_variable_name]       = 'Runoff from the land surface and/or subsurface stormflow'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# Qsb
pcrglobwb_variable_name = 'Qsb'
netcdf_short_name[pcrglobwb_variable_name] = 'Qsb'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'subsurface_runoff_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'Subsurface runoff'
description[pcrglobwb_variable_name]       = 'Gravity drainage and/or slow response lateral flow.'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

# Qsm
pcrglobwb_variable_name = 'Qsm'
netcdf_short_name[pcrglobwb_variable_name] = 'Qsm'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'surface_snow_melt_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'snowmelt'
description[pcrglobwb_variable_name]       = 'Average liquid water generated from solid to liquid phase change in the snow'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#PotEvap
pcrglobwb_variable_name = 'PotEvap'
netcdf_short_name[pcrglobwb_variable_name] = 'PotEvap'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'water_potential_evaporation_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'potential evapotranspiration'
description[pcrglobwb_variable_name]       = 'The flux as computed for evapotranspiration but will all resistances set to zero, except the aerodynamic resistance, positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#ECanop
pcrglobwb_variable_name = 'ECanop'
netcdf_short_name[pcrglobwb_variable_name] = 'ECanop'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'water_evaporation_flux_from_canopy'
netcdf_long_name[pcrglobwb_variable_name]  = 'interception evaporation'
description[pcrglobwb_variable_name]       = 'Evaporation from canopy interception, averaged over all vegetation types within a grid cell, positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#TVeg
pcrglobwb_variable_name = 'TVeg'
netcdf_short_name[pcrglobwb_variable_name] = 'TVeg'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'transpiration_flux'
netcdf_long_name[pcrglobwb_variable_name]  = 'vegetation transpiration'
description[pcrglobwb_variable_name]       = 'Vegetation transpiration, averaged over all vegetation types within a grid cell, positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#ESoil
pcrglobwb_variable_name = 'ESoil'
netcdf_short_name[pcrglobwb_variable_name] = 'ESoil'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'water_evaporation_flux_from_soil'
netcdf_long_name[pcrglobwb_variable_name]  = 'bare soil evaporation'
description[pcrglobwb_variable_name]       = 'Evaporation from bare soil, positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#EWater
pcrglobwb_variable_name = 'EWater'
netcdf_short_name[pcrglobwb_variable_name] = 'EWater'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Open water evaporation'
description[pcrglobwb_variable_name]       = 'Evaporation from surface water storage (lakes, river Chanel, floodplains, etc.), positive downwards'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#RivOut
pcrglobwb_variable_name = 'RivOut'
netcdf_short_name[pcrglobwb_variable_name] = 'RivOut'
netcdf_unit[pcrglobwb_variable_name]       = 'm3 s-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'river discharge'
description[pcrglobwb_variable_name]       = 'Water volume leaving the cell, positive downstream'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#%% State variables

#SWE
pcrglobwb_variable_name = 'SWE'
netcdf_short_name[pcrglobwb_variable_name] = 'SWE'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'liquid_water_content_of_surface_snow'
netcdf_long_name[pcrglobwb_variable_name]  = 'Snow water equivalent'
description[pcrglobwb_variable_name]       = 'Total water mass of the snowpack (liquid or frozen), averaged over a grid cell'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#CanopInt
pcrglobwb_variable_name = 'CanopInt'
netcdf_short_name[pcrglobwb_variable_name] = 'SWE'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Total canopy water storage'
description[pcrglobwb_variable_name]       = 'Total canopy interception, averaged over all vegetation types within a grid cell (included both solid and liquid)'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#SurfStor
pcrglobwb_variable_name = 'SurfStor'
netcdf_short_name[pcrglobwb_variable_name] = 'SurfStor'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Surface Water Storage'
description[pcrglobwb_variable_name]       = 'Total liquid water storage, other than soil, snow or interception storage (i.e. lakes, river channel or depression storage).'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#SurfMoist
pcrglobwb_variable_name = 'SurfMoist'
netcdf_short_name[pcrglobwb_variable_name] = 'SurfMoist'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Surface soil moisture'
description[pcrglobwb_variable_name]       = 'first model layer (SurfLayerThick)'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#RootMoist
pcrglobwb_variable_name = 'RootMoist'
netcdf_short_name[pcrglobwb_variable_name] = 'RootMoist'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Root zone soil moisture'
description[pcrglobwb_variable_name]       = 'Total soil moisture available for evapotranspiration (RootLayerThick)'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#GroundMoist
pcrglobwb_variable_name = 'GroundMoist'
netcdf_short_name[pcrglobwb_variable_name] = 'GroundMoist'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'groundwater'
description[pcrglobwb_variable_name]       = 'groundwater not directly available for evapotranspiration'
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

#TotMoist
pcrglobwb_variable_name = 'TotMoist'
netcdf_short_name[pcrglobwb_variable_name] = 'TotMoist'
netcdf_unit[pcrglobwb_variable_name]       = 'kg m-2'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_standard_name[pcrglobwb_variable_name] = 'N.A.'
netcdf_long_name[pcrglobwb_variable_name]  = 'Total soil moisture'
description[pcrglobwb_variable_name]       = 'Vertically integrated total soil moisture (RootLayerThick)'
comment[pcrglobwb_variable_name]           = 'equals RootMoist'
latex_symbol[pcrglobwb_variable_name]      = None

# RvB 23/02/2017: end of edit

#~ # remove/clear pcrglobwb_variable_name 
#~ pcrglobwb_variable_name = None
#~ del pcrglobwb_variable_name
