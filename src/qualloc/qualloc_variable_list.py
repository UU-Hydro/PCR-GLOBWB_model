#!/usr/bin/env python
#  -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# CALEROS Landscape Development Model:                                        #
#                                                                             #
# Copyright (c) 2019 Ludovicus P.H. (Rens) van Beek - r.vanbeek@uu.nl         #
# Department of Physical Geography, Faculty of Geosciences,                   #
# Utrecht University, Utrecht, The Netherlands.                               #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
#
# This development is part of the CALEROS landscape development.              #
#                                                                             #
###############################################################################

"""
qualloc_variable_list.py: module that lists all the reportable variables of the \
QUAlloc hydrological model.

All variables are listed as follows:  it includes the variable name that is \
used as the key and identifier and dictionaries that specify the units, \
standard name and long name and a description, comment and the latex code for \
the formatted variable's unit. In addition it includes two boolean variables \
that identify whether the variable is timed and/or spatial that are used in \
initializing the netCDF output files. Also defined is a standard 8-character \
long name that can be used to report PCRaster maps and the corresponding data \
type that is used to initialize the data type of the netCDF file.
 
"""

# all variables are listed: it includes the variable name that is used as the
# key and identifier and dictionaries that specify the units, standard name and
# long name and a description, comment and the latex code for the formatted
#  variable's unit. In addition it includes two boolean variables that identify
# whether the variable is timed and/or spatial that are used in initializing
# the netCDF output files. Also defined is a standard 8-character long name that
# can be used to report PCRaster maps.

netcdf_variable_name = {}
netcdf_standard_name = {}
netcdf_long_name     = {}
netcdf_units         = {}
netcdf_is_timed      = {} 
netcdf_is_spatial    = {} 
description          = {}
comment              = {}
latex_symbol         = {}
pcr_short_name       = {}
pcr_datatype         = {}

###########
# example #
###########

#netcdf_variable_name                        = ''
#netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
#netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
#netcdf_units[netcdf_variable_name]          = ''
#netcdf_is_timed[netcdf_variable_name]       = False
#netcdf_is_spatial[netcdf_variable_name]     = False
#description[netcdf_variable_name]           = None
#comment[netcdf_variable_name]               = None
#latex_symbol[netcdf_variable_name]          = None
#pcr_short_name[netcdf_variable_name]        = ''
#pcr_datatype[netcdf_variable_name]          = 'Scalar'

#####################
# forcing variables #
#####################
# the following variables are present as forcing and stored as totals for the
# current time step in units of [m water slice]
# 'precipitation'
# 'referencepotet'
# 'groundwater_recharge'
# 'direct_runoff'
# 'interflow'
# 'irrigation_gross_demand'
# 'domesticgrossdemand'
# 'domesticnettodemand'
# 'industrygrossdemand'
# 'industrynettodemand'
# 'livestockgrossdemand'
# 'livestocknettodemand'


# precipitation
netcdf_variable_name                        = 'precipitation_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'prec'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# referencepotet
netcdf_variable_name                        = 'referencepotet_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'epotref'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater_recharge
netcdf_variable_name                        = 'groundwater_recharge_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gwrec'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# direct_runoff
netcdf_variable_name                        = 'direct_runoff_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'qdir'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# interflow
netcdf_variable_name                        = 'interflow_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'qssf'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# irrigation_gross_demand
netcdf_variable_name                        = 'irrigation_gross_demand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'irrdemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# domesticgrossdemand
netcdf_variable_name                        = 'domesticgrossdemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'domdemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# domesticnettodemand
netcdf_variable_name                        = 'domesticnettodemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'domdemn'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# livestockgrossdemand
netcdf_variable_name                        = 'livestockgrossdemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'livdemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# livestocknettodemand
netcdf_variable_name                        = 'livestocknettodemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'livdemn'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# industrygrossdemand
netcdf_variable_name                        = 'industrygrossdemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'inddemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# industrynettodemand
netcdf_variable_name                        = 'industrynettodemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'inddemn'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# manufacturegrossdemand
netcdf_variable_name                        = 'manufacturegrossdemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'mandemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# manufacturenettodemand
netcdf_variable_name                        = 'manufacturenettodemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'mandemn'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# thermoelectricgrossdemand
netcdf_variable_name                        = 'thermoelectricgrossdemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'thrdemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# thermoelectricnettodemand
netcdf_variable_name                        = 'thermoelectricnettodemand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'thrdemn'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# environment_gross_demand
netcdf_variable_name                        = 'environment_gross_demand_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'envdemg'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# surface water temperature 
netcdf_variable_name                        = 'surfacewater_temperature_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'oC'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_tp'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# surface water biochemical oxigen demand 
netcdf_variable_name                        = 'surfacewater_organic_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_or'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# surface water total dissolved solids 
netcdf_variable_name                        = 'surfacewater_salinity_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_sl'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# surface water fecal coliforms 
netcdf_variable_name                        = 'surfacewater_pathogen_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'cfu/100ml'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_fc'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater temperature 
netcdf_variable_name                        = 'groundwater_temperature_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'oC'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_tp'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater biochemical oxigen demand 
netcdf_variable_name                        = 'groundwater_organic_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_or'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater total dissolved solids 
netcdf_variable_name                        = 'groundwater_salinity_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_sl'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater fecal coliforms 
netcdf_variable_name                        = 'groundwater_pathogen_forcing'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'cfu/100ml'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_fc'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

###############
# groundwater #
###############
# the following variables are pertinent to the groundwater module gwm
# base_flow : base flow in [m waterslice] per time step
# recharge  : groundwater recharge in [m waterslice] per time step
# storage   : groundwater storage in [m water slice]

# total, accumulated base_flow
netcdf_variable_name                        = 'total_base_flow'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gwm_qbft'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# storage
netcdf_variable_name                        = 'groundwater_storage'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gwm_stor'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

#################
# surface water #
#################
# the following variables are pertinent to the surface module swm
# runoff    : base flow in [m waterslice] per time step
# discharge : discharge [m3/s]
# storage   : surface water storage in [m water slice]

# discharge
netcdf_variable_name                        = 'discharge'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/s'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'swm_qch'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# storage
netcdf_variable_name                        = 'surfacewater_storage'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'swm_stor'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

#################
# water quality #
#################
# the following variables are pertinent to the water quality module
# surfacewater_longterm_temperature : long-term surface water temperature 
#                                     in water slice [oC]
# surfacewater_longterm_organic     : long-term surface water biochemical oxigen demand
#                                     in water slice [mg/l]
# surfacewater_longterm_salinity    : long-term surface water total dissolved solids
#                                     in water slice [mg/l]
# surfacewater_longterm_pathogen    : long-term surface water fecal coliforms
#                                     in water slice [cfu/100ml]
# groundwater_longterm_temperature  : long-term groundwater temperature 
#                                     in water slice [oC]
# groundwater_longterm_organic      : long-term groundwater biochemical oxigen demand
#                                     in water slice [mg/l]
# groundwater_longterm_salinity     : long-term groundwater total dissolved solids
#                                     in water slice [mg/l]
# groundwater_longterm_pathogen     : long-term groundwater fecal coliforms
#                                     in water slice [cfu/100ml]

# long-term surface water temperature 
netcdf_variable_name                        = 'surfacewater_longterm_temperature'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'oC'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_tp_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water biochemical oxigen demand 
netcdf_variable_name                        = 'surfacewater_longterm_organic'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_or_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water total dissolved solids 
netcdf_variable_name                        = 'surfacewater_longterm_salinity'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_sl_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water fecal coliforms 
netcdf_variable_name                        = 'surfacewater_longterm_pathogen'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'cfu/100ml'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_fc_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater temperature 
netcdf_variable_name                        = 'groundwater_longterm_temperature'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'oC'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_tp_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater biochemical oxigen demand 
netcdf_variable_name                        = 'groundwater_longterm_organic'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_or_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater total dissolved solids 
netcdf_variable_name                        = 'groundwater_longterm_salinity'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'mg/L'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_sl_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater fecal coliforms 
netcdf_variable_name                        = 'groundwater_longterm_pathogen'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'cfu/100ml'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_fc_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

####################
# water management #
####################
# the following variables are pertinent to the water management module
# surfacewater_longterm_availability : long-term surface water availability 
#                                      in water slice [m3/m2/month]
# groundwater_longterm_availability  : long-term groundwater availability
#                                      in water slice [m3/m2/month]
# total_gross_demand
netcdf_variable_name                        = 'total_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'demg_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# total_net_demand
netcdf_variable_name                        = 'total_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'demn_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# total_consumption
netcdf_variable_name                        = 'total_consumption'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'cons_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# total_return flow
netcdf_variable_name                        = 'total_return_flow'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'retf_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# total_withdrawal: water withdrawn locally to meet demand
netcdf_variable_name                        = 'total_withdrawal'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'with_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# total_allocation: allocated water provided to meet the demand
netcdf_variable_name                        = 'total_allocation'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'allo_tot'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: domestic_gross_demand
netcdf_variable_name                        = 'domestic_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'dom_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: domestic_net_demand
netcdf_variable_name                        = 'domestic_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'dom_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: irrigation_gross_demand
netcdf_variable_name                        = 'irrigation_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'irr_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: irrigation_net_demand
netcdf_variable_name                        = 'irrigation_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'irr_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: livestock_gross_demand
netcdf_variable_name                        = 'livestock_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'liv_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: livestock_net_demand
netcdf_variable_name                        = 'livestock_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'liv_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: industry_gross_demand
netcdf_variable_name                        = 'industry_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'ind_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: industry_net_demand
netcdf_variable_name                        = 'industry_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'ind_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: manufacture_gross_demand
netcdf_variable_name                        = 'manufacture_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'man_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: manufacture_net_demand
netcdf_variable_name                        = 'manufacture_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'man_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: thermoelectric_gross_demand
netcdf_variable_name                        = 'thermoelectric_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'thr_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: thermoelectric_net_demand
netcdf_variable_name                        = 'thermoelectric_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'thr_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: environment_gross_demand
netcdf_variable_name                        = 'environment_gross_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'env_dm_gr'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# sectoral demands: environment_net_demand
netcdf_variable_name                        = 'environment_net_demand'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'env_dm_nt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water discharge 
netcdf_variable_name                        = 'surfacewater_longterm_discharge'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/s'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'ds_av_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water runoff 
netcdf_variable_name                        = 'surfacewater_longterm_runoff'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'ro_av_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater storage 
netcdf_variable_name                        = 'groundwater_longterm_storage'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'st_av_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term domestic gross demand
netcdf_variable_name                        = 'gross_demand_longterm_domestic'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'dom_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term irrigation gross demand
netcdf_variable_name                        = 'gross_demand_longterm_irrigation'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'irr_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term livestock gross demand
netcdf_variable_name                        = 'gross_demand_longterm_livestock'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'liv_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term industry gross demand
netcdf_variable_name                        = 'gross_demand_longterm_industry'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'ind_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term manufacture gross demand
netcdf_variable_name                        = 'gross_demand_longterm_manufacture'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'man_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term thermoelectric gross demand
netcdf_variable_name                        = 'gross_demand_longterm_thermoelectric'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'thr_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term environment gross demand
netcdf_variable_name                        = 'gross_demand_longterm_environment'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'env_dm_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term surface water potential withdrawal 
netcdf_variable_name                        = 'surfacewater_longterm_potential_withdrawal'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_pw_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# long-term groundwater potential withdrawal 
netcdf_variable_name                        = 'groundwater_longterm_potential_withdrawal'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_pw_lt'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# surface water withdrawal capacity 
netcdf_variable_name                        = 'surfacewater_withdrawal_capacity'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'sw_wcap'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# groundwater withdrawal capacity 
netcdf_variable_name                        = 'groundwater_withdrawal_capacity'
netcdf_standard_name [netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
netcdf_units[netcdf_variable_name]          = 'm3/day'
netcdf_is_timed[netcdf_variable_name]       = True
netcdf_is_spatial[netcdf_variable_name]     = True
description[netcdf_variable_name]           = None
comment[netcdf_variable_name]               = None
latex_symbol[netcdf_variable_name]          = None
pcr_short_name[netcdf_variable_name]        = 'gw_wcap'
pcr_datatype[netcdf_variable_name]          = 'Scalar'

# addition of the allocated water demand
for pcr_var_key, netcdf_variable_name in { \
        
        'wpotrsw': 'potential_withdrawal_renewable_surfacewater', \
        'wpotnsw': 'potential_withdrawal_nonrenewable_surfacewater', \
        'wpotrgw': 'potential_withdrawal_renewable_groundwater', \
        'wpotngw': 'potential_withdrawal_nonrenewable_groundwater', \
        
        'wactrsw': 'actual_withdrawal_renewable_surfacewater', \
        'wactnsw': 'actual_withdrawal_nonrenewable_surfacewater', \
        'wactrgw': 'actual_withdrawal_renewable_groundwater', \
        'wactngw': 'actual_withdrawal_nonrenewable_groundwater', \
        
        'wunursw': 'unused_withdrawal_renewable_surfacewater', \
        'wununsw': 'unused_withdrawal_nonrenewable_surfacewater', \
        'wunurgw': 'unused_withdrawal_renewable_groundwater', \
        'wunungw': 'unused_withdrawal_nonrenewable_groundwater', \
        
        'ddomrs' : 'demand_domestic_allocated_to_renewable_surfacewater', \
        'dindrs' : 'demand_industry_allocated_to_renewable_surfacewater', \
        'dirrrs' : 'demand_irrigation_allocated_to_renewable_surfacewater', \
        'dlivrs' : 'demand_livestock_allocated_to_renewable_surfacewater', \
        'dmanrs' : 'demand_manufacture_allocated_to_renewable_surfacewater', \
        'dthers' : 'demand_thermoelectric_allocated_to_renewable_surfacewater', \
        'denvrs' : 'demand_environment_allocated_to_renewable_surfacewater', \
        
        'ddomns' : 'demand_domestic_allocated_to_nonrenewable_surfacewater', \
        'dindns' : 'demand_industry_allocated_to_nonrenewable_surfacewater', \
        'dirrns' : 'demand_irrigation_allocated_to_nonrenewable_surfacewater', \
        'dlivns' : 'demand_livestock_allocated_to_nonrenewable_surfacewater', \
        'dmanns' : 'demand_manufacture_allocated_to_nonrenewable_surfacewater', \
        'dthens' : 'demand_thermoelectric_allocated_to_nonrenewable_surfacewater', \
        'denvns' : 'demand_environment_allocated_to_nonrenewable_surfacewater', \
        
        'ddomrg' : 'demand_domestic_allocated_to_renewable_groundwater', \
        'dindrg' : 'demand_industry_allocated_to_renewable_groundwater', \
        'dirrrg' : 'demand_irrigation_allocated_to_renewable_groundwater', \
        'dlivrg' : 'demand_livestock_allocated_to_renewable_groundwater', \
        'dmanrg' : 'demand_manufacture_allocated_to_renewable_groundwater', \
        'dtherg' : 'demand_thermoelectric_allocated_to_renewable_groundwater', \
        'denvrg' : 'demand_environment_allocated_to_renewable_groundwater', \
        
        'ddomng' : 'demand_domestic_allocated_to_nonrenewable_groundwater', \
        'dindng' : 'demand_industry_allocated_to_nonrenewable_groundwater', \
        'dirrng' : 'demand_irrigation_allocated_to_nonrenewable_groundwater', \
        'dlivng' : 'demand_livestock_allocated_to_nonrenewable_groundwater', \
        'dmanng' : 'demand_manufacture_allocated_to_nonrenewable_groundwater', \
        'dtheng' : 'demand_thermoelectric_allocated_to_nonrenewable_groundwater', \
        'denvng' : 'demand_environment_allocated_to_nonrenewable_groundwater', \
        
        'ddomdw' : 'demand_domestic_allocated_to_desalinated_water', \
        'dinddw' : 'demand_industry_allocated_to_desalinated_water', \
        'dirrdw' : 'demand_irrigation_allocated_to_desalinated_water', \
        'dlivdw' : 'demand_livestock_allocated_to_desalinated_water', \
        'dmandw' : 'demand_manufacture_allocated_to_desalinated_water', \
        'dthedw' : 'demand_thermoelectric_allocated_to_desalinated_water', \
        'denvdw' : 'demand_environment_allocated_to_desalinated_water', \
        
        'cdomrs' : 'consumption_domestic_allocated_to_renewable_surfacewater', \
        'cindrs' : 'consumption_industry_allocated_to_renewable_surfacewater', \
        'cirrrs' : 'consumption_irrigation_allocated_to_renewable_surfacewater', \
        'clivrs' : 'consumption_livestock_allocated_to_renewable_surfacewater', \
        'cmanrs' : 'consumption_manufacture_allocated_to_renewable_surfacewater', \
        'cthers' : 'consumption_thermoelectric_allocated_to_renewable_surfacewater', \
        'cenvrs' : 'consumption_environment_allocated_to_renewable_surfacewater', \
        
        'cdomns' : 'consumption_domestic_allocated_to_nonrenewable_surfacewater', \
        'cindns' : 'consumption_industry_allocated_to_nonrenewable_surfacewater', \
        'cirrns' : 'consumption_irrigation_allocated_to_nonrenewable_surfacewater', \
        'clivns' : 'consumption_livestock_allocated_to_nonrenewable_surfacewater', \
        'cmanns' : 'consumption_manufacture_allocated_to_nonrenewable_surfacewater', \
        'cthens' : 'consumption_thermoelectric_allocated_to_nonrenewable_surfacewater', \
        'cenvns' : 'consumption_environment_allocated_to_nonrenewable_surfacewater', \
        
        'cdomrg' : 'consumption_domestic_allocated_to_renewable_groundwater', \
        'cindrg' : 'consumption_industry_allocated_to_renewable_groundwater', \
        'cirrrg' : 'consumption_irrigation_allocated_to_renewable_groundwater', \
        'clivrg' : 'consumption_livestock_allocated_to_renewable_groundwater', \
        'cmanrg' : 'consumption_manufacture_allocated_to_renewable_groundwater', \
        'ctherg' : 'consumption_thermoelectric_allocated_to_renewable_groundwater', \
        'cenvrg' : 'consumption_environment_allocated_to_renewable_groundwater', \
        
        'cdomng' : 'consumption_domestic_allocated_to_nonrenewable_groundwater', \
        'cindng' : 'consumption_industry_allocated_to_nonrenewable_groundwater', \
        'cirrng' : 'consumption_irrigation_allocated_to_nonrenewable_groundwater', \
        'clivng' : 'consumption_livestock_allocated_to_nonrenewable_groundwater', \
        'cmanng' : 'consumption_manufacture_allocated_to_nonrenewable_groundwater', \
        'ctheng' : 'consumption_thermoelectric_allocated_to_nonrenewable_groundwater', \
        'cenvng' : 'consumption_environment_allocated_to_nonrenewable_groundwater', \
        
        'cdomdw' : 'consumption_domestic_allocated_to_desalinated_water', \
        'cinddw' : 'consumption_industry_allocated_to_desalinated_water', \
        'cirrdw' : 'consumption_irrigation_allocated_to_desalinated_water', \
        'clivdw' : 'consumption_livestock_allocated_to_desalinated_groundwater', \
        'cmandw' : 'consumption_manufacture_allocated_to_desalinated_water', \
        'cthedw' : 'consumption_thermoelectric_allocated_to_desalinated_water', \
        'cenvdw' : 'consumption_environment_allocated_to_desalinated_water', \
        
        'rdomrs' : 'return_flow_domestic_allocated_to_renewable_surfacewater', \
        'rindrs' : 'return_flow_industry_allocated_to_renewable_surfacewater', \
        'rirrrs' : 'return_flow_irrigation_allocated_to_renewable_surfacewater', \
        'rlivrs' : 'return_flow_livestock_allocated_to_renewable_surfacewater', \
        'rmanrs' : 'return_flow_manufacture_allocated_to_renewable_surfacewater', \
        'rthers' : 'return_flow_thermoelectric_allocated_to_renewable_surfacewater', \
        'renvrs' : 'return_flow_environment_allocated_to_renewable_surfacewater', \
        
        'rdomns' : 'return_flow_domestic_allocated_to_nonrenewable_surfacewater', \
        'rindns' : 'return_flow_industry_allocated_to_nonrenewable_surfacewater', \
        'rirrns' : 'return_flow_irrigation_allocated_to_nonrenewable_surfacewater', \
        'rlivns' : 'return_flow_livestock_allocated_to_nonrenewable_surfacewater', \
        'rmanns' : 'return_flow_manufacture_allocated_to_nonrenewable_surfacewater', \
        'rthens' : 'return_flow_thermoelectric_allocated_to_nonrenewable_surfacewater', \
        'renvns' : 'return_flow_environment_allocated_to_nonrenewable_surfacewater', \
        
        'rdomrg' : 'return_flow_domestic_allocated_to_renewable_groundwater', \
        'rindrg' : 'return_flow_industry_allocated_to_renewable_groundwater', \
        'rirrrg' : 'return_flow_irrigation_allocated_to_renewable_groundwater', \
        'rlivrg' : 'return_flow_livestock_allocated_to_renewable_groundwater', \
        'rmanrg' : 'return_flow_manufacture_allocated_to_renewable_groundwater', \
        'rtherg' : 'return_flow_thermoelectric_allocated_to_renewable_groundwater', \
        'renvrg' : 'return_flow_environment_allocated_to_renewable_groundwater', \
        
        'rdomng' : 'return_flow_domestic_allocated_to_nonrenewable_groundwater', \
        'rindng' : 'return_flow_industry_allocated_to_nonrenewable_groundwater', \
        'rirrng' : 'return_flow_irrigation_allocated_to_nonrenewable_groundwater', \
        'rlivng' : 'return_flow_livestock_allocated_to_nonrenewable_groundwater', \
        'rmanng' : 'return_flow_manufacture_allocated_to_nonrenewable_groundwater', \
        'rtheng' : 'return_flow_thermoelectric_allocated_to_nonrenewable_groundwater', \
        'renvng' : 'return_flow_environment_allocated_to_nonrenewable_groundwater', \
        
        'rdomdw' : 'return_flow_domestic_allocated_to_desalinated_water', \
        'rinddw' : 'return_flow_industry_allocated_to_desalinated_water', \
        'rirrdw' : 'return_flow_irrigation_allocated_to_desalinated_water', \
        'rlivdw' : 'return_flow_livestock_allocated_to_desalinated_water', \
        'rmandw' : 'return_flow_manufacture_allocated_to_desalinated_water', \
        'rthedw' : 'return_flow_thermoelectric_allocated_to_desalinated_water', \
        'renvdw' : 'return_flow_environment_allocated_to_desalinated_water', \
        
        'wdomrs' : 'withdrawal_domestic_allocated_to_renewable_surfacewater', \
        'windrs' : 'withdrawal_industry_allocated_to_renewable_surfacewater', \
        'wirrrs' : 'withdrawal_irrigation_allocated_to_renewable_surfacewater', \
        'wlivrs' : 'withdrawal_livestock_allocated_to_renewable_surfacewater', \
        'wmanrs' : 'withdrawal_manufacture_allocated_to_renewable_surfacewater', \
        'wthers' : 'withdrawal_thermoelectric_allocated_to_renewable_surfacewater', \
        'wenvrs' : 'withdrawal_environment_allocated_to_renewable_surfacewater', \
        
        'wdomns' : 'withdrawal_domestic_allocated_to_nonrenewable_surfacewater', \
        'windns' : 'withdrawal_industry_allocated_to_nonrenewable_surfacewater', \
        'wirrns' : 'withdrawal_irrigation_allocated_to_nonrenewable_surfacewater', \
        'wlivns' : 'withdrawal_livestock_allocated_to_nonrenewable_surfacewater', \
        'wmanns' : 'withdrawal_manufacture_allocated_to_nonrenewable_surfacewater', \
        'wthens' : 'withdrawal_thermoelectric_allocated_to_nonrenewable_surfacewater', \
        'wenvns' : 'withdrawal_environment_allocated_to_nonrenewable_surfacewater', \
        
        'wdomrg' : 'withdrawal_domestic_allocated_to_renewable_groundwater', \
        'windrg' : 'withdrawal_industry_allocated_to_renewable_groundwater', \
        'wirrrg' : 'withdrawal_irrigation_allocated_to_renewable_groundwater', \
        'wlivrg' : 'withdrawal_livestock_allocated_to_renewable_groundwater', \
        'wmanrg' : 'withdrawal_manufacture_allocated_to_renewable_groundwater', \
        'wtherg' : 'withdrawal_thermoelectric_allocated_to_renewable_groundwater', \
        'wenvrg' : 'withdrawal_environment_allocated_to_renewable_groundwater', \
        
        'wdomng' : 'withdrawal_domestic_allocated_to_nonrenewable_groundwater', \
        'windng' : 'withdrawal_industry_allocated_to_nonrenewable_groundwater', \
        'wirrng' : 'withdrawal_irrigation_allocated_to_nonrenewable_groundwater', \
        'wlivng' : 'withdrawal_livestock_allocated_to_nonrenewable_groundwater', \
        'wmanng' : 'withdrawal_manufacture_allocated_to_nonrenewable_groundwater', \
        'wtheng' : 'withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater', \
        'wenvng' : 'withdrawal_environment_allocated_to_nonrenewable_groundwater', \
        
        'wdomdw' : 'withdrawal_domestic_allocated_to_desalinated_water', \
        'winddw' : 'withdrawal_industry_allocated_to_desalinated_water', \
        'wirrdw' : 'withdrawal_irrigation_allocated_to_desalinated_water', \
        'wlivdw' : 'withdrawal_livestock_allocated_to_desalinated_water', \
        'wmandw' : 'withdrawal_manufacture_allocated_to_desalinated_water', \
        'wthedw' : 'withdrawal_thermoelectric_allocated_to_desalinated_water', \
        'wenvdw' : 'withdrawal_environment_allocated_to_desalinated_water', \
        
        }.items():
    
    # add the variable using the dictionary items
    netcdf_standard_name[netcdf_variable_name]  = netcdf_variable_name
    netcdf_long_name[netcdf_variable_name]      = netcdf_variable_name
    netcdf_units[netcdf_variable_name]          = 'm3/day'
    netcdf_is_timed[netcdf_variable_name]       = True
    netcdf_is_spatial[netcdf_variable_name]     = True
    description[netcdf_variable_name]           = None
    comment[netcdf_variable_name]               = None
    latex_symbol[netcdf_variable_name]          = None
    pcr_short_name[netcdf_variable_name]        = pcr_var_key
    pcr_datatype[netcdf_variable_name]          = 'Scalar'

#/end of variable list /
