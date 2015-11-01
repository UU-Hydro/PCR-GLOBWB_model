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

# totalBaseflowVolume
pcrglobwb_variable_name = 'totalBaseflowVolumeRate'
netcdf_short_name[pcrglobwb_variable_name] = 'total_baseflow_volume_rate'
netcdf_unit[pcrglobwb_variable_name]       = 'm3.day'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = "total_exchange_between_surface_water_and_groundwater_bodies"
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Note positive values indicate water entering aquifer bodies."
latex_symbol[pcrglobwb_variable_name]      = None

# accesibleGroundwaterVolume
pcrglobwb_variable_name = 'accesibleGroundwaterVolume'
netcdf_short_name[pcrglobwb_variable_name] = 'accesible_groundwater_volume'
netcdf_unit[pcrglobwb_variable_name]       = 'm3'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Note that this calculated groundwater volume is until a certain depth or aquifer bottom elevation. Please check the assumption."
latex_symbol[pcrglobwb_variable_name]      = None

# accesibleGroundwaterThickness
pcrglobwb_variable_name = 'accesibleGroundwaterThickness'
netcdf_short_name[pcrglobwb_variable_name] = 'accesible_groundwater_thickness'
netcdf_unit[pcrglobwb_variable_name]       = 'm'
netcdf_monthly_total_unit[pcrglobwb_variable_name] = None 
netcdf_yearly_total_unit[pcrglobwb_variable_name]  = None
netcdf_long_name[pcrglobwb_variable_name]  = None
description[pcrglobwb_variable_name]       = None
comment[pcrglobwb_variable_name]           = "Note that this calculated groundwater thickness is until a certain depth or aquifer bottom elevation. Please check the assumption."
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

#~ # remove/clear pcrglobwb_variable_name 
#~ pcrglobwb_variable_name = None
#~ del pcrglobwb_variable_name
