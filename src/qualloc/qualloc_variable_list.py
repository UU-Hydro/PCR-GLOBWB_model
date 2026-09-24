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

# all variables are listed with their name as key and identifier, and dictionaries with
# the unit, standard name, long name, description, comment and LaTeX unit; two booleans
# identify whether the variable is timed and/or spatial (used to initialize the netCDF
# output files), and an 8-character short name is used to report PCRaster maps

netcdf_variable_name = {}
netcdf_standard_name = {}
netcdf_long_name = {}
netcdf_units = {}
netcdf_is_timed = {}
netcdf_is_spatial = {}
description = {}
comment = {}
latex_symbol = {}
pcr_short_name = {}
pcr_datatype = {}


# forcing variables: totals for the current time step (m water slice)


netcdf_variable_name = "precipitation_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "prec"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "referencepotet_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "epotref"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_recharge_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gwrec"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "direct_runoff_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "qdir"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "interflow_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "qssf"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "irrigation_gross_demand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "irrdemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "domesticgrossdemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "domdemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "domesticnettodemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "domdemn"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "livestockgrossdemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "livdemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "livestocknettodemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "livdemn"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "industrygrossdemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "inddemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "industrynettodemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "inddemn"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "manufacturegrossdemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "mandemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "manufacturenettodemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "mandemn"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "thermoelectricgrossdemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "thrdemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "thermoelectricnettodemand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "thrdemn"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "environment_gross_demand_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "envdemg"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_temperature_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "oC"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_tp"
pcr_datatype[netcdf_variable_name] = "Scalar"

# surface water biochemical oxygen demand
netcdf_variable_name = "surfacewater_organic_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_or"
pcr_datatype[netcdf_variable_name] = "Scalar"

# surface water total dissolved solids
netcdf_variable_name = "surfacewater_salinity_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_sl"
pcr_datatype[netcdf_variable_name] = "Scalar"

# surface water fecal coliforms
netcdf_variable_name = "surfacewater_pathogen_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "cfu/100ml"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_fc"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_temperature_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "oC"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_tp"
pcr_datatype[netcdf_variable_name] = "Scalar"

# groundwater biochemical oxygen demand
netcdf_variable_name = "groundwater_organic_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_or"
pcr_datatype[netcdf_variable_name] = "Scalar"

# groundwater total dissolved solids
netcdf_variable_name = "groundwater_salinity_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_sl"
pcr_datatype[netcdf_variable_name] = "Scalar"

# groundwater fecal coliforms
netcdf_variable_name = "groundwater_pathogen_forcing"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "cfu/100ml"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_fc"
pcr_datatype[netcdf_variable_name] = "Scalar"

# groundwater module: base flow and recharge (m water slice per time step), storage (m water slice)

netcdf_variable_name = "total_base_flow"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gwm_qbft"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_storage"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gwm_stor"
pcr_datatype[netcdf_variable_name] = "Scalar"

# surface water module: runoff (m water slice per time step), discharge (m3/s), storage (m water slice)

netcdf_variable_name = "discharge"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/s"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "swm_qch"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_storage"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "swm_stor"
pcr_datatype[netcdf_variable_name] = "Scalar"

# water quality module: long-term temperature (degC), biochemical oxygen demand (mg/L),
# total dissolved solids (mg/L) and fecal coliforms (cfu/100mL) of surface water and groundwater

netcdf_variable_name = "surfacewater_longterm_temperature"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "oC"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_tp_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term surface water biochemical oxygen demand
netcdf_variable_name = "surfacewater_longterm_organic"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_or_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term surface water total dissolved solids
netcdf_variable_name = "surfacewater_longterm_salinity"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_sl_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term surface water fecal coliforms
netcdf_variable_name = "surfacewater_longterm_pathogen"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "cfu/100ml"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_fc_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_longterm_temperature"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "oC"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_tp_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term groundwater biochemical oxygen demand
netcdf_variable_name = "groundwater_longterm_organic"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_or_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term groundwater total dissolved solids
netcdf_variable_name = "groundwater_longterm_salinity"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "mg/L"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_sl_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# long-term groundwater fecal coliforms
netcdf_variable_name = "groundwater_longterm_pathogen"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "cfu/100ml"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_fc_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

# water management module
netcdf_variable_name = "total_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "demg_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "total_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "demn_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "total_consumption"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "cons_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "total_return_flow"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "retf_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

# water withdrawn locally to meet the demand
netcdf_variable_name = "total_withdrawal"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "with_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

# water allocated to meet the demand
netcdf_variable_name = "total_allocation"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "allo_tot"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "domestic_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "dom_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "domestic_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "dom_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "irrigation_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "irr_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "irrigation_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "irr_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "livestock_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "liv_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "livestock_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "liv_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "industry_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "ind_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "industry_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "ind_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "manufacture_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "man_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "manufacture_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "man_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "thermoelectric_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "thr_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "thermoelectric_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "thr_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "environment_gross_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "env_dm_gr"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "environment_net_demand"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "env_dm_nt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_longterm_discharge"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/s"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "ds_av_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_longterm_runoff"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "ro_av_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_longterm_storage"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "st_av_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_domestic"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "dom_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_irrigation"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "irr_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_livestock"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "liv_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_industry"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "ind_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_manufacture"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "man_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_thermoelectric"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "thr_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "gross_demand_longterm_environment"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "env_dm_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_longterm_potential_withdrawal"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_pw_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_longterm_potential_withdrawal"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_pw_lt"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "surfacewater_withdrawal_capacity"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "sw_wcap"
pcr_datatype[netcdf_variable_name] = "Scalar"

netcdf_variable_name = "groundwater_withdrawal_capacity"
netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
netcdf_units[netcdf_variable_name] = "m3/day"
netcdf_is_timed[netcdf_variable_name] = True
netcdf_is_spatial[netcdf_variable_name] = True
description[netcdf_variable_name] = None
comment[netcdf_variable_name] = None
latex_symbol[netcdf_variable_name] = None
pcr_short_name[netcdf_variable_name] = "gw_wcap"
pcr_datatype[netcdf_variable_name] = "Scalar"

# allocated water demand per sector
for pcr_var_key, netcdf_variable_name in {
    "wpotrsw": "potential_withdrawal_renewable_surfacewater",
    "wpotnsw": "potential_withdrawal_nonrenewable_surfacewater",
    "wpotrgw": "potential_withdrawal_renewable_groundwater",
    "wpotngw": "potential_withdrawal_nonrenewable_groundwater",
    "wactrsw": "actual_withdrawal_renewable_surfacewater",
    "wactnsw": "actual_withdrawal_nonrenewable_surfacewater",
    "wactrgw": "actual_withdrawal_renewable_groundwater",
    "wactngw": "actual_withdrawal_nonrenewable_groundwater",
    "wunursw": "unused_withdrawal_renewable_surfacewater",
    "wununsw": "unused_withdrawal_nonrenewable_surfacewater",
    "wunurgw": "unused_withdrawal_renewable_groundwater",
    "wunungw": "unused_withdrawal_nonrenewable_groundwater",
    "ddomrs": "demand_domestic_allocated_to_renewable_surfacewater",
    "dindrs": "demand_industry_allocated_to_renewable_surfacewater",
    "dirrrs": "demand_irrigation_allocated_to_renewable_surfacewater",
    "dlivrs": "demand_livestock_allocated_to_renewable_surfacewater",
    "dmanrs": "demand_manufacture_allocated_to_renewable_surfacewater",
    "dthers": "demand_thermoelectric_allocated_to_renewable_surfacewater",
    "denvrs": "demand_environment_allocated_to_renewable_surfacewater",
    "ddomns": "demand_domestic_allocated_to_nonrenewable_surfacewater",
    "dindns": "demand_industry_allocated_to_nonrenewable_surfacewater",
    "dirrns": "demand_irrigation_allocated_to_nonrenewable_surfacewater",
    "dlivns": "demand_livestock_allocated_to_nonrenewable_surfacewater",
    "dmanns": "demand_manufacture_allocated_to_nonrenewable_surfacewater",
    "dthens": "demand_thermoelectric_allocated_to_nonrenewable_surfacewater",
    "denvns": "demand_environment_allocated_to_nonrenewable_surfacewater",
    "ddomrg": "demand_domestic_allocated_to_renewable_groundwater",
    "dindrg": "demand_industry_allocated_to_renewable_groundwater",
    "dirrrg": "demand_irrigation_allocated_to_renewable_groundwater",
    "dlivrg": "demand_livestock_allocated_to_renewable_groundwater",
    "dmanrg": "demand_manufacture_allocated_to_renewable_groundwater",
    "dtherg": "demand_thermoelectric_allocated_to_renewable_groundwater",
    "denvrg": "demand_environment_allocated_to_renewable_groundwater",
    "ddomng": "demand_domestic_allocated_to_nonrenewable_groundwater",
    "dindng": "demand_industry_allocated_to_nonrenewable_groundwater",
    "dirrng": "demand_irrigation_allocated_to_nonrenewable_groundwater",
    "dlivng": "demand_livestock_allocated_to_nonrenewable_groundwater",
    "dmanng": "demand_manufacture_allocated_to_nonrenewable_groundwater",
    "dtheng": "demand_thermoelectric_allocated_to_nonrenewable_groundwater",
    "denvng": "demand_environment_allocated_to_nonrenewable_groundwater",
    "ddomdw": "demand_domestic_allocated_to_desalinated_water",
    "dinddw": "demand_industry_allocated_to_desalinated_water",
    "dirrdw": "demand_irrigation_allocated_to_desalinated_water",
    "dlivdw": "demand_livestock_allocated_to_desalinated_water",
    "dmandw": "demand_manufacture_allocated_to_desalinated_water",
    "dthedw": "demand_thermoelectric_allocated_to_desalinated_water",
    "denvdw": "demand_environment_allocated_to_desalinated_water",
    "cdomrs": "consumption_domestic_allocated_to_renewable_surfacewater",
    "cindrs": "consumption_industry_allocated_to_renewable_surfacewater",
    "cirrrs": "consumption_irrigation_allocated_to_renewable_surfacewater",
    "clivrs": "consumption_livestock_allocated_to_renewable_surfacewater",
    "cmanrs": "consumption_manufacture_allocated_to_renewable_surfacewater",
    "cthers": "consumption_thermoelectric_allocated_to_renewable_surfacewater",
    "cenvrs": "consumption_environment_allocated_to_renewable_surfacewater",
    "cdomns": "consumption_domestic_allocated_to_nonrenewable_surfacewater",
    "cindns": "consumption_industry_allocated_to_nonrenewable_surfacewater",
    "cirrns": "consumption_irrigation_allocated_to_nonrenewable_surfacewater",
    "clivns": "consumption_livestock_allocated_to_nonrenewable_surfacewater",
    "cmanns": "consumption_manufacture_allocated_to_nonrenewable_surfacewater",
    "cthens": "consumption_thermoelectric_allocated_to_nonrenewable_surfacewater",
    "cenvns": "consumption_environment_allocated_to_nonrenewable_surfacewater",
    "cdomrg": "consumption_domestic_allocated_to_renewable_groundwater",
    "cindrg": "consumption_industry_allocated_to_renewable_groundwater",
    "cirrrg": "consumption_irrigation_allocated_to_renewable_groundwater",
    "clivrg": "consumption_livestock_allocated_to_renewable_groundwater",
    "cmanrg": "consumption_manufacture_allocated_to_renewable_groundwater",
    "ctherg": "consumption_thermoelectric_allocated_to_renewable_groundwater",
    "cenvrg": "consumption_environment_allocated_to_renewable_groundwater",
    "cdomng": "consumption_domestic_allocated_to_nonrenewable_groundwater",
    "cindng": "consumption_industry_allocated_to_nonrenewable_groundwater",
    "cirrng": "consumption_irrigation_allocated_to_nonrenewable_groundwater",
    "clivng": "consumption_livestock_allocated_to_nonrenewable_groundwater",
    "cmanng": "consumption_manufacture_allocated_to_nonrenewable_groundwater",
    "ctheng": "consumption_thermoelectric_allocated_to_nonrenewable_groundwater",
    "cenvng": "consumption_environment_allocated_to_nonrenewable_groundwater",
    "cdomdw": "consumption_domestic_allocated_to_desalinated_water",
    "cinddw": "consumption_industry_allocated_to_desalinated_water",
    "cirrdw": "consumption_irrigation_allocated_to_desalinated_water",
    "clivdw": "consumption_livestock_allocated_to_desalinated_groundwater",
    "cmandw": "consumption_manufacture_allocated_to_desalinated_water",
    "cthedw": "consumption_thermoelectric_allocated_to_desalinated_water",
    "cenvdw": "consumption_environment_allocated_to_desalinated_water",
    "rdomrs": "return_flow_domestic_allocated_to_renewable_surfacewater",
    "rindrs": "return_flow_industry_allocated_to_renewable_surfacewater",
    "rirrrs": "return_flow_irrigation_allocated_to_renewable_surfacewater",
    "rlivrs": "return_flow_livestock_allocated_to_renewable_surfacewater",
    "rmanrs": "return_flow_manufacture_allocated_to_renewable_surfacewater",
    "rthers": "return_flow_thermoelectric_allocated_to_renewable_surfacewater",
    "renvrs": "return_flow_environment_allocated_to_renewable_surfacewater",
    "rdomns": "return_flow_domestic_allocated_to_nonrenewable_surfacewater",
    "rindns": "return_flow_industry_allocated_to_nonrenewable_surfacewater",
    "rirrns": "return_flow_irrigation_allocated_to_nonrenewable_surfacewater",
    "rlivns": "return_flow_livestock_allocated_to_nonrenewable_surfacewater",
    "rmanns": "return_flow_manufacture_allocated_to_nonrenewable_surfacewater",
    "rthens": "return_flow_thermoelectric_allocated_to_nonrenewable_surfacewater",
    "renvns": "return_flow_environment_allocated_to_nonrenewable_surfacewater",
    "rdomrg": "return_flow_domestic_allocated_to_renewable_groundwater",
    "rindrg": "return_flow_industry_allocated_to_renewable_groundwater",
    "rirrrg": "return_flow_irrigation_allocated_to_renewable_groundwater",
    "rlivrg": "return_flow_livestock_allocated_to_renewable_groundwater",
    "rmanrg": "return_flow_manufacture_allocated_to_renewable_groundwater",
    "rtherg": "return_flow_thermoelectric_allocated_to_renewable_groundwater",
    "renvrg": "return_flow_environment_allocated_to_renewable_groundwater",
    "rdomng": "return_flow_domestic_allocated_to_nonrenewable_groundwater",
    "rindng": "return_flow_industry_allocated_to_nonrenewable_groundwater",
    "rirrng": "return_flow_irrigation_allocated_to_nonrenewable_groundwater",
    "rlivng": "return_flow_livestock_allocated_to_nonrenewable_groundwater",
    "rmanng": "return_flow_manufacture_allocated_to_nonrenewable_groundwater",
    "rtheng": "return_flow_thermoelectric_allocated_to_nonrenewable_groundwater",
    "renvng": "return_flow_environment_allocated_to_nonrenewable_groundwater",
    "rdomdw": "return_flow_domestic_allocated_to_desalinated_water",
    "rinddw": "return_flow_industry_allocated_to_desalinated_water",
    "rirrdw": "return_flow_irrigation_allocated_to_desalinated_water",
    "rlivdw": "return_flow_livestock_allocated_to_desalinated_water",
    "rmandw": "return_flow_manufacture_allocated_to_desalinated_water",
    "rthedw": "return_flow_thermoelectric_allocated_to_desalinated_water",
    "renvdw": "return_flow_environment_allocated_to_desalinated_water",
    "wdomrs": "withdrawal_domestic_allocated_to_renewable_surfacewater",
    "windrs": "withdrawal_industry_allocated_to_renewable_surfacewater",
    "wirrrs": "withdrawal_irrigation_allocated_to_renewable_surfacewater",
    "wlivrs": "withdrawal_livestock_allocated_to_renewable_surfacewater",
    "wmanrs": "withdrawal_manufacture_allocated_to_renewable_surfacewater",
    "wthers": "withdrawal_thermoelectric_allocated_to_renewable_surfacewater",
    "wenvrs": "withdrawal_environment_allocated_to_renewable_surfacewater",
    "wdomns": "withdrawal_domestic_allocated_to_nonrenewable_surfacewater",
    "windns": "withdrawal_industry_allocated_to_nonrenewable_surfacewater",
    "wirrns": "withdrawal_irrigation_allocated_to_nonrenewable_surfacewater",
    "wlivns": "withdrawal_livestock_allocated_to_nonrenewable_surfacewater",
    "wmanns": "withdrawal_manufacture_allocated_to_nonrenewable_surfacewater",
    "wthens": "withdrawal_thermoelectric_allocated_to_nonrenewable_surfacewater",
    "wenvns": "withdrawal_environment_allocated_to_nonrenewable_surfacewater",
    "wdomrg": "withdrawal_domestic_allocated_to_renewable_groundwater",
    "windrg": "withdrawal_industry_allocated_to_renewable_groundwater",
    "wirrrg": "withdrawal_irrigation_allocated_to_renewable_groundwater",
    "wlivrg": "withdrawal_livestock_allocated_to_renewable_groundwater",
    "wmanrg": "withdrawal_manufacture_allocated_to_renewable_groundwater",
    "wtherg": "withdrawal_thermoelectric_allocated_to_renewable_groundwater",
    "wenvrg": "withdrawal_environment_allocated_to_renewable_groundwater",
    "wdomng": "withdrawal_domestic_allocated_to_nonrenewable_groundwater",
    "windng": "withdrawal_industry_allocated_to_nonrenewable_groundwater",
    "wirrng": "withdrawal_irrigation_allocated_to_nonrenewable_groundwater",
    "wlivng": "withdrawal_livestock_allocated_to_nonrenewable_groundwater",
    "wmanng": "withdrawal_manufacture_allocated_to_nonrenewable_groundwater",
    "wtheng": "withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater",
    "wenvng": "withdrawal_environment_allocated_to_nonrenewable_groundwater",
    "wdomdw": "withdrawal_domestic_allocated_to_desalinated_water",
    "winddw": "withdrawal_industry_allocated_to_desalinated_water",
    "wirrdw": "withdrawal_irrigation_allocated_to_desalinated_water",
    "wlivdw": "withdrawal_livestock_allocated_to_desalinated_water",
    "wmandw": "withdrawal_manufacture_allocated_to_desalinated_water",
    "wthedw": "withdrawal_thermoelectric_allocated_to_desalinated_water",
    "wenvdw": "withdrawal_environment_allocated_to_desalinated_water",
}.items():

    netcdf_standard_name[netcdf_variable_name] = netcdf_variable_name
    netcdf_long_name[netcdf_variable_name] = netcdf_variable_name
    netcdf_units[netcdf_variable_name] = "m3/day"
    netcdf_is_timed[netcdf_variable_name] = True
    netcdf_is_spatial[netcdf_variable_name] = True
    description[netcdf_variable_name] = None
    comment[netcdf_variable_name] = None
    latex_symbol[netcdf_variable_name] = None
    pcr_short_name[netcdf_variable_name] = pcr_var_key
    pcr_datatype[netcdf_variable_name] = "Scalar"
