import logging
import os
import sys

import pcraster as pcr

from qualloc import qualloc_variable_list as variable_attr
from qualloc.allocation import get_key
from qualloc.netCDF_recipes import netCDF_output_handler

logger = logging.getLogger(__name__)

critical_improvements = str.join("\n\t", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "inherit intervals from model_time",
        "include a solution to report non-spatial data",
        "include min and max",
        "include the variable list, that can hold information on the (non)spatial nature of data",
        "",
    ),
)

print("\nDevelopmens for reporting class:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()


pcrFieldType = pcr.Field
NoneType = type(None)

# data types used to initialize the netCDF output files
datatypes = {
    "Scalar": "f8",
    "Nominal": "i4",
    "Boolean": "b",
    "Ordinal": "f4",
    "Directional": "f8",
    "Ldd": "b",
}

# intervals and their corresponding adjectives

intervals = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
    "yearly": "year",
    "decadal": "decade",
    "centennial": "century",
}


class qualloc_reporting(object):

    def __init__(self, model_configuration):

        # reporting keeps track of the elapsed time (days) and of all variables based on
        # the monthly totals

        object.__init__(self)

        self.model_configuration = model_configuration
        statistics = [
            "tot",
            "avg",
        ]

        # report intervals, all None initially
        self.report_intervals = []
        for interval in intervals.keys():
            for statistic in statistics:
                report_interval = "%s_%s" % (interval, statistic)
                self.report_intervals.append(report_interval)

        self.statistics = {
            "tot": ["sum"],
            "avg": ["sum", "count"],
        }

        self.process_variables = []

    def reset_values_at_time(self, time_flag=None, time_flag_condition=None):
        """
        reset_values_at_time : function that resets the process variables to initial
                               values. This can be global or specifici for the time
                               flags and conditions provided

        input:
        =====
        time_flag             : string setting the name of the time flag;
        time_flag_condition   : boolean variable, specifying that the corresponding
                               variable names should be updated;
                               if both are None, the update is global and all var-
                               iables are updated.

        output:
        ======
        None                 : returns None
        """
        message_str = "Reporting variables are updated for the following intervals:"
        interval_list = []

        variablename_info = {}

        for interval in intervals.keys():
            for process_variable in self.process_variables:
                if interval in process_variable:

                    ix = process_variable.find(interval)
                    variablename = process_variable[: ix - 1]
                    statistic = process_variable[ix + len(interval) + 1 :]

                    update_status = False

                    if not isinstance(time_flag, NoneType) and interval in time_flag:

                        if not isinstance(time_flag_condition, NoneType):
                            update_status = time_flag_condition

                    # set the update status if global
                    if isinstance(time_flag, NoneType) and isinstance(
                        time_flag_condition, NoneType
                    ):

                        update_status = True

                    if update_status:
                        if process_variable not in variablename_info.keys():
                            variablename_info[process_variable] = (
                                variablename,
                                statistic,
                            )
                        if interval not in interval_list:
                            interval_list.append(interval)

        for key, (variablename, statistic) in variablename_info.items():

            if statistic == "min":
                vars(self)[key] = pcr.spatial(pcr.scalar(1.0e12))

            elif statistic == "max":
                vars(self)[key] = pcr.spatial(pcr.scalar(-1.0e12))

            elif statistic == "count":
                vars(self)[key] = int(0)

            else:
                vars(self)[key] = pcr.spatial(pcr.scalar(0))

        for interval in interval_list:
            message_str = str.join("", (message_str, " ", interval, ","))
        logger.debug(message_str)

        return None

    def initialize(self):
        """
        initialize: function that reads the reporting options from the configuration \
        file and initializes all the required output.
        """
        # copy the report intervals and statistics, removing non-existing ones
        report_intervals = []

        for report_interval in self.report_intervals:

            if report_interval in self.model_configuration.reporting.keys():

                value = self.model_configuration.convert_string_to_input(
                    self.model_configuration.reporting[report_interval], str
                )

                if not isinstance(value, NoneType):

                    if not isinstance(value, list):
                        value = [value]

                    setattr(self, report_interval, value)

                    report_intervals.append(report_interval)

        self.report_intervals = report_intervals[:]

        for report_interval in self.report_intervals:

            interval, statistic_key = report_interval.split("_")

            for variablename in getattr(self, report_interval):

                for statistic in self.statistics[statistic_key]:

                    # key of the variable for the current interval
                    key = "%s_%s_%s" % (variablename, interval, statistic)

                    if not key in vars(self).keys():

                        if key not in self.process_variables:
                            self.process_variables.append(key)

                    # key of the variable for the monthly interval, needed to initialize the values
                    # and make the updates work
                    key = "%s_%s_%s" % (variablename, "monthly", statistic)

                    if not key in vars(self).keys():

                        if key not in self.process_variables:
                            self.process_variables.append(key)

        self.reset_values_at_time()

        # initialize the netCDF output files

        self.nc_handler = netCDF_output_handler(self.model_configuration)

        for report_interval in self.report_intervals:

            interval, statistic_key = report_interval.split("_")

            for variablename in getattr(self, report_interval):

                report_key = "%s_%s_%s" % (variablename, interval, statistic_key)
                ncfilename = os.path.join(
                    self.model_configuration.netcdfpath,
                    str.join("", (report_key, ".nc")),
                )

                # initialize the netCDF (automatically added to the cache); the units of totals are
                # modified for all intervals other than daily
                variable_units = variable_attr.netcdf_units[variablename]
                if statistic_key == "tot" and interval != "daily":
                    if "day" in variable_units:
                        variable_units = variable_units.replace(
                            "day", intervals[interval]
                        )

                datatype = datatypes[str(variable_attr.pcr_datatype[variablename])]

                self.nc_handler.initialize_nc_variable(
                    ncfilename=ncfilename,
                    variablename=variablename,
                    variable_units=variable_units,
                    is_spatial=variable_attr.netcdf_is_timed[variablename],
                    is_temporal=variable_attr.netcdf_is_spatial[variablename],
                    long_name=variable_attr.netcdf_long_name[variablename],
                    standard_name=variable_attr.netcdf_standard_name[variablename],
                    datatype=datatype,
                )

        return None

    def report(self, model_time, model):
        """
        report: function of the module caleros_reporting which updates all the
                variables to be reported and writes them eventually to file.
        """

        self.update_reportable_variables(model)

        # update the weekly and monthly variables first
        for key in self.process_variables:

            if "daily" in key:
                ix = key.find("daily")
                variablename = key[: ix - 1]
                vars(self)[key] = pcr.scalar(vars(self)[variablename])

            elif "weekly" in key or "monthly" in key:
                if "weekly" in key:
                    ix = key.find("weekly")
                elif "monthly" in key:
                    ix = key.find("monthly")
                else:
                    ix = None
                variablename = key[: ix - 1]

                if "count" in key:
                    vars(self)[key] = vars(self)[key] + 1

                if "sum" in key:
                    vars(self)[key] = vars(self)[key] + pcr.scalar(
                        vars(self)[variablename]
                    )

                if "ssq" in key:
                    vars(self)[key] = vars(self)[key] + pcr.scalar(
                        vars(self)[variablename] ** 2
                    )

                if "min" in key:
                    vars(self)[key] = pcr.min(
                        vars(self)[key], pcr.scalar(vars(self)[variablename])
                    )

                if "max" in key:
                    vars(self)[key] = pcr.max(
                        vars(self)[key], pcr.scalar(vars(self)[variablename])
                    )
            else:
                pass

        # update the other variables
        if model_time.report_flags["monthly"]:
            for key in self.process_variables:
                if not "daily" in key and not "weekly" in key and not "monthly" in key:

                    # corresponding monthly key
                    ix = key.rfind("_")
                    statistic = key[ix + 1 :]
                    monthly_key = key[:ix]
                    ix = monthly_key.rfind("_")
                    monthly_key = monthly_key[:ix]
                    monthly_key = "%s_%s_%s" % (monthly_key, "monthly", statistic)
                    if "count" in key:
                        vars(self)[key] = vars(self)[key] + vars(self)[monthly_key]

                    if "sum" in key:
                        vars(self)[key] = vars(self)[key] + vars(self)[monthly_key]

                    if "ssq" in key:
                        vars(self)[key] = vars(self)[key] + vars(self)[monthly_key]

                    if "min" in key:
                        vars(self)[key] = pcr.min(
                            vars(self)[key], vars(self)[monthly_key]
                        )

                    if "max" in key:
                        vars(self)[key] = pcr.max(
                            vars(self)[key], vars(self)[monthly_key]
                        )

        # report the intervals
        for time_flag in model_time.report_flags.keys():

            if model_time.report_flags[time_flag]:

                logger.info(
                    "reporting any %s output for %s" % (time_flag, model_time.date)
                )

                for report_interval in self.report_intervals:
                    if time_flag in report_interval:

                        interval, statistic_key = report_interval.split("_")

                        for variablename in getattr(self, report_interval):

                            report_key = "%s_%s_%s" % (
                                variablename,
                                interval,
                                statistic_key,
                            )

                            # min, max and total need no post-processing; average and standard deviation do
                            if statistic_key == "min":
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    statistic_key,
                                )

                                value_field = vars(self)[process_key]

                            elif statistic_key == "max":
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    statistic_key,
                                )

                                value_field = vars(self)[process_key]

                            elif statistic_key == "tot":
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "sum",
                                )

                                value_field = vars(self)[process_key]

                            elif statistic_key == "avg":
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "sum",
                                )

                                value_field = vars(self)[process_key]

                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "count",
                                )

                                value_field = value_field / vars(self)[process_key]

                            elif statistic_key == "std":
                                # standard deviation
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "sum",
                                )

                                value_field = vars(self)[process_key] ** 2

                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "count",
                                )

                                value_field = value_field / vars(self)[process_key]

                                # sum of squares
                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "ssq",
                                )

                                value_field = vars(self)[process_key] - value_field

                                process_key = "%s_%s_%s" % (
                                    variablename,
                                    interval,
                                    "count",
                                )

                                value_field = value_field / vars(self)[process_key]

                                value_field = value_field**0.5

                            else:
                                pass

                            # add the spatial data to the netCDF file
                            ncfilename = os.path.join(
                                self.model_configuration.netcdfpath,
                                str.join("", (report_key, ".nc")),
                            )

                            # dates of timed variables
                            if variable_attr.netcdf_is_timed[variablename]:
                                is_timed = True
                                dates = [model_time.date]
                            else:
                                is_timed = False
                                dates = None

                            self.nc_handler.add_data_to_netCDF(
                                ncfilename=ncfilename,
                                variablename=variablename,
                                variable_array=pcr.pcr2numpy(
                                    value_field, self.nc_handler.default_fill_value
                                ),
                                is_timed=is_timed,
                                dates=dates,
                            )

        # reset the variables
        for time_flag, time_flag_condition in model_time.report_flags.items():

            if time_flag_condition:
                self.reset_values_at_time(time_flag, time_flag_condition)

        return None

    def close(self):

        self.nc_handler.close_cache()

        return None

    def update_reportable_variables(self, model):

        # update all reportable variables; forcing variables in m water slice per time step
        for forcing_variable, info in model.forcing_info.items():
            setattr(
                self,
                forcing_variable.lower() + "forcing",
                getattr(model, forcing_variable.lower()),
            )

        for forcing_variable, info in model.water_quality_forcing_info.items():
            setattr(
                self,
                forcing_variable.lower() + "forcing",
                getattr(model, forcing_variable.lower()),
            )

        # groundwater
        self.groundwater_recharge = model.groundwater.total_recharge
        self.groundwater_storage = model.groundwater.storage

        # surface water
        self.discharge = model.surfacewater.discharge
        self.surfacewater_storage = model.surfacewater.storage

        # water management: totals
        self.total_net_demand = model.water_management.total_net_demand
        self.total_gross_demand = model.water_management.total_gross_demand
        self.total_consumption = model.water_management.total_consumption
        self.total_return_flow = model.water_management.total_return_flow
        self.total_withdrawal = model.water_management.total_withdrawal
        self.total_allocation = model.water_management.total_allocation

        # sectoral demands
        for sector_name in model.water_management.sector_names:
            setattr(
                self,
                sector_name + "_gross_demand",
                getattr(model.water_management, "gross_demand")[sector_name],
            )
            setattr(
                self,
                sector_name + "_net_demand",
                getattr(model.water_management, "net_demand")[sector_name],
            )

        # potential, actual and unused withdrawals
        self.potential_withdrawal_renewable_groundwater = (
            model.water_management.potential_renewable_withdrawal["groundwater"]
        )
        self.potential_withdrawal_nonrenewable_groundwater = (
            model.water_management.potential_nonrenewable_withdrawal["groundwater"]
        )
        self.potential_withdrawal_renewable_surfacewater = (
            model.water_management.potential_renewable_withdrawal["surfacewater"]
        )
        self.potential_withdrawal_nonrenewable_surfacewater = (
            model.water_management.potential_nonrenewable_withdrawal["surfacewater"]
        )

        self.actual_withdrawal_renewable_groundwater = (
            model.water_management.actual_renewable_withdrawal["groundwater"]
        )
        self.actual_withdrawal_nonrenewable_groundwater = (
            model.water_management.actual_nonrenewable_withdrawal["groundwater"]
        )
        self.actual_withdrawal_renewable_surfacewater = (
            model.water_management.actual_renewable_withdrawal["surfacewater"]
        )
        self.actual_withdrawal_nonrenewable_surfacewater = (
            model.water_management.actual_nonrenewable_withdrawal["surfacewater"]
        )

        self.unused_withdrawal_renewable_groundwater = (
            model.water_management.unused_renewable_withdrawal["groundwater"]
        )
        self.unused_withdrawal_nonrenewable_groundwater = (
            model.water_management.unused_nonrenewable_withdrawal["groundwater"]
        )
        self.unused_withdrawal_renewable_surfacewater = (
            model.water_management.unused_renewable_withdrawal["surfacewater"]
        )
        self.unused_withdrawal_nonrenewable_surfacewater = (
            model.water_management.unused_nonrenewable_withdrawal["surfacewater"]
        )

        # withdrawal capacities
        self.groundwater_withdrawal_capacity = (
            model.water_management.groundwater_withdrawal_capacity
        )
        self.surfacewater_withdrawal_capacity = (
            model.water_management.surfacewater_withdrawal_capacity
        )

        # allocated withdrawal, demand, consumption and return flows, bulk added from the dictionaries
        allocation_info = {
            "withdrawal": "allocated_withdrawal_per_sector",
            "demand": "allocated_demand_per_sector",
            "consumption": "consumed_demand_per_sector",
            "return_flow": "return_flow_demand_per_sector",
        }

        for withdrawal_name in model.water_management.withdrawal_names:
            for source_name in model.water_management.source_names:

                alloc_key = get_key([withdrawal_name, source_name])

                # per sector: var_name is the model variable to read, rep_name the reportable variable
                for sector_name in model.water_management.sector_names:
                    for rep_root, var_name in allocation_info.items():

                        rep_name = get_key(
                            [rep_root, sector_name, "allocated", "to", alloc_key]
                        )

                        setattr(
                            self,
                            rep_name,
                            getattr(model.water_management, var_name)[alloc_key][
                                sector_name
                            ],
                        )

        # desalinated water use per sector: var_name is the model variable to read,
        # rep_name the reportable variable
        for sector_name in model.water_management.sector_names:
            for rep_root, var_name in allocation_info.items():

                rep_name = get_key(
                    [rep_root, sector_name, "allocated", "to", "desalinated", "water"]
                )

                var_name = "%s_desalwater" % var_name
                setattr(
                    self,
                    rep_name,
                    getattr(model.water_management, var_name)[sector_name],
                )
        return None


class qualloc_report_initial_conditions(object):
    """
qualloc_report_initial_conditions: class that can be used to report the initial \
conditions as netCDF dependent whether they are single PCRaster fields or \
dictionaries with the dates provided.
"""

    def __init__(self, model_configuration, initial_conditions, model_flags):

        # reporting of the initial conditions, combining reports in different formats

        object.__init__(self)

        logger.info("Initializing reporting of initial conditions.")

        self.statespath = model_configuration.statespath
        self.overwrite_initial_conditions = model_configuration.convert_string_to_input(
            model_configuration.reporting["overwrite_initial_conditions"], bool
        )
        self.initialize_netcdfs = True

        self.nc_handler = netCDF_output_handler(model_configuration)

        modules = list(initial_conditions.keys())
        self.variablenames = dict(
            (module, list(initial_conditions[module].keys())) for module in modules
        )

        return None

    def report(self, date, initial_conditions):
        """
        report: function to report recursively the initial conditions as netCDF files.
        """

        # delete the initial conditions if overwrite is True
        if self.overwrite_initial_conditions and len(self.nc_handler.cache) > 0:

            # close the cache if the files must be overwritten
            self.nc_handler.close_cache()

            # recreate the netCDF files
            self.initialize_netcdfs = True

        date_str = "_%s-%02d-%02d" % (date.year, date.month, date.day)

        if self.initialize_netcdfs:

            for module, variablenames in self.variablenames.items():

                for variablename in variablenames:
                    logger.debug(
                        "Creating netCDF output file for initial condition %s for %s"
                        % (variablename, module)
                    )

                    ncfilename = os.path.join(
                        self.statespath, str.join("", (variablename, date_str, ".nc"))
                    )

                    self.nc_handler.initialize_nc_variable(
                        ncfilename=ncfilename,
                        variablename=variablename,
                        variable_units=variable_attr.netcdf_units[variablename],
                        is_spatial=variable_attr.netcdf_is_timed[variablename],
                        is_temporal=variable_attr.netcdf_is_spatial[variablename],
                        long_name=variable_attr.netcdf_long_name[variablename],
                        standard_name=variable_attr.netcdf_standard_name[variablename],
                        datatype=datatypes[
                            str(variable_attr.pcr_datatype[variablename])
                        ],
                    )

            self.initialize_netcdfs = False

            for module, variablenames in self.variablenames.items():

                for variablename in variablenames:

                    ncfilename = os.path.join(
                        self.statespath, str.join("", (variablename, date_str, ".nc"))
                    )

                    if isinstance(initial_conditions[module][variablename], dict):

                        dates = list(initial_conditions[module][variablename].keys())
                        dates.sort()
                        values = []
                        for dt in dates:
                            values.append(initial_conditions[module][variablename][dt])

                    elif isinstance(
                        initial_conditions[module][variablename], pcrFieldType
                    ):

                        dates = [date]
                        values = [initial_conditions[module][variablename]]

                    else:
                        sys.exit(
                            "initial conditions of type %s cannot be used"
                            % str(type(initial_conditions[module][variablename]))
                        )

                    # write the information to the netCDF file
                    for dt in dates:

                        self.nc_handler.add_data_to_netCDF(
                            ncfilename=ncfilename,
                            variablename=variablename,
                            variable_array=pcr.pcr2numpy(
                                values[dates.index(dt)],
                                self.nc_handler.default_fill_value,
                            ),
                            is_timed=variable_attr.netcdf_is_spatial[variablename],
                            dates=[dt],
                        )

                    logger.debug(
                        "Information written for initial condition %s for %s"
                        % (variablename, module)
                    )

        logger.info("Reported initial conditions for %s" % date)

        return None

    def close(self):

        self.nc_handler.close_cache()

        return None
