import datetime
import logging
import os
import sys
from copy import deepcopy

import pcraster as pcr

from qualloc.basic_functions import pcr_return_val_div_zero, sum_list
from qualloc.file_handler import close_nc_cache, compose_filename, read_file_entry
from qualloc.groundwater import groundwater
from qualloc.initial_conditions_handler import (
    get_initial_condition_as_timed_dict,
    get_initial_conditions,
)
from qualloc.qualloc_reporting import qualloc_report_initial_conditions
from qualloc.spatialDataSet2PCR import setClone, spatialAttributes
from qualloc.surfacewater import surfacewater
from qualloc.water_management import (
    very_small_number,
    water_management,
    water_management_missing_value,
)
from qualloc.water_quality import (
    unattainable_threshold,
    water_quality,
    water_quality_forcing_variables,
)

logger = logging.getLogger(__name__)


critical_improvements = str.join("\n\t", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "streamline input: should be able to read config files but also floats etc.",
        "add flags!",
        "include the functions to read the initial conditions and return them!\n",
        "at the moment domestic, industrial and livestock water demand are read from ",
        "a single netCDF file as is the case in PCR-GLOBWB to provide the gross and net ",
        "water demand for these sectors(Gross, Netto sic); for clarity, these entries ",
        "could be split out here explicitly rather than doing this under the hood in ",
        "the main; however, a lookup table may still be required to manage the various ",
        "variable names in the original netCDF files that could be managed more clearly via the cfg file.",
        "",
    ),
)

print("\nDevelopmens for main module:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()


NoneType = type(None)

# default forcing variables
forcing_variables = {
    "precipitation": "precipitation",
    "referencePotET": "refpot_evaporation",
    "groundwater_recharge": "groundwater_recharge",
    "direct_runoff": "direct_runoff",
    "interflow": "interflow",
    "irrigationGrossDemand": "irrigation_water_demand",
    "domesticGrossDemand": "domestic_water_demand",
    "domesticNettoDemand": "domestic_water_demand",
    "industryGrossDemand": "industrial_water_demand",
    "industryNettoDemand": "industrial_water_demand",
    "livestockGrossDemand": "livestock_water_demand",
    "livestockNettoDemand": "livestock_water_demand",
    "manufactureGrossDemand": "manufacture_water_demand",
    "manufactureNettoDemand": "manufacture_water_demand",
    "thermoelectricGrossDemand": "thermoelectric_water_demand",
    "thermoelectricNettoDemand": "thermoelectric_water_demand",
    "environmentGrossDemand": "environment_water_demand",
}


def ncvariable_name(section, key, default=None):
    """
ncvariable_name: returns the name of the netCDF variable that holds the entry \
of key in the given configuration section. This is the key itself, or default \
where given, unless the section provides an explicit <key>_ncvariable override; \
PCRaster input ignores the name and is unaffected.
"""

    if isinstance(default, NoneType):
        default = key

    return section.get("%s_ncvariable" % key, default)


class qualloc_model(object):

    def __init__(
        self, model_configuration, model_time, model_flags={}, initial_conditions=None
    ):

        object.__init__(self)

        self.model_configuration = model_configuration

        self.model_flags = model_flags

        self.model_flags["water_quality_flag"] = False
        if "water_quality" in vars(self.model_configuration).keys():
            self.model_flags["water_quality_flag"] = eval(
                self.model_configuration.water_quality["water_quality_flag"]
            )

        self.model_flags["groundwater_pumping_capacity_flag"] = False
        if (
            "groundwater_regional_pumping_capacity"
            in self.model_configuration.water_management.keys()
            and self.model_configuration.water_management[
                "groundwater_regional_pumping_capacity"
            ]
            != "None"
        ):
            self.model_flags["groundwater_pumping_capacity_flag"] = True

        self.model_flags["surfacewater_pumping_capacity_flag"] = False
        if (
            "surfacewater_regional_pumping_capacity"
            in self.model_configuration.water_management.keys()
            and self.model_configuration.water_management[
                "surfacewater_regional_pumping_capacity"
            ]
            != "None"
        ):
            self.model_flags["surfacewater_pumping_capacity_flag"] = True

        self.model_flags["desalinated_water_use_flag"] = False
        if (
            "desalinated_water_use_flag"
            in self.model_configuration.water_management.keys()
        ):
            self.model_flags["desalinated_water_use_flag"] = eval(
                self.model_configuration.water_management["desalinated_water_use_flag"]
            )

        # modules with initial conditions
        self.modules = [
            "surfacewater",
            "groundwater",
            "water_management",
            "water_quality",
        ]
        self.initial_conditions = initial_conditions

        self.model_time = model_time
        self.time_step = self.model_time.time_increment

        # set the clone from the spatial attributes
        clone_file, file_exists = compose_filename(
            model_configuration.general["clone"], model_configuration.inputpath
        )
        if file_exists:
            setattr(
                self.model_configuration,
                "clone_attributes",
                spatialAttributes(clone_file),
            )
            setClone(self.model_configuration.clone_attributes)
        else:
            sys.exit("clone file %s does not exist" % clone_file)

        message_str = str.join(
            "\n",
            (
                "",
                "",
                "#" * 80,
                "# %-76s #" % ("QUAlloc water use and allocation model"),
                "#" * 80,
                "",
                "",
            ),
        )
        logger.info(message_str)

        message_str = (
            "run started at %s for %s over %s - %s using %s time increments"
            % (
                self.model_configuration._timestamp_str,
                self.model_configuration.general["scenarioname"],
                self.model_time.date,
                self.model_time.enddate,
                self.model_time.time_increment,
            )
        )
        logger.info(message_str)

        return None

    def initialize(
        self,
        online_coupling=False,
        landmask=None,
        cellarea=None,
        groundwater_alpha=None,
        total_base_flow_ini=None,
        groundwater_storage_ini=None,
        ldd=None,
        fraction_water=None,
        water_cropfactor=None,
        channel_gradient=None,
        channel_width=None,
        channel_length=None,
        mannings_n=None,
        surfacewater_storage_ini=None,
    ):

        # stand-alone QUAlloc: read the land mask
        self.landmask = read_file_entry(
            filename=self.model_configuration.general["clone"],
            variablename=self.model_configuration.general["landmask_ncvariable"],
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Boolean,
        )

        self.cellarea = read_file_entry(
            filename=self.model_configuration.general["cellarea"],
            variablename=self.model_configuration.general["cellarea_ncvariable"],
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )

        # initial conditions: files to exclude
        files_to_exclude = []

        # check the use of pumping capacity
        if (
            not self.model_flags["groundwater_pumping_capacity_flag"]
            or self.model_configuration.water_management[
                "groundwater_longterm_potential_withdrawal_ini"
            ]
            == "None"
        ):
            files_to_exclude.append("groundwater_longterm_potential_withdrawal_ini")
        if (
            not self.model_flags["surfacewater_pumping_capacity_flag"]
            or self.model_configuration.water_management[
                "surfacewater_longterm_potential_withdrawal_ini"
            ]
            == "None"
        ):
            files_to_exclude.append("surfacewater_longterm_potential_withdrawal_ini")

        if isinstance(self.initial_conditions, NoneType):
            # initial warm states
            self.initial_conditions = get_initial_conditions(
                self.model_configuration,
                self.model_time.startdate,
                files_to_exclude=files_to_exclude,
            )

        # reporting of the initial conditions
        self.report_initial_conditions_to_file = qualloc_report_initial_conditions(
            self.model_configuration, self.initial_conditions, self.model_flags
        )

        # forcing: all dynamic input for the selected time step
        inputpath = self.model_configuration.general["inputpath"]
        allow_year_substitution = True
        date_selection_method = "exact"
        datatype = pcr.Scalar

        # totals and rates
        forcing_totals = self.model_configuration.convert_string_to_input(
            self.model_configuration.forcing["totals"], str
        )
        forcing_rates = self.model_configuration.convert_string_to_input(
            self.model_configuration.forcing["rates"], str
        )

        # remove unused forcing variables (sectors)
        del_keys = []
        for forcing_variable, ncfileroot in forcing_variables.items():
            if f"{ncfileroot}_ncfile" not in self.model_configuration.forcing.keys():
                del_keys.append(forcing_variable)
        for del_key in del_keys:
            forcing_variables.pop(del_key, None)

        # coupled QUAlloc
        if online_coupling:
            del_keys = ["precipitation", "referencePotET", "direct_runoff", "interflow"]
            for del_key in del_keys:
                if del_key in forcing_variables.keys():
                    forcing_variables.pop(del_key, None)

        self.forcing_info = {}
        for forcing_variable, ncfileroot in forcing_variables.items():

            # netCDF file name and the variable it holds
            ncfilename = self.model_configuration.forcing["%s_ncfile" % ncfileroot]
            ncvariable = ncvariable_name(
                self.model_configuration.forcing, ncfileroot, forcing_variable
            )

            # type of variable
            if ncfileroot in forcing_totals:
                total_to_rate = True
            elif ncfileroot in forcing_rates:
                total_to_rate = False
            else:
                total_to_rate = False

            self.forcing_info[forcing_variable] = {
                "ncfilename": ncfilename,
                "ncvariable": ncvariable,
                "inputpath": inputpath,
                "datatype": datatype,
                "date_selection_method": date_selection_method,
                "allow_year_substitution": allow_year_substitution,
                "total_to_rate": total_to_rate,
            }

        logger.info("forcing information initialized")

        # groundwater; stand-alone QUAlloc: read the groundwater alpha
        self.initial_conditions["groundwater"]["groundwater_storage"] = pcr.ifthen(
            self.landmask,
            pcr.cover(self.initial_conditions["groundwater"]["groundwater_storage"], 0),
        )
        alpha = read_file_entry(
            filename=self.model_configuration.groundwater["alpha"],
            variablename="alpha",
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        alpha_default = read_file_entry(
            filename=self.model_configuration.groundwater["alpha_default"],
            variablename="alpha",
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        alpha = pcr.ifthen(self.landmask, pcr.cover(alpha, alpha_default))

        # initial total base flow and groundwater storage
        total_base_flow_ini = self.initial_conditions["groundwater"]["total_base_flow"]
        groundwater_storage_ini = self.initial_conditions["groundwater"][
            "groundwater_storage"
        ]

        self.groundwater = groundwater(
            alpha=alpha,
            total_base_flow_ini=total_base_flow_ini,
            storage_ini=groundwater_storage_ini,
        )

        alpha = None
        alpha_default = None
        total_base_flow_ini = None
        groundwater_storage_ini = None
        del alpha, alpha_default, total_base_flow_ini, groundwater_storage_ini

        # surface water: ldd, fractional water area, channel properties and initial storage

        # stand-alone QUAlloc
        self.initial_conditions["surfacewater"]["surfacewater_storage"] = pcr.ifthen(
            self.landmask,
            pcr.cover(
                self.initial_conditions["surfacewater"]["surfacewater_storage"], 0
            ),
        )
        surfacewater_storage_ini = self.initial_conditions["surfacewater"][
            "surfacewater_storage"
        ]

        ldd = read_file_entry(
            filename=self.model_configuration.surfacewater["ldd"],
            variablename=ncvariable_name(self.model_configuration.surfacewater, "ldd"),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Ldd,
        )
        fraction_water = read_file_entry(
            filename=self.model_configuration.surfacewater["fraction_water"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "fraction_water"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        water_cropfactor = read_file_entry(
            filename=self.model_configuration.surfacewater["water_cropfactor"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "water_cropfactor"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        channel_gradient = read_file_entry(
            filename=self.model_configuration.surfacewater["channel_gradient"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "channel_gradient"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        channel_width = read_file_entry(
            filename=self.model_configuration.surfacewater["channel_width"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "channel_width"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        channel_length = read_file_entry(
            filename=self.model_configuration.surfacewater["channel_length"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "channel_length"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        mannings_n = read_file_entry(
            filename=self.model_configuration.surfacewater["mannings_n"],
            variablename=ncvariable_name(
                self.model_configuration.surfacewater, "mannings_n"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )

        self.surfacewater = surfacewater(
            ldd=ldd,
            cellarea=self.cellarea,
            fraction_water=fraction_water,
            water_cropfactor=water_cropfactor,
            channel_gradient=channel_gradient,
            channel_width=channel_width,
            channel_length=channel_length,
            mannings_n=mannings_n,
            storage_ini=surfacewater_storage_ini,
        )

        ldd = None
        fraction_water = None
        water_cropfactor = None
        channel_gradient = None
        channel_width = None
        channel_depth = None
        channel_length = None
        mannings_n = None
        surfacewater_storage_ini = None
        del (
            ldd,
            fraction_water,
            water_cropfactor,
            channel_gradient,
            channel_width,
            channel_depth,
            channel_length,
            mannings_n,
            surfacewater_storage_ini,
        )

        # water management: sectors, sources and withdrawals
        sector_names = ["irrigation", "domestic", "industry", "livestock"]
        if "sector_names" in self.model_configuration.water_management.keys():
            sector_names = self.model_configuration.convert_string_to_input(
                self.model_configuration.water_management["sector_names"], str
            )

        source_names = ["groundwater", "surfacewater"]
        if "source_names" in self.model_configuration.water_management.keys():
            source_names = self.model_configuration.convert_string_to_input(
                self.model_configuration.water_management["source_names"], str
            )

        withdrawal_names = ["renewable", "nonrenewable"]
        if "withdrawal_names" in self.model_configuration.water_management.keys():
            withdrawal_names = self.model_configuration.convert_string_to_input(
                self.model_configuration.water_management["withdrawal_names"], str
            )

        # allocation zones
        groundwater_allocation_zones = read_file_entry(
            filename=self.model_configuration.water_management[
                "groundwater_allocation_zones"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "groundwater_allocation_zones",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Nominal,
        )
        surfacewater_allocation_zones = read_file_entry(
            filename=self.model_configuration.water_management[
                "surfacewater_allocation_zones"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "surfacewater_allocation_zones",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Nominal,
        )
        desalwater_allocation_zones = read_file_entry(
            filename=self.model_configuration.water_management[
                "desalwater_allocation_zones"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management, "desalwater_allocation_zones"
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Nominal,
        )
        groundwater_allocation_zones = pcr.ifthen(
            self.landmask & (groundwater_allocation_zones != 0),
            groundwater_allocation_zones,
        )
        surfacewater_allocation_zones = pcr.ifthen(
            self.landmask & (surfacewater_allocation_zones != 0),
            surfacewater_allocation_zones,
        )
        desalwater_allocation_zones = pcr.ifthen(
            self.landmask & (desalwater_allocation_zones != 0),
            desalwater_allocation_zones,
        )

        # withdrawal points
        groundwater_withdrawal_points = read_file_entry(
            filename=self.model_configuration.water_management[
                "groundwater_withdrawal_points"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "groundwater_withdrawal_points",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Ordinal,
        )
        surfacewater_withdrawal_points = read_file_entry(
            filename=self.model_configuration.water_management[
                "surfacewater_withdrawal_points"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "surfacewater_withdrawal_points",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Ordinal,
        )
        desalwater_withdrawal_points = read_file_entry(
            filename=self.model_configuration.water_management[
                "desalwater_withdrawal_points"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "desalwater_withdrawal_points",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Ordinal,
        )
        groundwater_withdrawal_points = pcr.cover(groundwater_withdrawal_points, 0)
        surfacewater_withdrawal_points = pcr.cover(surfacewater_withdrawal_points, 0)
        desalwater_withdrawal_points = pcr.cover(desalwater_withdrawal_points, 0)

        # withdrawal capacity
        groundwater_withdrawal_capacity = read_file_entry(
            filename=self.model_configuration.water_management[
                "groundwater_withdrawal_capacity"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "groundwater_withdrawal_capacity",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        surfacewater_withdrawal_capacity = read_file_entry(
            filename=self.model_configuration.water_management[
                "surfacewater_withdrawal_capacity"
            ],
            variablename=ncvariable_name(
                self.model_configuration.water_management,
                "surfacewater_withdrawal_capacity",
            ),
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )

        # long-term values at time intervals identified by dates: a dictionary with dates as keys and
        # maps of long-term water availability as values, read by the initial conditions module; if
        # None or a single map/value is given, a dictionary is created with missing values for the
        # undefined cells

        # dummy year and corresponding dates for the water management module (monthly intervals only)
        dummy_year = self.model_time.startdate.year
        water_management_dates = [
            datetime.datetime(dummy_year, month, 1) for month in range(1, 13)
        ]

        # long-term groundwater availability from the long-term groundwater storage (m at the end of the day)
        self.initial_conditions["water_management"]["groundwater_longterm_storage"] = (
            get_initial_condition_as_timed_dict(
                self.initial_conditions["water_management"][
                    "groundwater_longterm_storage"
                ],
                water_management_dates,
                missing_value=water_management_missing_value,
                message_str="Setting initial long-term groundwater storage",
            )
        )

        # long-term surface water availability from the long-term discharge (m3/s)
        self.initial_conditions["water_management"][
            "surfacewater_longterm_discharge"
        ] = get_initial_condition_as_timed_dict(
            self.initial_conditions["water_management"][
                "surfacewater_longterm_discharge"
            ],
            water_management_dates,
            missing_value=water_management_missing_value,
            message_str="Setting initial long-term surface water discharge",
        )

        # long-term surface water availability from the long-term total runoff (m/day)
        self.initial_conditions["water_management"]["surfacewater_longterm_runoff"] = (
            get_initial_condition_as_timed_dict(
                self.initial_conditions["water_management"][
                    "surfacewater_longterm_runoff"
                ],
                water_management_dates,
                missing_value=water_management_missing_value,
                message_str="Setting initial long-term surface water total runoff",
            )
        )

        # long-term gross sectoral water demand (m/day)
        gross_demand_longterm = {}
        for sector_name in sector_names:
            var = "gross_demand_longterm_%s" % sector_name
            self.initial_conditions["water_management"][var] = (
                get_initial_condition_as_timed_dict(
                    self.initial_conditions["water_management"][var],
                    water_management_dates,
                    missing_value=water_management_missing_value,
                    message_str="Setting initial long-term %s gross water demand"
                    % sector_name,
                )
            )

            gross_demand_longterm[sector_name] = self.initial_conditions[
                "water_management"
            ][var]

        # long-term potential withdrawal per source (m3/day)
        longterm_potential_withdrawal = {}
        if self.model_flags["groundwater_pumping_capacity_flag"]:
            self.initial_conditions["water_management"][
                "groundwater_longterm_potential_withdrawal"
            ] = get_initial_condition_as_timed_dict(
                self.initial_conditions["water_management"][
                    "groundwater_longterm_potential_withdrawal"
                ],
                water_management_dates,
                missing_value=water_management_missing_value,
                message_str="Setting initial long-term groundwater potential withdrawal",
            )

            longterm_potential_withdrawal["groundwater"] = self.initial_conditions[
                "water_management"
            ]["groundwater_longterm_potential_withdrawal"]

        if self.model_flags["surfacewater_pumping_capacity_flag"]:
            self.initial_conditions["water_management"][
                "surfacewater_longterm_potential_withdrawal"
            ] = get_initial_condition_as_timed_dict(
                self.initial_conditions["water_management"][
                    "surfacewater_longterm_potential_withdrawal"
                ],
                water_management_dates,
                missing_value=water_management_missing_value,
                message_str="Setting initial long-term surface water potential withdrawal",
            )

            longterm_potential_withdrawal["surfacewater"] = self.initial_conditions[
                "water_management"
            ]["surfacewater_longterm_potential_withdrawal"]

        # weights per water source
        groundwater_update_weight = read_file_entry(
            filename=self.model_configuration.water_management[
                "groundwater_update_weight"
            ],
            variablename="groundwater_update_weight",
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )
        surfacewater_update_weight = read_file_entry(
            filename=self.model_configuration.water_management[
                "surfacewater_update_weight"
            ],
            variablename="surfacewater_update_weight",
            inputpath=self.model_configuration.general["inputpath"],
            clone_attributes=self.model_configuration.clone_attributes,
            datatype=pcr.Scalar,
        )

        # weights per sector
        gross_demand_update_weight = {}
        for sector_name in sector_names:
            var = "%s_update_weight" % sector_name
            gross_demand_update_weight[sector_name] = read_file_entry(
                filename=self.model_configuration.water_management[var],
                variablename=var,
                inputpath=self.model_configuration.general["inputpath"],
                clone_attributes=self.model_configuration.clone_attributes,
                datatype=pcr.Scalar,
            )

        # prioritization: source names including desalinated water use
        source_names_prioritization = source_names.copy()
        if (
            self.model_flags["desalinated_water_use_flag"]
            and "desalwater" not in source_names
        ):
            source_names_prioritization.append("desalwater")

        # by default, all sectors are prioritized per source
        prioritization = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.spatial(pcr.scalar(1.00)))
                    for sector_name in sector_names
                ),
            )
            for source_name in source_names_prioritization
        )

        # prioritization from the configuration file (if specified)
        for source_name in source_names_prioritization:
            for sector_name in sector_names:

                key = "prioritization_%s_%s" % (source_name, sector_name)

                if key in self.model_configuration.water_management.keys():

                    values = read_file_entry(
                        filename=self.model_configuration.water_management[key],
                        variablename=self.model_configuration.water_management[key],
                        inputpath=self.model_configuration.general["inputpath"],
                        clone_attributes=self.model_configuration.clone_attributes,
                        datatype=pcr.Scalar,
                    )

                    # fill and mask
                    var_out = pcr.cover(
                        values, prioritization[source_name][sector_name]
                    )
                    var_out = pcr.ifthen(self.landmask, var_out)

                    prioritization[source_name][sector_name] = var_out

        self.water_management = water_management(
            landmask=self.landmask,
            cellarea=self.cellarea,
            time_increment=self.model_configuration.water_management["time_increment"],
            time_step=self.model_time.time_increment,
            time_step_length=self.model_time.time_step_length,
            desalwater_allocation_zones=desalwater_allocation_zones,
            desalwater_withdrawal_points=desalwater_withdrawal_points,
            groundwater_allocation_zones=groundwater_allocation_zones,
            groundwater_withdrawal_points=groundwater_withdrawal_points,
            groundwater_withdrawal_capacity=groundwater_withdrawal_capacity,
            groundwater_update_weight=groundwater_update_weight,
            groundwater_longterm_storage=self.initial_conditions["water_management"][
                "groundwater_longterm_storage"
            ],
            surfacewater_allocation_zones=surfacewater_allocation_zones,
            surfacewater_withdrawal_points=surfacewater_withdrawal_points,
            surfacewater_withdrawal_capacity=surfacewater_withdrawal_capacity,
            surfacewater_update_weight=surfacewater_update_weight,
            surfacewater_longterm_discharge=self.initial_conditions["water_management"][
                "surfacewater_longterm_discharge"
            ],
            surfacewater_longterm_runoff=self.initial_conditions["water_management"][
                "surfacewater_longterm_runoff"
            ],
            longterm_potential_withdrawal=longterm_potential_withdrawal,
            gross_demand_update_weight=gross_demand_update_weight,
            gross_demand_longterm=gross_demand_longterm,
            total_return_flow_ini=self.initial_conditions["water_management"][
                "total_return_flow"
            ],
            prioritization=prioritization,
            sector_names=sector_names,
            source_names=source_names,
            withdrawal_names=withdrawal_names,
            water_quality_flag=self.model_flags["water_quality_flag"],
            desalinated_water_use_flag=self.model_flags["desalinated_water_use_flag"],
            groundwater_pumping_capacity_flag=self.model_flags[
                "groundwater_pumping_capacity_flag"
            ],
            surfacewater_pumping_capacity_flag=self.model_flags[
                "surfacewater_pumping_capacity_flag"
            ],
        )

        # remove temporary variables
        groundwater_allocation_zones = None
        surfacewater_allocation_zones = None
        groundwater_withdrawal_points = None
        surfacewater_withdrawal_points = None
        groundwater_withdrawal_capacity = None
        surfacewater_withdrawal_capacity = None
        desalwater_allocation_zones = None
        desalwater_withdrawal_points = None
        gross_demand_update_weight = None
        gross_demand_longterm = None
        prioritization = None
        source_names_prioritization = None
        sector_names = None
        source_names = None
        withdrawal_names = None

        del (
            groundwater_allocation_zones,
            surfacewater_allocation_zones,
            groundwater_withdrawal_points,
            surfacewater_withdrawal_points,
            groundwater_withdrawal_capacity,
            surfacewater_withdrawal_capacity,
            desalwater_allocation_zones,
            desalwater_withdrawal_points,
            gross_demand_update_weight,
            gross_demand_longterm,
            prioritization,
            source_names_prioritization,
            sector_names,
            source_names,
            withdrawal_names,
        )

        # forcing variables for water demand
        self.gross_demand_forcing_vars = {}
        self.net_demand_forcing_vars = {}

        for forcing_variable in forcing_variables.keys():
            for sector_name in self.water_management.sector_names:
                for demand_name_root in ["%s_gross_demand", "%sgrossdemand"]:
                    if forcing_variable.lower() == (demand_name_root % sector_name):
                        self.gross_demand_forcing_vars[sector_name] = (
                            forcing_variable.lower()
                        )

                for demand_name_root in [
                    "%s_net_demand",
                    "%snetdemand",
                    "%s_netto_demand",
                    "%snettodemand",
                ]:
                    if forcing_variable.lower() == (demand_name_root % sector_name):
                        self.net_demand_forcing_vars[sector_name] = (
                            forcing_variable.lower()
                        )

        # check for missing sectors
        for sector_name in self.gross_demand_forcing_vars.keys():
            if sector_name not in self.net_demand_forcing_vars.keys():
                self.net_demand_forcing_vars[sector_name] = (
                    self.gross_demand_forcing_vars[sector_name]
                )

        for sector_name in self.net_demand_forcing_vars.keys():
            if sector_name not in self.gross_demand_forcing_vars.keys():
                self.gross_demand_forcing_vars[sector_name] = (
                    self.net_demand_forcing_vars[sector_name]
                )

        message_str = (
            "Water demand per sector is associated to the following forcing variables:"
        )
        for sector_name in self.water_management.sector_names:
            message_str = str.join(
                "\n",
                (
                    message_str,
                    "Gross: %20s; Net: %20s"
                    % (
                        self.gross_demand_forcing_vars[sector_name],
                        self.net_demand_forcing_vars[sector_name],
                    ),
                ),
            )

        logger.info(message_str)

        # water quality: standard constituents
        constituent_names = ["temperature", "organic", "salinity", "pathogen"]

        # water quality thresholds per sector and constituent
        constituent_limits = {}
        for sector_name in self.water_management.sector_names:
            constituent_limits[sector_name] = {}

            for constituent_name in constituent_names:
                var = "limit_%s_%s" % (constituent_name, sector_name)

                if var in self.model_configuration.water_quality.keys():
                    limit = self.model_configuration.water_quality[var]
                else:
                    limit = None
                    logger.info(
                        "A threshold value for %s was not specified, an unattainable value of %s is assigned."
                        % (constituent_name, unattainable_threshold)
                    )

                # replace None with an unreachable threshold
                if limit == "None":
                    limit = str(unattainable_threshold)

                # the netCDF file and variable must have the same name
                ncvariable = os.path.basename(limit).split(".")[0]

                limit = read_file_entry(
                    filename=limit,
                    variablename=ncvariable,
                    inputpath=self.model_configuration.general["inputpath"],
                    clone_attributes=self.model_configuration.clone_attributes,
                    datatype=pcr.Scalar,
                )

                constituent_limits[sector_name][constituent_name] = limit

        # long-term water quality: dictionary with dates as keys and maps as values, read by the
        # initial conditions module
        for source_name in self.water_management.source_names:
            for constituent_name in constituent_names:
                var = "%s_longterm_%s" % (source_name, constituent_name)

                if self.model_flags["water_quality_flag"]:
                    # whether the constituent has long-term water quality data
                    if var + "_ini" in self.model_configuration.water_quality.keys():
                        constituent_longterm_quality = self.initial_conditions[
                            "water_quality"
                        ][var]
                    else:
                        constituent_longterm_quality = dict(
                            (date, pcr.spatial(pcr.scalar(0)))
                            for date in water_management_dates
                        )
                        logger.info(
                            "Long-term %s was not specified, a value of zero is assigned."
                            % constituent_name
                        )

                # zero concentrations if water quality is not evaluated
                else:
                    constituent_longterm_quality = dict(
                        (date, pcr.spatial(pcr.scalar(0)))
                        for date in water_management_dates
                    )

                # update the format of the initial conditions
                self.initial_conditions["water_quality"][var] = (
                    get_initial_condition_as_timed_dict(
                        initial_condition=constituent_longterm_quality,
                        dates=water_management_dates,
                        missing_value=water_management_missing_value,
                        message_str="Setting initial long-term %s state for %s source"
                        % (constituent_name, source_name),
                    )
                )

        # short-term water quality forcing information
        self.water_quality_forcing_info = {}

        for source_name in self.water_management.source_names:
            for constituent_name in constituent_names:
                var = "%s_%s" % (source_name, constituent_name)

                # whether the constituent has short-term water quality data
                if self.model_flags["water_quality_flag"]:
                    if var + "_ncfile" in self.model_configuration.water_quality.keys():
                        ncfilename = self.model_configuration.water_quality[
                            var + "_ncfile"
                        ]
                    else:
                        ncfilename = "0.0"
                        message_str = str.join(
                            "\n",
                            (
                                "Concentration values of %s for %s source"
                                % (constituent_name, source_name),
                                "were not specified, a value of zero is assigned.",
                            ),
                        )
                        logger.info(message_str)

                # zero concentrations if water quality is not evaluated
                else:
                    ncfilename = "0.0"

                self.water_quality_forcing_info[var] = {
                    "ncfilename": ncfilename,
                    "ncvariable": water_quality_forcing_variables[var],
                    "inputpath": self.model_configuration.general["inputpath"],
                }

        self.water_quality = water_quality(
            landmask=self.landmask,
            time_increment=self.model_configuration.water_management["time_increment"],
            source_names=self.water_management.source_names,
            constituent_names=constituent_names,
            constituent_limits=constituent_limits,
            quality_update_weight={
                "surfacewater": surfacewater_update_weight,
                "groundwater": groundwater_update_weight,
            },
            surfacewater_longterm_temperature=self.initial_conditions["water_quality"][
                "surfacewater_longterm_temperature"
            ],
            groundwater_longterm_temperature=self.initial_conditions["water_quality"][
                "groundwater_longterm_temperature"
            ],
            surfacewater_longterm_organic=self.initial_conditions["water_quality"][
                "surfacewater_longterm_organic"
            ],
            groundwater_longterm_organic=self.initial_conditions["water_quality"][
                "groundwater_longterm_organic"
            ],
            surfacewater_longterm_salinity=self.initial_conditions["water_quality"][
                "surfacewater_longterm_salinity"
            ],
            groundwater_longterm_salinity=self.initial_conditions["water_quality"][
                "groundwater_longterm_salinity"
            ],
            surfacewater_longterm_pathogen=self.initial_conditions["water_quality"][
                "surfacewater_longterm_pathogen"
            ],
            groundwater_longterm_pathogen=self.initial_conditions["water_quality"][
                "groundwater_longterm_pathogen"
            ],
        )

        # remove water quality and other temporary variables
        constituent_limits = None
        constituent_names = None
        groundwater_update_weight = None
        surfacewater_update_weight = None

        del (
            constituent_limits,
            constituent_names,
            groundwater_update_weight,
            surfacewater_update_weight,
        )

        message_str = "Water quality module is activated"
        logger.info(message_str)

        setattr(self.water_management, "water_quality", self.water_quality)

        return None

    def update(
        self,
        online_coupling_to_quantity=False,
        irrigationGrossDemand=None,
        domesticGrossDemand=None,
        domesticNettoDemand=None,
        industryGrossDemand=None,
        industryNettoDemand=None,
        livestockGrossDemand=None,
        livestockNettoDemand=None,
        manufactureGrossDemand=None,
        manufactureNettoDemand=None,
        thermoelectricGrossDemand=None,
        thermoelectricNettoDemand=None,
        environmentGrossDemand=None,
        surfacewater_storage=None,
        surfacewater_discharge=None,
        surfacewater_totalrunoff=None,
        groundwater_recharge=None,
        groundwater_baseflow=None,
        groundwater_storage=None,
        online_coupling_to_quality=False,
        surfacewater_temperature=None,
        surfacewater_organic=None,
        surfacewater_salinity=None,
        surfacewater_pathogen=None,
        groundwater_temperature=None,
        groundwater_organic=None,
        groundwater_salinity=None,
        groundwater_pathogen=None,
    ):

        date = self.model_time.date

        # forcing: hydrology; stand-alone QUAlloc
        if not online_coupling_to_quantity:
            for forcing_variable in forcing_variables.keys():

                var_out = read_file_entry(
                    filename=self.forcing_info[forcing_variable]["ncfilename"],
                    variablename=self.forcing_info[forcing_variable]["ncvariable"],
                    inputpath=self.forcing_info[forcing_variable]["inputpath"],
                    clone_attributes=self.model_configuration.clone_attributes,
                    datatype=self.forcing_info[forcing_variable]["datatype"],
                    date=date,
                    date_selection_method=self.forcing_info[forcing_variable][
                        "date_selection_method"
                    ],
                    allow_year_substitution=self.forcing_info[forcing_variable][
                        "allow_year_substitution"
                    ],
                )

                # clip to the land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))

                # convert totals to rates (m/month to m/day); by default, precipitation, referencePotET,
                # groundwater_recharge, direct_runoff, interflow and irrigation are in m/month and the domestic,
                # industry, livestock, manufacture, thermoelectric and environment demands in m/day
                if self.forcing_info[forcing_variable]["total_to_rate"]:
                    var_out = var_out / self.model_time.time_step_length

                setattr(self, forcing_variable.lower(), var_out)

                logger.debug(
                    "information on %s read for %s" % (forcing_variable.lower(), date)
                )

        # coupled QUAlloc (PCR-GLOBWB): forcing variables in m/day
        else:
            for forcing_variable in forcing_variables.keys():
                var_out = eval(forcing_variable)

                # clip to the land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))

                setattr(self, forcing_variable.lower(), var_out)

                logger.debug(
                    "information on %s imported from PCR-GLOBWB2 for %s"
                    % (forcing_variable.lower(), date)
                )

        # forcing: water quality
        constituent_shortterm_quality = {}

        for source_name in self.water_management.source_names:
            constituent_shortterm_quality[source_name] = {}
            for constituent_name in self.water_quality.constituent_names:
                key = "%s_%s" % (source_name, constituent_name)

                # value if the dataset is available
                if self.model_flags["water_quality_flag"]:

                    # stand-alone QUAlloc
                    if not online_coupling_to_quality:
                        var_out = read_file_entry(
                            filename=self.water_quality_forcing_info[key]["ncfilename"],
                            variablename=self.water_quality_forcing_info[key][
                                "ncvariable"
                            ],
                            inputpath=self.water_quality_forcing_info[key]["inputpath"],
                            clone_attributes=self.model_configuration.clone_attributes,
                            datatype=pcr.Scalar,
                            date=date,
                            date_selection_method="nearest",
                            allow_year_substitution=False,
                        )
                        logger.debug(
                            "information on %s %s short-term quality read for %s"
                            % (source_name, constituent_name, date)
                        )

                    # coupled QUAlloc (DynQual)
                    else:
                        var_out = eval(key)
                        msg_str = (
                            "information on %s %s short-term quality imported from DynQual for %s"
                            % (source_name, constituent_name, date)
                        )

                        # zeros if the variable is None
                        if isinstance(var_out, NoneType):
                            var_out = pcr.spatial(pcr.scalar(0))
                            msg_str = (
                                "no %s %s short-term quality is given for %s; a value of zero is considered"
                                % (source_name, constituent_name, date)
                            )

                        logger.debug(msg_str)

                # zero if the dataset is not available
                else:
                    var_out = pcr.spatial(pcr.scalar(0))
                    logger.debug(
                        "no %s %s short-term quality is given for %s; a value of zero is considered"
                        % (source_name, constituent_name, date)
                    )

                # cover NaN with zero concentration and clip to the land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))

                constituent_shortterm_quality[source_name][constituent_name] = var_out
                setattr(self, key, var_out)

        setattr(
            self.water_management.water_quality,
            "constituent_shortterm_quality",
            constituent_shortterm_quality,
        )

        # forcing: water management; desalinated water use (if activated)
        flag_name = "desalinated_water_use_flag"
        file_name = "desalinated_water_use"
        if self.model_flags[flag_name]:

            var_out = read_file_entry(
                filename=self.model_configuration.water_management[file_name],
                variablename=file_name,
                inputpath=self.model_configuration.general["inputpath"],
                clone_attributes=self.model_configuration.clone_attributes,
                datatype=pcr.Scalar,
                date=date,
                date_selection_method="exact",
                allow_year_substitution=True,
            )

            # clip to the land mask
            var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))

            setattr(self, file_name, var_out)

            logger.debug("information on %s read for %s" % (file_name, date))

        # regional pumping capacity (if activated)
        for source_name in self.water_management.source_names:
            flag_name = "%s_pumping_capacity_flag" % source_name
            file_name = "%s_regional_pumping_capacity" % source_name

            if self.model_flags[flag_name]:
                # on 1 January, as values are yearly totals; TODO: also handle the first time step if the run
                # does not start on 1 January
                if date.day == 1 and date.month == 1:
                    regional_pumping_capacity = {}

                    # regional pumping capacity and ids
                    for var, dtype in [
                        ("regional_pumping_limit", pcr.Scalar),
                        ("region_ids", pcr.Nominal),
                        ("region_ratios", pcr.Scalar),
                    ]:

                        var_out = read_file_entry(
                            filename=self.model_configuration.water_management[
                                file_name
                            ],
                            variablename=var,
                            inputpath=self.model_configuration.general["inputpath"],
                            clone_attributes=self.model_configuration.clone_attributes,
                            datatype=dtype,
                            date=datetime.datetime(date.year, 1, 1),
                            date_selection_method="exact",
                            allow_year_substitution=True,
                        )

                        # cover NaN with zero and clip to the land mask
                        var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))

                        regional_pumping_capacity[var] = var_out

                    setattr(
                        self,
                        "%s_pumping_capacity" % source_name,
                        regional_pumping_capacity,
                    )

                    logger.debug(
                        "information on %s regional pumping capacity read for %s"
                        % (source_name, date)
                    )

        # long-term

        if date.day == 1:

            # update the withdrawal capacity from the regional pumping capacity (if activated)
            for source_name in self.water_management.source_names:
                flag_name = "%s_pumping_capacity_flag" % source_name

                if self.model_flags[flag_name]:
                    # on 1 January, as values are yearly totals; TODO: also handle the first time step if the run
                    # does not start on 1 January
                    if date.day == 1 and date.month == 1:

                        regional_pumping_capacity = getattr(
                            self, "%s_pumping_capacity" % source_name
                        )

                        # withdrawal capacity (m3/day)
                        self.water_management.update_withdrawal_capacity(
                            source_name=source_name,
                            regional_pumping_limit=regional_pumping_capacity[
                                "regional_pumping_limit"
                            ],
                            region_ids=regional_pumping_capacity["region_ids"],
                            region_ratios=regional_pumping_capacity["region_ratios"],
                            time_step_length=self.model_time.time_step_length,
                            date=date,
                        )
                    logger.info(
                        "Pumping capacity is considered to limit %s withdrawals for %s."
                        % (date, source_name)
                    )

            # long-term availability for the date (m3/day)
            surfacewater_availability, groundwater_availability = (
                self.water_management.get_longterm_availability_for_date(
                    date=date,
                    ldd=self.surfacewater.ldd,
                    waterdepth=self.surfacewater.storage,
                    mannings_n=self.surfacewater.mannings_n,
                    channel_gradient=self.surfacewater.channel_gradient,
                    channel_width=self.surfacewater.channel_width,
                    channel_length=self.surfacewater.channel_length,
                    time_step_seconds=self.model_time.seconds_per_day,
                )
            )

            # long-term gross sectoral water demands for the date (m3/day)
            gross_demand_per_sector = (
                self.water_management.get_longterm_demand_for_date(date=date)
            )

            # allocate the long-term demand to the long-term availability for the date and time increment,
            # returning the met (renewable) and potentially unmet (non-renewable) withdrawal per source
            self.water_management.update_longterm_potential_withdrawals_for_date(
                availability={
                    "surfacewater": surfacewater_availability,
                    "groundwater": groundwater_availability,
                },
                demand=gross_demand_per_sector,
                date=date,
            )

        # the actual renewable and non-renewable withdrawals are initialized with the allocation of the
        # demand to the potential withdrawals, then updated iteratively; unmet demand is passed on to
        # the other sources within the same zone
        source_names_to_be_processed = self.water_management.sources_unmet_demand[:]

        # short-term

        # gross and net demand per sector for the current date
        gross_demand_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.water_management.sector_names
        )
        net_demand_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.water_management.sector_names
        )

        for sector_name in self.water_management.sector_names:
            # add the demand per sector to the gross and net demand (m3/day)
            gross_demand_per_sector[sector_name] = (
                gross_demand_per_sector[sector_name]
                + getattr(self, self.gross_demand_forcing_vars[sector_name])
                * self.cellarea
            )
            net_demand_per_sector[sector_name] = (
                net_demand_per_sector[sector_name]
                + getattr(self, self.net_demand_forcing_vars[sector_name])
                * self.cellarea
            )

        logger.debug("Water demand read for %s" % self.model_time.date)

        # pass the water demand to the water management module (m3/day)
        self.water_management.update_water_demand_for_date(
            gross_demand=gross_demand_per_sector,
            net_demand=net_demand_per_sector,
            date=date,
        )

        # allocate the desalinated water use to the selected sectors (domestic and manufacture) (m3/day)
        if self.model_flags["desalinated_water_use_flag"]:
            self.water_management.allocate_desalinated_water_for_date(
                availability=self.desalinated_water_use * self.cellarea, date=date
            )

        # update the potential withdrawals from the short-term gross water demands (m3/day)
        self.water_management.update_shortterm_potential_withdrawals_for_date(date)

        # surface water withdrawal: remove surface water from the potential sources to reuse
        source_name = "surfacewater"
        source_names_to_be_processed.remove(source_name)

        # total potential withdrawal per sector: the sum of the non-renewable and renewable withdrawals (m3/day)
        potential_withdrawal_per_sector = (
            self.water_management.get_total_potential_withdrawal(source_name)
        )

        # available surface water; stand-alone QUAlloc
        if not online_coupling_to_quantity:
            # channel runoff (m/day)
            self.channel_runoff = (
                self.precipitation
                - self.surfacewater.water_cropfactor * self.referencepotet
            )

            # return flow (m/day)
            total_return_flow = self.water_management.total_return_flow / self.cellarea

            # total runoff (m/day)
            self.surfacewater.get_total_runoff(
                direct_runoff=self.direct_runoff,
                interflow=self.interflow,
                base_flow=self.groundwater.total_base_flow
                / self.model_time.time_step_length,
                channel_runoff=self.channel_runoff,
                return_flow=total_return_flow,
                date=date,
            )

            # available surface water: storage at the start of the time step plus the total runoff over
            # the time step (m/day)
            surfacewater_available = (
                self.surfacewater.storage * self.surfacewater.fraction_water
                + self.surfacewater.total_runoff
            )

        # coupled QUAlloc
        else:
            # surface water availability is the channel storage (m/day)
            surfacewater_available = deepcopy(surfacewater_storage)

            # total runoff (m/day)
            self.surfacewater.total_runoff = deepcopy(surfacewater_totalrunoff)

        # actual withdrawals: short-term potential surface water withdrawal per sector, based on water
        # quality and the actual surface water availability (m3/day)
        potential_withdrawal_per_sector = self.water_management.update_surfacewater_potential_withdrawals(
            surfacewater_available=surfacewater_available,
            longterm_potential_withdrawal_per_sector=potential_withdrawal_per_sector,
        )

        potential_withdrawal = sum_list(list(potential_withdrawal_per_sector.values()))

        # stand-alone QUAlloc
        if not online_coupling_to_quantity:
            # actual renewable withdrawals, by routing the total runoff with the potential withdrawals (m3/day)
            actual_withdrawal = self.surfacewater.update(
                potential_withdrawal=potential_withdrawal,
                time_step_seconds=self.model_time.seconds_per_day,
            )

        # coupled QUAlloc
        else:
            # actual renewable withdrawals, based on the instantaneous channel storage (m3/day)
            actual_withdrawal = pcr.ifthen(
                pcr.defined(self.surfacewater.ldd),
                pcr.max(
                    0,
                    pcr.min(
                        potential_withdrawal, surfacewater_available * self.cellarea
                    ),
                ),
            )

            # discharge (m3/s) and surface water storage (m) of the surface water module
            self.surfacewater.storage = deepcopy(surfacewater_storage)
            self.surfacewater.discharge = deepcopy(surfacewater_discharge)

        # redistribute the renewable withdrawal by sector (m3/day)
        renewable_withdrawal = deepcopy(actual_withdrawal)
        renewable_withdrawal_per_sector = dict(
            (
                sector_name,
                actual_withdrawal
                * pcr_return_val_div_zero(
                    potential_withdrawal_per_sector[sector_name],
                    potential_withdrawal,
                    very_small_number,
                ),
            )
            for sector_name in self.water_management.sector_names
        )

        # no non-renewable withdrawal: all surface water withdrawals are currently renewable
        nonrenewable_withdrawal = pcr.ifthen(self.landmask, pcr.scalar(0))
        nonrenewable_withdrawal_per_sector = dict(
            (sector_name, nonrenewable_withdrawal)
            for sector_name in self.water_management.sector_names
        )

        # set the actual surface water withdrawal and add any unmet demand to the potential
        # non-renewable withdrawal of the remaining allowable sources
        self.water_management.update_withdrawals(
            source_name=source_name,
            renewable_withdrawal_per_sector=renewable_withdrawal_per_sector,
            nonrenewable_withdrawal_per_sector=nonrenewable_withdrawal_per_sector,
            source_names_to_be_processed=source_names_to_be_processed,
            water_available=surfacewater_available * self.cellarea,
            date=self.model_time.date,
        )

        # groundwater withdrawal: base flow is the total over the time step, used to compute the water
        # availability; it is passed directly from the groundwater to the surface water module, as it
        # lags by one time step
        source_name = "groundwater"
        source_names_to_be_processed.remove(source_name)

        # total potential withdrawal per sector: the sum of the non-renewable and renewable withdrawals (m3/day)
        potential_withdrawal_per_sector = (
            self.water_management.get_total_potential_withdrawal(source_name)
        )

        # available groundwater; stand-alone QUAlloc
        if not online_coupling_to_quantity:
            # total withdrawal of all sectors as water slice (m/day)
            potential_withdrawal = (
                sum_list(list(potential_withdrawal_per_sector.values())) / self.cellarea
            )

            # update the total base flow and total recharge (m/period)
            self.groundwater.get_storage(
                recharge=self.groundwater_recharge,
                potential_withdrawal=potential_withdrawal,
                time_step_length=self.model_time.time_step_length,
                date=self.model_time.date,
            )

            # available groundwater: storage at the start of the period (month) plus the total recharge
            # minus the total base flow over the period (m at the end of the period)
            storage = self.groundwater.storage + (
                self.groundwater.total_recharge - self.groundwater.total_base_flow
            )

            groundwater_available = deepcopy(storage)

        # coupled QUAlloc
        else:
            # groundwater availability is the groundwater storage (m/day)
            storage = deepcopy(groundwater_storage)
            groundwater_available = deepcopy(storage)

            # total recharge and total base flow (m/day)
            self.groundwater.total_recharge = deepcopy(self.groundwater_recharge)
            self.groundwater.total_base_flow = deepcopy(groundwater_baseflow)

        # actual withdrawals: short-term potential groundwater withdrawal per sector, based on water
        # quality and the actual groundwater availability (m3/period)
        potential_withdrawal_per_sector, groundwater_availability = (
            self.water_management.update_groundwater_potential_withdrawals(
                groundwater_available=groundwater_available,
                longterm_potential_withdrawal_per_sector=potential_withdrawal_per_sector,
                time_step_length=self.model_time.time_step_length,
            )
        )

        potential_withdrawal = sum_list(list(potential_withdrawal_per_sector.values()))

        # actual renewable and non-renewable withdrawals (m3/day)
        renewable_withdrawal = pcr.min(groundwater_availability, potential_withdrawal)

        nonrenewable_withdrawal = pcr.max(
            0, potential_withdrawal - renewable_withdrawal
        )

        renewable_withdrawal /= self.model_time.time_step_length
        nonrenewable_withdrawal /= self.model_time.time_step_length

        # update the storage (renewable groundwater storage before withdrawals, in m); stand-alone QUAlloc
        if not online_coupling_to_quantity:
            # (m/period)
            self.groundwater.update(
                renewable_withdrawal * self.model_time.time_step_length / self.cellarea,
                nonrenewable_withdrawal
                * self.model_time.time_step_length
                / self.cellarea,
            )

        # coupled QUAlloc
        else:
            # groundwater storage for the current date
            self.groundwater.storage = deepcopy(groundwater_storage)

        # redistribute the renewable withdrawals by sector (m3/day)
        renewable_withdrawal_per_sector = dict(
            (
                sector_name,
                renewable_withdrawal
                * pcr_return_val_div_zero(
                    potential_withdrawal_per_sector[sector_name],
                    potential_withdrawal,
                    very_small_number,
                ),
            )
            for sector_name in self.water_management.sector_names
        )

        # redistribute the non-renewable withdrawals by sector (m3/day)
        nonrenewable_withdrawal_per_sector = dict(
            (
                sector_name,
                nonrenewable_withdrawal
                * pcr_return_val_div_zero(
                    potential_withdrawal_per_sector[sector_name],
                    potential_withdrawal,
                    very_small_number,
                ),
            )
            for sector_name in self.water_management.sector_names
        )

        # set the actual groundwater withdrawal and add any unmet demand to the potential
        # non-renewable withdrawal of the remaining allowable sources
        self.water_management.update_withdrawals(
            source_name=source_name,
            renewable_withdrawal_per_sector=renewable_withdrawal_per_sector,
            nonrenewable_withdrawal_per_sector=nonrenewable_withdrawal_per_sector,
            source_names_to_be_processed=source_names_to_be_processed,
            water_available=groundwater_availability,
            date=self.model_time.date,
        )

        # water allocation: allocate the actual withdrawals to the demands and get the consumption and
        # return flows
        self.water_management.allocate_withdrawal_to_demand_for_date(
            date=self.model_time.date,
            availability={
                "surfacewater": surfacewater_available * self.cellarea,
                "groundwater": groundwater_availability,
            },
        )

        # long-term updating: long-term variables are accumulated over the month and divided by the
        # number of days in the time increment (monthly = 1, daily = 28-31) on the last day, to obtain
        # the monthly average

        # long-term water availability: groundwater storage (m/day), surface water discharge (m3/s)
        # and surface water runoff (m/day)
        self.water_management.update_longterm_availability(
            groundwater_storage=storage,
            surfacewater_discharge=self.surfacewater.discharge,
            surfacewater_runoff=self.surfacewater.total_runoff,
            date=date,
        )

        # long-term gross water demands (m/day)
        self.water_management.update_longterm_demand(date=date)

        # long-term potential withdrawal (m3/day)
        self.water_management.update_longterm_potential_withdrawals(date=date)

        # long-term water quality (degC, mg/L, cfu/100mL)
        self.water_management.water_quality.update_longterm_quality(
            source_names=self.water_management.source_names,
            time_step=self.model_time.time_increment,
            date=date,
        )

        return None

    def finalize_year(self):

        logger.info(
            "last day of year %d: updating water availability, demand and quality"
            % self.model_time.year
        )

        self.water_management.update_annual_water_availability()
        self.water_management.update_annual_water_demand()
        self.water_management.water_quality.update_annual_water_quality(
            source_names=self.water_management.source_names
        )

        # write the final states as the new initial conditions
        logger.info("last day of year %d: writing states" % self.model_time.year)

        self.update_initial_conditions(self.model_time.date)
        self.report_initial_conditions(self.model_time.date)

    def finalize_run(self):

        logger.info("final time step: closing down all files")

        # close the caches
        self.report_initial_conditions_to_file.close()
        close_nc_cache()

        return None

    def update_initial_conditions(self, date):
        """
        update_initial_conditions: function that updates the initial conditions from \
        the different modules that are required to start with a warm state.
        Returns None
        """

        for module_name in self.modules:

            # first get the states of the present module
            if module_name != "water_quality":
                state_info = getattr(self, module_name).get_final_conditions()
            else:
                state_info = self.water_management.water_quality.get_final_conditions()

            if not module_name in self.initial_conditions.keys():
                self.initial_conditions[module_name] = {}

            for key, value in state_info.items():
                self.initial_conditions[module_name][key] = value

        logger.info("Initial conditions updated for %s" % date)

        return None

    def report_initial_conditions(self, date):
        """
        report_initial_conditions: functions that report the initial conditions to file.
        Returns None
        """

        self.report_initial_conditions_to_file.report(date, self.initial_conditions)

        return None
