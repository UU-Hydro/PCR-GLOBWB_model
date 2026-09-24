import logging

import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class WaterManagement(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)

        self.iniItems = iniItems

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        # groundwater abstraction options: if limitAbstraction, only renewable groundwater is used
        if "limitAbstraction" not in list(iniItems.waterManagementOptions.keys()):
            iniItems.waterManagementOptions["limitAbstraction"] = False
        self.limitAbstraction = False
        if iniItems.waterManagementOptions["limitAbstraction"] == "True":
            self.limitAbstraction = True

        # option for the groundwater pumping capacity (limitRegionalAnnualGroundwaterAbstraction)
        if "pumpingCapacityNC" not in list(iniItems.waterManagementOptions.keys()):
            msg = 'The "pumpingCapacityNC" (annual groundwater pumping capacity limit netcdf file)'
            msg += "is not defined in the configuration file. "
            msg += "We assume no annual groundwater pumping limit used in this run. "
            msg += "It may result too high groundwater abstraction."
            logger.warning(msg)
            iniItems.waterManagementOptions["pumpingCapacityNC"] = "None"

        # option to limit regional groundwater abstraction
        if iniItems.waterManagementOptions["pumpingCapacityNC"] != "None":
            logger.info("Limit for annual regional groundwater abstraction is used.")
            self.limitRegionalAnnualGroundwaterAbstraction = True
            self.pumpingCapacityNC = vos.getFullPath(
                iniItems.waterManagementOptions["pumpingCapacityNC"],
                self.inputDir,
                False,
            )
        else:
            logger.warning(
                "NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction."
            )
            self.limitRegionalAnnualGroundwaterAbstraction = False

        # option to prioritize local sources before abstracting water from neighbouring cells
        self.prioritizeLocalSourceToMeetWaterDemand = True
        if (
            "prioritizeLocalSourceToMeetWaterDemand"
            in list(iniItems.waterManagementOptions.keys())
            and iniItems.waterManagementOptions["pumpingCapacityNC"] == "False"
        ):
            self.prioritizeLocalSourceToMeetWaterDemand = False
            logger.info(
                "The option prioritizeLocalSourceToMeetWaterDemand is set to 'False'."
            )

        # option to prioritize surface water (currently always False)
        self.surfaceWaterPiority = False

        # cell area (m2)
        cellArea = vos.readPCRmapClone(
            iniItems.routingOptions["cellAreaMap"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )
        self.cellArea = pcr.ifthen(self.landmask, cellArea)

        # option to use desalinated water
        self.includeDesalination = False
        if iniItems.waterManagementOptions["desalinationWater"] not in [
            "None",
            "False",
        ]:
            logger.info("Monthly desalination water use is included.")
            self.includeDesalination = True
            self.desalinationWaterFile = vos.getFullPath(
                iniItems.waterManagementOptions["desalinationWater"], self.inputDir
            )
        else:
            logger.info("Monthly desalination water is NOT included.")

        # allocation zones for desalinated water, surface water and groundwater; if not defined,
        # only the local cell water availability is considered
        self.using_allocationSegmentsForDesalinatedWaterSource = False
        self.using_allocationSegmentsForSurfaceWaterSource = False
        self.using_allocationSegmentsForGroundwaterSource = False

        sources = [
            "allocationSegmentsForDesalinatedWaterSource",
            "allocationSegmentsForSurfaceWaterSource",
            "allocationSegmentsForGroundwaterSource",
        ]

        for source in sources:
            if (
                source in iniItems.waterManagementOptions.keys()
                and iniItems.waterManagementOptions[source] not in ["False", "None"]
            ):
                vars(self)["using_" + source] = True
                vars(self)[source], vars(self)[source + "Areas"] = (
                    self.get_allocation_zone(iniItems.waterManagementOptions[source])
                )
            else:
                vars(self)[source], vars(self)[source + "Areas"] = None, None

        # water sources and sectors to evaluate
        self.source_names = [
            "desalinated_water",
            "surface_water",
            "renewable_groundwater",
            "nonrenewable_groundwater",
        ]
        self.sector_names = [
            "domestic",
            "industry",
            "manufacture",
            "thermoelectric",
            "livestock",
            "irrigation",
        ]

        # allocated_withdrawal_per_sector[source_name][sector_name]: water taken from source_name for
        # sector_name, from the point of view of the source cells
        self.allocated_withdrawal_per_sector = {}
        for source_name in self.source_names:
            self.allocated_withdrawal_per_sector[source_name] = {}
            for sector_name in self.sector_names:
                self.allocated_withdrawal_per_sector[source_name][sector_name] = (
                    pcr.scalar(0.0)
                )

        # allocated_demand_per_sector[source_name][sector_name]: water given to sector_name from
        # source_name, from the point of view of the demand cells
        self.allocated_demand_per_sector = {}
        for source_name in self.source_names:
            self.allocated_demand_per_sector[source_name] = {}
            for sector_name in self.sector_names:
                self.allocated_demand_per_sector[source_name][sector_name] = pcr.scalar(
                    0.0
                )

        # met_demand_per_sector[sector_name]: demand met per sector, from the point of view of the
        # demand cells (the sum of allocated_demand_per_sector)
        self.met_demand_per_sector = {}
        for sector_name in self.sector_names:
            self.met_demand_per_sector[sector_name] = pcr.scalar(0.0)

        # predefined surface water fraction to satisfy the irrigation and livestock demand
        self.swAbstractionFractionData = None
        self.swAbstractionFractionDataQuality = None
        if "irrigationSurfaceWaterAbstractionFractionData" in list(
            iniItems.waterManagementOptions.keys()
        ) and "irrigationSurfaceWaterAbstractionFractionDataQuality" in list(
            iniItems.waterManagementOptions.keys()
        ):

            if iniItems.waterManagementOptions[
                "irrigationSurfaceWaterAbstractionFractionData"
            ] not in ["None", "False"] or iniItems.waterManagementOptions[
                "irrigationSurfaceWaterAbstractionFractionDataQuality"
            ] not in [
                "None",
                "False",
            ]:

                logger.info(
                    "Using/incorporating the predefined surface water source of Siebert et al. (2010) for satisfying irrigation and livestock demand."
                )
                self.swAbstractionFractionData = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.waterManagementOptions[
                            "irrigationSurfaceWaterAbstractionFractionData"
                        ],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )
                self.swAbstractionFractionData = pcr.ifthen(
                    self.swAbstractionFractionData >= 0.0,
                    self.swAbstractionFractionData,
                )
                self.swAbstractionFractionDataQuality = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.waterManagementOptions[
                            "irrigationSurfaceWaterAbstractionFractionDataQuality"
                        ],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )
                # ignore values with a quality above 5 (very bad); only cells with quality <= 5 keep values
                self.swAbstractionFractionData = pcr.ifthen(
                    self.swAbstractionFractionDataQuality <= 5.0,
                    self.swAbstractionFractionData,
                )

        # thresholds (fractions) defining the preference for the irrigation water source:
        # threshold_to_maximize_irrigation_surface_water
        if "threshold_to_maximize_irrigation_surface_water" not in list(
            iniItems.waterManagementOptions.keys()
        ):
            msg = 'The option "threshold_to_maximize_irrigation_surface_water" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "1.0" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions[
                "threshold_to_maximize_irrigation_surface_water"
            ] = "1.0"
            # the default of 1.0 disables this threshold
        self.threshold_to_maximize_irrigation_surface_water = vos.readPCRmapClone(
            iniItems.waterManagementOptions[
                "threshold_to_maximize_irrigation_surface_water"
            ],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        # threshold_to_minimize_fossil_groundwater_irrigation
        if "threshold_to_minimize_fossil_groundwater_irrigation" not in list(
            iniItems.waterManagementOptions.keys()
        ):
            msg = 'The option "threshold_to_minimize_fossil_groundwater_irrigation" is not defined in the "waterManagementOptions" of configuration file. '
            msg += 'This run assumes "1.0" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions[
                "threshold_to_minimize_fossil_groundwater_irrigation"
            ] = "1.0"
            # the default of 1.0 disables this threshold
        self.threshold_to_minimize_fossil_groundwater_irrigation = vos.readPCRmapClone(
            iniItems.waterManagementOptions[
                "threshold_to_minimize_fossil_groundwater_irrigation"
            ],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        # maximum daily rate of groundwater abstraction (m/day)
        if "maximumDailyGroundwaterAbstraction" not in list(
            iniItems.waterManagementOptions.keys()
        ):
            msg = 'The option "maximumDailyGroundwaterAbstraction" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "0.050 m/day" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions["maximumDailyGroundwaterAbstraction"] = (
                "0.050"
            )
        self.maximumDailyGroundwaterAbstraction = vos.readPCRmapClone(
            iniItems.waterManagementOptions["maximumDailyGroundwaterAbstraction"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        # maximum daily rate of fossil groundwater abstraction (m/day)
        if "maximumDailyFossilGroundwaterAbstraction" not in list(
            iniItems.waterManagementOptions.keys()
        ):
            msg = 'The option "maximumDailyFossilGroundwaterAbstraction" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "0.020 m/day" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions[
                "maximumDailyFossilGroundwaterAbstraction"
            ] = "0.020"
        self.maximumDailyFossilGroundwaterAbstraction = vos.readPCRmapClone(
            iniItems.waterManagementOptions["maximumDailyFossilGroundwaterAbstraction"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        # maximum predefined surface water fraction to satisfy the industrial and domestic demand
        # (default: the maximum)
        self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = pcr.scalar(1.0)
        if "maximumNonIrrigationSurfaceWaterAbstractionFractionData" in list(
            iniItems.waterManagementOptions.keys()
        ):
            if (
                iniItems.waterManagementOptions[
                    "maximumNonIrrigationSurfaceWaterAbstractionFractionData"
                ]
                != "None"
                or iniItems.waterManagementOptions[
                    "maximumNonIrrigationSurfaceWaterAbstractionFractionData"
                ]
                != "False"
            ):

                logger.info(
                    "Set the maximum fraction for predefined surface water source for satisfying domestic and industrial demand."
                )
                self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = pcr.min(
                    1.0,
                    pcr.cover(
                        vos.readPCRmapClone(
                            iniItems.waterManagementOptions[
                                "maximumNonIrrigationSurfaceWaterAbstractionFractionData"
                            ],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        ),
                        1.0,
                    ),
                )

        # predefined surface water fraction to satisfy the industrial and domestic demand
        self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = None
        if "predefinedNonIrrigationSurfaceWaterAbstractionFractionData" in list(
            iniItems.waterManagementOptions.keys()
        ) and (
            iniItems.waterManagementOptions[
                "predefinedNonIrrigationSurfaceWaterAbstractionFractionData"
            ]
            != "None"
            or iniItems.waterManagementOptions[
                "predefinedNonIrrigationSurfaceWaterAbstractionFractionData"
            ]
            != "False"
        ):

            logger.info(
                "Set the predefined fraction of surface water source for satisfying domestic and industrial demand."
            )
            self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = pcr.min(
                1.0,
                pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.waterManagementOptions[
                            "predefinedNonIrrigationSurfaceWaterAbstractionFractionData"
                        ],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    1.0,
                ),
            )
            self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = pcr.max(
                0.0,
                pcr.min(
                    self.maximumNonIrrigationSurfaceWaterAbstractionFractionData,
                    self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData,
                ),
            )

    def get_allocation_zone(self, zonal_map_file_name):
        allocSegments = vos.readPCRmapClone(
            zonal_map_file_name,
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
            isLddMap=False,
            cover=None,
            isNomMap=True,
        )
        allocSegments = pcr.ifthen(self.landmask, allocSegments)
        allocSegments = pcr.clump(allocSegments)

        extrapolate = True
        if (
            "noParameterExtrapolation" in self.iniItems.waterManagementOptions.keys()
            and self.iniItems.waterManagementOptions["noParameterExtrapolation"]
            == "True"
        ):
            extrapolate = False

        if extrapolate:
            # extrapolate to half-degree resolution
            allocSegments = pcr.cover(
                allocSegments, pcr.windowmajority(allocSegments, 0.5)
            )

        allocSegments = pcr.ifthen(self.landmask, allocSegments)

        # clump and cover the rest with cell ids
        allocSegments = pcr.clump(allocSegments)
        cell_ids = (
            pcr.mapmaximum(pcr.scalar(allocSegments))
            + pcr.scalar(100.0)
            + pcr.uniqueid(pcr.boolean(1.0))
        )
        allocSegments = pcr.cover(allocSegments, pcr.nominal(cell_ids))
        allocSegments = pcr.clump(allocSegments)
        allocSegments = pcr.ifthen(self.landmask, allocSegments)

        # zone area (m2)
        segmentAreas = pcr.areatotal(pcr.cover(self.cellArea, 0.0), allocSegments)
        segmentAreas = pcr.ifthen(self.landmask, segmentAreas)

        return allocSegments, segmentAreas

    def waterAbstractionAndAllocation(
        self,
        water_demand_volume,
        available_water_volume,
        allocation_zones,
        zone_area=None,
        high_volume_threshold=None,
        debug_water_balance=True,
        extra_info_for_water_balance_reporting="",
        landmask=None,
        ignore_small_values=False,
        prioritizing_local_source=True,
    ):

        logger.debug("Allocation of abstraction.")

        if landmask is not None:
            water_demand_volume = pcr.ifthen(
                landmask, pcr.cover(water_demand_volume, 0.0)
            )
            available_water_volume = pcr.ifthen(
                landmask, pcr.cover(available_water_volume, 0.0)
            )
            allocation_zones = pcr.ifthen(landmask, allocation_zones)

        # satisfy the demand with local sources
        localAllocation = pcr.scalar(0.0)
        localAbstraction = pcr.scalar(0.0)
        cellVolDemand = pcr.max(0.0, water_demand_volume)
        cellAvlWater = pcr.max(0.0, available_water_volume)
        if prioritizing_local_source:
            logger.debug(
                "Allocation of abstraction - first, satisfy demand with local source."
            )

            # demand volume per cell (m3)
            if landmask is not None:
                cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))

            # available water volume per cell
            if landmask is not None:
                cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))

            # first satisfy the demand with local sources
            localAllocation = pcr.max(0.0, pcr.min(cellVolDemand, cellAvlWater))
            localAbstraction = localAllocation * 1.0

        logger.debug(
            "Allocation of abstraction - satisfy demand with neighbour sources."
        )

        # remaining demand and available water
        cellVolDemand = pcr.max(0.0, cellVolDemand - localAllocation)
        cellAvlWater = pcr.max(0.0, cellAvlWater - localAbstraction)

        # ignore small values of water availability
        if ignore_small_values:
            available_water_volume = pcr.max(0.0, pcr.rounddown(available_water_volume))

        # demand volume per cell (m3)
        cellVolDemand = pcr.max(0.0, cellVolDemand)
        if landmask is not None:
            cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))

        # total demand volume per zone (m3)
        zoneVolDemand = pcr.areatotal(cellVolDemand, allocation_zones)

        # avoid very high values of available water
        cellAvlWater = pcr.min(cellAvlWater, zoneVolDemand)

        # available water volume per cell
        cellAvlWater = pcr.max(0.0, cellAvlWater)
        if landmask is not None:
            cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))

        # total available water volume per zone (m3)
        zoneAvlWater = pcr.areatotal(cellAvlWater, allocation_zones)

        # total actual abstraction volume per zone (m3), limited to the available water
        zoneAbstraction = pcr.min(zoneAvlWater, zoneVolDemand)

        # actual abstraction volume per cell (m3)
        cellAbstraction = (
            vos.getValDivZero(cellAvlWater, zoneAvlWater, vos.smallNumber)
            * zoneAbstraction
        )
        cellAbstraction = pcr.min(cellAbstraction, cellAvlWater)

        # minimize numerical errors
        if high_volume_threshold is not None:
            # mask: 0 for small volumes, 1 for large volumes (e.g. lakes and reservoirs)
            mask = pcr.cover(
                pcr.ifthen(cellAbstraction > high_volume_threshold, pcr.boolean(1)),
                pcr.boolean(0),
            )
            zoneAbstraction = pcr.areatotal(
                pcr.ifthenelse(mask, 0.0, cellAbstraction), allocation_zones
            )
            zoneAbstraction += pcr.areatotal(
                pcr.ifthenelse(mask, cellAbstraction, 0.0), allocation_zones
            )

        # water allocated to meet the demand (m3)
        cellAllocation = (
            vos.getValDivZero(cellVolDemand, zoneVolDemand, vos.smallNumber)
            * zoneAbstraction
        )
        cellAllocation = pcr.min(cellAllocation, cellVolDemand)

        # add the local abstraction and allocation
        cellAbstraction = cellAbstraction + localAbstraction
        cellAllocation = cellAllocation + localAllocation

        if debug_water_balance and zone_area is not None:
            vos.waterBalanceCheck(
                [
                    pcr.cover(
                        pcr.areatotal(cellAbstraction, allocation_zones) / zone_area,
                        0.0,
                    )
                ],
                [
                    pcr.cover(
                        pcr.areatotal(cellAllocation, allocation_zones) / zone_area, 0.0
                    )
                ],
                [pcr.scalar(0.0)],
                [pcr.scalar(0.0)],
                "abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)",
                True,
                extra_info_for_water_balance_reporting,
                threshold=1e-4,
            )

        return cellAbstraction, cellAllocation, zoneAbstraction

    def update(
        self, vol_gross_sectoral_water_demands, groundwater, routing, currTimeStep
    ):

        # total irrigation and livestock demand, not limited by available water; needed to allocate
        # groundwater (m3)
        self.volTotalIrrigationLivestockDemand = (
            vol_gross_sectoral_water_demands["irrigation"]
            + vol_gross_sectoral_water_demands["livestock"]
        )

        # remaining and satisfied gross sectoral water demands (m3)
        self.satisfied_gross_sectoral_water_demands = {}
        self.remaining_gross_sectoral_water_demands = {}

        for sector_name in self.sector_names:
            self.satisfied_gross_sectoral_water_demands[sector_name] = pcr.scalar(0.0)
            self.remaining_gross_sectoral_water_demands[sector_name] = (
                vol_gross_sectoral_water_demands[sector_name]
            )

        # remaining volumes of surface water and renewable and non-renewable groundwater (m3)
        self.available_surface_water_volume = routing.readAvlChannelStorage
        self.available_renewable_groundwater = (
            groundwater.storGroundwater * self.cellArea
        )
        self.available_nonrenewable_groundwater = (
            groundwater.storGroundwaterFossil * self.cellArea
        )

        # abstract and allocate desalinated water
        self.abstraction_and_allocation_from_desalination(
            remaining_gross_sectoral_water_demands=self.remaining_gross_sectoral_water_demands,
            currTimeStep=currTimeStep,
        )

        # update the remaining and satisfied gross sectoral water demands
        for sector_name in self.sector_names:
            self.satisfied_gross_sectoral_water_demands[
                sector_name
            ] += self.allocated_demand_per_sector["desalinated_water"][sector_name]
            self.remaining_gross_sectoral_water_demands[
                sector_name
            ] -= self.allocated_demand_per_sector["desalinated_water"][sector_name]
            self.remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0, self.remaining_gross_sectoral_water_demands[sector_name]
            )

        # abstract and allocate surface water
        self.abstraction_and_allocation_from_surface_water(
            remaining_gross_sectoral_water_demands=self.remaining_gross_sectoral_water_demands,
            available_surface_water_volume=self.available_surface_water_volume,
            routing=routing,
            groundwater=groundwater,
            currTimeStep=currTimeStep,
        )

        # update the remaining and satisfied gross sectoral water demands
        for sector_name in self.sector_names:
            self.satisfied_gross_sectoral_water_demands[
                sector_name
            ] += self.allocated_demand_per_sector["surface_water"][sector_name]
            self.remaining_gross_sectoral_water_demands[
                sector_name
            ] -= self.allocated_demand_per_sector["surface_water"][sector_name]
            self.remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0, self.remaining_gross_sectoral_water_demands[sector_name]
            )

        # abstract and allocate groundwater
        self.abstraction_and_allocation_from_groundwater(
            remaining_gross_sectoral_water_demands=self.remaining_gross_sectoral_water_demands,
            routing=routing,
            groundwater=groundwater,
            currTimeStep=currTimeStep,
        )

        # update the remaining and satisfied demands after renewable groundwater allocation
        for sector_name in self.sector_names:
            self.satisfied_gross_sectoral_water_demands[
                sector_name
            ] += self.allocated_demand_per_sector["renewable_groundwater"][sector_name]
            self.remaining_gross_sectoral_water_demands[
                sector_name
            ] -= self.allocated_demand_per_sector["renewable_groundwater"][sector_name]
            self.remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0, self.remaining_gross_sectoral_water_demands[sector_name]
            )

        # update the remaining and satisfied demands after non-renewable groundwater allocation
        for sector_name in self.sector_names:
            self.satisfied_gross_sectoral_water_demands[
                sector_name
            ] += self.allocated_demand_per_sector["nonrenewable_groundwater"][
                sector_name
            ]
            self.remaining_gross_sectoral_water_demands[
                sector_name
            ] -= self.allocated_demand_per_sector["nonrenewable_groundwater"][
                sector_name
            ]
            self.remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0, self.remaining_gross_sectoral_water_demands[sector_name]
            )

    def allocate_satisfied_demand_to_each_sector(
        self,
        totalVolWaterAllocation,
        sectoral_remaining_demand_volume,
        total_remaining_demand_volume,
    ):

        allocated_demand_per_sector = {}

        # distribute the water allocated to the cell over the sectors, proportional to their remaining demands
        for sector_name in self.sector_names:
            allocated_demand_per_sector[sector_name] = pcr.ifthenelse(
                total_remaining_demand_volume > 0.0,
                totalVolWaterAllocation
                * vos.getValDivZero(
                    sectoral_remaining_demand_volume[sector_name],
                    total_remaining_demand_volume,
                ),
                0.0,
            )

        return allocated_demand_per_sector

    def allocate_withdrawal_to_each_sector(
        self,
        totalVolCellWaterAbstraction,
        totalVolZoneAbstraction,
        cellAllocatedDemandPerSector,
        allocation_zones=None,
    ):

        # initialize the output dictionary
        allocated_withdrawal_per_sector = {}

        # with allocation zones
        if allocation_zones is not None:
            zonal_allocated_withdrawal_per_sector = {}

            for sector_name in self.sector_names:
                # total water allocated per sector over the allocation zone
                zonal_allocated_withdrawal_per_sector[sector_name] = pcr.areatotal(
                    cellAllocatedDemandPerSector[sector_name], allocation_zones
                )

                # distribute the water abstracted per sector, scaling the cell abstraction by the zonal
                # allocation per sector over the total allocation (total zonal allocation = total zonal abstraction)
                allocated_withdrawal_per_sector[sector_name] = (
                    totalVolCellWaterAbstraction
                    * vos.getValDivZero(
                        zonal_allocated_withdrawal_per_sector[sector_name],
                        totalVolZoneAbstraction,
                    )
                )

        # without allocation zones, allocation equals abstraction
        else:
            allocated_withdrawal_per_sector = cellAllocatedDemandPerSector

        return allocated_withdrawal_per_sector

    def abstraction_and_allocation_from_desalination(
        self, remaining_gross_sectoral_water_demands, currTimeStep
    ):

        # total remaining demand (m3)
        volTotalRemainingDemand = pcr.scalar(0.0)
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            volTotalRemainingDemand = (
                volTotalRemainingDemand
                + remaining_gross_sectoral_water_demands[sector_name]
            )

        # desalinated water use (m/day)
        if self.includeDesalination:
            logger.debug("Monthly desalination water use is included.")
            if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
                desalinationWaterUse = pcr.ifthen(
                    self.landmask,
                    pcr.cover(
                        vos.netcdf2PCRobjClone(
                            self.desalinationWaterFile,
                            "automatic",
                            currTimeStep.fulldate,
                            useDoy="monthly",
                            cloneMapFileName=self.cloneMap,
                        ),
                        0.0,
                    ),
                )
                self.desalinationWaterUse = pcr.max(0.0, desalinationWaterUse)
        else:
            logger.debug("Monthly desalination water use is NOT included.")
            self.desalinationWaterUse = pcr.scalar(0.0)

        # convert to volume (m3)
        volDesalinationWaterUse = pcr.max(
            0.0, self.desalinationWaterUse * self.cellArea
        )

        # abstraction and allocation of desalinated water
        if self.using_allocationSegmentsForDesalinatedWaterSource:
            logger.debug("Allocation of supply from desalination water.")
            (
                volDesalinationAbstraction,
                volDesalinationAllocation,
                volZoneDesalinationAbstraction,
            ) = self.waterAbstractionAndAllocation(
                water_demand_volume=volTotalRemainingDemand,
                available_water_volume=volDesalinationWaterUse,
                allocation_zones=self.allocationSegmentsForDesalinatedWaterSource,
                zone_area=self.allocationSegmentsForDesalinatedWaterSourceAreas,
                high_volume_threshold=None,
                debug_water_balance=True,
                extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                landmask=self.landmask,
                ignore_small_values=False,
                prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
            )
        else:
            logger.debug(
                "Supply from desalination water is only for satisfying local demand (no network)."
            )
            volDesalinationAbstraction = pcr.min(
                volDesalinationWaterUse, volTotalRemainingDemand
            )
            volDesalinationAllocation = volDesalinationAbstraction
            volZoneDesalinationAbstraction = volDesalinationAbstraction

        # allocation of desalinated water per sector (m3)
        self.allocated_demand_per_sector["desalinated_water"] = (
            self.allocate_satisfied_demand_to_each_sector(
                totalVolWaterAllocation=volDesalinationAllocation,
                sectoral_remaining_demand_volume=remaining_gross_sectoral_water_demands,
                total_remaining_demand_volume=volTotalRemainingDemand,
            )
        )

        # abstraction of desalinated water per sector (m3)
        self.allocated_withdrawal_per_sector["desalinated_water"] = (
            self.allocate_withdrawal_to_each_sector(
                totalVolCellWaterAbstraction=volDesalinationAbstraction,
                totalVolZoneAbstraction=volZoneDesalinationAbstraction,
                cellAllocatedDemandPerSector=self.allocated_demand_per_sector[
                    "desalinated_water"
                ],
                allocation_zones=self.allocationSegmentsForDesalinatedWaterSource,
            )
        )

        # remaining desalinated water use (m3)
        self.volRemainingDesalinationWaterUse = pcr.max(
            0.0, volDesalinationWaterUse - volDesalinationAbstraction
        )

        # total desalinated water allocation and abstraction for other modules (m)
        self.desalinationAllocation = volDesalinationAllocation / self.cellArea
        self.desalinationAbstraction = volDesalinationAbstraction / self.cellArea

    def abstraction_and_allocation_from_surface_water(
        self,
        remaining_gross_sectoral_water_demands,
        available_surface_water_volume,
        routing,
        groundwater,
        currTimeStep,
    ):

        # abstraction and allocation of surface water, with the surface water demand estimated from swAbstractionFractionDict

        # partitioning of the abstraction sources: groundwater and surface water
        self.swAbstractionFractionDict = self.partitioningGroundSurfaceAbstraction(
            routing
        )

        # surface water fraction for the industrial, domestic, manufacturing and thermoelectric sectors
        # (excluding irrigation and livestock)
        swAbstractionFraction_industrial_domestic = pcr.min(
            self.swAbstractionFractionDict["max_for_non_irrigation"],
            self.swAbstractionFractionDict["estimate"],
        )

        if self.swAbstractionFractionDict["non_irrigation"] is not None:
            swAbstractionFraction_industrial_domestic = self.swAbstractionFractionDict[
                "non_irrigation"
            ]

        # remaining demands of the combined sectors (m3)
        remainingIndustrialDomestic = pcr.scalar(0.0)
        remainingIrrigationLivestock = pcr.scalar(0.0)

        for sector_name in remaining_gross_sectoral_water_demands.keys():
            if sector_name not in ["irrigation", "livestock"]:
                remainingIndustrialDomestic += remaining_gross_sectoral_water_demands[
                    sector_name
                ]
            else:
                remainingIrrigationLivestock += remaining_gross_sectoral_water_demands[
                    sector_name
                ]

        # total remaining demand of all sectors (m3)
        remainingTotalDemand = (
            remainingIndustrialDomestic + remainingIrrigationLivestock
        )

        # surface water demand estimate, first only for sectors other than irrigation and livestock (m3)
        surface_water_demand_estimate = (
            swAbstractionFraction_industrial_domestic * remainingIndustrialDomestic
        )

        # surface water demand estimate for irrigation and livestock (m3)
        surface_water_irrigation_demand_estimate = (
            self.swAbstractionFractionDict["irrigation"] * remainingIrrigationLivestock
        )

        # prioritize surface water if the groundwater irrigation fraction is relatively low (m3)
        surface_water_irrigation_demand_estimate = pcr.ifthenelse(
            self.swAbstractionFractionDict["irrigation"]
            >= self.swAbstractionFractionDict[
                "threshold_to_maximize_irrigation_surface_water"
            ],
            remainingIrrigationLivestock,
            surface_water_irrigation_demand_estimate,
        )

        # update the estimate of the surface water demand (m3)
        surface_water_demand_estimate += surface_water_irrigation_demand_estimate

        # prioritize surface water in non-productive aquifers with limited groundwater supply (m3)
        surface_water_demand_estimate = pcr.ifthenelse(
            groundwater.productive_aquifer,
            surface_water_demand_estimate,
            pcr.max(
                0.0,
                remainingIrrigationLivestock
                - pcr.min(groundwater.avgAllocationShort, groundwater.avgAllocation)
                * self.cellArea,
            ),
        )

        # maximize surface water use in areas where groundwater supply is overestimated (m3)
        surface_water_demand_estimate += pcr.max(
            0.0,
            pcr.max(
                groundwater.avgAllocationShort * self.cellArea,
                groundwater.avgAllocation * self.cellArea,
            )
            - (1.0 - self.swAbstractionFractionDict["irrigation"])
            * remainingIrrigationLivestock
            - (1.0 - swAbstractionFraction_industrial_domestic)
            * (remainingIndustrialDomestic),
        )

        # total demand to allocate from surface water, limited by swAbstractionFractionDict and the
        # remaining demand (m3)
        surface_water_demand_estimate = pcr.min(
            remainingTotalDemand, surface_water_demand_estimate
        )
        correctedRemainingIrrigationLivestock = pcr.min(
            surface_water_demand_estimate, remainingIrrigationLivestock
        )
        correctedRemainingIndustrialDomestic = pcr.min(
            remainingIndustrialDomestic,
            pcr.max(0.0, surface_water_demand_estimate - remainingIrrigationLivestock),
        )
        correctedSurfaceWaterDemandEstimate = (
            correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic
        )
        surface_water_demand = correctedSurfaceWaterDemandEstimate

        # surface water as the first priority
        if self.surfaceWaterPiority:
            surface_water_demand = remainingTotalDemand

        # TODO: incorporate Rens's environmental flow concept; this may affect the surface water demand estimate

        # abstraction and allocation of surface water
        if self.using_allocationSegmentsForSurfaceWaterSource:
            logger.debug("Allocation of supply from surface water.")
            (
                volSurfaceWaterAbstraction,
                volSurfaceWaterAllocation,
                volZoneSurfaceWaterAbstraction,
            ) = self.waterAbstractionAndAllocation(
                water_demand_volume=surface_water_demand,
                available_water_volume=available_surface_water_volume,
                allocation_zones=self.allocationSegmentsForSurfaceWaterSource,
                zone_area=self.allocationSegmentsForSurfaceWaterSourceAreas,
                high_volume_threshold=None,
                debug_water_balance=True,
                extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                landmask=self.landmask,
                ignore_small_values=False,
                prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
            )
        else:
            logger.debug(
                "Supply from surface water is only for satisfying local demand (no network)."
            )
            volSurfaceWaterAbstraction = pcr.min(
                available_surface_water_volume, surface_water_demand
            )
            volSurfaceWaterAllocation = volSurfaceWaterAbstraction
            volZoneSurfaceWaterAbstraction = volSurfaceWaterAbstraction

        # allocation of surface water per sector (m3)
        self.allocated_demand_per_sector["surface_water"] = (
            self.allocate_satisfied_demand_to_each_sector(
                totalVolWaterAllocation=volSurfaceWaterAllocation,
                sectoral_remaining_demand_volume=remaining_gross_sectoral_water_demands,
                total_remaining_demand_volume=remainingTotalDemand,
            )
        )

        # abstraction of surface water per sector (m3)
        self.allocated_withdrawal_per_sector["surface_water"] = (
            self.allocate_withdrawal_to_each_sector(
                totalVolCellWaterAbstraction=volSurfaceWaterAbstraction,
                totalVolZoneAbstraction=volZoneSurfaceWaterAbstraction,
                cellAllocatedDemandPerSector=self.allocated_demand_per_sector[
                    "surface_water"
                ],
                allocation_zones=self.allocationSegmentsForSurfaceWaterSource,
            )
        )

        # total surface water allocation and abstraction for other modules (m)
        self.allocSurfaceWaterAbstract = volSurfaceWaterAllocation / self.cellArea
        self.actSurfaceWaterAbstract = volSurfaceWaterAbstraction / self.cellArea

    def abstraction_and_allocation_from_groundwater(
        self, remaining_gross_sectoral_water_demands, routing, groundwater, currTimeStep
    ):

        # remaining demands of the combined sectors (m3)
        remainingIndustrialDomestic = pcr.scalar(0.0)
        remainingIrrigationLivestock = pcr.scalar(0.0)

        for sector_name in remaining_gross_sectoral_water_demands.keys():
            if sector_name not in ["irrigation", "livestock"]:
                remainingIndustrialDomestic += remaining_gross_sectoral_water_demands[
                    sector_name
                ]
            else:
                remainingIrrigationLivestock += remaining_gross_sectoral_water_demands[
                    sector_name
                ]

        # total remaining demand of all sectors (m3)
        remainingTotalDemand = (
            remainingIndustrialDomestic + remainingIrrigationLivestock
        )

        # abstraction and allocation of groundwater (renewable and non-renewable);
        # groundwater demand of the industrial and domestic sectors (all remaining demand must be satisfied)
        groundwater_demand_estimate = remainingIndustrialDomestic
        # demand of the irrigation and livestock sectors (only partly satisfied, as it may be too high
        # due to the uncertainty in the irrigation scheme)
        irrigationLivestockGroundwaterDemand = pcr.min(
            remainingIrrigationLivestock,
            pcr.max(
                0.0,
                (1.0 - self.swAbstractionFractionDict["irrigation"])
                * remainingIrrigationLivestock,
            ),
        )
        groundwater_demand_estimate += irrigationLivestockGroundwaterDemand

        # demand to be satisfied by groundwater abstraction, not limited by available water (m3/day)
        self.potVolGroundwaterAbstract = pcr.min(
            remainingTotalDemand, groundwater_demand_estimate
        )

        # update the regional annual groundwater pumping capacity at the start of the year or simulation
        # (groundwater_pumping_region_ids, regionalAnnualGroundwaterAbstractionLimit)

        if self.limitRegionalAnnualGroundwaterAbstraction:

            logger.debug(
                "Total groundwater abstraction is limited by regional annual pumping capacity."
            )
            if currTimeStep.doy == 1 or currTimeStep.timeStepPCR == 1:

                self.groundwater_pumping_region_ids = vos.netcdf2PCRobjClone(
                    groundwater.pumpingCapacityNC,
                    "region_ids",
                    currTimeStep.fulldate,
                    useDoy="yearly",
                    cloneMapFileName=self.cloneMap,
                )

                other_ids = (
                    pcr.mapmaximum(self.groundwater_pumping_region_ids)
                    + pcr.scalar(1000.0)
                    + pcr.uniqueid(self.landmask)
                )
                self.groundwater_pumping_region_ids = pcr.cover(
                    self.groundwater_pumping_region_ids, other_ids
                )
                self.groundwater_pumping_region_ids = pcr.ifthen(
                    self.landmask, pcr.nominal(self.groundwater_pumping_region_ids)
                )

                self.regionalAnnualGroundwaterAbstractionLimit = pcr.ifthen(
                    self.landmask,
                    pcr.cover(
                        vos.netcdf2PCRobjClone(
                            groundwater.pumpingCapacityNC,
                            "regional_pumping_limit",
                            currTimeStep.fulldate,
                            useDoy="yearly",
                            cloneMapFileName=self.cloneMap,
                        ),
                        0.0,
                    ),
                )

                self.regionalAnnualGroundwaterAbstractionLimit = pcr.areamaximum(
                    self.regionalAnnualGroundwaterAbstractionLimit,
                    self.groundwater_pumping_region_ids,
                )

                # (m3/year)
                self.regionalAnnualGroundwaterAbstractionLimit *= (
                    1000.0 * 1000.0 * 1000.0
                )
                self.regionalAnnualGroundwaterAbstractionLimit = pcr.ifthen(
                    self.landmask, self.regionalAnnualGroundwaterAbstractionLimit
                )
                # minimum value (m3/year, regional)
                minimum_value = 1000.0
                self.regionalAnnualGroundwaterAbstractionLimit = pcr.max(
                    minimum_value, self.regionalAnnualGroundwaterAbstractionLimit
                )
        else:
            logger.debug(
                "Total groundwater abstraction is NOT limited by regional annual pumping capacity."
            )
            self.groundwater_pumping_region_ids = None
            self.regionalAnnualGroundwaterAbstractionLimit = None

        # constrain groundwater abstraction with the regional annual pumping capacity
        if self.limitRegionalAnnualGroundwaterAbstraction:

            logger.debug(
                "Total groundwater abstraction is limited by regional annual pumping capacity."
            )

            # total groundwater abstraction over the last 365 days (m3)
            tolerating_days = 0.0
            annualGroundwaterAbstraction = (
                groundwater.avgAbstraction
                * self.cellArea
                * pcr.min(
                    pcr.max(0.0, 365.0 - tolerating_days),
                    routing.timestepsToAvgDischarge,
                )
            )
            # note: groundwater.avgAbstraction must be in m (consistent with previous versions)

            # total regional groundwater abstraction over the last 365 days (m3)
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(
                pcr.cover(annualGroundwaterAbstraction, 0.0),
                self.groundwater_pumping_region_ids,
            )

            # remaining regional pumping capacity (m3)
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.max(
                0.0,
                self.regionalAnnualGroundwaterAbstractionLimit
                - regionalAnnualGroundwaterAbstraction,
            )
            # safety factor (residence time, day-1)
            remainingRegionalAnnualGroundwaterAbstractionLimit *= 0.33

            # remaining regional pumping capacity (m3), limited by potVolGroundwaterAbstract
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.min(
                remainingRegionalAnnualGroundwaterAbstractionLimit,
                pcr.areatotal(
                    self.potVolGroundwaterAbstract, self.groundwater_pumping_region_ids
                ),
            )

            # remaining pumping capacity per cell (m3), downscaled using potVolGroundwaterAbstract
            remainingPixelAnnualGroundwaterAbstractionLimit = (
                remainingRegionalAnnualGroundwaterAbstractionLimit
                * vos.getValDivZero(
                    self.potVolGroundwaterAbstract,
                    pcr.areatotal(
                        self.potVolGroundwaterAbstract,
                        self.groundwater_pumping_region_ids,
                    ),
                )
            )

            # reduced potential groundwater abstraction (m3), considering the pumping capacity and average recharge (baseflow)
            self.potVolGroundwaterAbstract = pcr.min(
                self.potVolGroundwaterAbstract,
                remainingPixelAnnualGroundwaterAbstractionLimit
                + pcr.max(0.0, routing.avgBaseflow),
            )

        else:
            logger.debug(
                "NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction."
            )

        # abstraction and allocation of non-fossil groundwater;
        # accessible non-fossil groundwater storage (all variables in m3)
        readAvlStorGroundwater = pcr.cover(
            pcr.max(0.00, groundwater.storGroundwater * self.cellArea), 0.0
        )
        # maximum daily groundwater abstraction
        readAvlStorGroundwater = pcr.min(
            readAvlStorGroundwater,
            self.maximumDailyGroundwaterAbstraction * self.cellArea,
        )
        # ignore groundwater storage in non-productive aquifers
        readAvlStorGroundwater = pcr.ifthenelse(
            groundwater.productive_aquifer, readAvlStorGroundwater, 0.0
        )
        # in non-productive aquifers, limit readAvlStorGroundwater to the current recharge (baseflow)
        readAvlStorGroundwater = pcr.ifthenelse(
            groundwater.productive_aquifer,
            readAvlStorGroundwater,
            pcr.min(
                readAvlStorGroundwater,
                pcr.max(routing.avgBaseflow * 24.0 * 3600.0, 0.0),
            ),
        )
        # avoid abstracting the entire groundwater volume at once
        readAvlStorGroundwater *= 0.75

        # abstraction and allocation of renewable groundwater
        if self.using_allocationSegmentsForGroundwaterSource:
            logger.debug("Allocation of supply from renewable groundwater.")
            (
                volRenewGroundwaterAbstraction,
                volRenewGroundwaterAllocation,
                volZoneRenewGroundwaterAbstraction,
            ) = self.waterAbstractionAndAllocation(
                water_demand_volume=self.potVolGroundwaterAbstract,
                available_water_volume=readAvlStorGroundwater,
                allocation_zones=self.allocationSegmentsForGroundwaterSource,
                zone_area=self.allocationSegmentsForGroundwaterSourceAreas,
                high_volume_threshold=None,
                debug_water_balance=True,
                extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                landmask=self.landmask,
                ignore_small_values=False,
                prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
            )
        else:
            logger.debug(
                "Supply from renewable groundwater is only for satisfying local demand (no network)."
            )
            volRenewGroundwaterAbstraction = pcr.min(
                readAvlStorGroundwater, self.potVolGroundwaterAbstract
            )
            volRenewGroundwaterAllocation = volRenewGroundwaterAbstraction
            volZoneRenewGroundwaterAbstraction = volRenewGroundwaterAbstraction

        # allocation of renewable groundwater per sector (m3)
        self.allocated_demand_per_sector["renewable_groundwater"] = (
            self.allocate_satisfied_demand_to_each_sector(
                totalVolWaterAllocation=volRenewGroundwaterAllocation,
                sectoral_remaining_demand_volume=remaining_gross_sectoral_water_demands,
                total_remaining_demand_volume=remainingTotalDemand,
            )
        )

        # abstraction of renewable groundwater per sector (m3)
        self.allocated_withdrawal_per_sector["renewable_groundwater"] = (
            self.allocate_withdrawal_to_each_sector(
                totalVolCellWaterAbstraction=volRenewGroundwaterAbstraction,
                totalVolZoneAbstraction=volZoneRenewGroundwaterAbstraction,
                cellAllocatedDemandPerSector=self.allocated_demand_per_sector[
                    "renewable_groundwater"
                ],
                allocation_zones=self.allocationSegmentsForGroundwaterSource,
            )
        )

        # total renewable groundwater allocation and abstraction for other modules (m)
        self.allocNonFossilGroundwater = volRenewGroundwaterAllocation / self.cellArea
        self.nonFossilGroundwaterAbs = volRenewGroundwaterAbstraction / self.cellArea

        # needed to allocate fossil groundwater
        self.satisfiedIrrigationDemandFromNonFossilGroundwater = (
            self.allocated_demand_per_sector["renewable_groundwater"]["irrigation"]
        )

        # update the remaining demands after renewable groundwater allocation
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0,
                remaining_gross_sectoral_water_demands[sector_name]
                - self.allocated_demand_per_sector["renewable_groundwater"][
                    sector_name
                ],
            )

        # remaining renewable groundwater that can still be abstracted (m3)
        self.volRemainingRenewGroundwater = pcr.max(
            0.0, readAvlStorGroundwater - volRenewGroundwaterAbstraction
        )

        # reduce capillary rise so there is always enough water for non-fossil groundwater abstraction (m)
        self.reducedCapRise = volRenewGroundwaterAbstraction / self.cellArea

        # demand to be satisfied by fossil groundwater abstraction, not limited by available water (m3/day)
        self.potVolFossilGroundwaterAbstract = pcr.max(
            0.0, self.potVolGroundwaterAbstract - volRenewGroundwaterAllocation
        )

        # with limitAbstraction, there is no fossil groundwater abstraction
        if self.limitAbstraction:
            logger.debug("Fossil groundwater abstractions are NOT allowed")

        # abstraction and allocation of fossil groundwater; TODO: skip this for runs without water use

        if not self.limitAbstraction:

            logger.debug("Fossil groundwater abstractions are allowed.")

            # remaining water demand per sector (m3/day), not limited by potFossilGroundwaterAbstract
            remainingDomestic = remaining_gross_sectoral_water_demands["domestic"]
            remainingIndustry = remaining_gross_sectoral_water_demands["industry"]
            remainingLivestock = remaining_gross_sectoral_water_demands["livestock"]
            # irrigation (excluding livestock)
            remainingIrrigation = remaining_gross_sectoral_water_demands["irrigation"]

            remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
            # industrial and domestic (excluding livestock)
            remainingIndustrialDomestic = remainingIndustry + remainingDomestic
            remainingTotalDemand = (
                remainingIrrigationLivestock + remainingIndustrialDomestic
            )

            # TODO: make these variables more flexible, especially for more and different sectors

        # constrain fossil groundwater abstraction with the regional pumping capacity
        if self.limitRegionalAnnualGroundwaterAbstraction and not self.limitAbstraction:

            logger.debug(
                "Fossil groundwater abstraction is allowed, BUT limited by the regional annual pumping capacity."
            )

            # total groundwater abstraction over the last 365 days (m3), including non-fossil groundwater
            annualGroundwaterAbstraction += volRenewGroundwaterAbstraction

            regionalAnnualGroundwaterAbstraction = pcr.areatotal(
                pcr.cover(annualGroundwaterAbstraction, 0.0),
                self.groundwater_pumping_region_ids,
            )

            # fossil groundwater demand reduced by the pumping capacity (m3); the safety factor avoids
            # abstracting the remaining limit at once (due to overestimated groundwater demand)
            safety_factor_for_fossil_abstraction = 1.00
            self.potVolFossilGroundwaterAbstract *= pcr.min(
                1.00,
                pcr.cover(
                    pcr.ifthenelse(
                        self.regionalAnnualGroundwaterAbstractionLimit > 0.0,
                        pcr.max(
                            0.000,
                            self.regionalAnnualGroundwaterAbstractionLimit
                            * safety_factor_for_fossil_abstraction
                            - regionalAnnualGroundwaterAbstraction,
                        )
                        / self.regionalAnnualGroundwaterAbstractionLimit,
                        0.0,
                    ),
                    0.0,
                ),
            )

        # TODO: skip this for runs without water use
        if not self.limitAbstraction:

            # remaining total demand limited by potVolFossilGroundwaterAbstract (m3)

            correctedRemainingTotalDemand = pcr.min(
                self.potVolFossilGroundwaterAbstract, remainingTotalDemand
            )

            # remaining industrial, domestic and livestock demands limited by potVolFossilGroundwaterAbstract;
            # not corrected, as these demands are always satisfied first (m3)
            correctedRemainingIndustrialDomesticLivestock = pcr.min(
                remainingIndustrialDomestic + remainingLivestock,
                correctedRemainingTotalDemand,
            )

            # remaining irrigation demand limited by potFossilGroundwaterAbstract (m3)
            correctedRemainingIrrigation = pcr.min(
                remainingIrrigation,
                pcr.max(
                    0.0,
                    correctedRemainingTotalDemand
                    - correctedRemainingIndustrialDomesticLivestock,
                ),
            )

            # ignore small irrigation demands (less than 1 mm) (m3)
            correctedRemainingIrrigation = (
                pcr.rounddown(correctedRemainingIrrigation / self.cellArea * 1000.0)
                / 1000.0
                * self.cellArea
            )

            # corrected remaining total demand, limited by potVolFossilGroundwaterAbstract (m3)
            correctedRemainingTotalDemand = (
                correctedRemainingIndustrialDomesticLivestock
                + correctedRemainingIrrigation
            )

            # corrected remaining industrial and domestic demand, excluding livestock (m3)
            correctedRemainingIndustrialDomestic = pcr.min(
                remainingIndustrialDomestic, correctedRemainingTotalDemand
            )

            # remaining irrigation and livestock demand limited by potFossilGroundwaterAbstract (m3)
            correctedRemainingIrrigationLivestock = pcr.min(
                remainingIrrigationLivestock,
                pcr.max(
                    0.0,
                    correctedRemainingTotalDemand
                    - correctedRemainingIndustrialDomestic,
                ),
            )

            # corrected remaining total demand limited by potFossilGroundwaterAbstract (m3)
            correctedRemainingTotalDemand = (
                correctedRemainingIrrigationLivestock
                + correctedRemainingIndustrialDomestic
            )

            # TODO: check the water balance: correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic <= potFossilGroundwaterAbstract
            # constrain the irrigation groundwater demand with the groundwater source fraction (m3)
            correctedRemainingIrrigationLivestock = pcr.min(
                (1.0 - self.swAbstractionFractionDict["irrigation"])
                * remainingIrrigationLivestock,
                correctedRemainingIrrigationLivestock,
            )
            correctedRemainingIrrigationLivestock = pcr.max(
                0.0,
                pcr.min(
                    correctedRemainingIrrigationLivestock,
                    pcr.max(0.0, self.volTotalIrrigationLivestockDemand)
                    * (1.0 - self.swAbstractionFractionDict["irrigation"])
                    - self.satisfiedIrrigationDemandFromNonFossilGroundwater,
                ),
            )

            # no fossil groundwater abstraction in irrigation areas dominated by swAbstractionFractionDict['irrigation'] (m3)
            correctedRemainingIrrigationLivestock = pcr.ifthenelse(
                self.swAbstractionFractionDict["irrigation"]
                >= self.swAbstractionFractionDict[
                    "threshold_to_minimize_fossil_groundwater_irrigation"
                ],
                0.0,
                correctedRemainingIrrigationLivestock,
            )

            # reduce the fossil irrigation and livestock demands where there is enough non-fossil groundwater
            # (to minimize unrealistic fossil groundwater abstraction): supply from the average recharge
            # (baseflow) and non-fossil groundwater allocation (m3)
            nonFossilGroundwaterSupply = pcr.max(
                pcr.max(0.0, routing.avgBaseflow * vos.secondsPerDay()),
                groundwater.avgNonFossilAllocationShort * self.cellArea,
                groundwater.avgNonFossilAllocation * self.cellArea,
            )

            # irrigation supply from non-fossil groundwater (m3)
            nonFossilIrrigationGroundwaterSupply = (
                nonFossilGroundwaterSupply
                * vos.getValDivZero(remainingIrrigationLivestock, remainingTotalDemand)
            )

            # corrected irrigation and livestock demand (m3)
            correctedRemainingIrrigationLivestock = pcr.max(
                0.0,
                correctedRemainingIrrigationLivestock
                - nonFossilIrrigationGroundwaterSupply,
            )

            # corrected remaining total demand (m3)
            correctedRemainingTotalDemand = (
                correctedRemainingIndustrialDomestic
                + correctedRemainingIrrigationLivestock
            )

            # demand to be satisfied by fossil groundwater abstraction (m3)
            self.potVolFossilGroundwaterAbstract = pcr.min(
                self.potVolFossilGroundwaterAbstract, correctedRemainingTotalDemand
            )

            if (
                not groundwater.limitFossilGroundwaterAbstraction
                and not self.limitAbstraction
            ):

                # note: if limitFossilGroundwaterAbstraction is False, fossil groundwater allocation is not needed
                msg = "Fossil groundwater abstractions are without limit for satisfying local demand. "
                msg = "Allocation for fossil groundwater abstraction is NOT needed/implemented. "
                msg += "However, the fossil groundwater abstraction rate still consider the maximumDailyGroundwaterAbstraction."
                logger.debug(msg)

                # fossil groundwater abstraction (m3)
                self.fossilGroundwaterAbstrVol = self.potVolFossilGroundwaterAbstract
                self.fossilGroundwaterAbstrVol = pcr.min(
                    self.fossilGroundwaterAbstrVol,
                    pcr.max(
                        0.0,
                        self.maximumDailyGroundwaterAbstraction * self.cellArea
                        - volRenewGroundwaterAbstraction,
                    ),
                )

                # fossil groundwater allocation (m3)
                self.fossilGroundwaterAllocVol = self.fossilGroundwaterAbstrVol

            if (
                groundwater.limitFossilGroundwaterAbstraction
                and not self.limitAbstraction
            ):
                logger.debug(
                    "Fossil groundwater abstractions are allowed, but with limit."
                )

                # accessible fossil groundwater (m)
                readAvlFossilGroundwater = pcr.ifthenelse(
                    groundwater.productive_aquifer,
                    groundwater.storGroundwaterFossil,
                    0.0,
                )

                # residence time (day-1) or safety factor (avoids 'unrealistic' zero fossil groundwater)
                readAvlFossilGroundwater *= 0.10

                # maximum daily groundwater abstraction (m)
                readAvlFossilGroundwater = pcr.min(
                    readAvlFossilGroundwater,
                    self.maximumDailyFossilGroundwaterAbstraction,
                    pcr.max(
                        0.0,
                        self.maximumDailyGroundwaterAbstraction
                        - volRenewGroundwaterAbstraction / self.cellArea,
                    ),
                )
                readAvlFossilGroundwater = pcr.max(
                    pcr.cover(readAvlFossilGroundwater, 0.0), 0.0
                )

                # accessible fossil groundwater volume (m3)
                readAvlFossilGroundwaterVol = readAvlFossilGroundwater * self.cellArea

                # fossil groundwater abstraction and allocation (m3);
                # TODO: consider aquifer productivity in the allocation
                if self.using_allocationSegmentsForGroundwaterSource:
                    logger.debug("Allocation of fossil groundwater abstraction.")
                    (
                        volFossilGroundwaterAbstraction,
                        volFossilGroundwaterAllocation,
                        volZoneFossilGroundwaterAbstraction,
                    ) = self.waterAbstractionAndAllocation(
                        water_demand_volume=self.potVolFossilGroundwaterAbstract,
                        available_water_volume=pcr.max(
                            0.00, readAvlFossilGroundwaterVol
                        ),
                        allocation_zones=self.allocationSegmentsForGroundwaterSource,
                        zone_area=self.allocationSegmentsForGroundwaterSourceAreas,
                        high_volume_threshold=None,
                        debug_water_balance=True,
                        extra_info_for_water_balance_reporting=str(
                            currTimeStep.fulldate
                        ),
                        landmask=self.landmask,
                        ignore_small_values=False,
                        prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
                    )
                else:
                    logger.debug(
                        "Fossil groundwater abstraction is only for satisfying local demand. NO Allocation for fossil groundwater abstraction."
                    )

                    volFossilGroundwaterAbstraction = pcr.min(
                        pcr.max(0.0, readAvlFossilGroundwaterVol),
                        self.potVolFossilGroundwaterAbstract,
                    )
                    volFossilGroundwaterAllocation = volFossilGroundwaterAbstraction
                    volZoneFossilGroundwaterAbstraction = (
                        volFossilGroundwaterAbstraction
                    )

        # allocation of non-renewable groundwater per sector (m3)
        self.allocated_demand_per_sector["nonrenewable_groundwater"] = (
            self.allocate_satisfied_demand_to_each_sector(
                totalVolWaterAllocation=volFossilGroundwaterAllocation,
                sectoral_remaining_demand_volume=remaining_gross_sectoral_water_demands,
                total_remaining_demand_volume=remainingTotalDemand,
            )
        )

        # abstraction of non-renewable groundwater per sector (m3)
        self.allocated_withdrawal_per_sector["nonrenewable_groundwater"] = (
            self.allocate_withdrawal_to_each_sector(
                totalVolCellWaterAbstraction=volFossilGroundwaterAbstraction,
                totalVolZoneAbstraction=volZoneFossilGroundwaterAbstraction,
                cellAllocatedDemandPerSector=self.allocated_demand_per_sector[
                    "nonrenewable_groundwater"
                ],
                allocation_zones=self.allocationSegmentsForGroundwaterSource,
            )
        )

        # update the remaining demands after non-renewable groundwater allocation (m3)
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            remaining_gross_sectoral_water_demands[sector_name] = pcr.max(
                0.0,
                remaining_gross_sectoral_water_demands[sector_name]
                - self.allocated_demand_per_sector["nonrenewable_groundwater"][
                    sector_name
                ],
            )

        # total non-renewable groundwater allocation and abstraction for other modules (m)
        self.fossilGroundwaterAlloc = volFossilGroundwaterAllocation / self.cellArea
        self.fossilGroundwaterAbstr = volFossilGroundwaterAbstraction / self.cellArea

    def partitioningGroundSurfaceAbstraction(self, routing_module):

        # partition the abstraction sources (groundwater and surface water) following de Graaf et al. (2014),
        # based on the local average baseflow (m3/s) and upstream average discharge (m3/s)
        averageBaseflowInput = routing_module.avgBaseflow
        averageUpstreamInput = pcr.max(
            routing_module.avgDischarge,
            pcr.cover(
                pcr.upstream(routing_module.lddMap, routing_module.avgDischarge), 0.0
            ),
        )

        if self.using_allocationSegmentsForSurfaceWaterSource:
            averageBaseflowInput = pcr.max(
                0.0, pcr.ifthen(self.landmask, averageBaseflowInput)
            )
            averageUpstreamInput = pcr.max(
                0.0, pcr.ifthen(self.landmask, averageUpstreamInput)
            )

            averageBaseflowInput = pcr.cover(
                pcr.areaaverage(
                    averageBaseflowInput, self.allocationSegmentsForSurfaceWaterSource
                ),
                0.0,
            )
            averageUpstreamInput = pcr.cover(
                pcr.areamaximum(
                    averageUpstreamInput, self.allocationSegmentsForSurfaceWaterSource
                ),
                0.0,
            )

        else:
            logger.debug("Water demand can only be satisfied by local source.")

        swAbstractionFraction = vos.getValDivZero(
            averageUpstreamInput,
            averageUpstreamInput + averageBaseflowInput,
            vos.smallNumber,
        )
        swAbstractionFraction = pcr.roundup(swAbstractionFraction * 100.0) / 100.0
        swAbstractionFraction = pcr.max(0.0, swAbstractionFraction)
        swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)

        if self.using_allocationSegmentsForSurfaceWaterSource:
            swAbstractionFraction = pcr.areamaximum(
                swAbstractionFraction, self.allocationSegmentsForSurfaceWaterSource
            )

        swAbstractionFraction = pcr.cover(swAbstractionFraction, 1.0)
        swAbstractionFraction = pcr.ifthen(self.landmask, swAbstractionFraction)

        # surface water fractions for various purposes
        swAbstractionFractionDict = {}

        # default estimate (de Graaf et al., 2014)
        swAbstractionFractionDict["estimate"] = swAbstractionFraction

        # irrigation and livestock
        swAbstractionFractionDict["irrigation"] = swAbstractionFraction

        # industrial and domestic
        swAbstractionFractionDict["max_for_non_irrigation"] = swAbstractionFraction

        # threshold to maximize surface water withdrawal for irrigation: areas with
        # swAbstractionFractionDict['irrigation'] above it prioritize surface water for irrigation
        # (zero disables this)
        swAbstractionFractionDict["threshold_to_maximize_irrigation_surface_water"] = (
            self.threshold_to_maximize_irrigation_surface_water
        )

        # threshold to minimize (unrealistic) fossil groundwater withdrawal: areas with
        # swAbstractionFractionDict['irrigation'] above it do not abstract fossil groundwater
        swAbstractionFractionDict[
            "threshold_to_minimize_fossil_groundwater_irrigation"
        ] = self.threshold_to_minimize_fossil_groundwater_irrigation

        # by default the non-irrigation fraction is None (then the 'estimate' limited by 'max_for_non_irrigation' is used)
        swAbstractionFractionDict["non_irrigation"] = None

        # include the predefined surface water fraction (e.g. Siebert et al., 2014; McDonald et al., 2014)
        if self.swAbstractionFractionData is not None:
            logger.debug(
                "Using/incorporating the predefined fractions of surface water source."
            )
            swAbstractionFractionDict["estimate"] = swAbstractionFraction
            swAbstractionFractionDict["irrigation"] = (
                self.partitioningGroundSurfaceAbstractionForIrrigation(
                    swAbstractionFraction,
                    self.swAbstractionFractionData,
                    self.swAbstractionFractionDataQuality,
                )
            )
            swAbstractionFractionDict["max_for_non_irrigation"] = (
                self.maximumNonIrrigationSurfaceWaterAbstractionFractionData
            )

            if (
                self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData
                is not None
            ):
                swAbstractionFractionDict["non_irrigation"] = pcr.cover(
                    self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData,
                    swAbstractionFractionDict["estimate"],
                )
                swAbstractionFractionDict["non_irrigation"] = pcr.min(
                    swAbstractionFractionDict["non_irrigation"],
                    swAbstractionFractionDict["max_for_non_irrigation"],
                )
        else:
            logger.debug(
                "NOT using/incorporating the predefined fractions of surface water source."
            )

        return swAbstractionFractionDict

    def partitioningGroundSurfaceAbstractionForIrrigation(
        self,
        swAbstractionFractionEstimate,
        swAbstractionFractionData,
        swAbstractionFractionDataQuality,
    ):

        # surface water fraction from Stefan Siebert's map; with this factor, the minimum data_weight_value
        # is 0.75 (for swAbstractionFractionDataQuality == 5)
        factor = 0.5
        data_weight_value = (
            pcr.scalar(1.0)
            - (pcr.min(5.0, pcr.max(0.0, swAbstractionFractionDataQuality)) / 10.0)
            * factor
        )

        swAbstractionFractionForIrrigation = (
            data_weight_value * swAbstractionFractionData
            + (1.0 - data_weight_value) * swAbstractionFractionEstimate
        )

        swAbstractionFractionForIrrigation = pcr.cover(
            swAbstractionFractionForIrrigation, swAbstractionFractionEstimate
        )
        swAbstractionFractionForIrrigation = pcr.cover(
            swAbstractionFractionForIrrigation, 1.0
        )
        swAbstractionFractionForIrrigation = pcr.ifthen(
            self.landmask, swAbstractionFractionForIrrigation
        )

        return swAbstractionFractionForIrrigation
