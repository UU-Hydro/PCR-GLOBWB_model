# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 12:40:19 2017

@author: Ent00002
"""

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

'''
Takes care of reporting (writing) output to netcdf files. Aggregates totals and averages for various time periods.
@author: Edwin H. Sutanudjaja

Additional variables for Earth2Observe
@author: Ruud van der Ent, 2017-02-15
'''


    def post_processing(self):

        self.e2o_post_processing()
        
    def e2o_post_processing(self):
        
        # fluxes (/86.4 to go from "m day-1" to "kg m-2 s-1")
        self.Precip     =   self._model.meteo.precipitation / 86.4 # report in kg m-2 s-1
        self.Evap       = - (self._model.landSurface.actualET + 
                            self._model.routing.waterBodyEvaporation) / 86.4 # report in kg m-2 s-1
        self.Runoff     = - self._model.routing.runoff / 86.4 # report in kg m-2 s-1
        self.Qs         = - (self._model.landSurface.directRunoff + 
                            self._model.landSurface.interflowTotal) / 86.4  # report in kg m-2 s-1
        self.Qsb        = - self._model.groundwater.baseflow / 86.4 # report in kg m-2 s-1
        self.Qsm        =   self._model.landSurface.snowMelt / 86.4 # report in kg m-2 s-1
        self.PotEvap    = - self._model.meteo.referencePotET / 86.4 # report in kg m-2 s-1
        self.ECanop     = - self._model.landSurface.interceptEvap / 86.4 # report in kg m-2 s-1
        self.TVeg       = - self._model.landSurface.actTranspiTotal / 86.4 # report in kg m-2 s-1
        self.ESoil      = - self._model.landSurface.actBareSoilEvap / 86.4 # report in kg m-2 s-1
        self.EWater     = - self._model.routing.waterBodyEvaporation / 86.4 # report in kg m-2 s-1
        self.RivOut     =   self._model.routing.disChanWaterBody # report in m3/s
        
        # state variables (*1000 to go from "m" to "kg m-2")
        self.SWE        =   self._model.landSurface.snowCoverSWE * 1000 # report in kg m-2
        self.CanopInt   =   self._model.landSurface.interceptStor * 1000 # report in kg m-2
        self.SurfStor   =   ( self._model.landSurface.topWaterLayer 
                            + (self._model.routing.channelStorage/self._model.routing.cellArea) 
                            + pcr.ifthen(self._model.routing.landmask, 
                            pcr.ifthen(
                            pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.,
                                       self._model.routing.WaterBodies.waterBodyStorage)) ) * 1000  # report in kg m-2
        self.SurfMoist  =   self._model.landSurface.storUppTotal * 1000 # report in kg m-2 (water in SurfLayerThick)
        self.RootMoist  =   ( self._model.landSurface.storUppTotal + 
                            self._model.landSurface.storLowTotal ) * 1000 # report in kg m-2 (water in RootLayerThick)
        self.TotMoist   =   self.RootMoist # equals RootMoist...
        self.GroundMoist    = self._model.groundwater.storGroundwater * 1000  # self._model.groundwater. # report in kg m-2
