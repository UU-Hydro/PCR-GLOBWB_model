import datetime
import logging

import pcraster as pcr

from qualloc.allocation import get_zonal_total
from qualloc.basic_functions import max_dicts, pcr_return_val_div_zero, sum_list
from qualloc.model_time import (
    get_weights_from_dates,
    is_last_day_month,
    match_date_by_julian_number,
)

# water quality constituents: variable name in the configuration file as key and
# variable name in the netCDF file as value; groundwater variables are None as
# they are not developed yet
water_quality_forcing_variables = {
    "surfacewater_temperature": "waterTemperature",
    "surfacewater_organic": "organic",
    "surfacewater_salinity": "salinity",
    "surfacewater_pathogen": "pathogen",
    "groundwater_temperature": None,
    "groundwater_organic": None,
    "groundwater_salinity": None,
    "groundwater_pathogen": None,
}

# small number to avoid division by zero in PCRaster
very_small_number = 1.0e-12

# large number for sectors without water quality restrictions
unattainable_threshold = 1.0e20

NoneType = type(None)

logger = logging.getLogger(__name__)


class water_quality(object):

    def __init__(
        self,
        landmask,
        time_increment,
        source_names,
        constituent_names,
        constituent_limits,
        quality_update_weight,
        surfacewater_longterm_temperature,
        surfacewater_longterm_organic,
        surfacewater_longterm_salinity,
        surfacewater_longterm_pathogen,
        groundwater_longterm_temperature,
        groundwater_longterm_organic,
        groundwater_longterm_salinity,
        groundwater_longterm_pathogen,
    ):

        object.__init__(self)

        self.landmask = landmask
        self.time_increment = time_increment

        self.constituent_names = constituent_names
        self.constituent_limits = constituent_limits

        # long-term water quality
        self.quality_update_weight = quality_update_weight

        for source_name in source_names:
            for constituent_name in self.constituent_names:
                var_str = "%s_longterm_%s" % (source_name, constituent_name)
                var_out = eval(var_str)

                # cover NaN with zero concentration and clip to the land mask
                for date, values in var_out.items():
                    values = pcr.ifthenelse(values >= 0, values, pcr.scalar(0))
                    var_out[date] = pcr.ifthen(self.landmask, values)

                # store the variable and its sorted dates
                setattr(self, var_str, var_out)
                setattr(self, var_str + "_dates", sorted(list(var_out.keys())))

        # annual average water quality
        self.surfacewater_annual_temperature = pcr.scalar(0)
        self.surfacewater_annual_organic = pcr.scalar(0)
        self.surfacewater_annual_salinity = pcr.scalar(0)
        self.surfacewater_annual_pathogen = pcr.scalar(0)
        self.groundwater_annual_temperature = pcr.scalar(0)
        self.groundwater_annual_organic = pcr.scalar(0)
        self.groundwater_annual_salinity = pcr.scalar(0)
        self.groundwater_annual_pathogen = pcr.scalar(0)
        self.update_annual_water_quality(source_names)

        self.report_state_info = {
            "surfacewater_longterm_temperature": "surfacewater_longterm_temperature",
            "surfacewater_longterm_organic": "surfacewater_longterm_organic",
            "surfacewater_longterm_salinity": "surfacewater_longterm_salinity",
            "surfacewater_longterm_pathogen": "surfacewater_longterm_pathogen",
            "groundwater_longterm_temperature": "groundwater_longterm_temperature",
            "groundwater_longterm_organic": "groundwater_longterm_organic",
            "groundwater_longterm_salinity": "groundwater_longterm_salinity",
            "groundwater_longterm_pathogen": "groundwater_longterm_pathogen",
        }

        return None

    def update_annual_water_quality(self, source_names):
        """
        update_annual_water_quality :
                   update the overall water quality over the year per
                   source and constituent equivalent to water_management.
        """

        logger.info("annual water quality over a year updated")

        # update the long-term totals
        for source_name in source_names:
            for constituent_name in self.constituent_names:

                var_in = "%s_longterm_%s" % (source_name, constituent_name)

                # dates (months) and their weights
                dates = getattr(self, var_in + "_dates")
                weights = get_weights_from_dates(dates)

                # update the long-term total per constituent and source
                longterm_constituent_quality = getattr(self, var_in)
                values = sum(
                    list(
                        weights[date] * longterm_constituent_quality[date]
                        for date in dates
                    )
                )

                var_out = "%s_annual_%s" % (source_name, constituent_name)
                setattr(self, var_out, values)

        return None

    def get_longterm_quality_for_date(
        self,
        source_names,
        date,
    ):

        message_str = "long-term water quality for %s at %s level." % (
            date,
            self.time_increment,
        )

        # initialize the monthly average water quality states
        for source_name in source_names:
            for constituent_name in self.constituent_names:
                setattr(
                    self,
                    "average_%s_%s" % (source_name, constituent_name),
                    pcr.spatial(pcr.scalar(0)),
                )

        constituent_longterm_states = {}

        # monthly or yearly water quality states
        if self.time_increment in ["monthly", "yearly"]:
            for source_name in source_names:
                constituent_longterm_states[source_name] = {}
                for constituent_name in self.constituent_names:

                    if self.time_increment == "monthly":
                        # get the constituent state for the matching date

                        var_str = "%s_longterm_%s" % (source_name, constituent_name)

                        dates = getattr(self, var_str + "_dates")
                        date_index, matched_date, sub_message_str = (
                            match_date_by_julian_number(date, dates)
                        )

                        longterm_constituent_quality = getattr(self, var_str)
                        constituent_state = longterm_constituent_quality[matched_date]

                        message_str = str.join("\n", (message_str, sub_message_str))

                    elif self.time_increment == "yearly":
                        var_str = "%s_annual_%s" % (source_name, constituent_name)
                        constituent_state = getattr(self, var_str)

                    constituent_longterm_states[source_name][
                        constituent_name
                    ] = constituent_state

        else:
            logger.error(
                "the option %s for the time increment in the water quality module is not allowed!"
                % self.time_increment
            )
            sys.exit()

        logger.info(message_str)

        return constituent_longterm_states

    def update_longterm_quality(self, source_names, time_step, date):
        """
        update_longterm_quality:
                                  function that updates the quality
                                  per zone as a function of the date.
        """

        # accumulate the water quality over the month per source and constituent
        # (mg/L, degC, cfu/100mL)
        for source_name in source_names:
            for constituent_name in self.constituent_names:
                key = "average_%s_%s" % (source_name, constituent_name)
                average = getattr(self, key)
                average += self.constituent_shortterm_quality[source_name][
                    constituent_name
                ]
                setattr(self, key, average)

        # update the long-term water quality on the last day of the month
        if (time_step == "monthly") or (
            time_step == "daily" and is_last_day_month(date)
        ):

            # number of steps within the time step: days in the month for daily time
            # steps, one for monthly time steps
            steps = date.day

            for source_name in source_names:
                for constituent_name in self.constituent_names:
                    # monthly average: accumulated values divided by the number of steps
                    key = "average_%s_%s" % (source_name, constituent_name)
                    average_constituent_quality = getattr(self, key) / steps

                    var = "%s_longterm_%s" % (source_name, constituent_name)

                    # time step to update the long-term quality (monthly)
                    update_date = datetime.datetime(date.year, date.month, 1)
                    var_dates = getattr(self, var + "_dates")
                    date_index, matched_date, message_str = match_date_by_julian_number(
                        update_date, var_dates
                    )

                    # replace the value of the matched date by the weighted update; if the long-term
                    # value is not defined, use the present value
                    constituent_longterm_quality = getattr(self, var).pop(matched_date)
                    constituent_longterm_quality = pcr.cover(
                        self.quality_update_weight[source_name]
                        * average_constituent_quality
                        + (1 - self.quality_update_weight[source_name])
                        * constituent_longterm_quality,
                        average_constituent_quality,
                    )

                    getattr(self, var + "_dates")[date_index] = update_date

                    getattr(self, var)[update_date] = constituent_longterm_quality

                    message_str = str.join(
                        " ",
                        (
                            "%s from %s availability updated for"
                            % (constituent_name, source_name),
                            message_str,
                        ),
                    )
                    logger.debug(message_str)

        return None

    def get_suitability_per_sector(
        self,
        constituent_state,
        sector_names,
        fractional_flag=False,
    ):
        """
        get_suitability_per_sector:
                            function to define the suitability of the
                            available water to be used by a specific sector
        input
        =====
        constituent_state : dictionary with constituent names (keys) and
                            constituent concentrations/states (values)
        fractional_flag    : boolean; if False, water could either be suitable
                            to be used or not (i.e., 0 or 1)

        output
        ======
        suitability_per_sector :
                            dictionary with sector names (keys) and
                            overall suitability of available water to be used
                            (values) expressed as a ratio where 0 is not suitable
                            and 1 is perfectly suitable
        """

        suitability_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(1.0))) for sector_name in sector_names
        )

        for sector_name in sector_names:
            suitability_per_constituent = {}

            for constituent_name in self.constituent_names:
                # minimum and maximum water quality thresholds
                limit_min = pcr.spatial(pcr.scalar(0.0))
                limit_max = pcr.spatial(
                    pcr.scalar(self.constituent_limits[sector_name][constituent_name])
                )

                # suitability fraction and total
                suitability_per_constituent[constituent_name] = pcr_return_val_div_zero(
                    constituent_state[constituent_name] - limit_min,
                    limit_max - limit_min,
                    very_small_number,
                )

            # overall suitability per sector: the most unsuitable constituent dominates;
            # fractions are inverted so that one means fully suitable and zero unsuitable
            suitability = 1 - max_dicts(suitability_per_constituent)

            suitability = pcr.ifthenelse(
                suitability > 0.0,
                suitability,
                pcr.ifthenelse(suitability == 0.0, very_small_number, pcr.scalar(0.0)),
            )

            if not fractional_flag:
                suitability = pcr.ifthenelse(
                    suitability == 0, pcr.scalar(0), pcr.scalar(1)
                )

            suitability_per_sector[sector_name] = pcr.ifthen(
                self.landmask,
                pcr.cover(suitability, suitability_per_sector[sector_name]),
            )

        return suitability_per_sector

    def get_weights_availability_per_sector(
        self,
        source_name,
        sector_names,
        prioritization_per_sector,
        zones_per_sector,
        demand_per_sector,
        availability,
        suitability_per_sector=None,
        water_gap_flag=True,
    ):
        """
        get_weights_availability_per_sector :
                                    function to calculate the rates to distribute either water availability
                                    or demands based on the quality of the water, the sectoral gross demands
                                    and the sectoral prioritization

        input:
        =====
        source_name               : string with the source name
        sector_names              : list with sector names (string)
        prioritization_per_sector : dictionary with sector names (string) as keys and PCRaster maps with
                                    sectoral prioritization (nominal) as values
        zones_per_sector          : dictionary with sector names (string) as keys and PCRaster maps with
                                    allocation zones (nominal) as values
        demand_per_sector         : dictionary with sector names (string) as keys and PCRaster maps with
                                    sectoral gross demands as values (units: m3/period)
        availability              : PCRaster map with water availability of selected source (units: m3/period)
        suitability_per_sector    : dictionary with sector names (string) as keys and PCRaster maps with
                                    water suitability ratios as values
        water_gap_flag             : boolean; if True, sectoral prioritization is taken into account,
                                    if False, all sector has the same priority

        output:
        ======
        weight_per_sector      : dictionary with sector names (keys) and the weight of a sector (values)
                                 over a variable (e.g., availability) considering the water quality
        """
        weight_per_sector = dict(
            (sector_name, pcr.spatial(pcr.scalar(1.0))) for sector_name in sector_names
        )

        for sector_name in sector_names:

            # sectoral priority
            if not water_gap_flag:
                priority_sector = pcr.spatial(pcr.scalar(1.0))
            else:
                priority_sector = prioritization_per_sector[sector_name] ** -1

            # sectoral water demand per zone
            demand_sector_area = get_zonal_total(
                demand_per_sector[sector_name], zones_per_sector[sector_name]
            )

            demand_total_area = get_zonal_total(
                sum_list(list(demand_per_sector.values())),
                zones_per_sector[sector_name],
            )

            demand_sector_fraction = pcr_return_val_div_zero(
                demand_sector_area, demand_total_area, very_small_number
            )

            # sectoral suitability fractions
            if not isinstance(suitability_per_sector, NoneType):
                suitability_sector = suitability_per_sector[sector_name]
            else:
                suitability_sector = pcr.spatial(pcr.scalar(1))

            suitability_sector_area = get_zonal_total(
                suitability_sector, zones_per_sector[sector_name]
            )

            # suitable water availability
            availability_suitable_sector = suitability_sector * availability
            availability_suitable_sector_area = get_zonal_total(
                availability_suitable_sector, zones_per_sector[sector_name]
            )

            availability_sector_fraction = pcr_return_val_div_zero(
                suitability_sector_area,
                availability_suitable_sector_area,
                very_small_number,
            )

            weight = (
                priority_sector
                * demand_sector_fraction
                * availability_suitable_sector
                * availability_sector_fraction
            )

            weight_per_sector[sector_name] = weight

        # normalize the quality weights
        weight_total = sum_list(list(weight_per_sector.values()))
        for sector_name in sector_names:
            weight_per_sector[sector_name] = pcr_return_val_div_zero(
                weight_per_sector[sector_name], weight_total, very_small_number
            )

        return weight_per_sector

    def get_final_conditions(self):
        """
        get_final_conditions: function that returns a dictionary holding all states \
        of the water quality module that are necessary for a restart.
        Returns state_info, a dictionary with the key and the value
        """
        state_info = {}

        for report_name, attr_name in self.report_state_info.items():

            state_info[report_name] = getattr(self, attr_name)

        return state_info
