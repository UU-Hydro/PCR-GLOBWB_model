import logging

import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class WaterBodies(object):

    def __init__(self, iniItems, landmask, onlyNaturalWaterBodies=False, lddMap=None):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        self.iniItems = iniItems

        if lddMap is None:
            self.lddMap = vos.readPCRmapClone(
                iniItems.routingOptions["lddMap"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
                True,
            )
            self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
            self.lddMap = pcr.lddrepair(self.lddMap)
        else:
            self.lddMap = lddMap

        # option to activate the water balance check
        self.debugWaterBalance = True
        if (
            "debugWaterBalance" in list(iniItems.routingOptions.keys())
            and iniItems.routingOptions["debugWaterBalance"] == "False"
        ):
            self.debugWaterBalance = False

        # option to run with only natural lakes (without reservoirs)
        self.onlyNaturalWaterBodies = onlyNaturalWaterBodies
        if (
            "onlyNaturalWaterBodies" in list(iniItems.routingOptions.keys())
            and iniItems.routingOptions["onlyNaturalWaterBodies"] == "True"
        ):
            logger.info(
                "Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes."
            )
            self.onlyNaturalWaterBodies = True
            # a natural run only uses this date
            self.dateForNaturalCondition = "1900-01-01"

        # files with water body parameters
        self.useNetCDF = True
        if iniItems.routingOptions["waterBodyInputNC"] == str(None):
            self.useNetCDF = False
            self.fracWaterInp = iniItems.routingOptions["fracWaterInp"]
            self.waterBodyIdsInp = iniItems.routingOptions["waterBodyIds"]
            self.waterBodyTypInp = iniItems.routingOptions["waterBodyTyp"]
            self.resMaxCapInp = iniItems.routingOptions["resMaxCapInp"]
            self.resSfAreaInp = iniItems.routingOptions["resSfAreaInp"]
        else:
            self.useNetCDF = True
            self.ncFileInp = vos.getFullPath(
                iniItems.routingOptions["waterBodyInputNC"], self.inputDir
            )

        # minimum width (m) in the weir formula; TODO: base minWeirWidth on GLWD, GRanD and/or the bankfull discharge formula
        self.minWeirWidth = 10.0

        # storage fractions below which reservoir release stops and above which it equals
        # the long-term average outflow (defaults)
        self.minResvrFrac = 0.10
        self.maxResvrFrac = 0.75
        if "minResvrFrac" in list(iniItems.routingOptions.keys()):
            minResvrFrac = iniItems.routingOptions["minResvrFrac"]
            self.minResvrFrac = vos.readPCRmapClone(
                minResvrFrac, self.cloneMap, self.tmpDir, self.inputDir
            )
        if "maxResvrFrac" in list(iniItems.routingOptions.keys()):
            maxResvrFrac = iniItems.routingOptions["maxResvrFrac"]
            self.maxResvrFrac = vos.readPCRmapClone(
                maxResvrFrac, self.cloneMap, self.tmpDir, self.inputDir
            )

    def getParameterFiles(
        self,
        currTimeStep,
        cellArea,
        ldd,
        initial_condition_dictionary=None,
        currTimeStepInDateTimeFormat=False,
    ):

        # water body parameters: fracWat, waterBodyIds, waterBodyOut, waterBodyArea, waterBodyTyp, waterBodyCap

        self.cellArea = cellArea
        ldd = pcr.ifthen(self.landmask, ldd)

        # date used to extract the water body information
        if currTimeStepInDateTimeFormat:
            date_used = currTimeStep
            year_used = currTimeStep.year
        else:
            date_used = currTimeStep.fulldate
            year_used = currTimeStep.year
        if self.onlyNaturalWaterBodies:
            date_used = self.dateForNaturalCondition
            year_used = self.dateForNaturalCondition[0:4]

        # fraction of surface water bodies (-)
        self.fracWat = pcr.spatial(pcr.scalar(0.0))

        if self.useNetCDF:
            self.fracWat = vos.netcdf2PCRobjClone(
                self.ncFileInp,
                "fracWaterInp",
                date_used,
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
            )
        else:
            if self.fracWaterInp != "None":
                self.fracWat = vos.readPCRmapClone(
                    self.fracWaterInp + str(year_used) + ".map",
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

        self.fracWat = pcr.cover(self.fracWat, pcr.spatial(pcr.scalar(0.0)))
        self.fracWat = pcr.max(0.0, self.fracWat)
        self.fracWat = pcr.min(1.0, self.fracWat)

        self.waterBodyIds = pcr.spatial(pcr.nominal(0))
        self.waterBodyOut = pcr.spatial(pcr.boolean(0))
        self.waterBodyArea = pcr.spatial(pcr.scalar(0.0))

        if self.useNetCDF:
            self.waterBodyIds = vos.netcdf2PCRobjClone(
                self.ncFileInp,
                "waterBodyIds",
                date_used,
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
            )
        else:
            if self.waterBodyIdsInp != "None":
                self.waterBodyIds = vos.readPCRmapClone(
                    self.waterBodyIdsInp + str(year_used) + ".map",
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                    False,
                    None,
                    True,
                )
        self.waterBodyIds = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0.0, pcr.nominal(self.waterBodyIds)
        )

        # water body outlets (correcting the outlet positions)
        wbCatchment = pcr.catchmenttotal(pcr.scalar(1), ldd)
        # this may give more than one outlet, e.g. if several cells have the largest upstream area
        self.waterBodyOut = pcr.ifthen(
            wbCatchment == pcr.areamaximum(wbCatchment, self.waterBodyIds),
            self.waterBodyIds,
        )
        # make sure there is only one outlet per water body
        self.waterBodyOut = pcr.ifthen(
            pcr.areaorder(pcr.scalar(self.waterBodyOut), self.waterBodyOut) == 1.0,
            self.waterBodyOut,
        )
        self.waterBodyOut = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0.0, self.waterBodyOut
        )

        # TODO: also consider endorheic lakes

        self.waterBodyIds = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0.0,
            pcr.subcatchment(ldd, self.waterBodyOut),
        )

        self.waterBodyOut = pcr.ifthen(
            pcr.scalar(self.waterBodyOut) > 0.0, pcr.spatial(pcr.boolean(1))
        )

        # reservoir surface area (m2)
        if self.useNetCDF:
            resSfArea = (
                1000.0
                * 1000.0
                * vos.netcdf2PCRobjClone(
                    self.ncFileInp,
                    "resSfAreaInp",
                    date_used,
                    useDoy="yearly",
                    cloneMapFileName=self.cloneMap,
                )
            )
        else:
            if self.resSfAreaInp != "None":
                resSfArea = (
                    1000.0
                    * 1000.0
                    * vos.readPCRmapClone(
                        self.resSfAreaInp + str(year_used) + ".map",
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )
                )
            else:
                resSfArea = pcr.spatial(pcr.scalar(0.0))
        resSfArea = pcr.areaaverage(resSfArea, self.waterBodyIds)
        resSfArea = pcr.cover(resSfArea, 0.0)

        # water body surface area of lakes and reservoirs (m2)
        self.waterBodyArea = pcr.max(
            pcr.areatotal(
                pcr.cover(self.fracWat * self.cellArea, 0.0), self.waterBodyIds
            ),
            pcr.areaaverage(pcr.cover(resSfArea, 0.0), self.waterBodyIds),
        )
        self.waterBodyArea = pcr.ifthen(self.waterBodyArea > 0.0, self.waterBodyArea)

        # exclude all water bodies with zero surface area
        self.waterBodyIds = pcr.ifthen(self.waterBodyArea > 0.0, self.waterBodyIds)
        self.waterBodyOut = pcr.ifthen(
            pcr.boolean(self.waterBodyIds), self.waterBodyOut
        )

        # water body types: 2 = reservoir (regulated discharge), 1 = lake (weir formula),
        # 0 = neither (e.g. wetland)
        self.waterBodyTyp = pcr.nominal(0)

        if self.useNetCDF:
            self.waterBodyTyp = vos.netcdf2PCRobjClone(
                self.ncFileInp,
                "waterBodyTyp",
                date_used,
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
            )
        else:
            if self.waterBodyTypInp != "None":
                self.waterBodyTyp = vos.readPCRmapClone(
                    self.waterBodyTypInp + str(year_used) + ".map",
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                    False,
                    None,
                    True,
                )

        # exclude wetlands (type 0) from all lake/reservoir functions
        self.waterBodyTyp = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0, pcr.nominal(self.waterBodyTyp)
        )
        self.waterBodyTyp = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0, pcr.nominal(self.waterBodyTyp)
        )
        # choose one type per water body: lake or reservoir
        self.waterBodyTyp = pcr.areamajority(self.waterBodyTyp, self.waterBodyIds)
        self.waterBodyTyp = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0, pcr.nominal(self.waterBodyTyp)
        )
        self.waterBodyTyp = pcr.ifthen(
            pcr.boolean(self.waterBodyIds), self.waterBodyTyp
        )

        # correct the lake and reservoir ids and outlets
        self.waterBodyIds = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0, self.waterBodyIds
        )
        self.waterBodyOut = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0, self.waterBodyOut
        )

        # reservoir maximum capacity (m3)
        self.resMaxCap = pcr.scalar(0.0)
        self.waterBodyCap = pcr.scalar(0.0)

        if self.useNetCDF:
            self.resMaxCap = (
                1000.0
                * 1000.0
                * vos.netcdf2PCRobjClone(
                    self.ncFileInp,
                    "resMaxCapInp",
                    date_used,
                    useDoy="yearly",
                    cloneMapFileName=self.cloneMap,
                )
            )
        else:
            if self.resMaxCapInp != "None":
                self.resMaxCap = (
                    1000.0
                    * 1000.0
                    * vos.readPCRmapClone(
                        self.resMaxCapInp + str(year_used) + ".map",
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )
                )

        self.resMaxCap = pcr.ifthen(self.resMaxCap > 0.0, self.resMaxCap)
        self.resMaxCap = pcr.areaaverage(self.resMaxCap, self.waterBodyIds)

        # water body capacity of lakes and reservoirs (m3); most lakes have a capacity > 0
        self.waterBodyCap = pcr.cover(self.resMaxCap, 0.0)
        self.waterBodyCap = pcr.ifthen(
            pcr.boolean(self.waterBodyIds), self.waterBodyCap
        )

        # reservoirs with zero capacity are assumed to be lakes
        self.waterBodyTyp = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0.0, self.waterBodyTyp
        )
        self.waterBodyTyp = pcr.ifthenelse(
            self.waterBodyCap > 0.0,
            self.waterBodyTyp,
            pcr.ifthenelse(
                pcr.scalar(self.waterBodyTyp) == 2, pcr.nominal(1), self.waterBodyTyp
            ),
        )

        # final corrections: all lakes and reservoirs must have surface areas
        self.waterBodyTyp = pcr.ifthen(self.waterBodyArea > 0.0, self.waterBodyTyp)
        # only types 1 and 2 are considered in the lake/reservoir functions
        self.waterBodyTyp = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0.0, self.waterBodyTyp
        )
        # all lakes and reservoirs must have ids
        self.waterBodyIds = pcr.ifthen(
            pcr.scalar(self.waterBodyTyp) > 0.0, self.waterBodyIds
        )
        # all lakes and reservoirs must have outlets
        self.waterBodyOut = pcr.ifthen(
            pcr.scalar(self.waterBodyIds) > 0.0, self.waterBodyOut
        )

        # a natural run (onlyNaturalWaterBodies) only uses the year 1900: all reservoirs are lakes
        if self.onlyNaturalWaterBodies and date_used == self.dateForNaturalCondition:
            logger.info(
                "Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes."
            )
            self.waterBodyTyp = pcr.ifthen(
                pcr.scalar(self.waterBodyTyp) > 0.0, pcr.nominal(1)
            )

        # check that all lakes and reservoirs have types, ids, surface areas and outlets
        test = (
            pcr.defined(self.waterBodyTyp)
            & pcr.defined(self.waterBodyArea)
            & pcr.defined(self.waterBodyIds)
            & pcr.boolean(
                pcr.areamaximum(pcr.scalar(self.waterBodyOut), self.waterBodyIds)
            )
        )
        a, b, c = vos.getMinMaxMean(pcr.cover(pcr.scalar(test), 1.0) - pcr.scalar(1.0))
        threshold = 1e-3
        if abs(a) > threshold or abs(b) > threshold:
            logger.warning("Missing information in some lakes and/or reservoirs.")

        # get the initial conditions at the first time step
        if initial_condition_dictionary is not None and currTimeStep.timeStepPCR == 1:
            self.getICs(initial_condition_dictionary)

        # initialize storage and average inflow and outflow for new reservoirs (introduced at the
        # beginning of the year)
        try:
            self.waterBodyStorage = pcr.cover(self.waterBodyStorage, 0.0)
            self.avgInflow = pcr.cover(self.avgInflow, 0.0)
            self.avgOutflow = pcr.cover(self.avgOutflow, 0.0)
            self.waterBodyStorage = pcr.ifthen(self.landmask, self.waterBodyStorage)
            self.avgInflow = pcr.ifthen(self.landmask, self.avgInflow)
            self.avgOutflow = pcr.ifthen(self.landmask, self.avgOutflow)
        except Exception:
            pass
        # TODO: remove try/except

        # crop to the landmask
        self.fracWat = pcr.ifthen(self.landmask, self.fracWat)
        self.waterBodyIds = pcr.ifthen(self.landmask, self.waterBodyIds)
        self.waterBodyOut = pcr.ifthen(self.landmask, self.waterBodyOut)
        self.waterBodyArea = pcr.ifthen(self.landmask, self.waterBodyArea)
        self.waterBodyTyp = pcr.ifthen(self.landmask, self.waterBodyTyp)
        self.waterBodyCap = pcr.ifthen(self.landmask, self.waterBodyCap)

    def getICs(self, initial_condition):

        avgInflow = initial_condition["avgLakeReservoirInflowShort"]
        avgOutflow = initial_condition["avgLakeReservoirOutflowLong"]

        if initial_condition["waterBodyStorage"] is not None:
            waterBodyStorage = initial_condition["waterBodyStorage"]
        else:
            # waterBodyStorage at the lake and reservoir cells
            storageAtLakeAndReservoirs = pcr.cover(
                pcr.ifthen(
                    pcr.scalar(self.waterBodyIds) > 0.0,
                    initial_condition["channelStorage"],
                ),
                0.0,
            )
            # only non-negative, rounded-down values
            storageAtLakeAndReservoirs = pcr.max(
                0.00, pcr.rounddown(storageAtLakeAndReservoirs)
            )
            # lake and reservoir storage (m3), given for all lake/reservoir cells
            waterBodyStorage = pcr.ifthen(
                pcr.scalar(self.waterBodyIds) > 0.0,
                pcr.areatotal(storageAtLakeAndReservoirs, self.waterBodyIds),
            )

        # (m3/s)
        self.avgInflow = pcr.cover(avgInflow, 0.0)
        # (m3/s)
        self.avgOutflow = pcr.cover(avgOutflow, 0.0)
        # (m3)
        self.waterBodyStorage = pcr.cover(waterBodyStorage, 0.0)

        self.avgInflow = pcr.ifthen(self.landmask, self.avgInflow)
        self.avgOutflow = pcr.ifthen(self.landmask, self.avgOutflow)
        self.waterBodyStorage = pcr.ifthen(self.landmask, self.waterBodyStorage)

    def update(
        self,
        newStorageAtLakeAndReservoirs,
        timestepsToAvgDischarge,
        maxTimestepsToAvgDischargeShort,
        maxTimestepsToAvgDischargeLong,
        currTimeStep,
        avgChannelDischarge,
        length_of_time_step=vos.secondsPerDay(),
        downstreamDemand=None,
    ):

        if self.debugWaterBalance:
            # (m)
            preStorage = self.waterBodyStorage

        self.timestepsToAvgDischarge = (
            # TODO: include this in currTimeStep
            timestepsToAvgDischarge
        )

        self.moveFromChannelToWaterBody(
            newStorageAtLakeAndReservoirs,
            timestepsToAvgDischarge,
            maxTimestepsToAvgDischargeShort,
            length_of_time_step,
        )

        self.getWaterBodyOutflow(
            maxTimestepsToAvgDischargeLong,
            avgChannelDischarge,
            length_of_time_step,
            downstreamDemand,
        )

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [pcr.cover(self.inflow / self.waterBodyArea, 0.0)],
                [pcr.cover(self.waterBodyOutflow / self.waterBodyArea, 0.0)],
                [pcr.cover(preStorage / self.waterBodyArea, 0.0)],
                [pcr.cover(self.waterBodyStorage / self.waterBodyArea, 0.0)],
                "WaterBodyStorage (unit: m)",
                True,
                currTimeStep.fulldate,
                threshold=5e-3,
            )

        self.waterBodyBalance = (
            pcr.cover(self.inflow / self.waterBodyArea, 0.0)
            - pcr.cover(self.waterBodyOutflow / self.waterBodyArea, 0.0)
        ) - (
            pcr.cover(self.waterBodyStorage / self.waterBodyArea, 0.0)
            - pcr.cover(preStorage / self.waterBodyArea, 0.0)
        )

    def moveFromChannelToWaterBody(
        self,
        newStorageAtLakeAndReservoirs,
        timestepsToAvgDischarge,
        maxTimestepsToAvgDischargeShort,
        length_of_time_step=vos.secondsPerDay(),
    ):

        # new lake and reservoir storage (m3)
        newStorageAtLakeAndReservoirs = pcr.cover(
            pcr.areatotal(newStorageAtLakeAndReservoirs, self.waterBodyIds), 0.0
        )

        # incoming volume (m3)
        self.inflow = newStorageAtLakeAndReservoirs - self.waterBodyStorage

        # TODO: check whether this inflow includes evaporation losses

        # (m3/s)
        self.inflowInM3PerSec = self.inflow / length_of_time_step

        # update the (short-term) average inflow (m3/s), needed to constrain the lake outflow;
        # see the "weighted incremental algorithm" in http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        temp = pcr.max(
            1.0,
            pcr.min(
                maxTimestepsToAvgDischargeShort,
                self.timestepsToAvgDischarge
                - 1.0
                + length_of_time_step / vos.secondsPerDay(),
            ),
        )
        deltaInflow = self.inflowInM3PerSec - self.avgInflow
        R = deltaInflow * (length_of_time_step / vos.secondsPerDay()) / temp
        self.avgInflow = self.avgInflow + R
        self.avgInflow = pcr.max(0.0, self.avgInflow)

        self.waterBodyStorage = newStorageAtLakeAndReservoirs

    def getWaterBodyOutflow(
        self,
        maxTimestepsToAvgDischargeLong,
        avgChannelDischarge,
        length_of_time_step=vos.secondsPerDay(),
        downstreamDemand=None,
    ):

        # lake outflow (m3)
        lakeOutflow = self.getLakeOutflow(avgChannelDischarge, length_of_time_step)

        # reservoir outflow (m3)
        if downstreamDemand is None:
            downstreamDemand = pcr.scalar(0.0)
        reservoirOutflow = self.getReservoirOutflow(
            avgChannelDischarge, length_of_time_step, downstreamDemand
        )

        # outflow from lakes and reservoirs
        self.waterBodyOutflow = pcr.cover(reservoirOutflow, lakeOutflow)

        # make sure all water bodies have an outflow
        self.waterBodyOutflow = pcr.max(0.0, pcr.cover(self.waterBodyOutflow, 0.0))

        # limit the outflow to the available storage, to avoid flip-flopping
        factor = 0.25
        # (m3)
        self.waterBodyOutflow = pcr.min(
            self.waterBodyStorage * factor, self.waterBodyOutflow
        )
        # round values (m3)
        self.waterBodyOutflow = pcr.rounddown(self.waterBodyOutflow / 1.0) * 1.0

        # (m3/s)
        waterBodyOutflowInM3PerSec = self.waterBodyOutflow / length_of_time_step

        # update the (long-term) average outflow (m3/s), needed to constrain the reservoir outflow;
        # see the "weighted incremental algorithm" in http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        temp = pcr.max(
            1.0,
            pcr.min(
                maxTimestepsToAvgDischargeLong,
                self.timestepsToAvgDischarge
                - 1.0
                + length_of_time_step / vos.secondsPerDay(),
            ),
        )
        deltaOutflow = waterBodyOutflowInM3PerSec - self.avgOutflow
        R = deltaOutflow * (length_of_time_step / vos.secondsPerDay()) / temp
        self.avgOutflow = self.avgOutflow + R
        self.avgOutflow = pcr.max(0.0, self.avgOutflow)

        # update waterBodyStorage after outflow
        self.waterBodyStorage = self.waterBodyStorage - self.waterBodyOutflow
        self.waterBodyStorage = pcr.max(0.0, self.waterBodyStorage)

    # (m3/s)
    def weirFormula(self, waterHeight, weirWidth):
        sillElev = pcr.scalar(0.0)
        weirCoef = pcr.scalar(1.0)
        weirFormula = (
            1.7 * weirCoef * pcr.max(0, waterHeight - sillElev) ** 1.5
        ) * weirWidth
        return weirFormula

    def getLakeOutflow(
        self, avgChannelDischarge, length_of_time_step=vos.secondsPerDay()
    ):

        # water height (m), a function of storage; Rens used 0.001 m as minimum to make sure there
        # is always lake outflow, but it is still limited by the available waterBodyStorage
        minWaterHeight = 0.001
        waterHeight = pcr.cover(
            pcr.max(
                minWaterHeight,
                (self.waterBodyStorage - pcr.cover(self.waterBodyCap, 0.0))
                / self.waterBodyArea,
            ),
            0.0,
        )

        # weir width (m), estimated from avgOutflow (m3/s) using the bankfull discharge formula
        avgOutflow = self.avgOutflow
        # needed for new lakes/reservoirs (their avgOutflow is still zero)
        avgOutflow = pcr.ifthenelse(
            avgOutflow > 0.0,
            avgOutflow,
            pcr.max(avgChannelDischarge, self.avgInflow, 0.001),
        )
        avgOutflow = pcr.areamaximum(avgOutflow, self.waterBodyIds)
        bankfullWidth = pcr.cover(pcr.scalar(4.8) * ((avgOutflow) ** (0.5)), 0.0)
        weirWidthUsed = bankfullWidth
        # TODO: base minWeirWidth on the GRanD database
        weirWidthUsed = pcr.max(weirWidthUsed, self.minWeirWidth)
        weirWidthUsed = pcr.cover(
            pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.0, weirWidthUsed), 0.0
        )

        # (m3/s)
        lakeOutflowInM3PerSec = pcr.max(
            self.weirFormula(waterHeight, weirWidthUsed), self.avgInflow
        )

        # volume released by lakes (m3)
        lakeOutflow = lakeOutflowInM3PerSec * length_of_time_step
        lakeOutflow = pcr.min(self.waterBodyStorage, lakeOutflow)
        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.0, lakeOutflow)
        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 1, lakeOutflow)

        # TODO: consider endorheic lakes/basins (no outflow)

        return lakeOutflow

    def getReservoirOutflow(
        self, avgChannelDischarge, length_of_time_step, downstreamDemand
    ):

        # (m3/s)
        avgOutflow = self.avgOutflow
        # needed for new lakes/reservoirs (their avgOutflow is still zero)
        avgOutflow = pcr.ifthenelse(
            avgOutflow > 0.0, avgOutflow, pcr.max(avgChannelDischarge, self.avgInflow)
        )
        avgOutflow = pcr.ifthenelse(
            avgOutflow > 0.0, avgOutflow, pcr.downstream(self.lddMap, avgOutflow)
        )
        avgOutflow = pcr.areamaximum(avgOutflow, self.waterBodyIds)

        # reservoir outflow based on reservoir storage and avgDischarge, using a reduction factor:
        # release stops if relativeCapacity < minResvrFrac, and equals the long-term average if
        # relativeCapacity > maxResvrFrac
        reductionFactor = pcr.cover(
            pcr.min(
                1.0,
                pcr.max(
                    0.0, self.waterBodyStorage - self.minResvrFrac * self.waterBodyCap
                )
                / (self.maxResvrFrac - self.minResvrFrac)
                * self.waterBodyCap,
            ),
            0.0,
        )
        # (m3)
        resvOutflow = reductionFactor * avgOutflow * length_of_time_step

        # maximum release <= average inflow (especially in dry conditions) (m3)
        resvOutflow = pcr.max(
            0, pcr.min(resvOutflow, self.avgInflow * length_of_time_step)
        )

        # downstream demand (m3/s), reduced if storage < lower limit
        reductionFactor = vos.getValDivZero(
            downstreamDemand, self.minResvrFrac * self.waterBodyCap, vos.smallNumber
        )
        reductionFactor = pcr.cover(reductionFactor, 0.0)
        downstreamDemand = pcr.min(downstreamDemand, downstreamDemand * reductionFactor)
        # resvOutflow > downstreamDemand (m3)
        resvOutflow = pcr.max(resvOutflow, downstreamDemand * length_of_time_step)

        # floodOutflow: additional release if storage > upper limit
        ratioQBankfull = 2.3
        estmStorage = pcr.max(0.0, self.waterBodyStorage - resvOutflow)
        floodOutflow = pcr.max(0.0, estmStorage - self.waterBodyCap) + pcr.cover(
            pcr.max(0.0, estmStorage - self.maxResvrFrac * self.waterBodyCap)
            / ((1.0 - self.maxResvrFrac) * self.waterBodyCap),
            0.0,
        ) * pcr.max(
            0.0, ratioQBankfull * avgOutflow * vos.secondsPerDay() - resvOutflow
        )
        # limit floodOutflow: only bring the storage down to 3/4 of the upper limit capacity
        floodOutflow = pcr.max(
            0.0,
            pcr.min(
                floodOutflow, estmStorage - self.maxResvrFrac * self.waterBodyCap * 0.75
            ),
        )

        # update resvOutflow after floodOutflow
        resvOutflow = pcr.cover(resvOutflow, 0.0) + pcr.cover(floodOutflow, 0.0)

        # maximum release if storage > upper limit: only bring the storage down to 3/4 of the upper limit capacity
        resvOutflow = pcr.ifthenelse(
            self.waterBodyStorage > self.maxResvrFrac * self.waterBodyCap,
            pcr.min(
                resvOutflow,
                pcr.max(
                    0,
                    self.waterBodyStorage
                    - self.maxResvrFrac * self.waterBodyCap * 0.75,
                ),
            ),
            resvOutflow,
        )

        # if storage > upper limit: resvOutflow > avgInflow
        resvOutflow = pcr.ifthenelse(
            self.waterBodyStorage > self.maxResvrFrac * self.waterBodyCap,
            pcr.max(0.0, resvOutflow, self.avgInflow),
            resvOutflow,
        )

        # resvOutflow < waterBodyStorage
        resvOutflow = pcr.min(self.waterBodyStorage, resvOutflow)

        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.0, resvOutflow)
        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 2, resvOutflow)
        # (m3)
        return resvOutflow
