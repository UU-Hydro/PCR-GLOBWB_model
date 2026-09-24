import datetime
import logging
import sys
from copy import deepcopy

import pcraster as pcr

from qualloc.allocation import (
    allocate_demand_to_availability_with_options,
    allocate_demand_to_withdrawals,
    get_key,
    get_zonal_total,
    obtain_allocation_ratio,
)
from qualloc.basic_functions import (
    max_dicts,
    pcr_get_statistics,
    pcr_return_val_div_zero,
    sum_list,
)
from qualloc.model_time import (
    get_weights_from_dates,
    is_last_day_month,
    match_date_by_julian_number,
)

logger = logging.getLogger(__name__)

NoneType = type(None)

# small number to avoid division by zero in PCRaster
very_small_number = 1.00e-12

# missing id
mid = -1

# missing value for water management options, including the long-term water availability;
# missing values are treated with defaults when allocating water demand to resources and
# updating the long-term availability
water_management_missing_value = -9.99

# for debugging only
debug = True


def water_balance_check(
    states_ini,
    states_end,
    cellarea,
    process_name,
    var_name,
    date,
    zones=None,
    flag_warning=True,
    flag_debug=False,
    threshold=1e-5,
):
    """
    water_balance_check :
                   function to evaluate the water balance for a list of
                   input and output map files

    input:
    =====
    states_ini   : list of variable names of the initial state of variables
                   before processing, to be aggregated (units: m3/day)
    states_end   : list of variable names of the final state of variables
                   after processing, to be aggregated (units: m3/day)
    cellarea     : PCRaster map with cell area (units: m2)
    process_name : string with the name of the process evaluated
    date         : string with the current date
    zones        : PCRaster map with allocation zones per water source used to
                   aggregate water volumes
    flag_warning : boolean to specify if QUAlloc must get halted if water balance
                   does not close (False) or only print a warning (True, default)
    flag_debug   : boolean to specify if map is reported (True) in case the water
                   balance does not close or not (False, default)
    threshold    : float, minimum value allowed to determined if the water balance
                   is closed (units: m water-slice)
    """

    in_map = pcr.spatial(pcr.scalar(0.0))
    out_map = pcr.spatial(pcr.scalar(0.0))

    # aggregate all water on each side of the process
    for state_ini in states_ini:
        in_map += state_ini
    for state_end in states_end:
        out_map += state_end

    # aggregate the water volumes over the allocation zones
    if not isinstance(zones, NoneType):
        in_map = get_zonal_total(in_map, zones)
        out_map = get_zonal_total(out_map, zones)
        cellarea = get_zonal_total(cellarea, zones)

    # difference as water slice
    diff = (in_map - out_map) / cellarea
    vmin = pcr.cellvalue(pcr.mapminimum(diff), 1)[0]

    if vmin >= -threshold:
        msg = "[ %.10s Water Balance ] %s (%s): OK" % (date, process_name, var_name)
        if vmin < 0:
            msg += " (max mismatch of %.2e m)" % vmin
        logger.debug(msg)

    else:
        msg = "\n#################################################################################################################################################################\n"
        msg += (
            "WARNING !!!!!!!! [ Water Balance Error ] %s (%s): max mismatch of %.10f m [ %s ]"
            % (process_name, var_name, vmin, date)
        )
        msg += "\n#################################################################################################################################################################\n"
        logger.error(msg)

        if flag_debug:
            pcr.aguila(diff, diff * cellarea)

        if not flag_warning:
            sys.exit()


def estimate_waterdepth_from_discharge(
    discharge,
    waterdepth,
    mannings_n,
    channel_width,
    channel_gradient,
    beta=0.60,
    max_iterations=25,
    convergence_limit=1.0e-4,
):
    """
    estimate_waterdepth_from_discharge :
                       function to estimate the water depth correspondent to a discharge;
                       values are obtained by iteration, starting by a water depth of the
                       previous time-step

    input:
    =====
    discharge         : PCRaster map with discharge values (units: m3/s)
    waterdepth        : PCRaster map with water depth to start iteration (units: m)
    mannings_n        : PCRaster map with Manning's coefficient [m^-1/3*s]
    channel_width     : PCRaster map with the width for a rectangular channel (units: m)
    channel_gradient  : PCRaster map with the gradient along the channel (units: m/m)
    beta              : float, exponent in equatio Area = alpha * Q ** beta
    max_iterations    : integer, maximum number of iterations to calculate the correspondent
                        water depth to the input discharge
    convergence_limit : float, minimum convergence value expected to stop the iterative
                        process; calculated as the difference between the currently
                        estimated water depth and the one from the previous time-step

    output:
    ======
    waterdepth       : water depth at the end of the time-step based on the discharge
                       and the channel parameters (units: m)
    """

    # mask where water is present
    discharge_mask = discharge > 0

    icnt = 0
    convergence = False

    while icnt < max_iterations and not convergence:

        waterdepth_old = pcr.max(0.001, waterdepth)

        # wetted perimeter (m) of a rectangular channel and the corresponding alpha of the equation
        # A = alpha * Q ** beta
        wetted_perimeter = channel_width + 2 * waterdepth_old
        alpha = (
            mannings_n * wetted_perimeter ** (2.0 / 3.0) * channel_gradient**-0.5
        ) ** beta

        # new water depth
        wetted_area = alpha * discharge**beta
        waterdepth = pcr.max(0.001, wetted_area / channel_width)

        # check convergence of the water depth
        conv_value = pcr.cellvalue(
            pcr.mapmaximum(pcr.abs(waterdepth - waterdepth_old)), 1
        )[0]
        convergence = conv_value < convergence_limit

        icnt = icnt + 1

    waterdepth = pcr.ifthenelse(discharge_mask, waterdepth, pcr.scalar(0))

    message_str = (
        "water depth converged after %d iterations with a maximum deviation of %.3g"
        % (icnt, conv_value)
    )
    print(message_str)

    return waterdepth


"""
water_management: read in the monthly long-term availability for the discharge \
and the base flow.
"""


class water_management(object):
    """
water management module: class that holds the water management module of \
the QUAlloc model and manages water use through allocation and withdrawal.

Currently, only surface water and groundwater are considered but this can be \
expanded to include desalinated water too.
Also, it assumed that each cell receives water from a predined set of points \
for one resource only, i.e., zones are mutually exclusive per resource.
At the moment, all withdrawal points are fixed in time and the withdrawal \
capacity is not considered.
time_increment                    : time increment to be used;
                                    currently only monthly and yearly allowed
                                    and this refers to the update of the with-
                                    drawals given the long-term availability;
desalwater_allocation_zones,
surfacewater_allocation_zones,
groundwater_allocation_zones      : nominal map with the ID of the allocation
                                    zone per resource identified by non-zero
                                    values;
desalwater_withdrawal_points,
surfacewater_withdrawal_points,
groundwater_withdrawal_points     : map with the withdrawal points falling
                                    in a zone; this should be an ordinal map
                                    that gives each point a unique ID and
                                    that can be used to track local with-
                                    drawals and assign the withdrawal capac-
                                    ity.
surfacewater_withdrawal_capacity,
groundwater_withdrawal_capacity   : the capacity [m^3/day] to withdraw water
                                    from the resource specified. Currently,
                                    this can only be None, in which case the
                                    abstraction is unlimited or set to a pre-
                                    defined rate at the location. If with-
                                    drawal points were to become dynamic,
                                    this could be linked to the allocated
                                    demand and capped by a pre-defined capac-
                                    ity per region, as currenly is done in
                                    PCR-GLOBWB 2 with the groundwater pumping
                                    capacity.
surfacewater_update_weight,
groundwater_update_weight         : weight, defined as 1/N years, by which
                                    the long-term average water availability,
                                    abstractions and return flows are updat-
                                    ed with the current conditions [year^-1],
                                    weight should be greater than 0 and less
                                    than 1;
prioritization                    : priority for the allocation of the total
                                    demand to the available withdrawals, dimen-
                                    sionless, as a dictionary with the sector
                                    names as keys and scalar PCRaster fields
                                    as values; default value is None, in which
                                    case all sectors are given equal weight;
                                    priorities are given in ascending order,
                                    the lowest value having the highest prior-
                                    ity; priorities can be defined locally as
                                    maps but are spatially compared; currently,
                                    a single prioritization is provided but
                                    internally the sources surface water and
                                    groundwater are already distinguished.

Long-term averages per month need to be provided for the following variables
as monthly netCDFs:
surfacewater_longterm_dischage_ini        : long-term average monthly surface
                                            water discharge [m3/s]
surfacewater_longterm_runoff_ini           : long-term average monthly surface
                                            water runoff [m/day]
groundwater_longterm_storage_ini          : long-term average monthly groundwater
                                            storage [m per day]

# and the total return flow needs to be initialized, default is None,
# in which case it is set to zero
total_return_flow_ini                      : total return flow [m3/day]

"""

    def __init__(
        self,
        landmask,
        cellarea,
        time_increment,
        time_step,
        time_step_length,
        desalwater_allocation_zones,
        desalwater_withdrawal_points,
        groundwater_allocation_zones,
        groundwater_withdrawal_points,
        groundwater_withdrawal_capacity,
        groundwater_update_weight,
        groundwater_longterm_storage,
        surfacewater_allocation_zones,
        surfacewater_withdrawal_points,
        surfacewater_withdrawal_capacity,
        surfacewater_update_weight,
        surfacewater_longterm_discharge,
        surfacewater_longterm_runoff,
        longterm_potential_withdrawal,
        gross_demand_update_weight,
        gross_demand_longterm,
        total_return_flow_ini=None,
        prioritization=None,
        sector_names=["irrigation", "domestic", "industry", "livestock"],
        source_names=["groundwater", "surfacewater"],
        withdrawal_names=["renewable", "nonrenewable"],
        water_quality_flag=False,
        desalinated_water_use_flag=False,
        groundwater_pumping_capacity_flag=False,
        surfacewater_pumping_capacity_flag=False,
    ):
        """
        water management class requires the following input for its initialization:

            Input:
            ======
                landmask,
                time_increment,
                groundwater_allocation_zones,
                groundwater_withdrawal_points,
                groundwater_withdrawal_capacity,
                groundwater_update_weight,
                groundwater_longterm_baseflow,
                surfacewater_allocation_zones,
                surfacewater_withdrawal_points,
                surfacewater_withdrawal_capacity,
                surfacewater_update_weight,
                surfacewater_longterm_discharge,
                surfacewater_longterm_runoff,
                total_return_flow_ini = None
                prioritization       = None
                sector_names         = ['irrigation','domestic','industry','livestock']
                source_names         = ['groundwater','surfacewater']
                water_quality_flag                 = False
                desalinated_water_use_flag         = False
                groundwater_pumping_capacity_flag  = False
                surfacewater_pumping_capacity_flag = False
        See doc string of class for detailed info.

        """

        object.__init__(self)

        self.landmask = landmask

        self.cellarea = cellarea

        # source names used to process the withdrawals; largely ignored here, as the processing of the
        # different sources may vary
        self.source_names = source_names

        self.sector_names = sector_names

        # withdrawal types (renewable and non-renewable; hard-coded)
        self.withdrawal_names = withdrawal_names

        # settings to allocate demand to the availability (hard-coded, refer to the allocation functions);
        # time increment for updating the withdrawals from the long-term availability (monthly or yearly)
        self.time_increment = time_increment
        self.time_step = time_step
        self.time_step_length = time_step_length

        # use_local_first: boolean map indicating whether the local availability is used first; the flag
        # gives its overall setting for logging
        self.use_local_first = pcr.spatial(pcr.boolean(1))
        self.use_local_first_flag = (
            pcr.cellvalue(pcr.mapmaximum(pcr.scalar(self.use_local_first)), 1)[0] == 1
        )

        # reallocate_surplus: use any surplus to satisfy local demand
        self.reallocate_surplus = True

        # sources_unmet_demand: sequence of the sources for unmet demand (any or all available sources;
        # the first is the default); formerly surface water and groundwater, allocated proportionally
        # to the withdrawals
        self.sources_unmet_demand = ["surfacewater", "groundwater"]

        # pumping_capacity_flag: whether the withdrawal capacity caps the groundwater abstraction
        self.pumping_capacity_flag = {
            "surfacewater": surfacewater_pumping_capacity_flag,
            "groundwater": groundwater_pumping_capacity_flag,
        }

        # desalinated_water_use_flag: whether desalinated water contributes to the water supply before
        # the allocation from surface water and groundwater
        self.desalinated_water_use_flag = desalinated_water_use_flag

        # water_quality_flag: whether surface water quality caps the surface water availability
        self.water_quality_flag = water_quality_flag

        # withdrawal and allocation information: (1) the id per allocation zone in which the available
        # water is matched to the demand, (2) the withdrawal points, identified by the allocation zone
        # ids, and (3) the withdrawal capacity at the withdrawal points (m3/day); all are maps (nominal
        # ids, scalar capacity); a withdrawal capacity of None means unlimited withdrawal

        # allocation zones per sector
        self.groundwater_allocation_zones = dict(
            (sector_name, groundwater_allocation_zones) for sector_name in sector_names
        )
        self.surfacewater_allocation_zones = dict(
            (sector_name, surfacewater_allocation_zones) for sector_name in sector_names
        )
        self.desalwater_allocation_zones = dict(
            (sector_name, desalwater_allocation_zones) for sector_name in sector_names
        )

        # sectors that can use desalinated water
        self.sector_names_desalwater = ["domestic", "industry", "manufacture"]

        # sectors that can only withdraw surface water from their local zone (i.e. the same cell)
        self.sectors_local_surfacewater = ["thermoelectric", "environment"]

        # for these sectors, each cell is its own allocation zone
        for sector_name in self.sectors_local_surfacewater:
            if sector_name in self.sector_names:
                self.surfacewater_allocation_zones[sector_name] = pcr.ifthen(
                    pcr.scalar(surfacewater_allocation_zones) > 0,
                    pcr.nominal(
                        pcr.uniqueid(
                            pcr.ifthen(
                                pcr.scalar(surfacewater_allocation_zones) > 0,
                                pcr.boolean(1),
                            )
                        )
                    ),
                )

                self.groundwater_allocation_zones[sector_name] = pcr.ifthen(
                    pcr.scalar(groundwater_allocation_zones) > 0,
                    pcr.nominal(
                        pcr.uniqueid(
                            pcr.ifthen(
                                pcr.scalar(groundwater_allocation_zones) > 0,
                                pcr.boolean(1),
                            )
                        )
                    ),
                )

                # alternatively, set all groundwater allocation zones to missing values; all later calculations
                # must then be covered with zeros

        # withdrawal capacity per source
        self.groundwater_withdrawal_capacity = groundwater_withdrawal_capacity
        self.surfacewater_withdrawal_capacity = surfacewater_withdrawal_capacity

        # mask the withdrawal capacity
        if not isinstance(self.groundwater_withdrawal_capacity, NoneType):
            self.groundwater_withdrawal_capacity = pcr.ifthen(
                self.landmask, pcr.cover(self.groundwater_withdrawal_capacity, 0.0)
            )
        if not isinstance(self.surfacewater_withdrawal_capacity, NoneType):
            self.surfacewater_withdrawal_capacity = pcr.ifthen(
                self.landmask, pcr.cover(self.surfacewater_withdrawal_capacity, 0.0)
            )

        # withdrawal points
        self.desalwater_withdrawal_points = desalwater_withdrawal_points
        self.groundwater_withdrawal_points = groundwater_withdrawal_points
        self.surfacewater_withdrawal_points = surfacewater_withdrawal_points

        # prioritization per source and sector: equal weights if None, otherwise priorities in ascending
        # order (lowest value, highest priority); priorities can be maps but are compared spatially
        source_names_prioritization = deepcopy(self.source_names)
        if desalinated_water_use_flag and "desalwater" not in source_names:
            source_names_prioritization.append("desalwater")

        self.prioritization = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(1))))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in source_names_prioritization
        )

        if isinstance(prioritization, dict):
            for source_name in source_names_prioritization:
                for sector_name in self.sector_names:
                    self.prioritization[source_name][sector_name] = pcr.cover(
                        prioritization[source_name][sector_name],
                        self.prioritization[source_name][sector_name],
                    )

        # include the effect of the allocation zones: sectors that can only withdraw from local sources
        # get a higher priority (surface water and groundwater only)
        for source_name in self.source_names:
            zones = getattr(self, "%s_allocation_zones" % source_name)
            for sector_name in self.sector_names:
                n_cells = get_zonal_total(
                    pcr.ifthen(pcr.defined(zones[sector_name]), pcr.scalar(1)),
                    zones[sector_name],
                )
                self.prioritization[source_name][sector_name] = (
                    self.prioritization[source_name][sector_name] * n_cells
                )

        # long-term water availability: groundwater_longterm_storage (m at the end of the time step),
        # surfacewater_longterm_discharge (m3/s) and surfacewater_longterm_runoff (m/day)
        self.groundwater_longterm_storage = groundwater_longterm_storage
        self.surfacewater_longterm_discharge = surfacewater_longterm_discharge
        self.surfacewater_longterm_runoff = surfacewater_longterm_runoff

        # sorted dates of the long-term water availability
        self.groundwater_longterm_storage_dates = sorted(
            list(self.groundwater_longterm_storage.keys())
        )
        self.surfacewater_longterm_discharge_dates = sorted(
            list(self.surfacewater_longterm_discharge.keys())
        )
        self.surfacewater_longterm_runoff_dates = sorted(
            list(self.surfacewater_longterm_runoff.keys())
        )

        # long-term sectoral gross water demands (m/day) and their sorted dates
        for sector_name in self.sector_names:
            setattr(
                self,
                "gross_demand_longterm_%s" % sector_name,
                gross_demand_longterm[sector_name],
            )

            setattr(
                self,
                "gross_demand_longterm_%s_dates" % sector_name,
                sorted(list(gross_demand_longterm[sector_name].keys())),
            )

        # initial long-term potential surface water and groundwater withdrawal, to distribute the pumping
        # capacity (m3/day)
        for source_name in self.source_names:
            if self.pumping_capacity_flag[source_name]:
                if source_name == "groundwater":
                    # long-term groundwater potential withdrawal (m3/day) and its sorted dates
                    self.groundwater_longterm_potential_withdrawal = (
                        longterm_potential_withdrawal[source_name]
                    )

                    self.groundwater_longterm_pot_withdrawal_dates = sorted(
                        list(self.groundwater_longterm_potential_withdrawal.keys())
                    )

                if source_name == "surfacewater":
                    # long-term surface water potential withdrawal (m3/day) and its sorted dates
                    self.surfacewater_longterm_potential_withdrawal = (
                        longterm_potential_withdrawal[source_name]
                    )

                    self.surfacewater_longterm_pot_withdrawal_dates = sorted(
                        list(self.surfacewater_longterm_potential_withdrawal.keys())
                    )

        # weights to update the long-term water availability
        self.groundwater_update_weight = groundwater_update_weight
        self.surfacewater_update_weight = surfacewater_update_weight

        # weights to update the long-term sectoral gross water demand
        for sector_name in self.sector_names:
            setattr(
                self,
                "%s_update_weight" % sector_name,
                gross_demand_update_weight[sector_name],
            )

        # total (annual weighted average) long-term availability, in the units of the monthly values
        self.groundwater_total_storage = pcr.scalar(0)
        self.surfacewater_total_discharge = pcr.scalar(0)
        self.surfacewater_total_runoff = pcr.scalar(0)
        self.update_annual_water_availability()

        # total (annual weighted average) long-term demand (m3/day)
        for sector_name in self.sector_names:
            setattr(self, "gross_demand_total_%s" % sector_name, pcr.scalar(0))
        self.update_annual_water_demand()

        # sectoral gross and net water demand per cell (volume)
        self.gross_demand = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )
        self.net_demand = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )

        # total gross and net demand, consumption, return flow, total withdrawal and total allocated
        # demand per cell
        self.total_gross_demand = pcr.spatial(pcr.scalar(0))
        self.total_net_demand = pcr.spatial(pcr.scalar(0))
        self.total_consumption = pcr.spatial(pcr.scalar(0))
        self.total_return_flow = pcr.spatial(pcr.scalar(0))
        self.total_withdrawal = pcr.spatial(pcr.scalar(0))
        self.total_allocation = pcr.spatial(pcr.scalar(0))

        # use the initial total return flow if provided (m3/day)
        if not isinstance(total_return_flow_ini, NoneType):
            self.total_return_flow = pcr.cover(
                pcr.scalar(total_return_flow_ini), self.total_return_flow
            )

        # potential renewable and non-renewable withdrawal per source
        self.potential_renewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )
        self.potential_nonrenewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )

        # actual renewable and non-renewable withdrawal per source
        self.actual_renewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )
        self.actual_nonrenewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )

        # unused renewable and non-renewable withdrawal per source
        self.unused_renewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )
        self.unused_nonrenewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )

        # allocated withdrawal and demand as nested dictionaries (combined withdrawal/source name, then
        # sector name), and the consumption and return flow per cell from the allocation
        self.consumed_demand_per_sector = {}
        self.return_flow_demand_per_sector = {}
        self.allocated_withdrawal_per_sector = {}
        self.allocated_demand_per_sector = {}

        for withdrawal_name in self.withdrawal_names:
            for source_name in self.source_names:

                key = get_key([withdrawal_name, source_name])

                self.allocated_withdrawal_per_sector[key] = dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in sector_names
                )

                self.allocated_demand_per_sector[key] = dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in sector_names
                )

                self.consumed_demand_per_sector[key] = dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in sector_names
                )

                self.return_flow_demand_per_sector[key] = dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in sector_names
                )

        # idem for desalinated water use
        self.allocated_withdrawal_per_sector_desalwater = dict(
            (sector_name, pcr.spatial(pcr.scalar(0))) for sector_name in sector_names
        )

        self.allocated_demand_per_sector_desalwater = dict(
            (sector_name, pcr.spatial(pcr.scalar(0))) for sector_name in sector_names
        )

        self.consumed_demand_per_sector_desalwater = dict(
            (sector_name, pcr.spatial(pcr.scalar(0))) for sector_name in sector_names
        )

        self.return_flow_demand_per_sector_desalwater = dict(
            (sector_name, pcr.spatial(pcr.scalar(0))) for sector_name in sector_names
        )

        # state names: availability
        self.report_state_info = {
            "total_return_flow": "total_return_flow",
            "surfacewater_longterm_discharge": "surfacewater_longterm_discharge",
            "surfacewater_longterm_runoff": "surfacewater_longterm_runoff",
            "groundwater_longterm_storage": "groundwater_longterm_storage",
        }

        # gross demands
        for sector_name in self.sector_names:
            state_name = "gross_demand_longterm_%s" % sector_name
            self.report_state_info[state_name] = state_name

        # withdrawal capacity
        for source_name in self.source_names:
            if self.pumping_capacity_flag[source_name]:
                if source_name == "groundwater":
                    self.report_state_info[
                        "groundwater_longterm_potential_withdrawal"
                    ] = "groundwater_longterm_potential_withdrawal"
                if source_name == "surfacewater":
                    self.report_state_info[
                        "surfacewater_longterm_potential_withdrawal"
                    ] = "surfacewater_longterm_potential_withdrawal"

        # log the selected processing options
        message_str = "water demand options are processed with the following options:"
        for option_str in [
            "time_increment",
            "use_local_first_flag",
            "reallocate_surplus",
        ]:
            message_str = str.join(
                "\n\t",
                (message_str, "%-20s: %s" % (option_str, getattr(self, option_str))),
            )
        if isinstance(self.sources_unmet_demand, NoneType):
            message_str = str.join(
                "\n\t",
                (
                    message_str,
                    "No source is set for non-renewable",
                    "withdrawals and any demand that",
                    "is not met by the renewable resources,",
                    "is forfeited.",
                ),
            )
        else:
            sub_message_str = str.join(", ", (self.source_names))
            message_str = str.join(
                "\n\t",
                (
                    message_str,
                    "The following non-renewable sources are set to satisfy any unmet demand:",
                    sub_message_str,
                ),
            )
        for source_name in self.source_names:
            if self.pumping_capacity_flag[source_name]:
                message_str = str.join(
                    "\n\t",
                    (
                        message_str,
                        "Pumping capacity is considered to limit the %s abstraction."
                        % source_name,
                    ),
                )
        if self.water_quality_flag:
            message_str = str.join(
                "\n\t",
                (
                    message_str,
                    "Water quality is considered to determine the actual water availability.",
                ),
            )

        logger.info(message_str)

        return None

    def update_annual_water_availability(self):
        """
        update the total water availability over the year.
        """

        logger.info("annual water availability updated")

        # annual weighted averages, with the dates as keys

        # long-term total groundwater availability (storage, m at the end of the time step)
        weights = get_weights_from_dates(self.groundwater_longterm_storage_dates)
        self.groundwater_total_storage = sum(
            list(
                weights[date] * self.groundwater_longterm_storage[date]
                for date in self.groundwater_longterm_storage_dates
            )
        )

        # long-term total surface water availability (discharge, m3/s)
        weights = get_weights_from_dates(self.surfacewater_longterm_discharge_dates)
        self.surfacewater_total_discharge = sum(
            list(
                weights[date] * self.surfacewater_longterm_discharge[date]
                for date in self.surfacewater_longterm_discharge_dates
            )
        )

        # long-term total surface water availability (runoff, m/day)
        weights = get_weights_from_dates(self.surfacewater_longterm_runoff_dates)
        self.surfacewater_total_runoff = sum(
            list(
                weights[date] * self.surfacewater_longterm_runoff[date]
                for date in self.surfacewater_longterm_runoff_dates
            )
        )

        return None

    def update_annual_water_demand(self):
        """
        update the total water availability over the year.
        """

        logger.info("annual gross water demands updated")

        # long-term total sectoral gross water demands (m3/day)
        for sector_name in self.sector_names:
            var_value = getattr(self, "gross_demand_longterm_%s" % sector_name)
            var_dates = getattr(self, "gross_demand_longterm_%s_dates" % sector_name)
            weights = get_weights_from_dates(var_dates)
            setattr(
                self,
                "gross_demand_total_%s" % sector_name,
                sum(list(weights[date] * var_value[date] for date in var_dates)),
            )

        return None

    def update_withdrawal_capacity(
        self,
        source_name,
        regional_pumping_limit,
        region_ids,
        region_ratios,
        time_step_length,
        date,
    ):
        """
        update_withdrawal_capacity :
                                 function to calculate the withdrawal capacity
                                 based on the regional pumping capacity volumes reported
                                 over predefined regions.

        input:
        =====
        regional_pumping_limit : PCRaster map with regional values (same value across
                                 the region) of maximum water pumping capacity
                                 (units: billion cubic meters/year)
        region_ids             : PCRaster map with regional ID (units: nominal)
        region_ratio           : PCRaster map with scalar values that scale the actual
                                 pumping capacity comprised within the land mask (units: m3/m3)
        time_step_length       : integer, number of days in a period (e.g., 30 days/month)
        date                   : string, date of the update
        """

        # scale the regional pumping capacity to the land mask and convert from billion m3 to m3 per year
        regional_pumping_limit = regional_pumping_limit * region_ratios * 1000000000

        # long-term potential withdrawal per source (m3/day)
        if source_name == "groundwater":
            longterm_potential_withdrawal = deepcopy(
                self.groundwater_longterm_potential_withdrawal
            )
        if source_name == "surfacewater":
            longterm_potential_withdrawal = deepcopy(
                self.surfacewater_longterm_potential_withdrawal
            )

        # rate of water available during the month (m3/m3)
        maximum_monthly_longterm_potential_withdrawal = max_dicts(
            longterm_potential_withdrawal
        )

        total_maximum_monthly_longterm_potential_withdrawal = get_zonal_total(
            maximum_monthly_longterm_potential_withdrawal, region_ids
        )

        withdrawal_rate = pcr_return_val_div_zero(
            maximum_monthly_longterm_potential_withdrawal,
            total_maximum_monthly_longterm_potential_withdrawal,
            very_small_number,
        )

        # withdrawal capacity (m3/day)
        withdrawal_capacity = (
            regional_pumping_limit * withdrawal_rate / (12 * time_step_length)
        )
        if source_name == "groundwater":
            self.groundwater_withdrawal_capacity = pcr.ifthen(
                self.landmask, pcr.cover(withdrawal_capacity, 0.0)
            )
        if source_name == "surfacewater":
            self.surfacewater_withdrawal_capacity = pcr.ifthen(
                self.landmask, pcr.cover(withdrawal_capacity, 0.0)
            )

        return None

    def get_longterm_availability_for_date(
        self,
        date,
        ldd,
        waterdepth,
        mannings_n,
        channel_gradient,
        channel_width,
        channel_length,
        time_step_seconds=86400,
    ):
        """
        get_longterm_availability_for_date:
                                    function that gets the water availability for the time base
                                    to be used (monthly, in which case the date is matched to the
                                    nearest date in the availability; or yearly, in which case the
                                    total long-term availability is used)

        input:
        =====
        date                      : string, date of the update
        ldd                       : PCRaster map with flow directions
        waterdepth                : PCRaster map with water depth to start iteration (units: m)
        mannings_n                : PCRaster map with Manning's coefficient (units: m^-1/3*s)
        channel_gradient          : PCRaster map with the gradient along the channel (units: m/m)
        channel_width             : PCRaster map with the width for a rectangular channel (units: m)
        channel_length            : PCRaster map with the length of the channel (units: m)

        output:
        ======
        surfacewater_availability,
        groundwater_availability  : PCRaster map with the long-term surfacewater nad groundwater
                                    availability (m3/day)
        """

        message_str = (
            "Long-term water availability for %s base on %s time increment"
            % (date, self.time_increment)
        )

        self.average_groundwater_storage = pcr.spatial(pcr.scalar(0))
        self.average_surfacewater_discharge = pcr.spatial(pcr.scalar(0))
        self.average_surfacewater_runoff = pcr.spatial(pcr.scalar(0))

        # long-term water availability: set the long-term values, patch missing values with the pumping
        # capacity (if available), fill the rest with zeros, and limit the availability to the pumping
        # capacity (if available) and the withdrawal points

        if self.time_increment == "monthly":
            # groundwater and surface water availability for the matching date

            # groundwater storage (m per day)
            date_index, matched_date, sub_message_str = match_date_by_julian_number(
                date, self.groundwater_longterm_storage_dates
            )
            groundwater_storage = self.groundwater_longterm_storage[matched_date]

            message_str = str.join("\n", (message_str, sub_message_str))

            # surface water discharge (m3/s) and runoff (m/day)
            date_index, matched_date, sub_message_str = match_date_by_julian_number(
                date, self.surfacewater_longterm_discharge_dates
            )
            surfacewater_discharge = self.surfacewater_longterm_discharge[matched_date]

            date_index, matched_date, sub_message_str = match_date_by_julian_number(
                date, self.surfacewater_longterm_runoff_dates
            )
            surfacewater_runoff = self.surfacewater_longterm_runoff[matched_date]

            message_str = str.join("\n", (message_str, sub_message_str))

        elif self.time_increment == "yearly":
            # long-term totals: groundwater storage (m per day), surface water discharge (m3/s) and runoff (m/day)
            groundwater_storage = self.groundwater_total_storage
            surfacewater_discharge = self.surfacewater_total_discharge
            surfacewater_runoff = self.surfacewater_total_runoff

        else:
            logger.error(
                "the option %s for the time increment in the water management module is not allowed!"
            )
            sys.exit()

        # surface water: average daily discharge from the upstream cell plus the total runoff of this cell (m3/s)
        discharge = (
            pcr.upstream(ldd, surfacewater_discharge)
            + surfacewater_runoff * self.cellarea / time_step_seconds
        )

        # average daily water depth for this discharge (m per day)
        channel_depth = estimate_waterdepth_from_discharge(
            discharge=discharge,
            waterdepth=waterdepth,
            mannings_n=mannings_n,
            channel_width=channel_width,
            channel_gradient=channel_gradient,
        )

        # surface water availability (m3/day)
        surfacewater_availability = channel_depth * channel_width * channel_length

        # groundwater availability (m3/day)
        groundwater_availability = groundwater_storage * self.cellarea

        # exclude non-zero availability
        groundwater_availability = pcr.ifthen(
            groundwater_availability >= 0, groundwater_availability
        )
        surfacewater_availability = pcr.ifthen(
            surfacewater_availability >= 0, surfacewater_availability
        )

        # check for missing data; updates of the local availability do not affect the long-term
        # availability stored in the water management instance
        missing_availability = self.landmask & (
            pcr.pcrnot(pcr.defined(groundwater_availability))
            | pcr.pcrnot(pcr.defined(surfacewater_availability))
        )
        missing_availability_flag = (
            pcr.cellvalue(pcr.mapmaximum(pcr.scalar(missing_availability)), 1)[0] == 1
        )

        # patch missing cells with the pumping capacity if available: groundwater
        if not isinstance(self.groundwater_withdrawal_capacity, NoneType):
            groundwater_availability = pcr.cover(
                groundwater_availability, self.groundwater_withdrawal_capacity
            )
        # surface water
        if not isinstance(self.surfacewater_withdrawal_capacity, NoneType):
            surfacewater_availability = pcr.cover(
                surfacewater_availability, self.surfacewater_withdrawal_capacity
            )

        # warn if availability is missing and no capacity is defined
        if missing_availability_flag:

            message_str = str.join(
                "\n",
                (
                    message_str,
                    "Warning: long-term water availability contains missing values;",
                ),
            )

            if not isinstance(self.groundwater_withdrawal_capacity, NoneType):
                message_str = str.join(
                    "\n",
                    (
                        message_str,
                        "by default it is set to the pumping capacity for groundwater;",
                    ),
                )
            else:
                message_str = str.join(
                    "\n",
                    (message_str, "by default, zero values are added for groundwater;"),
                )

            if not isinstance(self.surfacewater_withdrawal_capacity, NoneType):
                message_str = str.join(
                    "\n",
                    (
                        message_str,
                        "by default it is set to the pumping capacity for surface water.",
                    ),
                )
            else:
                message_str = str.join(
                    "\n",
                    (
                        message_str,
                        "by default, zero values are added for surface water.",
                    ),
                )

        # cover the availability with zeros over the land mask
        surfacewater_availability = pcr.ifthen(
            self.landmask, pcr.cover(surfacewater_availability, 0)
        )
        groundwater_availability = pcr.ifthen(
            self.landmask, pcr.cover(groundwater_availability, 0)
        )

        # limit the availability to the pumping capacity
        if not isinstance(self.groundwater_withdrawal_capacity, NoneType):
            message_str = str.join(
                "\n",
                (
                    message_str,
                    "groundwater withdrawals are limited to the pumping capacity",
                ),
            )
            groundwater_availability = pcr.min(
                self.groundwater_withdrawal_capacity, groundwater_availability
            )

        if not isinstance(self.surfacewater_withdrawal_capacity, NoneType):
            message_str = str.join(
                "\n",
                (
                    message_str,
                    "surface water withdrawals are limited to the pumping capacity",
                ),
            )
            surfacewater_availability = pcr.min(
                self.surfacewater_withdrawal_capacity, surfacewater_availability
            )

        # and to the withdrawal points
        groundwater_availability = pcr.ifthenelse(
            pcr.scalar(self.groundwater_withdrawal_points) != 0,
            groundwater_availability,
            0,
        )
        surfacewater_availability = pcr.ifthenelse(
            pcr.scalar(self.surfacewater_withdrawal_points) != 0,
            surfacewater_availability,
            0,
        )

        return surfacewater_availability, groundwater_availability

    def get_longterm_demand_for_date(self, date):
        """
        get_longterm_demand_for_date:
                                  function to obtain the long-term sectoral gross water demands
                                  for current date

        input:
        =====
        date                    : string, date of the update

        output:
        ======
        gross_demand_per_sector : dictionary with sector names as keys (string) and PCRaster maps
                                  with long-term sectoral gross water demand as values in m3/day
                                  for the current day
        """

        message_str = (
            "Long-term sectoral gross water demand for %s base on %s time increment"
            % (date, self.time_increment)
        )

        gross_demand_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )

        self.average_gross_demand = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )

        # long-term sectoral gross water demand (m/day)
        if self.time_increment == "monthly":

            # water demand per sector for the matching date
            for sector_name in self.sector_names:
                var_value = getattr(self, "gross_demand_longterm_%s" % sector_name)
                var_dates = getattr(
                    self, "gross_demand_longterm_%s_dates" % sector_name
                )

                date_index, matched_date, sub_message_str = match_date_by_julian_number(
                    date, var_dates
                )
                gross_demand_per_sector[sector_name] += var_value[matched_date]

                message_str = str.join("\n", (message_str, sub_message_str))

        elif self.time_increment == "yearly":
            # long-term annual sectoral gross demand (m/day)
            for sector_name in self.sector_names:
                gross_demand_per_sector[sector_name] += getattr(
                    self, "gross_demand_total_%s" % sector_name
                )

        else:
            logger.error(
                "the option %s for the time increment in the water management module is not allowed!"
            )
            sys.exit()

        # convert the long-term sectoral gross water demand to volume and cover with zeros over the
        # land mask (m3/day)
        for sector_name in self.sector_names:

            gross_demand_per_sector[sector_name] = (
                gross_demand_per_sector[sector_name] * self.cellarea
            )

            gross_demand_per_sector[sector_name] = pcr.ifthen(
                self.landmask, pcr.cover(gross_demand_per_sector[sector_name], 0)
            )

        return gross_demand_per_sector

    def update_water_demand_for_date(self, gross_demand, net_demand, date):
        """
        update_water_demand_for_date:
                        function that updates the availability per
                        zone as a function of the date.

        input:
        ======
        gross_demand,
        net_demand    : gross and net demand as a dictionary
                        with the sector names as keys (m3/day)
                        as a PCRaster map.
        date          : date of the update.
        """

        self.gross_demand = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )
        self.net_demand = dict(
            (sector_name, pcr.spatial(pcr.scalar(0)))
            for sector_name in self.sector_names
        )

        for sector_name in self.sector_names:

            # gross demand (m3/day)
            if sector_name in gross_demand.keys():

                logger.debug("%s gross water demand set for %s" % (sector_name, date))

                self.gross_demand[sector_name] = gross_demand[sector_name]

            # net demand (m3/day)
            if sector_name in net_demand.keys():

                logger.debug("%s net water demand set for %s" % (sector_name, date))

                self.net_demand[sector_name] = net_demand[sector_name]

        # total gross and net demand (m3/day)
        self.total_gross_demand = sum_list(list(self.gross_demand.values()))
        self.total_net_demand = sum_list(list(self.net_demand.values()))

        # updatable gross demand (m3/day)
        self.gross_demand_remaining = deepcopy(self.gross_demand)

        logger.debug("total gross and net demand set for %s" % date)

        return None

    def allocate_desalinated_water_for_date(self, availability, date):
        """
        desalinated_water_allocation_for_date:
                       function that updates the potential withdrawal as a function
                       of the date to extract the water availability and the internal
                       model settings for the time base to be used (monthly, in which
                       case the date is matched to the nearest date in the availability;
                       or yearly, in which case the long-term availability is used) and
                       the allocation settings.
                       Sets the desalinated water use internally and updates the sectoral
                       gross demands.

        input:
        =====
        availability : PCRaster maps with desalinated water availability (m3/day)
        date         : date of the update
        """

        message_str = "Desalinated water use for %s." % (date)

        # input data
        remaining_availability = deepcopy(availability)

        unmet_demand_per_sector = deepcopy(self.gross_demand)
        sector_names_no_desalwater = [
            sector_name
            for sector_name in self.sector_names
            if sector_name not in self.sector_names_desalwater
        ]
        for sector_name in sector_names_no_desalwater:
            unmet_demand_per_sector[sector_name] = pcr.spatial(pcr.scalar(0))

        met_demand_per_sector = dict(
            (
                sector_name,
                pcr.spatial(pcr.scalar(0.0)),
            )
            for sector_name in self.sector_names
        )

        withdrawal_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(0.0)))
            for sector_name in self.sector_names
        )

        allocated_demand_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(0.0)))
            for sector_name in self.sector_names
        )

        zones_per_sector = self.desalwater_allocation_zones
        zones = self.desalwater_allocation_zones["domestic"]

        # desalinated water is perfectly suitable for all sectors (suitability = 1)
        suitability_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(1)))
            for sector_name in self.sector_names
        )

        iter_allocation = 1
        exit_condition = False
        max_iter_allocation = 25

        # distribute water until the demand is met or the supply is exhausted
        while not exit_condition:

            # initial zonal demand and supply (m3/day)
            if iter_allocation == 1:
                totz_demand_old = get_zonal_total(
                    local_values=pcr.max(
                        0, sum_list(list(unmet_demand_per_sector.values()))
                    ),
                    zones=zones,
                )

                totz_supply_old = get_zonal_total(
                    local_values=remaining_availability, zones=zones
                )
            else:
                totz_demand_old = deepcopy(total_zonal_demand)
                totz_supply_old = deepcopy(total_zonal_supply)

            # water availability weights per sector, accounting for water quality
            source_name = "desalwater"
            weights_per_sector = self.water_quality.get_weights_availability_per_sector(
                source_name=source_name,
                sector_names=self.sector_names,
                prioritization_per_sector=self.prioritization[source_name],
                suitability_per_sector=suitability_per_sector,
                demand_per_sector=unmet_demand_per_sector,
                availability=remaining_availability,
                zones_per_sector=zones_per_sector,
            )

            # allocate the sectoral gross demand of the current day and return the withdrawal, allocated,
            # met and unmet demands per sector
            for sector_name in self.sector_names:

                # available water assigned per sector
                remaining_availability_sector = (
                    remaining_availability * weights_per_sector[sector_name]
                )

                (
                    tmp_withdrawal,
                    tmp_allocated_demand,
                    tmp_met_demand,
                    tmp_unmet_demand,
                    sub_message_str,
                ) = allocate_demand_to_availability_with_options(
                    demand=unmet_demand_per_sector[sector_name],
                    availability={"desalwater": remaining_availability_sector},
                    zones={"desalwater": zones_per_sector[sector_name]},
                    source_names=["desalwater"],
                    use_local_first=self.use_local_first,
                    reallocate_surplus=self.reallocate_surplus,
                )

                met_demand_per_sector[sector_name] = (
                    met_demand_per_sector[sector_name] + tmp_met_demand
                )

                unmet_demand_per_sector[sector_name] = pcr.max(
                    0, unmet_demand_per_sector[sector_name] - tmp_met_demand
                )

                withdrawal_per_sector[sector_name] = (
                    withdrawal_per_sector[sector_name] + tmp_withdrawal["desalwater"]
                )

                allocated_demand_per_sector[sector_name] = (
                    allocated_demand_per_sector[sector_name]
                    + tmp_allocated_demand["desalwater"]
                )

            # aggregate withdrawals and allocations
            withdrawal = sum_list(list(withdrawal_per_sector.values()))

            remaining_availability = pcr.max(0, availability - withdrawal)

            # update the iteration number and exit condition
            total_zonal_demand = get_zonal_total(
                local_values=sum_list(list(unmet_demand_per_sector.values())),
                zones=zones,
            )
            total_zonal_supply = get_zonal_total(
                local_values=remaining_availability, zones=zones
            )

            update_mask = (total_zonal_demand < totz_demand_old) & (
                total_zonal_supply < totz_supply_old
            )

            iter_allocation = iter_allocation + 1
            exit_condition = (
                pcr.cellvalue(pcr.mapmaximum(pcr.scalar(update_mask)), 1)[0] == 0
            ) | (iter_allocation > max_iter_allocation)

        # desalinated withdrawals and allocation per sector and total (m3/day)
        self.allocated_withdrawal_per_sector_desalwater = dict(
            (sector_name, withdrawal_per_sector[sector_name])
            for sector_name in self.sector_names
        )
        self.allocated_demand_per_sector_desalwater = dict(
            (sector_name, allocated_demand_per_sector[sector_name])
            for sector_name in self.sector_names
        )

        self.allocated_withdrawal_desalwater = sum_list(
            list(self.allocated_withdrawal_per_sector_desalwater.values())
        )
        self.allocated_demand_desalwater = sum_list(
            list(self.allocated_demand_per_sector_desalwater.values())
        )

        # subtract the demand met by desalinated water from the gross sectoral demands; the met demands
        # of irrigation, thermoelectric and environment are zero (m3/day)
        for sector_name in self.sector_names:
            self.gross_demand_remaining[sector_name] = pcr.max(
                0.0, self.gross_demand[sector_name] - met_demand_per_sector[sector_name]
            )

        message_str = str.join("\n", (message_str, sub_message_str))
        logger.debug(message_str)

        return None

    def update_longterm_potential_withdrawals_for_date(
        self, availability, demand, date
    ):
        """
        update_longterm_potential_withdrawals_for_date:
                       function that updates the potential withdrawal as a function
                       of the date to extract the water availability and the internal
                       model settings for the time base to be used (monthly, in which
                       case the date is matched to the nearest date in the availability;
                       or yearly, in which case the long-term availability is used) and
                       the allocation settings.
                       Sets the potential withdrawal internally and returns it; the
                       similar approach is followed for the actual withdrawals.

        input:
        =====
        availability : dictionary with source names (string) as keys and PCRaster maps with
                       the long-term surfacewater and groundwater availability (m3/day)
        demand       : dictionary with sector names (string) as keys and PCRaster maps with
                       the long-term sectoral gross water demands (m3/day)
        date         : date of the update

        output:
        ======
        potential_renewable_withdrawal,
        potential_nonrenewable_withdrawal:
                       dictionary of the potential withdrawal as volume over the period
                       per cell per source
        """

        message_str = (
            "Potential water withdrawals estimated for %s based on the %s long-term availability."
            % (date, self.time_increment)
        )

        # potential renewable and non-renewable withdrawal per source
        self.potential_renewable_withdrawal = dict(
            (source_name, pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0))))
            for source_name in self.source_names
        )
        self.potential_nonrenewable_withdrawal = dict(
            (source_name, pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0))))
            for source_name in self.source_names
        )
        self.potential_renewable_withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0))))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )
        self.potential_nonrenewable_withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0))))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )

        # actual renewable and non-renewable withdrawal per source
        self.actual_renewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )
        self.actual_nonrenewable_withdrawal = dict(
            (source_name, pcr.spatial(pcr.scalar(0)))
            for source_name in self.source_names
        )
        self.actual_renewable_withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )
        self.actual_nonrenewable_withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.spatial(pcr.scalar(0)))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )

        # dictionaries of the allocation zones, withdrawal capacities and withdrawal points
        withdrawal_capacity = {
            "surfacewater": self.surfacewater_withdrawal_capacity,
            "groundwater": self.groundwater_withdrawal_capacity,
        }

        withdrawal_points = {
            "surfacewater": self.surfacewater_withdrawal_points,
            "groundwater": self.groundwater_withdrawal_points,
        }

        zones_per_sector = {
            "surfacewater": self.surfacewater_allocation_zones,
            "groundwater": self.groundwater_allocation_zones,
        }

        # potential renewable withdrawal: allocate the total gross demand of the current period and return
        # the withdrawal, allocated, met and unmet demands (m3/day)
        withdrawal_per_sector, met_demand_per_sector, sub_message_str = (
            self.allocate_demand_to_renewable_sources(
                availability=availability,
                demand_per_sector=demand,
                zones_per_sector=zones_per_sector,
                use_local_first=self.use_local_first,
                reallocate_surplus=self.reallocate_surplus,
                date=date,
            )
        )

        # potential renewable withdrawals and met demands per sector
        self.potential_renewable_withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, withdrawal_per_sector[source_name][sector_name])
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )

        met_demand_per_sector = dict(
            (sector_name, met_demand_per_sector[sector_name])
            for sector_name in self.sector_names
        )

        unmet_demand_per_sector = dict(
            (
                sector_name,
                pcr.max(0.0, demand[sector_name] - met_demand_per_sector[sector_name]),
            )
            for sector_name in self.sector_names
        )

        # aggregate the potential renewable withdrawals and met and unmet demands
        met_demand = sum_list(list(met_demand_per_sector.values()))
        unmet_demand = sum_list(list(unmet_demand_per_sector.values()))
        self.potential_renewable_withdrawal = dict(
            (
                source_name,
                sum_list(
                    list(
                        self.potential_renewable_withdrawal_per_sector[
                            source_name
                        ].values()
                    )
                ),
            )
            for source_name in self.source_names
        )

        logger.debug(sub_message_str)

        # potential non-renewable withdrawal: add the unmet demand from groundwater only, following
        # sources_unmet_demand; if no source for unsustainable abstraction is chosen, only sustainable
        # withdrawals are allowed (m3/day)
        source_name = "groundwater"
        self.allocate_unmet_demand_to_nonrenewable_sources(
            unmet_demand_per_sector=unmet_demand_per_sector,
            zones_per_sector=zones_per_sector,
            withdrawal_capacity=withdrawal_capacity,
            withdrawal_points=withdrawal_points,
        )

        sub_message_str = str.join(
            " ",
            (
                "unmet demand is allocated over the available resources",
                "and an average unmet demand of %g [m3] is met by",
                "a withdrawal from non-renewable resources of",
                "%g [m3].",
            ),
        )

        sub_message_str = sub_message_str % (
            pcr_get_statistics(unmet_demand)["average"],
            pcr_get_statistics(
                sum_list(list(self.potential_nonrenewable_withdrawal.values()))
            )["average"],
        )

        message_str = str.join("\n", (message_str, sub_message_str))

        logger.info(message_str)

        # ideal surface water and groundwater potential withdrawal, used to update the long-term potential
        # withdrawal; unmet_demand_per_sector['thermoelectric'] was popped in
        # allocated_unmet_demand_to_nonrenewable_sources (m3/day)
        self.surfacewater_potential_estimated_withdrawal = deepcopy(
            self.potential_renewable_withdrawal["surfacewater"]
        )
        self.groundwater_potential_estimated_withdrawal = (
            self.potential_renewable_withdrawal["groundwater"]
            + sum_list(list(unmet_demand_per_sector.values()))
        )

        # water balance check
        if debug:
            # per sector: long-term gross demands vs. long-term potential withdrawals
            for sector_name in self.sector_names:
                water_balance_check(
                    states_ini=[demand[sector_name]],
                    states_end=[
                        self.potential_renewable_withdrawal_per_sector["surfacewater"][
                            sector_name
                        ],
                        self.potential_renewable_withdrawal_per_sector["groundwater"][
                            sector_name
                        ],
                        self.potential_nonrenewable_withdrawal_per_sector[
                            "surfacewater"
                        ][sector_name],
                        self.potential_nonrenewable_withdrawal_per_sector[
                            "groundwater"
                        ][sector_name],
                    ],
                    cellarea=self.cellarea,
                    var_name=sector_name,
                    process_name="Long-term - gross demand vs potential withdrawal",
                    zones=zones_per_sector["surfacewater"][sector_name],
                    date=date,
                )

            # per source: long-term water availability vs. long-term potential withdrawals
            for source_name in self.source_names:
                water_balance_check(
                    states_ini=[availability[source_name]],
                    states_end=[
                        self.potential_renewable_withdrawal_per_sector[source_name][
                            sector_name
                        ]
                        for sector_name in self.sector_names
                    ],
                    cellarea=self.cellarea,
                    var_name=source_name,
                    process_name="Long-term - availability vs potential withdrawal",
                    date=date,
                )

            # per source: pumping capacity vs. long-term potential withdrawals
            for source_name in self.source_names:
                if self.pumping_capacity_flag[source_name]:
                    water_balance_check(
                        states_ini=[
                            getattr(self, "%s_withdrawal_capacity" % source_name)
                        ],
                        states_end=[
                            self.potential_renewable_withdrawal_per_sector[source_name][
                                sector_name
                            ]
                            for sector_name in self.sector_names
                        ]
                        + [
                            self.potential_nonrenewable_withdrawal_per_sector[
                                source_name
                            ][sector_name]
                            for sector_name in self.sector_names
                        ],
                        cellarea=self.cellarea,
                        var_name=source_name,
                        process_name="Long-term - pumping capacity  vs potential withdrawal",
                        date=date,
                    )

        return None

    def allocate_demand_to_renewable_sources(
        self,
        availability,
        demand_per_sector,
        zones_per_sector,
        use_local_first,
        reallocate_surplus,
        date,
    ):
        """
        allocate_demand_to_renewable_sources:
                                function to calculate the potential renewable water withdrawals
                                per source and sector for a certain date considering the water quality

        input:
        =====
        availability          : dictionary with source names (string) as keys and PCRaster maps with
                                long-term water availability per source as values (units: m3/period)
        demand_per_sector     : dictionary with sector names (string) as keys and PCRaster maps with
                                sectoral gross water demands as values (units: m3/period)
        zones_per_sector      : dictionary with sector names (string) as keys and PCRaster maps with
                                allocation zones per sector (nominal) as values
        use_local_first        : PCRaster map with boolean values to indicate water is first withdrawn
                                from local source
        reallocate_surplus    : boolean

        output:
        ======
        withdrawal_per_sector : dictionary with sector names (string) as keys and PCRaster maps with
                                sum of water withdrawals from renewable surface and groundwater sources
                                per sector as values (units: m3/d)
        met_demand_per_sector : dictionary with sector names (string) as keys and PCRaster maps with
                                sectoral met demands as values (units: m3/d)
        message_str           : output message
        """

        # input data
        remaining_availability = deepcopy(availability)
        unmet_demand_per_sector = deepcopy(demand_per_sector)

        met_demand_per_sector = dict(
            (
                sector_name,
                pcr.ifthen(demand_per_sector[sector_name] >= 0.0, pcr.scalar(0.0)),
            )
            for sector_name in self.sector_names
        )

        withdrawal_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.spatial(pcr.scalar(0.0)))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )

        allocated_demand_per_sector = dict(
            (
                source_name,
                dict(
                    (sector_name, pcr.spatial(pcr.scalar(0.0)))
                    for sector_name in self.sector_names
                ),
            )
            for source_name in self.source_names
        )

        # allocation zones (the domestic sector typically has the largest zone)
        zones = {
            "surfacewater": zones_per_sector["surfacewater"]["domestic"],
            "groundwater": zones_per_sector["groundwater"]["domestic"],
        }

        # long-term quality state for the current date
        constituent_longterm_states = self.water_quality.get_longterm_quality_for_date(
            source_names=self.source_names, date=date
        )

        # water quality suitability masks per sector and source
        self.suitability_per_sector = {}
        for source_name in self.source_names:
            self.suitability_per_sector[source_name] = (
                self.water_quality.get_suitability_per_sector(
                    constituent_state=constituent_longterm_states[source_name],
                    sector_names=self.sector_names,
                )
            )

        iter_allocation = 1
        exit_condition = False
        max_iter_allocation = 25
        totz_demand_old = {}
        totz_supply_old = {}

        # distribute water until the demand is met or the supply is exhausted
        while not exit_condition:

            # initial zonal demand and supply
            for source_name in self.source_names:
                if iter_allocation == 1:
                    totz_demand_old[source_name] = get_zonal_total(
                        local_values=pcr.max(
                            0, sum_list(list(unmet_demand_per_sector.values()))
                        ),
                        zones=zones[source_name],
                    )

                    totz_supply_old[source_name] = get_zonal_total(
                        local_values=remaining_availability[source_name],
                        zones=zones[source_name],
                    )
                else:
                    totz_demand_old[source_name] = deepcopy(
                        total_zonal_demand[source_name]
                    )
                    totz_supply_old[source_name] = deepcopy(
                        total_zonal_supply[source_name]
                    )

            # water availability weights per sector, accounting for water quality

            # surface water
            source_name = "surfacewater"
            unmet_demand_per_sector_surfacewater = deepcopy(unmet_demand_per_sector)
            weights_surfacewater_per_sector = (
                self.water_quality.get_weights_availability_per_sector(
                    source_name=source_name,
                    sector_names=self.sector_names,
                    prioritization_per_sector=self.prioritization[source_name],
                    suitability_per_sector=self.suitability_per_sector[source_name],
                    demand_per_sector=unmet_demand_per_sector_surfacewater,
                    availability=remaining_availability[source_name],
                    zones_per_sector=zones_per_sector[source_name],
                )
            )

            # groundwater
            source_name = "groundwater"
            unmet_demand_per_sector_groundwater = deepcopy(unmet_demand_per_sector)

            # thermoelectric sector or environmental flow requirements
            for sector_name in self.sectors_local_surfacewater:
                if sector_name in self.sector_names:
                    unmet_demand_per_sector_groundwater[sector_name] = pcr.spatial(
                        pcr.scalar(0)
                    )

            weights_groundwater_per_sector = (
                self.water_quality.get_weights_availability_per_sector(
                    source_name=source_name,
                    sector_names=self.sector_names,
                    prioritization_per_sector=self.prioritization[source_name],
                    suitability_per_sector=self.suitability_per_sector[source_name],
                    demand_per_sector=unmet_demand_per_sector_groundwater,
                    availability=remaining_availability[source_name],
                    zones_per_sector=zones_per_sector[source_name],
                )
            )

            # allocate the sectoral gross demand of the current period and return the withdrawal, allocated,
            # met and unmet demands per sector
            for sector_name in self.sector_names:

                # available water assigned per sector
                remaining_availability_surfacewater_sector = (
                    remaining_availability["surfacewater"]
                    * weights_surfacewater_per_sector[sector_name]
                    * self.suitability_per_sector["surfacewater"][sector_name]
                )

                remaining_availability_groundwater_sector = (
                    remaining_availability["groundwater"]
                    * weights_groundwater_per_sector[sector_name]
                    * self.suitability_per_sector["groundwater"][sector_name]
                )

                (
                    tmp_withdrawal,
                    tmp_allocated_demand,
                    tmp_met_demand,
                    tmp_unmet_demand,
                    message_str,
                ) = allocate_demand_to_availability_with_options(
                    demand=unmet_demand_per_sector[sector_name],
                    availability={
                        "surfacewater": remaining_availability_surfacewater_sector,
                        "groundwater": remaining_availability_groundwater_sector,
                    },
                    zones={
                        "surfacewater": zones_per_sector["surfacewater"][sector_name],
                        "groundwater": zones_per_sector["groundwater"][sector_name],
                    },
                    source_names=self.source_names,
                    use_local_first=use_local_first,
                    reallocate_surplus=reallocate_surplus,
                )

                met_demand_per_sector[sector_name] = (
                    met_demand_per_sector[sector_name] + tmp_met_demand
                )

                unmet_demand_per_sector[sector_name] = pcr.max(
                    0, unmet_demand_per_sector[sector_name] - tmp_met_demand
                )

                for source_name in self.source_names:
                    withdrawal_per_sector[source_name][sector_name] = (
                        withdrawal_per_sector[source_name][sector_name]
                        + tmp_withdrawal[source_name]
                    )

                    allocated_demand_per_sector[source_name][sector_name] = (
                        allocated_demand_per_sector[source_name][sector_name]
                        + tmp_allocated_demand[source_name]
                    )

            # aggregate withdrawals and allocations per source
            withdrawal = dict(
                (
                    source_name,
                    sum_list(list(withdrawal_per_sector[source_name].values())),
                )
                for source_name in self.source_names
            )
            allocated_demand = dict(
                (
                    source_name,
                    sum_list(list(allocated_demand_per_sector[source_name].values())),
                )
                for source_name in self.source_names
            )

            for source_name in self.source_names:
                remaining_availability[source_name] = pcr.max(
                    0, availability[source_name] - withdrawal[source_name]
                )

            # update the iteration number and exit condition
            total_zonal_demand = {}
            total_zonal_supply = {}
            for source_name in self.source_names:
                total_zonal_demand[source_name] = get_zonal_total(
                    local_values=sum_list(list(unmet_demand_per_sector.values())),
                    zones=zones[source_name],
                )
                total_zonal_supply[source_name] = get_zonal_total(
                    local_values=remaining_availability[source_name],
                    zones=zones[source_name],
                )

            update_mask = (
                (total_zonal_demand["surfacewater"] < totz_demand_old["surfacewater"])
                & (total_zonal_supply["surfacewater"] < totz_supply_old["surfacewater"])
            ) | (
                (total_zonal_demand["groundwater"] < totz_demand_old["groundwater"])
                & (total_zonal_supply["groundwater"] < totz_supply_old["groundwater"])
            )

            iter_allocation = iter_allocation + 1
            exit_condition = (
                pcr.cellvalue(pcr.mapmaximum(pcr.scalar(update_mask)), 1)[0] == 0
            ) | (iter_allocation > max_iter_allocation)

        return withdrawal_per_sector, met_demand_per_sector, message_str

    def allocate_unmet_demand_to_nonrenewable_sources(
        self,
        unmet_demand_per_sector,
        zones_per_sector,
        withdrawal_capacity,
        withdrawal_points,
    ):
        """
        allocate_unmet_demand_to_nonrenewable_sources:
                                       function to allocate the unmet demand (or claimed withdrawal)
                                       per sector to the groundwater sources based on its potential
                                       renewable withdrawals

        input:
        =====
        unmet_demand_per_sector      : dictionary with sector names (string) as keys and PCRaster maps
                                       with the amount of withdrawal that cannot be met and are assigned
                                       to the non-renewable groundwater (units: m3/day)
        zones_per_sector             : dictionary with sector names (string) as keys and PCRaster maps
                                       with allocation zones per sector (nominal)
        withdrawal_capacity          : dictionary with source names (string) as keys and PCRaster maps
                                       with water withdrawal capacity as values (units: m3/day)
        withdrawal_points            : dictionary with source names (string) as keys and PCRaster
                                       maps with water withdrawal points as values (nominal)
        """

        message_str = "Non-renewable withdrawals are assigned to the following sources"

        source_name = "groundwater"
        availability = deepcopy(self.potential_renewable_withdrawal[source_name])
        suitability = deepcopy(self.suitability_per_sector[source_name])
        zones = deepcopy(zones_per_sector[source_name])
        withdrawal_capacity = deepcopy(withdrawal_capacity[source_name])

        # sectors that can also withdraw groundwater, and their unmet demands
        sector_names = deepcopy(self.sector_names)
        for sector_name in self.sectors_local_surfacewater:
            if sector_name in self.sector_names:
                sector_names.remove(sector_name)
                unmet_demand_per_sector.pop(sector_name)

        # remaining withdrawal capacity per sector (if defined); includes the potential non-renewable
        # withdrawal, which is zero at the start of the allocation
        if not isinstance(withdrawal_capacity, NoneType):
            withdrawal_capacity_remaining = pcr.max(
                0,
                withdrawal_capacity
                - (
                    self.potential_renewable_withdrawal[source_name]
                    + self.potential_nonrenewable_withdrawal[source_name]
                ),
            )

            withdrawal_capacity_remaining_per_sector = {}
            for sector_name in sector_names:
                sector_rate = pcr_return_val_div_zero(
                    get_zonal_total(
                        unmet_demand_per_sector[sector_name], zones[sector_name]
                    ),
                    get_zonal_total(
                        sum_list(list(unmet_demand_per_sector.values())),
                        zones[sector_name],
                    ),
                    very_small_number,
                )

                withdrawal_capacity_remaining_per_sector[sector_name] = (
                    withdrawal_capacity_remaining * sector_rate
                )

        # availability per sector considering water quality; this favours the pumping capacity if water
        # is unavailable, highlighting non-renewable withdrawals
        for sector_name in sector_names:

            # withdrawal capacity; if undefined, the minimum non-zero availability, else 1, so water can
            # always be withdrawn
            if not isinstance(withdrawal_capacity, NoneType):
                capacity = withdrawal_capacity_remaining
                availability_per_sector = capacity * suitability[sector_name]
            else:
                capacity = pcr.areaminimum(availability, zones[sector_name])
                capacity = pcr.ifthenelse(capacity > 0, capacity, pcr.scalar(1))

                availability_per_sector = pcr.ifthenelse(
                    availability > 0,
                    availability * suitability[sector_name],
                    capacity * suitability[sector_name],
                )

            # availability considering the sectoral water quality requirements, only at the withdrawal points
            availability_per_sector = pcr.ifthenelse(
                pcr.scalar(withdrawal_points[source_name]) > 0,
                availability_per_sector,
                0,
            )

            # potential non-renewable withdrawal per sector (m3/day)
            allocation_rate = pcr_return_val_div_zero(
                availability_per_sector,
                get_zonal_total(availability_per_sector, zones[sector_name]),
                very_small_number,
            )

            allocated_demand = allocation_rate * get_zonal_total(
                unmet_demand_per_sector[sector_name], zones[sector_name]
            )

            # whether the pumping capacity limits the allocated demand
            if not isinstance(withdrawal_capacity, NoneType):
                allocated_demand = pcr.min(
                    allocated_demand,
                    withdrawal_capacity_remaining_per_sector[sector_name],
                )

            # (m3/day)
            self.potential_nonrenewable_withdrawal_per_sector[source_name][
                sector_name
            ] = (
                self.potential_nonrenewable_withdrawal_per_sector[source_name][
                    sector_name
                ]
                + allocated_demand
            )

        # aggregate the potential non-renewable withdrawal of all sectors (m3/day)
        self.potential_nonrenewable_withdrawal[source_name] = sum_list(
            list(
                self.potential_nonrenewable_withdrawal_per_sector[source_name].values()
            )
        )

        message_str = str.join(": ", (message_str, source_name))
        logger.debug(message_str)

        return None

    def update_shortterm_potential_withdrawals_for_date(self, date):
        """
        update_shortterm_potential_withdrawals_for_date:
                       update the long-term potential withdrawals considering the short-term
                       sectoral gross water demands per source and supply.
        """

        # redistribute the gross demand that is no longer needed: if short-term gross demands exceed the
        # long-term expectations, the system cannot supply this water due to infrastructure limitations

        # store the long-term variables
        if date.day == 1:
            self.longterm_potential_withdrawals_per_sector = {
                "renewable": deepcopy(self.potential_renewable_withdrawal_per_sector),
                "nonrenewable": deepcopy(
                    self.potential_nonrenewable_withdrawal_per_sector
                ),
            }

        # redistribute water
        for sector_name in self.sector_names:

            # total potential withdrawal (renewable + non-renewable) and allocation zones per source
            potential_withdrawal = dict(
                (
                    source_name,
                    self.longterm_potential_withdrawals_per_sector["renewable"][
                        source_name
                    ][sector_name]
                    + self.longterm_potential_withdrawals_per_sector["nonrenewable"][
                        source_name
                    ][sector_name],
                )
                for source_name in self.source_names
            )

            zones = {
                "surfacewater": self.surfacewater_allocation_zones[sector_name],
                "groundwater": self.groundwater_allocation_zones[sector_name],
            }

            # source distribution ratio
            zonal_availability, zonal_potential_allocation, allocation_ratio = (
                obtain_allocation_ratio(
                    demand=self.gross_demand_remaining[sector_name],
                    availability=potential_withdrawal,
                    zones=zones,
                    source_names=self.source_names,
                )
            )

            # split the gross demands per water source (m3/day)
            demands_per_source = dict(
                (
                    source_name,
                    self.gross_demand_remaining[sector_name]
                    * allocation_ratio[source_name],
                )
                for source_name in self.source_names
            )

            # redistribute the gross demands over the long-term potential renewable withdrawals first (m3/day)
            distribution_ratio = dict(
                (
                    source_name,
                    pcr_return_val_div_zero(
                        self.longterm_potential_withdrawals_per_sector["renewable"][
                            source_name
                        ][sector_name],
                        get_zonal_total(
                            self.longterm_potential_withdrawals_per_sector["renewable"][
                                source_name
                            ][sector_name],
                            zones[source_name],
                        ),
                        very_small_number,
                    ),
                )
                for source_name in self.source_names
            )

            potential_withdrawal = dict(
                (
                    source_name,
                    distribution_ratio[source_name]
                    * get_zonal_total(
                        demands_per_source[source_name], zones[source_name]
                    ),
                )
                for source_name in self.source_names
            )

            # update the potential non-renewable withdrawal (m3/day)
            for source_name in self.source_names:
                self.potential_renewable_withdrawal_per_sector[source_name][
                    sector_name
                ] = pcr.min(
                    potential_withdrawal[source_name],
                    self.longterm_potential_withdrawals_per_sector["renewable"][
                        source_name
                    ][sector_name],
                )

            # outstanding gross water demand (m3/day)
            outstanding_demand = dict(
                (
                    source_name,
                    pcr.max(
                        0,
                        demands_per_source[source_name]
                        - self.potential_renewable_withdrawal_per_sector[source_name][
                            sector_name
                        ],
                    ),
                )
                for source_name in self.source_names
            )

            # then redistribute the outstanding gross demands over the long-term potential non-renewable
            # withdrawals (m3/day)
            distribution_ratio = dict(
                (
                    source_name,
                    pcr_return_val_div_zero(
                        self.longterm_potential_withdrawals_per_sector["nonrenewable"][
                            source_name
                        ][sector_name],
                        get_zonal_total(
                            self.longterm_potential_withdrawals_per_sector[
                                "nonrenewable"
                            ][source_name][sector_name],
                            zones[source_name],
                        ),
                        very_small_number,
                    ),
                )
                for source_name in self.source_names
            )

            potential_withdrawal = dict(
                (
                    source_name,
                    distribution_ratio[source_name]
                    * get_zonal_total(
                        outstanding_demand[source_name], zones[source_name]
                    ),
                )
                for source_name in self.source_names
            )

            # update the potential withdrawal per sector (m3/day)
            for source_name in self.source_names:
                self.potential_nonrenewable_withdrawal_per_sector[source_name][
                    sector_name
                ] = pcr.min(
                    potential_withdrawal[source_name],
                    self.longterm_potential_withdrawals_per_sector["nonrenewable"][
                        source_name
                    ][sector_name],
                )

        # update the total potential withdrawal (m3/day)
        for source_name in self.source_names:
            self.potential_renewable_withdrawal[source_name] = sum_list(
                list(
                    self.potential_renewable_withdrawal_per_sector[source_name].values()
                )
            )
            self.potential_nonrenewable_withdrawal[source_name] = sum_list(
                list(
                    self.potential_nonrenewable_withdrawal_per_sector[
                        source_name
                    ].values()
                )
            )

        message_str = (
            "Long-term potential withdrawals are updated considering short-term gross demands for %s."
            % (date)
        )
        logger.info(message_str)

        # water balance check
        if debug:
            # per source: long-term vs. short-term potential withdrawals
            for withdrawal_name in self.withdrawal_names:
                for source_name in self.source_names:
                    water_balance_check(
                        states_ini=[
                            self.longterm_potential_withdrawals_per_sector[
                                withdrawal_name
                            ][source_name][sector_name]
                            for sector_name in self.sector_names
                        ],
                        states_end=[
                            getattr(self, "potential_%s_withdrawal" % withdrawal_name)[
                                source_name
                            ]
                        ],
                        cellarea=self.cellarea,
                        var_name="%s %s" % (withdrawal_name, source_name),
                        process_name="Long-term withdrawal vs Short-term withdrawal",
                        date=date,
                    )

            # per source: pumping capacity vs. short-term potential withdrawals
            for source_name in self.source_names:
                if self.pumping_capacity_flag[source_name]:
                    water_balance_check(
                        states_ini=[
                            getattr(self, "%s_withdrawal_capacity" % source_name)
                        ],
                        states_end=[
                            self.potential_renewable_withdrawal_per_sector[source_name][
                                sector_name
                            ]
                            for sector_name in self.sector_names
                        ]
                        + [
                            self.potential_nonrenewable_withdrawal_per_sector[
                                source_name
                            ][sector_name]
                            for sector_name in self.sector_names
                        ],
                        cellarea=self.cellarea,
                        var_name=source_name,
                        process_name="Short-term - pumping capacity vs potential withdrawal",
                        date=date,
                    )

        return None

    def get_total_potential_withdrawal(self, source_name):
        """
        get_total_potential_withdrawal:
                                  function to get the potential withdrawals per sector
                                  as the sum of renewable and non-renewable water withdrawals
                                  limited by the withdrawal capacity

        input:
        =====
        source_name             : string, source name under evaluation

        output:
        ======
        total_potential_withdrawal_per_sector:
                                  dictionary with sector names (string) as keys and
                                  PCRaster maps with sum of renewable and non-renewable
                                  potential withdrawals per sector, limited by withdrawal
                                  capacity (units: m3/day)
        """

        message_str = "updating potential withdrawals per sector"

        # check whether the potential withdrawals are affected by the withdrawal capacity
        if not isinstance(self.surfacewater_withdrawal_capacity, NoneType):
            if (
                pcr.cellvalue(
                    pcr.mapminimum(
                        self.surfacewater_withdrawal_capacity
                        - (
                            self.potential_renewable_withdrawal["surfacewater"]
                            + self.potential_nonrenewable_withdrawal["surfacewater"]
                        )
                    ),
                    1,
                )[0]
                < -1
            ):
                logger.error(
                    "WARNING !!!!!!!! Sum of potential surface water renewable and non-renewable withdrawals are larger than surface water withdrawal capacity"
                )

        if not isinstance(self.groundwater_withdrawal_capacity, NoneType):
            if (
                pcr.cellvalue(
                    pcr.mapminimum(
                        self.groundwater_withdrawal_capacity
                        - (
                            self.potential_renewable_withdrawal["groundwater"]
                            + self.potential_nonrenewable_withdrawal["groundwater"]
                        )
                    ),
                    1,
                )[0]
                < -1
            ):
                logger.error(
                    "WARNING !!!!!!!! Sum of potential groundwater renewable and non-renewable withdrawals are larger than groundwater withdrawal capacity"
                )

        # total long-term potential renewable and non-renewable withdrawals per sector (m3/day)
        total_potential_withdrawal_per_sector = dict(
            (
                sector_name,
                self.potential_renewable_withdrawal_per_sector[source_name][sector_name]
                + self.potential_nonrenewable_withdrawal_per_sector[source_name][
                    sector_name
                ],
            )
            for sector_name in self.sector_names
        )

        logger.debug(message_str)

        return total_potential_withdrawal_per_sector

    def update_surfacewater_potential_withdrawals(
        self, surfacewater_available, longterm_potential_withdrawal_per_sector
    ):
        """
        update_surfacewater_potential_withdrawals:
                                       function that calculates the actual water withdrawals from the
                                       channel based on the potential sectoral demands (potential_withdrawal)
                                       and the oustanding potential evapotranspiration (channel_runoff < 0)

        input:
        =====
        surfacewater_available       : PCRaster map with surface water availableas the sum of the surface water
                                       storage at the start of the time-step over the fraction of water and the
                                       total runoff (sum of the different surface water components)
                                       (units: m per day)
        longterm_potential_withdrawal_per_sector :
                                       dictionary with sector names (string) as keys and PCRaster maps
                                       with sum of renewable and non-renewable potential withdrawals per
                                       sector obtained considering long-term water quality as values
                                       (units: m3/day)

        output:
        ======
        potential_withdrawal_per_sector :
                                       dictionary with sector names (string) as keys and PCRaster maps
                                       with potential water withdrawal per sector based on short-term water
                                       quality and current surface water availability (units: m3/day)
        """

        source_name = "surfacewater"

        # short-term potential surface water availability (m3/day)
        potential_surfacewater_availability = pcr.max(
            0, surfacewater_available * self.cellarea
        )

        # suitability per sector from the short-term surface water quality (-)
        suitability_per_sector = self.water_quality.get_suitability_per_sector(
            constituent_state=self.water_quality.constituent_shortterm_quality[
                source_name
            ],
            sector_names=self.sector_names,
        )

        # short-term potential surface water withdrawals: the long-term potential withdrawals updated with
        # the short-term water quality suitability (m3/day)
        shortterm_potential_withdrawal_per_sector = dict(
            (
                sector_name,
                longterm_potential_withdrawal_per_sector[sector_name]
                * suitability_per_sector[sector_name],
            )
            for sector_name in self.sector_names
        )

        # aggregate the potential withdrawals of all sectors (m3/day)
        shortterm_potential_withdrawal = sum_list(
            list(shortterm_potential_withdrawal_per_sector.values())
        )

        # current potential surface water withdrawals from the suitability per sector; needed due to the
        # accuthresholdstate/flux routing (m3/day)
        potential_withdrawal_per_sector = dict(
            (
                sector_name,
                pcr.min(
                    shortterm_potential_withdrawal_per_sector[sector_name],
                    potential_surfacewater_availability
                    * suitability_per_sector[sector_name]
                    * pcr_return_val_div_zero(
                        shortterm_potential_withdrawal_per_sector[sector_name],
                        shortterm_potential_withdrawal,
                        very_small_number,
                    ),
                ),
            )
            for sector_name in self.sector_names
        )

        # potential surface water withdrawals per sector for the current time step (m3/day)
        return potential_withdrawal_per_sector

    def update_groundwater_potential_withdrawals(
        self,
        groundwater_available,
        longterm_potential_withdrawal_per_sector,
        time_step_length,
    ):
        """
        update_groundwater_potential_withdrawals:
                                             function to update the potential groundwater withdrawals
                                             considering the short-term water quality and distributing
                                             among renewable and non-renewable sources based on the
                                             storage

        input:
        =====
        groundwater_available              : PCRaster map with groundwater storage of the previous time-
                                             step (units: m)
        longterm_potential_withdrawal_per_sector :
                                             dictionary with sector names (string) as keys and PCRaster maps
                                             with sum of renewable and non-renewable potential withdrawals per
                                             sector obtained considering long-term water quality as values
                                             (units: m3/day)
        time_step_length                   : integer, number of days in period (e.g., 30 days/month)

        output:
        ======
        potential_withdrawal_per_sector    : dictionary with sector names (string) as keys and PCRaster maps
                                             with sum of renewable and non-renewable potential withdrawals per
                                             sector obtained considering short-term water quality as values
                                             (units: m/period)
        """
        source_name = "groundwater"

        # short-term groundwater availability (m3 at the end of the period)
        groundwater_availability = pcr.max(0, groundwater_available * self.cellarea)

        # suitability per sector from the short-term groundwater quality
        suitability_per_sector = self.water_quality.get_suitability_per_sector(
            constituent_state=self.water_quality.constituent_shortterm_quality[
                source_name
            ],
            sector_names=self.sector_names,
        )

        # short-term potential groundwater withdrawals: the long-term potential withdrawals updated with
        # the short-term water quality suitability (m3/period)
        potential_withdrawal_per_sector = dict(
            (
                sector_name,
                longterm_potential_withdrawal_per_sector[sector_name]
                * suitability_per_sector[sector_name]
                * time_step_length,
            )
            for sector_name in self.sector_names
        )

        # potential groundwater withdrawals per sector and groundwater availability for the current time
        # step (m3/period)
        return potential_withdrawal_per_sector, groundwater_availability

    def update_withdrawals(
        self,
        source_name,
        renewable_withdrawal_per_sector,
        nonrenewable_withdrawal_per_sector,
        source_names_to_be_processed,
        water_available=None,
        date=None,
    ):
        """
        update_withdrawals           : function that wraps around two individual actions
                                       that are needed to update the potential and actual
                                       withdrawals:
                                       1) set the actual withdrawals on the basis of the
                                          water that can be withdrawn from the source provided
                                          in a renewable or non-renewable fashion;
                                       2) pass any unmet demand to the nonrenewable potential
                                          withdrawals to the remaining allowable sources.

        input:
        =====
        source_name                  : source name currently processed; the renewable
                                       and non-renewable withdrawals are the amounts
                                       that currently could be actually withdrawn
        renewable_withdrawal_per_sector,
        nonrenewable_withdrawal_per_sector :
                                       total amount of water withdrawn from the
                                       renewable and non-renewable storage for the
                                       current source (units: m3/period)
        source_names_to_be_processed : a list of the sector names that are elligi-
                                       ble to accommodate any unmet demand as pot-
                                       ential non-renewable withdrawals.
        water_available              : PCRaster map with short-term water available from
                                       either source (only use for water balance checking)
                                       (units: m3/day)
        date                         : string, current date
        """

        # actual withdrawals
        self.set_actual_withdrawals(
            source_name,
            renewable_withdrawal_per_sector,
            nonrenewable_withdrawal_per_sector,
        )

        # unmet demand per sector: potential minus actual withdrawal
        unmet_withdrawal_per_sector = dict(
            (
                sector_name,
                pcr.max(
                    0,
                    (
                        self.potential_renewable_withdrawal_per_sector[source_name][
                            sector_name
                        ]
                        + self.potential_nonrenewable_withdrawal_per_sector[
                            source_name
                        ][sector_name]
                    )
                    - (
                        self.actual_renewable_withdrawal_per_sector[source_name][
                            sector_name
                        ]
                        + self.actual_nonrenewable_withdrawal_per_sector[source_name][
                            sector_name
                        ]
                    ),
                ),
            )
            for sector_name in self.sector_names
        )

        # selectable source names
        source_names = []
        for source_name_to_be_processed in source_names_to_be_processed:
            source_names.append(source_name_to_be_processed)

        # allocate unmet withdrawals to the non-renewable groundwater source
        if "groundwater" in source_names:
            message_str = "Non-renewable withdrawals are assigned to the following sources: groundwater"
            self.allocate_unmet_demand_to_nonrenewable_sources(
                unmet_demand_per_sector=unmet_withdrawal_per_sector,
                zones_per_sector={
                    "surfacewater": self.surfacewater_allocation_zones,
                    "groundwater": self.groundwater_allocation_zones,
                },
                withdrawal_capacity={
                    "surfacewater": self.surfacewater_withdrawal_capacity,
                    "groundwater": self.groundwater_withdrawal_capacity,
                },
                withdrawal_points={
                    "surfacewater": self.surfacewater_withdrawal_points,
                    "groundwater": self.groundwater_withdrawal_points,
                },
            )
            logger.debug(message_str)

        # water balance check
        if debug:
            # per source: short-term water availability vs. actual withdrawals
            water_balance_check(
                states_ini=[water_available],
                states_end=[
                    self.actual_renewable_withdrawal_per_sector[source_name][
                        sector_name
                    ]
                    for sector_name in self.sector_names
                ],
                cellarea=self.cellarea,
                var_name=source_name,
                process_name="Short-term - availability vs actual withdrawal",
                date=date,
            )

            # per source: pumping capacity vs. short-term potential withdrawals
            if "groundwater" in source_names:
                source_name = "groundwater"
                if self.pumping_capacity_flag[source_name]:
                    water_balance_check(
                        states_ini=[
                            getattr(self, "%s_withdrawal_capacity" % source_name)
                        ],
                        states_end=[
                            self.potential_renewable_withdrawal_per_sector[source_name][
                                sector_name
                            ]
                            for sector_name in self.sector_names
                        ]
                        + [
                            self.potential_nonrenewable_withdrawal_per_sector[
                                source_name
                            ][sector_name]
                            for sector_name in self.sector_names
                        ],
                        cellarea=self.cellarea,
                        var_name=source_name,
                        process_name="Short-term - pumping capacity vs reallocated unmet demand",
                        date=date,
                    )

        return None

    def set_actual_withdrawals(
        self,
        source_name,
        renewable_withdrawal_per_sector,
        nonrenewable_withdrawal_per_sector,
    ):
        """
        set_actual_withdrawals             : function that sets the actual withdrawals for
                                             the source given the name and the amounts of
                                             renewable and non-renewable withdrawals in a cell

        input:
        =====
        source_name                        : name of the source currently being processed;
                                             for this source the renewable and non-renewable
                                             withdrawals are the amounts thar currently could
                                             be actually withdrawn
        renewable_withdrawal_per_sector    : total amount of water withdrawn from the
                                             renewable storage for the current source;
        nonrenewable_withdrawal_per_sector : idem, but then withdrawn from the non-
                                             renewable storage for the current source.
        """

        self.actual_renewable_withdrawal[source_name] = sum_list(
            list(renewable_withdrawal_per_sector.values())
        )

        self.actual_nonrenewable_withdrawal[source_name] = sum_list(
            list(nonrenewable_withdrawal_per_sector.values())
        )

        self.actual_renewable_withdrawal_per_sector[source_name] = dict(
            (sector_name, renewable_withdrawal_per_sector[sector_name])
            for sector_name in self.sector_names
        )

        self.actual_nonrenewable_withdrawal_per_sector[source_name] = dict(
            (sector_name, nonrenewable_withdrawal_per_sector[sector_name])
            for sector_name in self.sector_names
        )

        return None

    def allocate_withdrawal_to_demand_for_date(self, date, availability):
        """
        allocate_demand_to_withdrawals:
                       function that internally allocates the gross demand to the
                       sources on a cell-by-cell basis given the actual withdrawals
                       and updates the consumption and return flows

        input:
        =====
        date         : string, date of the update
        availability : dictionary with sources (string) as keys and PCRaster maps
                       with current surface water and groundwater availability
                       (units: m3/day)
        """
        message_str = "Actual water withdrawals allocated to the demand for %s." % date

        # allocate the water demand per renewable/non-renewable withdrawal and source; allocated
        # withdrawal and demand are stored internally, unused withdrawal and met demand are not used
        # directly; the remaining unused withdrawals are kept for checks and added to the return flows
        # to avoid balance errors; sub_message_str holds the allocation information for logging (m3/day)
        (
            self.allocated_withdrawal_per_sector,
            unused_withdrawal,
            self.allocated_demand_per_sector,
            met_demands,
            sub_message_str,
        ) = allocate_demand_to_withdrawals(
            withdrawal_names=self.withdrawal_names,
            source_names=self.source_names,
            sector_names=self.sector_names,
            demand_per_sector=self.gross_demand_remaining,
            renewable_withdrawal_per_sector=self.actual_renewable_withdrawal_per_sector,
            nonrenewable_withdrawal_per_sector=self.actual_nonrenewable_withdrawal_per_sector,
            zones_per_sector={
                "surfacewater": self.surfacewater_allocation_zones,
                "groundwater": self.groundwater_allocation_zones,
            },
            use_local_first=self.use_local_first,
        )

        logger.debug(sub_message_str)

        # note: add the unused and actual withdrawals per withdrawal type and source (m3/day)
        for withdrawal_name in self.withdrawal_names:

            var_str = get_key(["unused", withdrawal_name, "withdrawal"])

            setattr(
                self,
                var_str,
                dict(
                    (source_name, unused_withdrawal[withdrawal_name][source_name])
                    for source_name in self.source_names
                ),
            )

        # total withdrawal, including unused withdrawals (m3/day)
        self.total_withdrawal = sum_list(
            list(self.actual_renewable_withdrawal.values())
        ) + sum_list(list(self.actual_nonrenewable_withdrawal.values()))

        # total allocated water, consumption and return flow, updated per sector
        self.total_allocation = pcr.spatial(pcr.scalar(0))
        self.total_consumption = pcr.spatial(pcr.scalar(0))
        self.total_return_flow = pcr.spatial(pcr.scalar(0))

        for sector_name in self.sector_names:

            # return flow ratio (-)
            return_flow_ratio = self.get_return_flow_ratio(
                gross_demand=self.gross_demand[sector_name],
                net_demand=self.net_demand[sector_name],
            )

            for key in self.allocated_demand_per_sector.keys():

                # consumption and return flow per sector (m3/day)
                self.return_flow_demand_per_sector[key][sector_name] = (
                    return_flow_ratio
                    * self.allocated_demand_per_sector[key][sector_name]
                )

                self.consumed_demand_per_sector[key][sector_name] = pcr.max(
                    0,
                    self.allocated_demand_per_sector[key][sector_name]
                    - self.return_flow_demand_per_sector[key][sector_name],
                )

                # (m3/day)
                self.total_allocation = (
                    self.total_allocation
                    + self.allocated_demand_per_sector[key][sector_name]
                )

                # (m3/day)
                self.total_return_flow = (
                    self.total_return_flow
                    + self.return_flow_demand_per_sector[key][sector_name]
                )
                self.total_consumption = (
                    self.total_consumption
                    + self.consumed_demand_per_sector[key][sector_name]
                )

            # include desalinated water use if used
            if self.desalinated_water_use_flag:
                self.return_flow_demand_per_sector_desalwater[sector_name] = (
                    return_flow_ratio
                    * self.allocated_demand_per_sector_desalwater[sector_name]
                )
                self.consumed_demand_per_sector_desalwater[sector_name] = pcr.max(
                    0,
                    self.allocated_demand_per_sector_desalwater[sector_name]
                    - self.return_flow_demand_per_sector_desalwater[sector_name],
                )

                self.total_allocation = (
                    self.total_allocation
                    + self.allocated_demand_per_sector_desalwater[sector_name]
                )

                self.total_return_flow = (
                    self.total_return_flow
                    + self.return_flow_demand_per_sector_desalwater[sector_name]
                )
                self.total_consumption = (
                    self.total_consumption
                    + self.consumed_demand_per_sector_desalwater[sector_name]
                )

        # the total return flow also contains the unused withdrawals (m3/day)
        self.total_return_flow = (
            self.total_return_flow
            + sum_list(list(self.unused_renewable_withdrawal.values()))
            + sum_list(list(self.unused_nonrenewable_withdrawal.values()))
        )

        logger.info(message_str)
        logger.info(
            "return flows and consumption added on the basis of the allocated demand"
        )

        # water balance check
        if debug:
            # per sector: short-term gross demands vs. actual allocated demand
            for sector_name in self.sector_names:
                water_balance_check(
                    states_ini=[self.gross_demand[sector_name]],
                    states_end=[
                        self.allocated_demand_per_sector["renewable_surfacewater"][
                            sector_name
                        ],
                        self.allocated_demand_per_sector["renewable_groundwater"][
                            sector_name
                        ],
                        self.allocated_demand_per_sector["nonrenewable_surfacewater"][
                            sector_name
                        ],
                        self.allocated_demand_per_sector["nonrenewable_groundwater"][
                            sector_name
                        ],
                        self.allocated_demand_per_sector_desalwater[sector_name],
                    ],
                    cellarea=self.cellarea,
                    var_name=sector_name,
                    process_name="Short-term demand vs Water allocation",
                    zones=self.surfacewater_allocation_zones[sector_name],
                    date=date,
                )

            # per source: short-term water availability vs. actual allocated withdrawal
            for source_name in self.source_names:
                water_balance_check(
                    states_ini=[availability[source_name]],
                    states_end=[
                        self.allocated_withdrawal_per_sector[
                            "renewable_%s" % source_name
                        ][sector_name]
                        for sector_name in self.sector_names
                    ],
                    cellarea=self.cellarea,
                    var_name=source_name,
                    process_name="Short-term availability vs Water withdrawal",
                    date=date,
                )

            # per withdrawal, source and sector: actual allocated demand vs. actual allocated withdrawal
            for withdrawal_name in self.withdrawal_names:
                for source_name in self.source_names:
                    for sector_name in self.sector_names:
                        water_balance_check(
                            states_ini=[
                                self.allocated_demand_per_sector[
                                    "%s_%s" % (withdrawal_name, source_name)
                                ][sector_name]
                            ],
                            states_end=[
                                self.allocated_withdrawal_per_sector[
                                    "%s_%s" % (withdrawal_name, source_name)
                                ][sector_name]
                            ],
                            cellarea=self.cellarea,
                            var_name="%s %s %s"
                            % (withdrawal_name, source_name, sector_name),
                            process_name="Water allocation vs Water withdrawal",
                            zones=getattr(self, "%s_allocation_zones" % source_name)[
                                sector_name
                            ],
                            date=date,
                        )

            # per source: pumping capacity vs. actual allocated withdrawal
            for source_name in self.source_names:
                if self.pumping_capacity_flag[source_name]:
                    water_balance_check(
                        states_ini=[
                            getattr(self, "%s_withdrawal_capacity" % source_name)
                        ],
                        states_end=[
                            self.allocated_withdrawal_per_sector[
                                "renewable_%s" % source_name
                            ][sector_name]
                            for sector_name in self.sector_names
                        ]
                        + [
                            self.allocated_withdrawal_per_sector[
                                "nonrenewable_%s" % source_name
                            ][sector_name]
                            for sector_name in self.sector_names
                        ],
                        cellarea=self.cellarea,
                        var_name=source_name,
                        process_name="Pumping capacity vs Water withdrawal",
                        date=date,
                    )

        return None

    def get_return_flow_ratio(self, gross_demand, net_demand):
        """
        get_return_flow_ratio:
                           function which returns the return flow ratio as the
                           ratio of the net and gross demand per sector.
                           Assumes that all input is compatible with spatial scalar PCRaster fields.

        input:
        =====
        gross_demand     : gross water demand per sector [volume or waterslice]
        net_demand       : net water demand per sector   [volume or waterslice]

        output:
        ======
        return_flow_ratio : return flow ratio [-]
        """

        # return flow ratio; small gross water demands give a ratio of zero
        return_flow_ratio = pcr.max(
            0.00,
            1.00 - pcr_return_val_div_zero(net_demand, gross_demand, very_small_number),
        )
        return return_flow_ratio

    def update_longterm_availability(
        self, groundwater_storage, surfacewater_discharge, surfacewater_runoff, date
    ):
        """
        update_longterm_availability: function that updates the availability per
        zone as a function of the date.

        input:
        ======
        groundwater_storage    : PCRaster maps with groundwater potential storage
                                 the last fay of the month (units: m)
        surfacewater_discharge : PCRaster maps with surface discharge (units: m3/s)
        surfacewater_runoff     : PCRaster maps with surface total runoff (units: m/day)
        date                   : date of the update
        """

        # accumulate the water availability over the month
        self.average_groundwater_storage += groundwater_storage
        self.average_surfacewater_discharge += surfacewater_discharge
        self.average_surfacewater_runoff += surfacewater_runoff

        # update the long-term variables on the last day of the month
        if (self.time_step == "monthly") or (
            self.time_step == "daily" and is_last_day_month(date)
        ):

            # number of steps within the time step: days in the month for daily time steps, one for monthly
            steps = date.day

            update_date = datetime.datetime(date.year, date.month, 1)

            # monthly average: accumulated values divided by the number of steps
            self.average_groundwater_storage /= steps
            self.average_surfacewater_discharge /= steps
            self.average_surfacewater_runoff /= steps

            # groundwater storage
            date_index, matched_date, message_str = match_date_by_julian_number(
                update_date, self.groundwater_longterm_storage_dates
            )

            # replace the value of the matched date by the weighted update; if the long-term value is not
            # defined, use the present value (m per day)
            groundwater_longterm_storage = self.groundwater_longterm_storage.pop(
                matched_date
            )
            groundwater_longterm_storage = pcr.cover(
                self.groundwater_update_weight * self.average_groundwater_storage
                + (1 - self.groundwater_update_weight) * groundwater_longterm_storage,
                self.average_groundwater_storage,
            )
            self.groundwater_longterm_storage_dates[date_index] = update_date

            self.groundwater_longterm_storage[update_date] = (
                groundwater_longterm_storage
            )

            message_str = str.join(
                " ", ("groundwater long-term total base flow updated for", message_str)
            )
            logger.debug(message_str)

            # surface water discharge (monthly)
            date_index, matched_date, message_str = match_date_by_julian_number(
                update_date, self.surfacewater_longterm_discharge_dates
            )

            # replace the value of the matched date by the weighted update; if the long-term value is not
            # defined, use the present value (m3/s)
            surfacewater_longterm_discharge = self.surfacewater_longterm_discharge.pop(
                matched_date
            )
            surfacewater_longterm_discharge = pcr.cover(
                self.surfacewater_update_weight * self.average_surfacewater_discharge
                + (1 - self.surfacewater_update_weight)
                * surfacewater_longterm_discharge,
                self.average_surfacewater_discharge,
            )

            self.surfacewater_longterm_discharge_dates[date_index] = update_date

            self.surfacewater_longterm_discharge[update_date] = (
                surfacewater_longterm_discharge
            )

            message_str = str.join(
                " ", ("surface water long-term discharge updated for", message_str)
            )
            logger.debug(message_str)

            # surface water runoff (monthly)
            date_index, matched_date, message_str = match_date_by_julian_number(
                update_date, self.surfacewater_longterm_runoff_dates
            )

            # replace the value of the matched date by the weighted update; if the long-term value is not
            # defined, use the present value (m/day)
            surfacewater_longterm_runoff = self.surfacewater_longterm_runoff.pop(
                matched_date
            )
            surfacewater_longterm_runoff = pcr.cover(
                self.surfacewater_update_weight * self.average_surfacewater_runoff
                + (1 - self.surfacewater_update_weight) * surfacewater_longterm_runoff,
                self.average_surfacewater_runoff,
            )

            self.surfacewater_longterm_runoff_dates[date_index] = update_date

            self.surfacewater_longterm_runoff[update_date] = (
                surfacewater_longterm_runoff
            )

            message_str = str.join(
                " ", ("surface water long-term total runoff updated for", message_str)
            )
            logger.debug(message_str)

        return None

    def update_longterm_demand(self, date):
        """
        update_longterm_demand: function that updates the gross sectoral water demands
                                as a function of the date.

        input:
        ======
        date                  : date of the update
        """

        # accumulate the gross water demands over the month (m/day)
        for sector_name in self.sector_names:
            self.average_gross_demand[sector_name] += (
                self.gross_demand[sector_name] / self.cellarea
            )

        # update the long-term variables on the last day of the month
        if (self.time_step == "monthly") or (
            self.time_step == "daily" and is_last_day_month(date)
        ):

            # number of steps within the time step: days in the month for daily time steps, one for monthly
            steps = date.day

            for sector_name in self.sector_names:
                # monthly average: accumulated values divided by the number of steps
                average_gross_demand = self.average_gross_demand[sector_name] / steps

                var_value = getattr(self, "gross_demand_longterm_%s" % sector_name)
                var_dates = getattr(
                    self, "gross_demand_longterm_%s_dates" % sector_name
                )
                var_weight = getattr(self, "%s_update_weight" % sector_name)

                update_date = datetime.datetime(date.year, date.month, 1)
                date_index, matched_date, message_str = match_date_by_julian_number(
                    update_date, var_dates
                )

                # replace the value of the matched date by the weighted update; if the long-term value is not
                # defined, use the present value (m/day)
                gross_demand_longterm = var_value.pop(matched_date)
                gross_demand_longterm = pcr.cover(
                    var_weight * average_gross_demand
                    + (1 - var_weight) * gross_demand_longterm,
                    average_gross_demand,
                )
                var_dates[date_index] = update_date

                var_value[update_date] = gross_demand_longterm

                setattr(self, "gross_demand_longterm_%s" % sector_name, var_value)
                setattr(self, "gross_demand_longterm_%s_dates" % sector_name, var_dates)

                message_str = str.join(
                    " ",
                    (
                        "%s long-term gross demand updated for" % sector_name,
                        message_str,
                    ),
                )
                logger.debug(message_str)

        return None

    def update_longterm_potential_withdrawals(self, date):
        """
        update_longterm_potential_withdrawals:
               function that updates the groundwater potential withdrawals as a function
               of the date

        input:
        ======
        date : date of the update.
        """

        # update the long-term variables on the last day of the month
        if (self.time_step == "monthly") or (
            self.time_step == "daily" and is_last_day_month(date)
        ):

            # groundwater
            if self.pumping_capacity_flag["groundwater"]:
                # groundwater potential withdrawals for the date (m3/day)
                groundwater_potential_withdrawal = (
                    self.groundwater_potential_estimated_withdrawal
                )

                # time step to update the groundwater potential withdrawal (monthly), matching
                # groundwater_longterm_avail_dates
                update_date = datetime.datetime(date.year, date.month, 1)
                date_index, matched_date, message_str = match_date_by_julian_number(
                    update_date, self.groundwater_longterm_pot_withdrawal_dates
                )

                # replace the value of the matched date by the weighted update; if the long-term value is not
                # defined, use the present value
                groundwater_longterm_pot_withdrawal = (
                    self.groundwater_longterm_potential_withdrawal.pop(matched_date)
                )
                groundwater_longterm_pot_withdrawal = pcr.cover(
                    self.groundwater_update_weight * groundwater_potential_withdrawal
                    + (1 - self.groundwater_update_weight)
                    * groundwater_longterm_pot_withdrawal,
                    groundwater_potential_withdrawal,
                )

                self.groundwater_longterm_pot_withdrawal_dates[date_index] = update_date

                self.groundwater_longterm_potential_withdrawal[update_date] = (
                    groundwater_longterm_pot_withdrawal
                )

                message_str = str.join(
                    " ", ("groundwater potential withdrawals updated for", message_str)
                )
                logger.debug(message_str)

            # surface water
            if self.pumping_capacity_flag["surfacewater"]:
                # surface water potential withdrawals for the date (m3/day)
                surfacewater_potential_withdrawal = (
                    self.surfacewater_potential_estimated_withdrawal
                )

                # time step to update the surface water potential withdrawal (monthly), matching
                # groundwater_longterm_avail_dates
                update_date = datetime.datetime(date.year, date.month, 1)
                date_index, matched_date, message_str = match_date_by_julian_number(
                    update_date, self.surfacewater_longterm_pot_withdrawal_dates
                )

                # replace the value of the matched date by the weighted update; if the long-term value is not
                # defined, use the present value
                surfacewater_longterm_pot_withdrawal = (
                    self.surfacewater_longterm_potential_withdrawal.pop(matched_date)
                )
                surfacewater_longterm_pot_withdrawal = pcr.cover(
                    self.surfacewater_update_weight * surfacewater_potential_withdrawal
                    + (1 - self.surfacewater_update_weight)
                    * surfacewater_longterm_pot_withdrawal,
                    surfacewater_potential_withdrawal,
                )

                self.surfacewater_longterm_pot_withdrawal_dates[date_index] = (
                    update_date
                )

                self.surfacewater_longterm_potential_withdrawal[update_date] = (
                    surfacewater_longterm_pot_withdrawal
                )

                message_str = str.join(
                    " ",
                    ("surface water potential withdrawals updated for", message_str),
                )
                logger.debug(message_str)

        return None

    def get_final_conditions(self):
        """
        get_final_conditions: function that returns a dictionary holding all states and fluxes
                             of the soil hydrology module that are necessary for a restart.

        output:
        ======
        state_info         : a dictionary with the key and the value
        """

        state_info = {}

        for report_name, attr_name in self.report_state_info.items():

            state_info[report_name] = getattr(self, attr_name)

        return state_info
