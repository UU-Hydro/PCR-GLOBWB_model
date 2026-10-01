import pcraster as pcr

from qualloc.basic_functions import (
    pcr_get_statistics,
    pcr_return_val_div_zero,
    sum_list,
)

# small number to avoid division by zero in PCRaster
very_small_number = 1.0e-12


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


# functions based on the allocation in PCR-GLOBWB, using values aggregated over
# zones with the PCRaster area functions


def get_zonal_total(local_values, zones):
    """
get_zonal_fraction: function that computes the fractional value per cell over \
the total of the provided zones.

    Input:
    ======
    local values:            local cell values as a scalar PCRaster field;
    zones:                   zones over which the totals are computed as
                             a nominal PCRaster field.

    Output:
    =======
    totals:                  totals over the zones per cell as a scalar
                             PCRaster field.

"""

    return pcr.areatotal(local_values, zones)


def get_zonal_fraction(local_values, zones):
    """
get_zonal_fraction: function that computes the fractional value per cell over \
the total of the provided zones.

    Input:
    ======
    local values:            local cell values as a scalar PCRaster field;
    zones:                   zones over which the fractional values for the
                             cells are computed as a nominal PCRaster field.

    Output:
    =======
    fractional_values:       fractional values, summing to unity over the ap-
                             propriate zone, as a scalar PCRaster field.

"""

    totals = get_zonal_total(local_values, zones)

    fractional_values = pcr_return_val_div_zero(local_values, totals, very_small_number)

    return fractional_values


def group_sources_by_zones(
    zones: dict[str, pcr.Field] | None,
    sources: list[str],
) -> dict[str, list[str]]:
    """
    Groups the sources that share the same zone map (the same object); without
    zones, every cell is its own zone for all sources, so they form one group.

    Input:
    ======
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source;
    sources (list[str]):            names of the sources.

    Output:
    =======
    groups (dict[str, list[str]]):  sources per group, in the order of sources; the
                                    key joins the source names with underscores.
    """

    # identical maps are recognized by object, not by content: pcr_same_map can be
    # used beforehand to make identical zone maps the same object
    groups = {}
    for s in sources:
        key = None if zones is None else id(zones[s])
        groups.setdefault(key, []).append(s)

    return {get_key(members): members for members in groups.values()}


def combine_sources(
    availability: dict[str, pcr.Field],
    zones: dict[str, pcr.Field] | None,
    groups: dict[str, list[str]],
) -> tuple[dict[str, pcr.Field], dict[str, pcr.Field] | None]:
    """
    Combines the sources of each group into one source: their supply is summed and
    their shared zone map is kept.

    Input:
    ======
    availability (dict[str, pcr.Field]):
                                    scalar supply per cell per source;
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source;
    groups (dict[str, list[str]]):  sources per group.

    Output:
    =======
    group_availability (dict[str, pcr.Field]):
                                    summed supply per group;
    group_zones (dict[str, pcr.Field] | None):
                                    zone map per group; None if zones is None.
    """

    group_availability = {
        g: sum_list([availability[s] for s in members]) for g, members in groups.items()
    }
    if zones is None:
        return group_availability, None

    group_zones = {g: zones[members[0]] for g, members in groups.items()}
    return group_availability, group_zones


def split_sources(
    availability: dict[str, pcr.Field],
    zones: dict[str, pcr.Field] | None,
    groups: dict[str, list[str]],
    group_untapped: dict[str, pcr.Field],
    group_allocated: dict[str, pcr.Field],
) -> tuple[dict[str, pcr.Field], dict[str, pcr.Field]]:
    """
    Splits the untapped supply and allocated demand of each group back over its
    sources. All sources in a group lose the same fraction of their supply in every
    iteration, so each keeps the group's untapped fraction and gets the group's
    allocation in proportion to its share of the zonal supply.

    Input:
    ======
    availability (dict[str, pcr.Field]):
                                    scalar supply per cell per source;
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source;
    groups (dict[str, list[str]]):  sources per group;
    group_untapped (dict[str, pcr.Field]):
                                    untapped supply per group;
    group_allocated (dict[str, pcr.Field]):
                                    demand allocated per group.

    Output:
    =======
    untapped (dict[str, pcr.Field]):
                                    untapped supply per source;
    allocated (dict[str, pcr.Field]):
                                    demand allocated per source.
    """

    untapped = {}
    allocated = {}
    for g, members in groups.items():

        # a single source is its own group
        if len(members) == 1:
            untapped[members[0]] = group_untapped[g]
            allocated[members[0]] = group_allocated[g]
            continue

        # untapped supply: the group's untapped fraction of each source's supply
        group_availability = sum_list([availability[s] for s in members])
        untapped_fraction = pcr_return_val_div_zero(
            group_untapped[g], group_availability, very_small_number
        )

        # allocated demand: in proportion to each source's share of the zonal supply;
        # without zones, every cell is its own zone
        if zones is not None:
            zonal_availability = {
                s: get_zonal_total(availability[s], zones[s]) for s in members
            }
        else:
            zonal_availability = {s: availability[s] for s in members}
        zonal_availability_total = sum_list(list(zonal_availability.values()))

        for s in members:
            untapped[s] = availability[s] * untapped_fraction
            allocated[s] = group_allocated[g] * pcr_return_val_div_zero(
                zonal_availability[s], zonal_availability_total, very_small_number
            )

    # in the original order of the sources
    untapped = {s: untapped[s] for s in availability.keys()}
    allocated = {s: allocated[s] for s in availability.keys()}

    return untapped, allocated


def obtain_allocation_ratio(
    demand: pcr.Field,
    availability: dict[str, pcr.Field],
    source_names: list[str],
    zones: dict[str, pcr.Field] | None = None,
    zonal_availability: dict[str, pcr.Field] | None = None,
) -> tuple[dict[str, pcr.Field], dict[str, pcr.Field], dict[str, pcr.Field]]:
    """
    Splits the demand over the sources in proportion to their potential allocation:
    the cell's share of the zone's demand times the zone's availability, per source.

    Input:
    ======
    demand (pcr.Field):             scalar demand per cell;
    availability (dict[str, pcr.Field]):
                                    scalar availability per cell per source;
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source; if None,
                                    every cell is its own zone;
    zonal_availability (dict[str, pcr.Field] | None):
                                    availability per zone per source; if None, it
                                    is computed from availability and zones.

    Output:
    =======
    zonal_availability (dict[str, pcr.Field]):
                                    availability per zone per source;
    potential_allocation (dict[str, pcr.Field]):
                                    the cell's share of the zonal demand times the
                                    zonal availability, per source;
    source_share (dict[str, pcr.Field]):
                                    share of the cell's demand per source; sums to
                                    one over the sources wherever there is a
                                    potential allocation.
    """

    # zonal availability of the supply not yet withdrawn; computed if not provided
    if zonal_availability is None:
        if zones is not None:
            zonal_availability = {
                s: get_zonal_total(availability[s], zones[s]) for s in source_names
            }
        else:
            zonal_availability = {s: availability[s] for s in source_names}

    # zonal unmet demand per source
    if zones is not None:
        zonal_demand = {
            s: get_zonal_total(
                demand,
                zones[s],
            )
            for s in source_names
        }
    else:
        zonal_demand = {s: demand for s in source_names}

    # Demand share:
    # The local demand as a proportion of the zonal demand
    demand_share = {
        s: pcr_return_val_div_zero(
            demand,
            zonal_demand[s],
            very_small_number,
        )
        for s in source_names
    }

    # Potential allocation:
    # The demand share of the zonal availability
    potential_allocation = {
        s: demand_share[s] * zonal_availability[s] for s in source_names
    }

    # Source share:
    # The potential allocation of a source as a proportion of the total potential
    # allocation over all sources
    potential_allocation_total = sum_list(list(potential_allocation.values()))
    source_share = {
        s: pcr_return_val_div_zero(
            potential_allocation[s],
            potential_allocation_total,
            very_small_number,
        )
        for s in source_names
    }

    return zonal_availability, potential_allocation, source_share


def allocate_demand_to_availability(
    demand: pcr.Field,
    availability: dict[str, pcr.Field],
    source_names: list[str],
    zones: dict[str, pcr.Field] | None,
    max_iterations: int = 100,
    relative_tolerance: float = 1e-6,
    summarize: bool = False,
    verbose: bool = False,
) -> tuple[pcr.Field, dict[str, pcr.Field], dict[str, pcr.Field], str]:
    """
    Allocates the demand to the available supply of one or more sources.

    Each source pools its supply over its zones: a cell claims a share of the
    zone's untapped supply equal to its share of the zone's unmet demand, split
    over the sources and limited to its unmet demand. What a zone allocates is
    withdrawn from its cells in proportion to their untapped supply. Iterates
    until the demand is met, the supply is exhausted or no progress is made.

    Sources that share the same zone map (the same object) are allocated as one
    source with their summed supply and split back afterwards, which gives the same
    result with fewer zonal totals.

    Input:
    ======
    demand (pcr.Field):             scalar demand per cell; negatives count as 0;
    availability (dict[str, pcr.Field]):
                                    scalar supply per cell per source; negatives
                                    count as 0;
    zones (dict[str, pcr.Field] | None):
                                    nominal allocation zones per source; if None,
                                    every cell is its own zone;
    max_iterations (int):           maximum number of iterations;
    relative_tolerance (float):     fraction of the initial demand and supply below
                                    which they count as zero;
    summarize (bool):               add statistics to the message;
    verbose (bool):                 print the progress of every iteration.

    Output:
    =======
    unmet (pcr.Field):              unmet demand; met = max(demand, 0) - unmet;
    untapped (dict[str, pcr.Field]):
                                    untapped supply per source;
                                    withdrawn = max(availability, 0) - untapped;
    allocated (dict[str, pcr.Field]):
                                    demand allocated per source, i.e. where the
                                    water is delivered, not where it is withdrawn;
    message (str):                  log of the allocation, with statistics if
                                    summarize.
    """

    demand = pcr.max(demand, 0)
    availability = {s: pcr.max(availability[s], 0) for s in source_names}

    # allocate the sources as they are if none share a zone map, or if there is no
    # demand (splitting the groups back would only cost zonal totals)
    groups = group_sources_by_zones(zones, source_names)
    has_demand = pcr.cellvalue(pcr.maptotal(pcr.scalar(demand > 0)), 1)[0] > 0
    if len(groups) == len(availability) or not has_demand:
        return _allocate_demand_to_availability(
            demand=demand,
            availability=availability,
            source_names=source_names,
            zones=zones,
            max_iterations=max_iterations,
            relative_tolerance=relative_tolerance,
            summarize=summarize,
            verbose=verbose,
        )

    # otherwise, allocate the combined sources and split the result back per source
    group_availability, group_zones = combine_sources(availability, zones, groups)

    unmet, group_untapped, group_allocated, message = _allocate_demand_to_availability(
        demand=demand,
        availability=group_availability,
        source_names=list(groups.keys()),
        zones=group_zones,
        max_iterations=max_iterations,
        relative_tolerance=relative_tolerance,
        summarize=summarize,
        verbose=verbose,
    )

    untapped, allocated = split_sources(
        availability, zones, groups, group_untapped, group_allocated
    )

    return unmet, untapped, allocated, message


def _allocate_demand_to_availability(
    demand: pcr.Field,
    availability: dict[str, pcr.Field],
    source_names: list[str],
    zones: dict[str, pcr.Field] | None,
    max_iterations: int = 100,
    relative_tolerance: float = 1e-6,
    summarize: bool = False,
    verbose: bool = False,
) -> tuple[pcr.Field, dict[str, pcr.Field], dict[str, pcr.Field], str]:
    """
    Allocates the demand to the available supply of each source as given, without
    combining sources that share a zone map; see allocate_demand_to_availability
    for the method, input and output.
    """

    message = "allocation of demand to availability"

    demand = pcr.max(demand, 0)
    availability = {s: pcr.max(availability[s], 0) for s in source_names}
    demand_initial = demand
    availability_initial = dict(availability)

    unmet = demand
    untapped = dict(availability)
    allocated = {
        s: pcr.ifthen(pcr.defined(demand), pcr.scalar(0)) for s in source_names
    }

    # nothing to allocate if there is no unmet demand
    # unmet demand below these tolerances count as zero
    unmet_tolerance = relative_tolerance * unmet
    mask = unmet > unmet_tolerance
    n_unmet = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
    if n_unmet == 0:
        message = "All demand is initially met."
        return unmet, untapped, allocated, message

    # zonal untapped supply per source; it is computed once and then reduced by the
    # withdrawn fraction, as every cell in a zone loses the same fraction; without
    # zones, every cell is its own zone
    if zones is not None:
        zonal_untapped = {
            s: get_zonal_total(
                untapped[s],
                zones[s],
            )
            for s in source_names
        }
    else:
        zonal_untapped = {s: untapped[s] for s in source_names}

    # nothing to allocate if there is no untapped supply
    # untapped supply below these tolerances count as zero
    zonal_untapped_tolerance = relative_tolerance * sum_list(
        list(zonal_untapped.values())
    )
    mask = mask & (sum_list(list(zonal_untapped.values())) > zonal_untapped_tolerance)
    n_availability = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
    if n_availability == 0:
        message = "No available supply to meet the unmet demand."
        return unmet, untapped, allocated, message

    n_unmet_start = n_unmet
    iteration = 1
    while iteration <= max_iterations:

        _, potential_allocation, source_share = obtain_allocation_ratio(
            demand=unmet,
            availability=untapped,
            source_names=source_names,
            zones=zones,
            zonal_availability=zonal_untapped,
        )

        # Allocation:
        # Minimum of the potential allocation and the source share of the unmet demand
        allocation = {
            s: pcr.min(
                potential_allocation[s],
                source_share[s] * unmet,
            )
            for s in source_names
        }

        # zonal allocation per source
        if zones is not None:
            zonal_allocation = {
                s: get_zonal_total(
                    allocation[s],
                    zones[s],
                )
                for s in source_names
            }
        else:
            zonal_allocation = {s: allocation[s] for s in source_names}

        # Withdrawal fraction:
        # The zonal allocation as a proportion of the zonal untapped supply; every cell
        # in the zone loses this fraction of its untapped supply
        withdrawal_fraction = {
            s: pcr_return_val_div_zero(
                zonal_allocation[s],
                zonal_untapped[s],
                very_small_number,
            )
            for s in source_names
        }
        withdrawal_fraction = {
            s: pcr.min(withdrawal_fraction[s], 1) for s in source_names
        }

        # Update the unmet demand, the (zonal) untapped supply and the allocated demand
        unmet = pcr.max(unmet - sum_list(list(allocation.values())), 0)
        untapped = {
            s: pcr.max(untapped[s] * (1 - withdrawal_fraction[s]), 0)
            for s in source_names
        }
        zonal_untapped = {
            s: pcr.max(zonal_untapped[s] * (1 - withdrawal_fraction[s]), 0)
            for s in source_names
        }
        allocated = {s: allocated[s] + allocation[s] for s in source_names}

        # Exit conditions: the number of cells with unmet demand, and of those that
        # also have untapped supply left
        mask = unmet > unmet_tolerance
        n_unmet_current = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
        mask = mask & (
            sum_list(list(zonal_untapped.values())) > zonal_untapped_tolerance
        )
        n_availability_current = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]

        # Reporting
        if verbose:
            message_iteration = "allocation iteration %d\n" % iteration
            message_iteration += "cells with unmet demand: %6d / %6d in total\n" % (
                n_unmet_current,
                n_unmet_start,
            )
            print(message_iteration)

        # Stop if there is no more unmet demand
        if n_unmet_current == 0:
            break
        # Stop if no cell with unmet demand has untapped supply left
        if not n_availability_current:
            break
        # Stop if the number of cells with unmet demand no longer decreases
        if n_unmet_current >= n_unmet:
            break

        n_unmet = n_unmet_current
        iteration = iteration + 1

    if summarize:
        met = demand_initial - unmet
        withdrawn = {s: availability_initial[s] - untapped[s] for s in source_names}

        demand_stats = pcr_get_statistics(demand_initial)
        met_stats = pcr_get_statistics(met)
        unmet_stats = pcr_get_statistics(unmet)
        availability_stats = pcr_get_statistics(
            sum_list(list(availability_initial.values()))
        )
        withdrawn_stats = pcr_get_statistics(sum_list(list(withdrawn.values())))
        untapped_stats = pcr_get_statistics(sum_list(list(untapped.values())))

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
                    "initial availability",
                    availability_stats["count"],
                    availability_stats["average"],
                    availability_stats["min"],
                    availability_stats["max"],
                ),
                "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "withdrawn availability",
                    withdrawn_stats["count"],
                    withdrawn_stats["average"],
                    withdrawn_stats["min"],
                    withdrawn_stats["max"],
                ),
                "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "untapped availability",
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
    availability: dict[str, pcr.Field],
    source_names: list[str],
    zones: dict[str, pcr.Field],
    use_local_first: pcr.Field,
    use_allocation_zone: bool = True,
    reallocate_surplus: bool = True,
    summarize: bool = False,
) -> tuple[pcr.Field, dict[str, pcr.Field], dict[str, pcr.Field], str]:
    """
    Allocates the demand to the available supply of one or more sources in up to
    three steps with allocate_demand_to_availability:

    1. local (use_local_first): cells first use their own supply;
    2. zonal (use_allocation_zone): the unmet demand is allocated over the zones;
    3. surplus (reallocate_surplus, sources with two or more different zone maps):
       allocations that other sources can cover from their untapped supply in the
       same cell are moved to them; the freed supply returns to where it was
       withdrawn and is allocated again over the zones.

    Input:
    ======
    demand (pcr.Field):             scalar demand per cell; negatives count as 0;
    availability (dict[str, pcr.Field]):
                                    scalar supply per cell per source; negatives
                                    count as 0;
    zones (dict[str, pcr.Field]):   nominal allocation zones per source;
    use_local_first (pcr.Field):    boolean; cells that use their own supply first;
    use_allocation_zone (bool):     apply step 2;
    reallocate_surplus (bool):      apply step 3;
    summarize (bool):               add statistics to the message.

    Output:
    =======
    As allocate_demand_to_availability, combined over all steps.
    """

    demand = pcr.max(demand, 0)
    availability = {s: pcr.max(availability[s], 0) for s in source_names}
    demand_initial = demand
    availability_initial = dict(availability)

    unmet = demand
    untapped = dict(availability)
    allocated = {s: pcr.scalar(0) for s in source_names}

    message = "allocation of demand to availability with options:"

    # local allocation (if used): every cell is its own zone; cells outside
    # use_local_first get no demand or supply in this step
    use_local = (
        pcr.cellvalue(pcr.mapmaximum(pcr.scalar(pcr.spatial(use_local_first))), 1)[0]
        == 1
    )
    if use_local:
        message = str.join("\n", (message, "", "* allocating local resources first:"))

        unmet_local = pcr.ifthenelse(use_local_first, unmet, 0)
        untapped_local = {
            s: pcr.ifthenelse(use_local_first, untapped[s], 0) for s in source_names
        }

        (
            opt_unmet,
            opt_untapped,
            opt_allocated,
            opt_message,
        ) = allocate_demand_to_availability(
            demand=unmet_local,
            availability=untapped_local,
            source_names=source_names,
            zones=None,
            summarize=summarize,
        )

        # update the unmet demand, untapped supply and allocated demand; cells outside
        # use_local_first keep their values
        unmet = pcr.ifthenelse(use_local_first, opt_unmet, unmet)
        untapped = {
            s: pcr.ifthenelse(use_local_first, opt_untapped[s], untapped[s])
            for s in source_names
        }
        allocated = {s: allocated[s] + opt_allocated[s] for s in source_names}
        message = str.join("\n", (message, opt_message))

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
            opt_message,
        ) = allocate_demand_to_availability(
            demand=unmet,
            availability=untapped,
            zones=zones,
            source_names=source_names,
            summarize=summarize,
        )

        # update the unmet demand, untapped supply and allocated demand
        unmet = opt_unmet
        untapped = {s: opt_untapped[s] for s in source_names}
        allocated = {s: allocated[s] + opt_allocated[s] for s in source_names}
        message = str.join("\n", (message, opt_message))

    # reallocate any surplus (if used); sources that all share one zone map have
    # nothing to free: after the zonal step, every zone has either no unmet demand
    # or no untapped supply left
    n_zone_groups = len(group_sources_by_zones(zones, source_names))
    if reallocate_surplus and n_zone_groups > 1:
        message = str.join(
            "\n",
            (
                message,
                "",
                "* allocating any surplus from available supply to satisfy outstanding demand:",
            ),
        )

        # free up supply per source:
        # 0: initialize the deficit as the unmet demand; it is reduced by the freed supply
        # then, per source:
        # 1: determine the zonal deficit over the zones of the source
        # 2: determine the surplus, i.e. the untapped supply of the other sources in the
        #    same cell, and the share of each other source in it
        # 3: limit the surplus to the demand allocated to this source and determine the
        #    fraction of the zonal surplus needed to cover the zonal deficit
        # 4: move allocated demand from this source to the other sources, which take it
        #    from their untapped supply in the same cell
        # 5: return the freed supply to the cells it was withdrawn from
        # finally, allocate the unmet demand again over the zones, now with the freed
        # supply

        deficit = unmet

        for source in source_names:
            other_sources = [s for s in source_names if s != source]

            s_str = str.join("", other_sources)
            s_str = str.join(
                "", ("- processing %s with any surplus for " % source, s_str)
            )
            message = str.join("\n", (message, s_str))

            zonal_deficit = get_zonal_total(
                deficit,
                zones[source],
            )

            # Source share:
            # The untapped supply of each other source as a proportion of the surplus
            surplus = sum_list([untapped[s] for s in other_sources])
            source_share = {
                s: pcr_return_val_div_zero(untapped[s], surplus, very_small_number)
                for s in other_sources
            }

            # limit the surplus to what can actually be freed, before getting the zonal surplus
            surplus = pcr.min(allocated[source], surplus)
            zonal_surplus = get_zonal_total(
                surplus,
                zones[source],
            )

            # fraction of the zonal surplus to free: enough to cover the zonal deficit,
            # at most all of it; nothing can be freed without surplus
            allocation_ratio = pcr.min(
                pcr_return_val_div_zero(
                    zonal_deficit,
                    zonal_surplus,
                    very_small_number,
                ),
                1,
            )

            # free the supply per other source; total_supply_freed is the zonal total
            # and withdrawn_source the withdrawal of this source before freeing
            total_supply_freed = pcr.scalar(0)
            withdrawn_source = availability_initial[source] - untapped[source]
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
                allocated[source] = pcr.max(0, allocated[source] - supply_freed)
                untapped[other_source] = pcr.max(
                    0, untapped[other_source] - supply_freed
                )
                allocated[other_source] = allocated[other_source] + supply_freed

                total_supply_freed = total_supply_freed + get_zonal_total(
                    supply_freed,
                    zones[source],
                )

            # return the freed supply to the cells it was withdrawn from, in proportion
            # to their withdrawal, rather than to the cells where the demand was met
            zonal_withdrawn_source = get_zonal_total(withdrawn_source, zones[source])
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
            opt_message,
        ) = allocate_demand_to_availability(
            demand=unmet,
            availability=untapped,
            source_names=source_names,
            zones=zones,
            summarize=summarize,
        )

        # update the unmet demand, untapped supply and allocated demand
        unmet = opt_unmet
        untapped = {s: opt_untapped[s] for s in source_names}
        allocated = {s: allocated[s] + opt_allocated[s] for s in source_names}
        message = str.join("\n", (message, opt_message))

    if summarize:

        met = demand_initial - unmet
        withdrawn = {s: availability_initial[s] - untapped[s] for s in source_names}

        message = str.join(
            "\n",
            (
                message,
                "",
                "* overall allocation of the available supply over the provided zones:",
            ),
        )

        demand_stats = pcr_get_statistics(demand_initial)
        met_stats = pcr_get_statistics(met)
        unmet_stats = pcr_get_statistics(unmet)
        availability_stats = pcr_get_statistics(
            sum_list(list(availability_initial.values()))
        )
        withdrawn_stats = pcr_get_statistics(sum_list(list(withdrawn.values())))
        untapped_stats = pcr_get_statistics(sum_list(list(untapped.values())))

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
                    "initial availability",
                    availability_stats["count"],
                    availability_stats["average"],
                    availability_stats["min"],
                    availability_stats["max"],
                ),
                "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "withdrawn availability",
                    withdrawn_stats["count"],
                    withdrawn_stats["average"],
                    withdrawn_stats["min"],
                    withdrawn_stats["max"],
                ),
                "%20s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                % (
                    "untapped availability",
                    untapped_stats["count"],
                    untapped_stats["average"],
                    untapped_stats["min"],
                    untapped_stats["max"],
                ),
            ),
        )

    return unmet, untapped, allocated, message


def allocate_withdrawals_to_demand(
    demand: dict[str, pcr.Field],
    withdrawal: dict[str, dict[str, pcr.Field]],
    source_names: list[str],
    sector_names: list[str],
    zones: dict[str, dict[str, pcr.Field]] | None,
    summarize: bool = False,
) -> tuple[
    dict[str, pcr.Field],
    dict[str, dict[str, pcr.Field]],
    dict[str, dict[str, pcr.Field]],
    str,
]:
    """
    Allocates the withdrawn water to the demand per sector.

    Each source's withdrawal for a sector is allocated to the unmet demand of that
    sector in a single pass, one source at a time in the order of withdrawal, which
    sets the priority: a cell claims a share of the zone's unused withdrawal equal
    to its share of the zone's unmet demand, limited to its unmet demand. What a
    zone allocates is taken from its cells in proportion to their unused withdrawal.

    Input:
    ======
    demand (dict[str, pcr.Field]):  scalar demand per sector; negatives count as 0;
    withdrawal (dict[str, dict[str, pcr.Field]]):
                                    scalar withdrawal per source per sector;
                                    negatives count as 0;
    zones (dict[str, dict[str, pcr.Field]] | None):
                                    nominal allocation zones per source per sector;
                                    if None, every cell is its own zone;
    summarize (bool):               add statistics to the message.

    Output:
    =======
    unmet (dict[str, pcr.Field]):   unmet demand per sector;
                                    met = max(demand, 0) - unmet;
    unused (dict[str, dict[str, pcr.Field]]):
                                    unused withdrawal per source per sector;
                                    used = max(withdrawal, 0) - unused;
    allocated (dict[str, dict[str, pcr.Field]]):
                                    demand allocated per source per sector;
    message (str):                  log of the allocation, with statistics if
                                    summarize.
    """

    demand = {se: pcr.max(demand[se], 0) for se in sector_names}
    withdrawal = {
        so: {se: pcr.max(withdrawal[so][se], 0) for se in sector_names}
        for so in source_names
    }
    demand_initial = dict(demand)
    withdrawal_initial = {so: dict(withdrawal[so]) for so in source_names}

    unmet = dict(demand)
    unused = {so: dict(withdrawal[so]) for so in source_names}
    allocated = {
        so: {
            se: pcr.ifthen(pcr.defined(demand[se]), pcr.scalar(0))
            for se in sector_names
        }
        for so in source_names
    }

    # one pass per source and sector: with a single source, the allocation is exact
    # after one pass; the order of the sources sets the priority
    for source in source_names:
        for sector in sector_names:

            # skip sources without withdrawal for this sector, e.g. non-renewable
            # surface water
            if pcr.cellvalue(pcr.maptotal(unused[source][sector]), 1)[0] == 0:
                continue

            # zonal totals; without zones, every cell is its own zone
            if zones is not None:
                zonal_unused = get_zonal_total(
                    unused[source][sector], zones[source][sector]
                )
                zonal_unmet = get_zonal_total(unmet[sector], zones[source][sector])
            else:
                zonal_unused = unused[source][sector]
                zonal_unmet = unmet[sector]

            # Demand share:
            # The local demand as a proportion of the zonal demand
            demand_share = pcr_return_val_div_zero(
                unmet[sector], zonal_unmet, very_small_number
            )

            # Potential allocation:
            # The demand share of the zonal withdrawal
            potential_allocation = demand_share * zonal_unused

            # Allocation:
            # Minimum of the potential allocation and the unmet demand
            allocation = pcr.min(potential_allocation, unmet[sector])

            if zones is not None:
                zonal_allocation = get_zonal_total(allocation, zones[source][sector])
            else:
                zonal_allocation = allocation

            # Withdrawal fraction:
            # The zonal allocation as a proportion of the zonal unused withdrawal; every
            # cell in the zone loses this fraction of its unused withdrawal
            withdrawal_fraction = pcr_return_val_div_zero(
                zonal_allocation, zonal_unused, very_small_number
            )
            withdrawal_fraction = pcr.min(withdrawal_fraction, 1)

            # update the unmet demand, unused withdrawal and allocated demand
            unmet[sector] = pcr.max(unmet[sector] - allocation, 0)
            unused[source][sector] = pcr.max(
                unused[source][sector] * (1 - withdrawal_fraction), 0
            )
            allocated[source][sector] = allocated[source][sector] + allocation

    message = "allocation of withdrawals to demand"

    if summarize:
        met = {se: demand_initial[se] - unmet[se] for se in sector_names}
        used = {
            so: {se: withdrawal_initial[so][se] - unused[so][se] for se in sector_names}
            for so in source_names
        }

        for sector in sector_names:
            demand_stats = pcr_get_statistics(demand_initial[sector])
            met_stats = pcr_get_statistics(met[sector])
            unmet_stats = pcr_get_statistics(unmet[sector])

            message = str.join(
                "\n",
                (
                    message,
                    "",
                    "=" * len("statistics - %s demand:" % sector),
                    "statistics - %s demand:" % sector,
                    "=" * len("statistics - %s demand:" % sector),
                    "-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                    % (
                        "initial demand",
                        demand_stats["count"],
                        demand_stats["average"],
                        demand_stats["min"],
                        demand_stats["max"],
                    ),
                    "-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                    % (
                        "met demand",
                        met_stats["count"],
                        met_stats["average"],
                        met_stats["min"],
                        met_stats["max"],
                    ),
                    "-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                    % (
                        "unmet demand",
                        unmet_stats["count"],
                        unmet_stats["average"],
                        unmet_stats["min"],
                        unmet_stats["max"],
                    ),
                ),
            )

            for source in source_names:
                withdrawal_stats = pcr_get_statistics(
                    withdrawal_initial[source][sector]
                )
                used_stats = pcr_get_statistics(used[source][sector])
                unused_stats = pcr_get_statistics(unused[source][sector])

                message = str.join(
                    "\n",
                    (
                        message,
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "%s - %s" % ("initial withdrawal", source),
                            withdrawal_stats["count"],
                            withdrawal_stats["average"],
                            withdrawal_stats["min"],
                            withdrawal_stats["max"],
                        ),
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "%s - %s" % ("used withdrawal", source),
                            used_stats["count"],
                            used_stats["average"],
                            used_stats["min"],
                            used_stats["max"],
                        ),
                        "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                        % (
                            "%s - %s" % ("unused withdrawal", source),
                            unused_stats["count"],
                            unused_stats["average"],
                            unused_stats["min"],
                            unused_stats["max"],
                        ),
                    ),
                )

    return unmet, unused, allocated, message


def allocate_withdrawals_to_demand_with_options(
    demand: dict[str, pcr.Field],
    renewable: dict[str, dict[str, pcr.Field]],
    nonrenewable: dict[str, dict[str, pcr.Field]],
    withdrawal_names: list[str],
    source_names: list[str],
    sector_names: list[str],
    zones: dict[str, dict[str, pcr.Field]],
    use_local_first: pcr.Field,
    summarize: bool = False,
) -> tuple[
    dict[str, pcr.Field],
    dict[str, dict[str, dict[str, pcr.Field]]],
    dict[str, dict[str, dict[str, pcr.Field]]],
    str,
]:
    """
    Allocates the renewable and non-renewable withdrawals to the demand per sector
    in up to two steps with allocate_withdrawals_to_demand, each for the renewable
    withdrawals first and then for the non-renewable ones:

    1. local (use_local_first): cells first use their own withdrawal;
    2. zonal: the unmet demand is allocated over the zones.

    Input:
    ======
    demand (dict[str, pcr.Field]):  scalar demand per sector; negatives count as 0;
    renewable (dict[str, dict[str, pcr.Field]]):
                                    renewable withdrawal per source per sector;
                                    negatives count as 0;
    nonrenewable (dict[str, dict[str, pcr.Field]]):
                                    non-renewable withdrawal per source per sector;
                                    negatives count as 0;
    zones (dict[str, dict[str, pcr.Field]]):
                                    nominal allocation zones per source per sector;
    use_local_first (pcr.Field):    boolean; cells that use their own withdrawal
                                    first;
    summarize (bool):               add statistics to the message.

    Output:
    =======
    unmet (dict[str, pcr.Field]):   unmet demand per sector;
                                    met = max(demand, 0) - unmet;
    unused (dict[str, dict[str, dict[str, pcr.Field]]]):
                                    unused withdrawal per withdrawal type
                                    ("renewable", "nonrenewable"), source and sector;
    allocated (dict[str, dict[str, dict[str, pcr.Field]]]):
                                    demand allocated per withdrawal type, source
                                    and sector;
    message (str):                  log of the steps, with statistics if summarize.
    """

    demand = {se: pcr.max(demand[se], 0) for se in sector_names}
    renewable = {
        so: {se: pcr.max(renewable[so][se], 0) for se in sector_names}
        for so in source_names
    }
    nonrenewable = {
        so: {se: pcr.max(nonrenewable[so][se], 0) for se in sector_names}
        for so in source_names
    }
    withdrawal_initial = {
        "renewable": {so: dict(renewable[so]) for so in source_names},
        "nonrenewable": {so: dict(nonrenewable[so]) for so in source_names},
    }

    unmet = dict(demand)
    unused = {
        "renewable": {so: dict(renewable[so]) for so in source_names},
        "nonrenewable": {so: dict(nonrenewable[so]) for so in source_names},
    }
    allocated = {
        "renewable": {
            so: {se: pcr.scalar(0) for se in sector_names} for so in source_names
        },
        "nonrenewable": {
            so: {se: pcr.scalar(0) for se in sector_names} for so in source_names
        },
    }

    message = "allocation of demand to supply with water quality:"

    # local allocation (if used): every cell is its own zone; cells outside
    # use_local_first get no demand or withdrawal in this step
    use_local = (
        pcr.cellvalue(pcr.mapmaximum(pcr.scalar(pcr.spatial(use_local_first))), 1)[0]
        == 1
    )
    if use_local:
        message = str.join(
            "\n",
            (
                message,
                "",
                "allocating local withdrawals",
            ),
        )

        # renewable before non-renewable withdrawals
        for kind in withdrawal_names:

            message = str.join(
                "\n",
                (message, "- allocating demand to %s withdrawal" % kind),
            )

            unmet_local = {
                se: pcr.ifthenelse(use_local_first, unmet[se], 0) for se in sector_names
            }
            unused_local = {
                so: {
                    se: pcr.ifthenelse(use_local_first, unused[kind][so][se], 0)
                    for se in sector_names
                }
                for so in source_names
            }

            (
                opt_unmet,
                opt_unused,
                opt_allocated,
                opt_message,
            ) = allocate_withdrawals_to_demand(
                demand=unmet_local,
                withdrawal=unused_local,
                source_names=source_names,
                sector_names=sector_names,
                zones=None,
                summarize=summarize,
            )

            # update the unmet demand, unused withdrawal and allocated demand; cells
            # outside use_local_first keep their values
            unmet = {
                se: pcr.ifthenelse(use_local_first, opt_unmet[se], unmet[se])
                for se in sector_names
            }
            unused[kind] = {
                so: {
                    se: pcr.ifthenelse(
                        use_local_first, opt_unused[so][se], unused[kind][so][se]
                    )
                    for se in sector_names
                }
                for so in source_names
            }
            allocated[kind] = {
                so: {
                    se: allocated[kind][so][se] + opt_allocated[so][se]
                    for se in sector_names
                }
                for so in source_names
            }
            message = str.join("\n", (message, opt_message))

    # zonal allocation, renewable before non-renewable withdrawals
    message = str.join(
        "\n",
        (
            message,
            "",
            "allocating zonal withdrawals",
        ),
    )

    for kind in withdrawal_names:

        message = str.join(
            "\n",
            (message, "- allocating demand to %s withdrawal" % kind),
        )

        (
            opt_unmet,
            opt_unused,
            opt_allocated,
            opt_message,
        ) = allocate_withdrawals_to_demand(
            demand=unmet,
            withdrawal=unused[kind],
            source_names=source_names,
            sector_names=sector_names,
            zones=zones,
            summarize=summarize,
        )

        # update the unmet demand, unused withdrawal and allocated demand
        unmet = {se: opt_unmet[se] for se in sector_names}
        unused[kind] = {
            so: {se: opt_unused[so][se] for se in sector_names} for so in source_names
        }
        allocated[kind] = {
            so: {
                se: allocated[kind][so][se] + opt_allocated[so][se]
                for se in sector_names
            }
            for so in source_names
        }
        message = str.join("\n", (message, opt_message))

    if summarize:
        message = str.join(
            "\n",
            (
                message,
                "",
                "=" * len("statistics - supply"),
                "statistics - supply",
                "=" * len("statistics - supply"),
            ),
        )

        used = {
            k: {
                so: {
                    se: withdrawal_initial[k][so][se] - unused[k][so][se]
                    for se in sector_names
                }
                for so in source_names
            }
            for k in withdrawal_names
        }

        for kind in withdrawal_names:
            for source in source_names:
                for sector in sector_names:
                    withdrawal_stats = pcr_get_statistics(
                        withdrawal_initial[kind][source][sector]
                    )
                    used_stats = pcr_get_statistics(used[kind][source][sector])
                    unused_stats = pcr_get_statistics(unused[kind][source][sector])

                    message = str.join(
                        "\n",
                        (
                            message,
                            "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                            % (
                                "%s - %s - %s - %s"
                                % ("initial withdrawal", kind, source, sector),
                                withdrawal_stats["count"],
                                withdrawal_stats["average"],
                                withdrawal_stats["min"],
                                withdrawal_stats["max"],
                            ),
                            "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                            % (
                                "%s - %s - %s - %s"
                                % ("used withdrawal", kind, source, sector),
                                used_stats["count"],
                                used_stats["average"],
                                used_stats["min"],
                                used_stats["max"],
                            ),
                            "%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g"
                            % (
                                "%s - %s - %s - %s"
                                % ("unused withdrawal", kind, source, sector),
                                unused_stats["count"],
                                unused_stats["average"],
                                unused_stats["min"],
                                unused_stats["max"],
                            ),
                        ),
                    )

    return unmet, unused, allocated, message
