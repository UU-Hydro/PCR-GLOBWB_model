from copy import deepcopy

import pcraster as pcr

from qualloc.basic_functions import (
    pcr_get_statistics,
    pcr_return_val_div_zero,
    sum_list,
)

# small number to avoid division by zero in PCRaster
very_small_number = 1.0e-12

NoneType = type(None)


def get_key(str_list):

    if isinstance(str_list, list):
        key = str_list[0]
    else:
        key = str(str_list)

    for ix in range(1, len(str_list)):

        if str_list[ix - 1] == "":
            d_str = ""
        else:
            d_str = "_"

        key = str.join(d_str, (key, str_list[ix]))

    return key


def allocate_demand_to_availability(
    demand: pcr.Field,
    available: dict[str, pcr.Field],
    zones: dict[str, pcr.Field] | None,
    verbose: bool = False,
    max_iterations: int = 100,
    relative_tolerance: float = 1e-6
) -> tuple[pcr.Field, dict[str, pcr.Field], dict[str, pcr.Field], str]:
    """
    Allocates the demand to the available supply of one or more sources.

    Each source pools its supply over its zones: a cell claims a share of the
    zone's untapped supply equal to its share of the zone's unmet demand, split
    over the sources and limited to its unmet demand. What a zone allocates is
    withdrawn from its cells in proportion to their untapped supply. Iterates
    until the demand is met, the supply is exhausted or no progress is made.

    Input:
    ======
    demand (pcr.Field):             scalar demand per cell; negatives count as 0;
    available (dict[str, pcr.Field]):
                                    scalar supply per cell per source; negatives
                                    count as 0;
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source; if None,
                                    every cell is its own zone;
    verbose (bool):                 print the progress of every iteration;
    max_iterations (int):           maximum number of iterations;
    relative_tolerance (float):     fraction of the initial demand and supply below
                                    which they count as zero.

    Output:
    =======
    unmet (pcr.Field):              unmet demand; met = max(demand, 0) - unmet;
    untapped (dict[str, pcr.Field]):
                                    untapped supply per source;
                                    withdrawn = max(available, 0) - untapped;
    allocated (dict[str, pcr.Field]):
                                    demand allocated per source, i.e. where the
                                    water is delivered, not where it is withdrawn;
    message (str):                  log of the iterations and statistics.
    """
    
    demand = pcr.max(demand, 0)
    available = {s: pcr.max(available[s], 0) for s in available.keys()}
    demand_initial = demand
    available_initial = dict(available)

    demand_tolerance = relative_tolerance * demand
    available_tolerance = relative_tolerance * sum(list(available.values()))

    unmet = demand
    untapped = dict(available)
    allocated = {s: pcr.scalar(0) for s in untapped.keys()}
    
    if zones is not None:
        zonal_untapped = {
            s: pcr.areatotal(
                untapped[s],
                zones[s],
            )
            for s in zones.keys()
        }
    else:
        zonal_untapped = {s: untapped[s] for s in untapped.keys()}

    mask = unmet > demand_tolerance
    n_unmet = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
    n_unmet_start = n_unmet

    if n_unmet == 0:
        message = "All demand is initially met."
        return unmet, untapped, allocated, message

    message = "allocation of demand to availability:"
    iteration = 1
    while iteration <= max_iterations:

        if zones is not None:
            zonal_unmet = {
                s: pcr.areatotal(
                    unmet,
                    zones[s],
                )
                for s in zones.keys()
            }
        else: 
            zonal_unmet = {s: unmet for s in zonal_untapped.keys()}

        # Demand share:
        # The local demand as a proportion of the zonal demand
        demand_share = {
            s: pcr_return_val_div_zero(
                    unmet, 
                    zonal_unmet[s], 
                    very_small_number,
                )
                for s in zonal_unmet.keys()
        }

        # Potential allocation:
        # The demand share of the zonal availability
        potential_allocation = {
            s: demand_share[s] * zonal_untapped[s]
            for s in zonal_untapped.keys()
        }

        # Source share:
        # The source allocation as the proportion of the total allocation
        potential_allocation_total = sum(list(potential_allocation.values()))
        source_share = {
            s: pcr_return_val_div_zero(
                potential_allocation[s],
                potential_allocation_total,
                very_small_number,
            )
            for s in potential_allocation.keys()
        }
        
        # Allocation:
        # Minimum of the potential allocation and the source share of the unmet demand
        allocation = {
            s: pcr.min(
                potential_allocation[s],
                source_share[s] * unmet,
            )
            for s in potential_allocation.keys()
        }

        if zones is not None:
            zonal_allocation = {
                s: pcr.areatotal(
                    allocation[s],
                    zones[s],
                )
                for s in zones.keys()
            }
        else:
            zonal_allocation = {s: allocation[s] for s in allocation.keys()}

        # Withdrawal fraction:
        # Proportion of the (local and zonal) availability
        withdrawal_fraction = {
            s: pcr_return_val_div_zero(
                    zonal_allocation[s],
                    zonal_untapped[s],
                    very_small_number,
                )
                for s in zonal_allocation.keys()
        }
        withdrawal_fraction = {s: pcr.min(withdrawal_fraction[s], 1) for s in withdrawal_fraction.keys()}

        # Register
        unmet = pcr.max(unmet - sum(list(allocation.values())), 0)
        untapped = {s: pcr.max(untapped[s] * (1 - withdrawal_fraction[s]), 0) for s in untapped.keys()}
        zonal_untapped = {s: pcr.max(zonal_untapped[s] * (1 - withdrawal_fraction[s]), 0) for s in zonal_untapped.keys()}
        allocated = {s: allocated[s] + allocation[s] for s in allocated.keys()}

        # Exit conditions
        mask = unmet > demand_tolerance
        n_unmet_current = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
        mask = mask & (sum(list(untapped.values())) > available_tolerance)
        n_available = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]

        # Reporting
        message_iteration = "allocation iteration %d\n" % iteration
        message_iteration += "cells with unmet demand: %6d / %6d in total\n" % (n_unmet_current, n_unmet_start)
        if verbose:
            print(message_iteration)
        message = str.join(
            "\n", (message, message_iteration)
        )

        # Skip the loop if there is no more unmet demand
        if n_unmet_current == 0:
            break
        # Skip the loop if there is no more availability
        if not n_available:
            break
        # Skip the loop if there is not progress
        if n_unmet_current >= n_unmet:
            break

        n_unmet = n_unmet_current
        iteration = iteration + 1

    met = demand_initial - unmet
    withdrawn = {s: available_initial[s] - untapped[s] for s in untapped.keys()}

    # add the final information to the message string
    demand_stats = pcr_get_statistics(demand_initial)
    met_stats = pcr_get_statistics(met)
    unmet_stats = pcr_get_statistics(unmet)
    available_stats = pcr_get_statistics(sum(list(available_initial.values())))
    withdrawn_stats = pcr_get_statistics(sum(list(withdrawn.values())))
    untapped_stats = pcr_get_statistics(sum(list(untapped.values())))

    message = str.join(
        "\n",
        (
            message,
            "statistics:",
            "=" * len("statistics:"),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "initial demand",
                demand_stats["count"],
                demand_stats["average"],
                demand_stats["min"],
                demand_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "met demand",
                met_stats["count"],
                met_stats["average"],
                met_stats["min"],
                met_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "unmet demand",
                unmet_stats["count"],
                unmet_stats["average"],
                unmet_stats["min"],
                unmet_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "initial available",
                available_stats["count"],
                available_stats["average"],
                available_stats["min"],
                available_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "withdrawn available",
                withdrawn_stats["count"],
                withdrawn_stats["average"],
                withdrawn_stats["min"],
                withdrawn_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "untapped available",
                untapped_stats["count"],
                untapped_stats["average"],
                untapped_stats["min"],
                untapped_stats["max"],
            ),
        ),
    )

    return unmet, untapped, allocated, message


def allocate_demand_to_availability_with_options(
    demand: pcr.Field,
    available: dict[str, pcr.Field],
    zones: dict[str, pcr.Field],
    use_local_first: pcr.Field,
    use_allocation_zone: bool = True,
    reallocate_surplus: bool = True,
) -> tuple[pcr.Field, dict[str, pcr.Field], dict[str, pcr.Field], str]:
    """
    Allocates the demand to the available supply of one or more sources in up to
    three steps with allocate_demand_to_availability:

    1. local (use_local_first): cells first use their own supply;
    2. zonal (use_allocation_zone): the unmet demand is allocated over the zones;
    3. surplus (reallocate_surplus, two or more sources): allocations that other
       sources can cover from their untapped supply in the same cell are moved to
       them; the freed supply returns to where it was withdrawn and is allocated
       again over the zones.

    Input:
    ======
    demand (pcr.Field):             scalar demand per cell; negatives count as 0;
    available (dict[str, pcr.Field]):
                                    scalar supply per cell per source; negatives
                                    count as 0;
    zones (dict[str, pcr.Field]):   nominal allocation zones per source;
    use_local_first (pcr.Field):    boolean; cells that use their own supply first;
    use_allocation_zone (bool):     apply step 2;
    reallocate_surplus (bool):      apply step 3.

    Output:
    =======
    As allocate_demand_to_availability, combined over all steps.
    """
    
    demand = pcr.max(demand, 0)
    available = {s: pcr.max(available[s], 0) for s in available.keys()}
    demand_initial = demand
    available_initial = dict(available)

    unmet = demand
    untapped = dict(available)
    allocated = {s: pcr.scalar(0) for s in untapped.keys()}
    
    message = "allocation of demand to availability with options:"

    # local allocation (if used)
    use_local = pcr.cellvalue(pcr.maptotal(pcr.scalar(use_local_first)), 1)[0] > 0
    if use_local:
        message = str.join(
            "\n", (message, "", "* allocating local resources first:")
        )

        unmet_local = pcr.ifthenelse(use_local_first, unmet, 0)
        untapped_local = {s: pcr.ifthenelse(use_local_first, untapped[s], 0) for s in untapped.keys()}

        (
            opt_unmet,
            opt_untapped,
            opt_allocated,
            sub_message_str,
        ) = allocate_demand_to_availability(
            demand=unmet_local,
            available=untapped_local,
            zones=None,
        )

        # update the met demand, withdrawal, allocated demand and untapped supply per source
        unmet = pcr.ifthenelse(use_local_first, opt_unmet, unmet)
        untapped = {s: pcr.ifthenelse(use_local_first, opt_untapped[s], untapped[s]) for s in untapped.keys()}
        allocated = {s: allocated[s] + opt_allocated[s] for s in allocated.keys()}
        message = str.join("\n", (message, sub_message_str))

    # zonal allocation (if used) with the provided zones
    if use_allocation_zone:
        message = str.join(
            "\n",
            (
                message,
                "",
                "* allocating the available supply over the provided zones:",
            ),
        )

        (
            opt_unmet,
            opt_untapped,
            opt_allocated,
            sub_message_str,
        ) = allocate_demand_to_availability(
            demand=unmet,
            available=untapped,
            zones=zones,
        )

        # update the met demand, withdrawal, allocated demand and untapped supply per source
        unmet = opt_unmet
        untapped = {s: opt_untapped[s] for s in opt_untapped.keys()}
        allocated = {s: allocated[s] + opt_allocated[s] for s in allocated.keys()}
        message = str.join("\n", (message, sub_message_str))

    # reallocate any surplus (if used)
    if reallocate_surplus and len(available) > 1:
        message = str.join(
            "\n",
            (
                message,
                "",
                "* allocating any surplus from available supplyresources to satisfy outstanding demand:",
            ),
        )

        # free up supply iteratively:
        # 0: initialize the deficit as the unmet demand; it is reduced by the freed supply
        # then, per source:
        # 1: determine the zonal deficit for the current allocation zone
        # 2: get the (zonal) surplus from the supply needed to satisfy the deficit
        # 3: before limiting the surplus, determine the ratio to assess the relative
        #    contribution of the other sources
        # 4: determine the ratio of the deficit over the surplus to free
        # 5: move water from the other sources to the allocated supply, freeing it from the
        #    allocated supply of the present source

        deficit = unmet

        for source in available.keys():
            other_sources = [s for s in available.keys() if s != source]

            s_str = str.join("", other_sources)
            s_str = str.join(
                "", ("- processing %s with any surplus for " % source, s_str)
            )
            message = str.join("\n", (message, s_str))

            zonal_deficit = pcr.areatotal(
                deficit,
                zones[source],
            )

            # Source share:
            # The source surplus as the proportion of the total surplus
            surplus = sum([untapped[s] for s in other_sources])
            source_share = {
                s: pcr_return_val_div_zero(
                    untapped[s], surplus, very_small_number
                )
                for s in other_sources
            }

            # limit the surplus to what can actually be freed, before getting the zonal surplus
            surplus = pcr.min(allocated[source], surplus)
            zonal_surplus = pcr.areatotal(
                surplus,
                zones[source],
            )

            # free up supply; nothing can be freed without surplus
            allocation_ratio = pcr.min(
                pcr_return_val_div_zero(
                    zonal_deficit,
                    zonal_surplus,
                    very_small_number,
                ),
                1,
            )

            # supply that can be freed (total per zone)
            total_supply_freed = pcr.scalar(0)
            withdrawn_source = available_initial[source] - untapped[source]
            for other_source in other_sources:

                supply_freed = (
                    source_share[other_source]
                    * allocation_ratio
                    * pcr.min(
                        allocated[source],
                        untapped[other_source],
                    )
                )

                # move the freed supply from the allocated demand of this source to the
                # other source, which takes it from its untapped supply in the same cell
                allocated[source] = pcr.max(
                    0, allocated[source] - supply_freed
                )
                untapped[other_source] = pcr.max(
                    0, untapped[other_source] - supply_freed
                )
                allocated[other_source] = (
                    allocated[other_source] + supply_freed
                )

                total_supply_freed = total_supply_freed + pcr.areatotal(
                    supply_freed,
                    zones[source],
                )

            # return the freed supply to the cells it was withdrawn from, in proportion
            # to their withdrawal, rather than to the cells where the demand was met
            zonal_withdrawn_source = pcr.areatotal(withdrawn_source, zones[source])
            withdrawal_fraction = pcr.min(
                1.0,
                pcr_return_val_div_zero(
                    total_supply_freed,
                    zonal_withdrawn_source,
                    very_small_number,
                ),
            )
            untapped[source] += withdrawn_source * withdrawal_fraction

            # use the freed supply to satisfy any outstanding demand
            deficit = pcr.max(
                0,
                deficit
                - total_supply_freed
                * pcr_return_val_div_zero(deficit, zonal_deficit, very_small_number),
            )

        # repeat the reallocation with the freed supply
        (
            opt_unmet,
            opt_untapped,
            opt_allocated,
            sub_message_str,
        ) = allocate_demand_to_availability(
            demand=unmet,
            available=untapped,
            zones=zones,
        )
        # update the met demand, withdrawal, allocated demand and untapped supply per source
        unmet = opt_unmet
        untapped = {s: opt_untapped[s] for s in opt_untapped.keys()}
        allocated = {s: allocated[s] + opt_allocated[s] for s in allocated.keys()}
        message = str.join("\n", (message, sub_message_str))

    # add the overall statistics
    message = str.join(
        "\n",
        (
            message,
            "",
            "* overall allocation of the available supply resources over the provided zones:",
        ),
    )

    met = demand_initial - unmet
    withdrawn = {s: available_initial[s] - untapped[s] for s in untapped.keys()}
    
    demand_stats = pcr_get_statistics(demand_initial)
    met_stats = pcr_get_statistics(met)
    unmet_stats = pcr_get_statistics(unmet)
    available_stats = pcr_get_statistics(sum(list(available_initial.values())))
    withdrawn_stats = pcr_get_statistics(sum(list(withdrawn.values())))
    untapped_stats = pcr_get_statistics(sum(list(untapped.values())))

    message = str.join(
        "\n",
        (
            message,
            "statistics:",
            "=" * len("statistics:"),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "initial demand",
                demand_stats["count"],
                demand_stats["average"],
                demand_stats["min"],
                demand_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "met demand",
                met_stats["count"],
                met_stats["average"],
                met_stats["min"],
                met_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "unmet demand",
                unmet_stats["count"],
                unmet_stats["average"],
                unmet_stats["min"],
                unmet_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "initial available",
                available_stats["count"],
                available_stats["average"],
                available_stats["min"],
                available_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "withdrawn available",
                withdrawn_stats["count"],
                withdrawn_stats["average"],
                withdrawn_stats["min"],
                withdrawn_stats["max"],
            ),
            "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
            % (
                "untapped available",
                untapped_stats["count"],
                untapped_stats["average"],
                untapped_stats["min"],
                untapped_stats["max"],
            ),
        ),
    )

    return unmet, untapped, allocated, message


def allocate_demand_to_withdrawals(
    withdrawal_names,
    source_names,
    sector_names,
    demand_per_sector,
    renewable_withdrawal_per_sector,
    nonrenewable_withdrawal_per_sector,
    zones_per_sector,
    use_local_first,
):
    """
    allocate_demand_to_withdrawals:
                            function that allocates the supply to \
                            the demand per sector.

    input:
    =====
    withdrawal_names      : list with withdrawal names to be processed
                            (i.e., renewable and non-renewable)
    source_names          : list with source names to be processed
                            (i.e., surfacewater and groundwater)
    sector_names          : list with sector names to be processed
    demand_per_sector     : dictionary with the sector names as keys and as
                            values the corresponding sectoral demand as scalar
    renewable_withdrawal_per_sector :
                            dictionary with source names (string) as keys with
                            another dictionary with sector names (string) as keys
                            and PCRaster maps with actual water withdrawal from
                            renewable sources
    nonrenewable_withdrawal_per_sector :
                            dictionary with source names (string) as keys with
                            another dictionary with sector names (string) as keys
                            and PCRaster maps with actual water withdrawal from
                            non-renewable sources
    zones_per_sector      : dictionary with source names (string) as keys with
                            another dictionary with sector names (string) as keys
                            and PCRaster maps with zones over which the demand and
                            availability are totaled
    use_local_first        : boolean PCRaster map that indicates if the local
                            availability should be used first

    output:
    ======
    allocated_supply_per_sector:
                            supply, allocated to the different sectors, organ-
                            ized as a dictionary with the combined key of sup-
                            ply - source name as a composite key and a nested
                            dictionary as value with the sector name as key and
                            a scalar PCRaster field of the allocated supply per
                            cell as value;
    remaining_supply_per_source:
                            a dictionary organized similarly as the input
                            supply_per_source but now with any supply that is
                            not allocated to meet the demand;
    allocated_demand_per_sector:
                            demand, allocated to the different sectors, organ-
                            ized as a dictionary with the combined key of sup-
                            ply - source name as a composite key and a nested
                            dictionary as value with the sector name as key and
                            a scalar PCRaster field of the allocated demand per
                            cell as value; the supply is what is locally
                            withdrawn, the demand is what is locally allocated
                            to meet the demand and over the appropriate alloc-
                            ation zone should balance;
    met_demand_per_sector:  dictionary organzized as the input demand_per_sector
                            with the sector names as keys and as values the
                            demand per sector that is actually met;
    message_str:            a message string that provides an overview of the
                            allocation process, including the number of iter-
                            ations and the allocated supply/demand.

    The package requires all input to be compatible with spatial, scalar PCRaster
    fields and the values of supply and demand to have the same value, being volume
    over time per cell.
    """

    message_str = "allocation of demand to supply with water quality:"

    # allocated withdrawal and demand per sector (grouped per withdrawal and source)
    # and total met demand per sector
    allocated_withdrawal_per_sector = {}
    allocated_demand_per_sector = {}

    for withdrawal_name in withdrawal_names:
        for source_name in source_names:
            key = get_key([withdrawal_name, source_name])
            allocated_withdrawal_per_sector[key] = dict(
                (
                    sector_name,
                    pcr.ifthen(demand_per_sector[sector_name] >= 0, pcr.scalar(0)),
                )
                for sector_name in sector_names
            )

            allocated_demand_per_sector[key] = dict(
                (
                    sector_name,
                    pcr.ifthen(demand_per_sector[sector_name] >= 0, pcr.scalar(0)),
                )
                for sector_name in sector_names
            )

    met_demand_per_sector = dict(
        (sector_name, pcr.ifthen(demand_per_sector[sector_name] >= 0, pcr.scalar(0)))
        for sector_name in sector_names
    )

    # total remaining withdrawal and demand per source
    remaining_withdrawal_per_source_sector = {
        "renewable": deepcopy(renewable_withdrawal_per_sector),
        "nonrenewable": deepcopy(nonrenewable_withdrawal_per_sector),
    }

    # allocate the withdrawn water to cells: first locally (single cell ids as zones),
    # then with the actual allocation zones

    use_local_first = pcr.spatial(use_local_first)
    use_local_first_flag = (
        pcr.cellvalue(pcr.mapmaximum(pcr.scalar(use_local_first)), 1)[0] == 1
    )
    local_zones = dict(
        (
            source_name,
            dict(
                (
                    sector_name,
                    pcr.ifthen(
                        use_local_first, pcr.nominal(pcr.uniqueid(use_local_first))
                    ),
                )
                for sector_name in sector_names
            ),
        )
        for source_name in source_names
    )

    # local and zonal resources
    for option_str, (option_flag, option_mask, option_zones) in {
        "allocating local resources": (
            use_local_first_flag,
            use_local_first,
            local_zones,
        ),
        "allocating zonal resources": (
            True,
            pcr.spatial(pcr.boolean(1)),
            zones_per_sector,
        ),
    }.items():

        if option_flag:
            message_str = str.join("\n", (message_str, "", "* %s:" % option_str))

            for withdrawal_name in withdrawal_names:
                for source_name in source_names:

                    message_str = str.join(
                        "\n",
                        (
                            message_str,
                            "- allocating demand to %s %s withdrawal"
                            % (withdrawal_name, source_name),
                        ),
                    )

                    actual_allocated_withdrawal = pcr.scalar(0)

                    key = get_key([withdrawal_name, source_name])

                    # allocate the withdrawals to the demand per sector
                    for sector_name in sector_names:

                        # total zonal withdrawal per sector
                        total_zonal_withdrawal = get_zonal_total(
                            local_values=remaining_withdrawal_per_source_sector[
                                withdrawal_name
                            ][source_name][sector_name],
                            zones=option_zones[source_name][sector_name],
                        )

                        # allocated withdrawal per cell from the fractional total demand per sector and the
                        # total zonal withdrawal; may exceed the demand if withdrawal is plentiful
                        allocated_withdrawal = (
                            total_zonal_withdrawal
                            * get_zonal_fraction(
                                local_values=pcr.max(
                                    0,
                                    demand_per_sector[sector_name]
                                    - met_demand_per_sector[sector_name],
                                ),
                                zones=option_zones[source_name][sector_name],
                            )
                        )

                        # withdrawal applied locally for the current sector, supply and source; added to
                        # the allocated demand per sector below
                        allocated_withdrawal_demand = pcr.min(
                            allocated_withdrawal,
                            pcr.max(
                                0,
                                demand_per_sector[sector_name]
                                - met_demand_per_sector[sector_name],
                            ),
                        )

                        # required supply: the allocated supply scaled by the ratio of the zonal totals of
                        # allocated_withdrawal_demand and the total zonal supply; also updates the allocated
                        # supply per section and actual_allocated_withdrawal
                        required_allocated_withdrawal = (
                            remaining_withdrawal_per_source_sector[withdrawal_name][
                                source_name
                            ][sector_name]
                            * pcr.min(
                                1.0,
                                pcr_return_val_div_zero(
                                    get_zonal_total(
                                        local_values=allocated_withdrawal_demand,
                                        zones=option_zones[source_name][sector_name],
                                    ),
                                    total_zonal_withdrawal,
                                    very_small_number,
                                ),
                            )
                        )

                        # update the allocated demand and met demand per sector and the actual allocated withdrawal
                        allocated_demand_per_sector[key][
                            sector_name
                        ] += allocated_withdrawal_demand

                        met_demand_per_sector[
                            sector_name
                        ] += allocated_withdrawal_demand

                        allocated_withdrawal_per_sector[key][
                            sector_name
                        ] += required_allocated_withdrawal

                        actual_allocated_withdrawal += required_allocated_withdrawal

                        remaining_withdrawal_per_source_sector[withdrawal_name][
                            source_name
                        ][sector_name] = pcr.max(
                            0.0,
                            remaining_withdrawal_per_source_sector[withdrawal_name][
                                source_name
                            ][sector_name]
                            - required_allocated_withdrawal,
                        )

    # aggregate the results
    remaining_withdrawal_per_source = {}
    for withdrawal_name in withdrawal_names:
        remaining_withdrawal_per_source[withdrawal_name] = {}
        for source_name in source_names:
            remaining_withdrawal_per_source[withdrawal_name][source_name] = sum_list(
                list(
                    remaining_withdrawal_per_source_sector[withdrawal_name][
                        source_name
                    ].values()
                )
            )

    # add the overall statistics on withdrawal, remaining withdrawal, demand and met demand
    message_str = str.join(
        "\n",
        (
            message_str,
            "",
            "* overall allocation of the supply to meet demand over the provided zones:",
        ),
    )

    # demand and allocation per sector
    for sector_name in sector_names:

        demand_stats = pcr_get_statistics(demand_per_sector[sector_name])
        met_demand_stats = pcr_get_statistics(met_demand_per_sector[sector_name])

        message_str = str.join(
            "\n",
            (
                message_str,
                "",
                "=" * len("statistics - %s demand:" % sector_name),
                "statistics - %s demand:" % sector_name,
                "=" * len("statistics - %s demand:" % sector_name),
                "-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "demand",
                    demand_stats["count"],
                    demand_stats["average"],
                    demand_stats["min"],
                    demand_stats["max"],
                ),
                "-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "met demand",
                    met_demand_stats["count"],
                    met_demand_stats["average"],
                    met_demand_stats["min"],
                    met_demand_stats["max"],
                ),
            ),
        )

        for withdrawal_name in withdrawal_names:
            for source_name in source_names:
                key = get_key([withdrawal_name, source_name])
                key_str = get_key([sector_name, "from", key])

                withdrawal_stats = pcr_get_statistics(
                    allocated_withdrawal_per_sector[key][sector_name]
                )
                demand_stats = pcr_get_statistics(
                    allocated_demand_per_sector[key][sector_name]
                )

                message_str = str.join(
                    "\n",
                    (
                        message_str,
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "%s - %s" % ("supply", key_str),
                            withdrawal_stats["count"],
                            withdrawal_stats["average"],
                            withdrawal_stats["min"],
                            withdrawal_stats["max"],
                        ),
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "%s - %s" % ("demand", key_str),
                            demand_stats["count"],
                            demand_stats["average"],
                            demand_stats["min"],
                            demand_stats["max"],
                        ),
                    ),
                )

    # overall supply
    message_str = str.join(
        "\n",
        (
            message_str,
            "",
            "=" * len("statistics - supply"),
            "statistics - supply",
            "=" * len("statistics - supply"),
        ),
    )

    for withdrawal_name in withdrawal_names:
        for source_name in source_names:
            for sector_name in sector_names:
                withdrawal_per_source = {
                    "renewable": renewable_withdrawal_per_sector,
                    "nonrenewable": nonrenewable_withdrawal_per_sector,
                }
                total_withdrawal_stats = pcr_get_statistics(
                    withdrawal_per_source[withdrawal_name][source_name][sector_name]
                )
                remaining_withdrawal_stats = pcr_get_statistics(
                    remaining_withdrawal_per_source_sector[withdrawal_name][
                        source_name
                    ][sector_name]
                )

                message_str = str.join(
                    "\n",
                    (
                        message_str,
                        "",
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "total supply %s - %s - %s"
                            % (withdrawal_name, source_name, sector_name),
                            total_withdrawal_stats["count"],
                            total_withdrawal_stats["average"],
                            total_withdrawal_stats["min"],
                            total_withdrawal_stats["max"],
                        ),
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "remaining supply %s - %s - %s"
                            % (withdrawal_name, source_name, sector_name),
                            remaining_withdrawal_stats["count"],
                            remaining_withdrawal_stats["average"],
                            remaining_withdrawal_stats["min"],
                            remaining_withdrawal_stats["max"],
                        ),
                    ),
                )

    message_str = str.join("\n", (message_str, ""))

    return (
        allocated_withdrawal_per_sector,
        remaining_withdrawal_per_source,
        allocated_demand_per_sector,
        met_demand_per_sector,
        message_str,
    )
