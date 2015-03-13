'''
List of variables.

Created on July 7, 2014

@author: Edwin H. Sutanudjaja
'''

netcdf_short_name = {}
netcdf_unit       = {}
netcdf_monthly_total_unit = {} 
netcdf_yearly_total_unit  = {}
netcdf_long_name  = {}
description       = {}
comment           = {}
latex_symbol      = {}

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
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None

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
comment[pcrglobwb_variable_name]           = None
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

# evaporation_from_irrigation
pcrglobwb_variable_name = 'evaporation_from_irrigation'
netcdf_short_name[pcrglobwb_variable_name] = 'evaporation_from_irrigation'
netcdf_unit[pcrglobwb_variable_name]       = 'm.day-1'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = 'm.month-1' 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = 'm.year-1'
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = 'Flux values given are over the entire cell area (not only irrigation fraction).'
latex_symbol[pcrglobwb_variable_name]      = None

# fractioon_of_surface_water
pcrglobwb_variable_name = 'dynamicFracWat'
netcdf_short_name[pcrglobwb_variable_name] = 'fractioon_of_surface_water'
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
comment[pcrglobwb_variable_name]           = None
latex_symbol[pcrglobwb_variable_name]      = None


#~ # remove/clear pcrglobwb_variable_name 
#~ pcrglobwb_variable_name = None
#~ del pcrglobwb_variable_name
