import logging
import os
import shutil

import pcraster as pcr

from pcrglobwb import groundwater, landSurface, meteo, routing
from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)

"""
Created on Oct 25, 2013

@author: Niels Drost
"""


class PCRGlobWB(object):

    def __init__(self, configuration, currTimeStep, initialState=None, spinUpRun=None):
        self._configuration = configuration
        self._modelTime = currTimeStep

        pcr.setclone(configuration.cloneMap)

        self.lddMap = vos.readPCRmapClone(
            configuration.routingOptions["lddMap"],
            configuration.cloneMap,
            configuration.tmpDir,
            configuration.globalOptions["inputDir"],
            True,
        )
        # make sure the ldd map is correct and of type ldd
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))

        if configuration.globalOptions["landmask"] != "None":
            self.landmask = vos.readPCRmapClone(
                configuration.globalOptions["landmask"],
                configuration.cloneMap,
                configuration.tmpDir,
                configuration.globalOptions["inputDir"],
            )
        else:
            self.landmask = pcr.defined(self.lddMap)

        # catchment areas
        self.catchment_class = 1.0

        # number of upper soil layers
        self.numberOfSoilLayers = int(
            configuration.landSurfaceOptions["numberOfUpperSoilLayers"]
        )

        self.createSubmodels(initialState)

        # option to save monthly end states
        self.save_monthly_end_states = False
        if "save_monthly_end_states" in list(configuration.reportingOptions.keys()):
            self.save_monthly_end_states = (
                configuration.reportingOptions["save_monthly_end_states"] == "True"
            )

        # option for debugging against PCR-GLOBWB version 1
        self.debug_to_version_one = False
        if configuration.debug_to_version_one:
            self.debug_to_version_one = True
        if self.debug_to_version_one:

            self.directory_for_initial_maps = vos.getFullPath(
                "initials/", self.configuration.mapsDir
            )
            if os.path.exists(self.directory_for_initial_maps):
                shutil.rmtree(self.directory_for_initial_maps)
            os.makedirs(self.directory_for_initial_maps)

            self.dumpState(self.directory_for_initial_maps, "initial")

        # whether this run is a spin-up run
        self.spinUpRun = spinUpRun

    @property
    def configuration(self):
        return self._configuration

    def createSubmodels(self, initialState):

        self.meteo = meteo.Meteo(self._configuration, self.landmask, initialState)
        self.landSurface = landSurface.LandSurface(
            self._configuration, self.landmask, initialState
        )
        self.groundwater = groundwater.Groundwater(
            self._configuration, self.landmask, initialState
        )
        self.routing = routing.Routing(self._configuration, initialState, self.lddMap)

        # short name for every land cover type (used in file names)
        self.shortNames = ["f", "g", "p", "n"]

    def dumpState(self, outputDirectory, specific_date_string=None):
        # write all states to disk to allow restarting

        if specific_date_string == None:
            specific_date_string = str(self._modelTime.fulldate)

        state = self.getState()

        meteoState = state["meteo"]
        for variable, map in list(meteoState.items()):
            vos.writePCRmapToDir(
                map,
                str(variable) + "_" + specific_date_string + ".map",
                outputDirectory,
            )

        landSurfaceState = state["landSurface"]
        for coverType, coverTypeState in list(landSurfaceState.items()):
            for variable, map in list(coverTypeState.items()):
                vos.writePCRmapToDir(
                    map,
                    str(variable)
                    + "_"
                    + coverType
                    + "_"
                    + specific_date_string
                    + ".map",
                    outputDirectory,
                )

        groundWaterState = state["groundwater"]
        for variable, map in list(groundWaterState.items()):
            vos.writePCRmapToDir(
                map,
                str(variable) + "_" + specific_date_string + ".map",
                outputDirectory,
            )

        routingState = state["routing"]
        for variable, map in list(routingState.items()):
            vos.writePCRmapToDir(
                map,
                str(variable) + "_" + specific_date_string + ".map",
                outputDirectory,
            )

    def calculateAndDumpMonthlyValuesForMODFLOW(
        self, outputDirectory, timeStamp="Default"
    ):

        logger.debug(
            "Calculating (accumulating and averaging) and dumping some monthly variables for the MODFLOW input."
        )

        if self._modelTime.day == 1 or self._modelTime.timeStepPCR == 1:

            self.variables = {}

            self.variables["monthly_discharge_cubic_meter_per_second"] = pcr.ifthen(
                self.routing.landmask, pcr.max(0.0, self.routing.disChanWaterBody)
            )
            self.variables["groundwater_recharge_meter_per_day"] = pcr.ifthen(
                self.routing.landmask, self.landSurface.gwRecharge
            )
            self.variables["groundwater_abstraction_meter_per_day"] = pcr.ifthen(
                self.routing.landmask, self.landSurface.totalGroundwaterAbstraction
            )

        self.variables["monthly_discharge_cubic_meter_per_second"] += pcr.ifthen(
            self.routing.landmask, pcr.max(0.0, self.routing.disChanWaterBody)
        )
        self.variables["groundwater_recharge_meter_per_day"] += pcr.ifthen(
            self.routing.landmask, self.landSurface.gwRecharge
        )
        self.variables["groundwater_abstraction_meter_per_day"] += pcr.ifthen(
            self.routing.landmask, self.landSurface.totalGroundwaterAbstraction
        )

        if self._modelTime.isLastDayOfMonth():

            # monthly averages of discharge, groundwater recharge and groundwater abstraction
            number_of_days = min(self._modelTime.day, self._modelTime.timeStepPCR)
            # (m3/s)
            self.variables["monthly_discharge_cubic_meter_per_second"] = (
                self.variables["monthly_discharge_cubic_meter_per_second"]
                / number_of_days
            )
            # (m/day)
            self.variables["groundwater_recharge_meter_per_day"] = (
                self.variables["groundwater_recharge_meter_per_day"] / number_of_days
            )
            # (m/day)
            self.variables["groundwater_abstraction_meter_per_day"] = (
                self.variables["groundwater_abstraction_meter_per_day"] / number_of_days
            )

            # channel storage at the last day of the month (m/day)
            self.variables["channel_storage_cubic_meter"] = pcr.ifthen(
                self.routing.landmask, self.routing.channelStorage
            )

            # time stamp used in the file name
            if timeStamp == "Default":
                timeStamp = str(self._modelTime.fulldate)

            logger.info("Dumping some monthly variables for the MODFLOW input.")

            for variable, map in list(self.variables.items()):
                vos.writePCRmapToDir(
                    map, str(variable) + "_" + timeStamp + ".map", outputDirectory
                )

    def resume(self):
        # restore the state from disk (used when restarting)
        pass

    # TODO: implement
    def setState(self, state):
        logger.error("cannot set state")

    def report_summary(
        self,
        landWaterStoresAtBeginning,
        landWaterStoresAtEnd,
        surfaceWaterStoresAtBeginning,
        surfaceWaterStoresAtEnd,
    ):

        # reset the totals on the first day of the year
        if self._modelTime.doy == 1 or self._modelTime.isFirstTimestep():

            self.precipitationAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            self.list_of_land_surface_variables = self.landSurface.fluxVars + [
                "desalinationAbstraction",
                "desalinationAllocation",
                "actSurfaceWaterAbstract",
                "allocSurfaceWaterAbstract",
                "nonFossilGroundwaterAbs",
                "allocNonFossilGroundwater",
                "fossilGroundwaterAbstr",
                "fossilGroundwaterAlloc",
                "totalGroundwaterAbstraction",
                "totalGroundwaterAllocation",
                "nonIrrReturnFlow",
            ]

            for var in self.list_of_land_surface_variables:
                vars(self)[var + "Acc"] = pcr.ifthen(
                    self.landmask, pcr.spatial(pcr.scalar(0.0))
                )

            self.baseflowAcc = pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0.0)))

            self.surfaceWaterInfAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            self.runoffAcc = pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0.0)))
            self.unmetDemandAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            self.waterBalanceAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )
            self.absWaterBalanceAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            # non-irrigation water use (m)
            self.nonIrrigationWaterUseAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            # non-irrigation return flow to water bodies and water body evaporation (m)
            self.nonIrrReturnFlowAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )
            self.waterBodyEvaporationAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            # surface water input/loss volume (m3) and outgoing volume at pits (m3)
            self.surfaceWaterInputAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )
            self.dischargeAtPitAcc = pcr.ifthen(
                self.landmask, pcr.spatial(pcr.scalar(0.0))
            )

            # storages at the first day of the year (or first time step): land surface (m)
            self.storageAtFirstDay = pcr.ifthen(
                self.landmask, landWaterStoresAtBeginning
            )
            # channel storage (m3)
            self.channelVolumeAtFirstDay = pcr.ifthen(
                self.landmask, surfaceWaterStoresAtBeginning
            )

        # accumulate until the last day of the year
        self.precipitationAcc += self.meteo.precipitation
        for var in self.list_of_land_surface_variables:
            vars(self)[var + "Acc"] += vars(self.landSurface)[var]

        self.baseflowAcc += self.groundwater.baseflow

        self.surfaceWaterInfAcc += self.groundwater.surfaceWaterInf

        self.runoffAcc += self.routing.runoff
        self.unmetDemandAcc += self.groundwater.unmetDemand

        self.waterBalance = (
            landWaterStoresAtBeginning
            - landWaterStoresAtEnd
            + self.meteo.precipitation
            + self.landSurface.irrigationWaterWithdrawal / self.routing.cellArea
            + self.groundwater.surfaceWaterInf
            - self.landSurface.actualET
            - self.routing.runoff
            - self.groundwater.nonFossilGroundwaterAbs
        )

        self.waterBalanceAcc += self.waterBalance
        self.absWaterBalanceAcc += pcr.abs(self.waterBalance)

        # consumptive water use for non-irrigation demand (m)
        self.nonIrrigationWaterUseAcc += self.landSurface.nonIrrWaterConsumption

        self.waterBodyEvaporationAcc += self.routing.waterBodyEvaporation

        # (m3)
        self.surfaceWaterInputAcc += self.routing.local_input_to_surface_water
        # (m3)
        self.dischargeAtPitAcc += self.routing.outgoing_volume_at_pits

        if self._modelTime.isLastDayOfYear() or self._modelTime.isLastTimeStep():

            logger.info("")
            msg = "The following summary values do not include storages in surface water bodies (lake, reservoir and channel storages)."
            # TODO: improve these water balance checks
            logger.info(msg)

            totalCellArea = vos.getMapTotal(
                pcr.ifthen(self.landmask, self.routing.cellArea)
            )
            msg = "Total area = %e km2" % (totalCellArea / 1e6)
            logger.info(msg)

            deltaStorageOneYear = vos.getMapVolume(
                pcr.ifthen(self.landmask, landWaterStoresAtBeginning)
                - pcr.ifthen(self.landmask, self.storageAtFirstDay),
                self.routing.cellArea,
            )
            msg = "Delta total storage days 1 to %i in %i = %e km3 = %e mm" % (
                int(self._modelTime.doy),
                int(self._modelTime.year),
                deltaStorageOneYear / 1e9,
                deltaStorageOneYear * 1000 / totalCellArea,
            )
            logger.info(msg)

            variableList = [
                "precipitation",
                "baseflow",
                "surfaceWaterInf",
                "runoff",
                "unmetDemand",
            ]
            variableList += self.list_of_land_surface_variables

            variableList += ["waterBalance", "absWaterBalance", "nonIrrigationWaterUse"]

            for var in variableList:
                volume = vos.getMapVolume(
                    self.__getattribute__(var + "Acc"), self.routing.cellArea
                )

                # TODO: the calculation does not always start on day 1
                msg = "Accumulated %s days 1 to %i in %i = %e km3 = %e mm" % (
                    var,
                    int(self._modelTime.doy),
                    int(self._modelTime.year),
                    volume / 1e9,
                    volume * 1000 / totalCellArea,
                )
                logger.info(msg)

            logger.info("")
            msg = "The following summary is for surface water bodies."
            logger.info(msg)

            deltaChannelStorageOneYear = vos.getMapTotal(
                pcr.ifthen(self.landmask, surfaceWaterStoresAtEnd)
                - pcr.ifthen(self.landmask, self.channelVolumeAtFirstDay)
            )
            msg = "Delta surface water storage days 1 to %i in %i = %e km3 = %e mm" % (
                int(self._modelTime.doy),
                int(self._modelTime.year),
                deltaChannelStorageOneYear / 1e9,
                deltaChannelStorageOneYear * 1000 / totalCellArea,
            )
            logger.info(msg)

            variableList = ["waterBodyEvaporation"]
            for var in variableList:
                volume = vos.getMapVolume(
                    self.__getattribute__(var + "Acc"), self.routing.cellArea
                )
                msg = "Accumulated %s days 1 to %i in %i = %e km3 = %e mm" % (
                    var,
                    int(self._modelTime.doy),
                    int(self._modelTime.year),
                    volume / 1e9,
                    volume * 1000 / totalCellArea,
                )
                logger.info(msg)

            surfaceWaterInputTotal = vos.getMapTotal(self.surfaceWaterInputAcc)
            msg = "Accumulated %s days 1 to %i in %i = %e km3 = %e mm" % (
                "surfaceWaterInput",
                int(self._modelTime.doy),
                int(self._modelTime.year),
                surfaceWaterInputTotal / 1e9,
                surfaceWaterInputTotal * 1000 / totalCellArea,
            )
            logger.info(msg)

            dischargeAtPitTotal = vos.getMapTotal(self.dischargeAtPitAcc)
            msg = "Accumulated %s days 1 to %i in %i = %e km3 = %e mm" % (
                "dischargeAtPitTotal",
                int(self._modelTime.doy),
                int(self._modelTime.year),
                dischargeAtPitTotal / 1e9,
                dischargeAtPitTotal * 1000 / totalCellArea,
            )
            logger.info(msg)

            surfaceWaterBalance = (
                deltaChannelStorageOneYear
                - surfaceWaterInputTotal
                + dischargeAtPitTotal
            )
            msg = "Accumulated %s days 1 to %i in %i = %e km3 = %e mm" % (
                "surfaceWaterBalance",
                int(self._modelTime.doy),
                int(self._modelTime.year),
                surfaceWaterBalance / 1e9,
                surfaceWaterBalance * 1000 / totalCellArea,
            )
            logger.info(msg)

    def getState(self):
        result = {}

        result["meteo"] = self.meteo.getState()

        result["landSurface"] = self.landSurface.getState()
        result["groundwater"] = self.groundwater.getState()
        result["routing"] = self.routing.getState()

        return result

    def getPseudoState(self):
        result = {}

        result["meteo"] = self.meteo.getPseudoState()

        result["landSurface"] = self.landSurface.getPseudoState()
        result["groundwater"] = self.groundwater.getPseudoState()
        result["routing"] = self.routing.getPseudoState()

        return result

    def getAllState(self):
        result = {}

        result["meteo"] = self.meteo.getState()
        result["meteo"].update(self.meteo.getPseudoState())

        result["landSurface"] = self.landSurface.getState()
        result["landSurface"].update(self.landSurface.getPseudoState())

        result["groundwater"] = self.groundwater.getState()
        result["groundwater"].update(self.groundwater.getPseudoState())

        result["routing"] = self.routing.getState()
        result["routing"].update(self.routing.getPseudoState())

        return result

    def totalLandWaterStores(self):
        # (m), excluding surface water bodies

        if self.numberOfSoilLayers == 2:
            total = (
                self.landSurface.interceptStor
                + self.landSurface.snowFreeWater
                + self.landSurface.snowCoverSWE
                + self.landSurface.topWaterLayer
                + self.landSurface.storUpp
                + self.landSurface.storLow
                + self.groundwater.storGroundwater
            )

        if self.numberOfSoilLayers == 3:
            total = (
                self.landSurface.interceptStor
                + self.landSurface.snowFreeWater
                + self.landSurface.snowCoverSWE
                + self.landSurface.topWaterLayer
                + self.landSurface.storUpp000005
                + self.landSurface.storUpp005030
                + self.landSurface.storLow030150
                + self.groundwater.storGroundwater
            )

        total = pcr.ifthen(self.landmask, total)

        return total

    def totalSurfaceWaterStores(self):
        # (m3), surface water bodies only

        return pcr.ifthen(self.landmask, self.routing.channelStorage)

    def checkLandSurfaceWaterBalance(self, storesAtBeginning, storesAtEnd):

        # all stores (snow, interception, soil, groundwater), excluding routing: incoming fluxes (m)
        precipitation = pcr.ifthen(self.landmask, self.meteo.precipitation)
        satisfiedIrrGrossDemand = pcr.ifthen(
            self.landmask,
            self.landSurface.irrigationWaterWithdrawal / self.routing.cellArea,
        )
        surfaceWaterInf = pcr.ifthen(self.landmask, self.groundwater.surfaceWaterInf)
        # outgoing fluxes (m)
        actualET = pcr.ifthen(self.landmask, self.landSurface.actualET)
        runoff = pcr.ifthen(self.landmask, self.routing.runoff)
        nonFossilGroundwaterAbs = pcr.ifthen(
            self.landmask, self.groundwater.nonFossilGroundwaterAbs
        )
        # added by Joren; TODO: add an option to switch between the new and old module
        transportVolSnow = self.landSurface.transportVolSnow / self.routing.cellArea
        incomingVolSnow = self.landSurface.incomingVolSnow / self.routing.cellArea

        incomingFreeWater = self.landSurface.incomingFreeWater / self.routing.cellArea
        transportFreeWater = self.landSurface.transportFreeWater / self.routing.cellArea

        vos.waterBalanceCheck(
            [
                precipitation,
                surfaceWaterInf,
                satisfiedIrrGrossDemand,
                incomingVolSnow,
                incomingFreeWater,
            ],
            [
                actualET,
                runoff,
                nonFossilGroundwaterAbs,
                transportVolSnow,
                transportFreeWater,
            ],
            [storesAtBeginning],
            [storesAtEnd],
            "all stores (snow + interception + soil + groundwater), but except river/routing",
            True,
            self._modelTime.fulldate,
            threshold=1e-3,
        )

    def read_forcings(self):
        logger.info("Reading forcings for time %s", self._modelTime)
        self.meteo.read_forcings(self._modelTime)

    def update(self, report_water_balance=False):
        logger.info("Updating model for time %s", self._modelTime)

        if report_water_balance:
            # excluding surface water bodies
            landWaterStoresAtBeginning = self.totalLandWaterStores()
            surfaceWaterStoresAtBeginning = self.totalSurfaceWaterStores()

        self.meteo.update(self.routing, self._modelTime)
        self.landSurface.update(
            self.meteo, self.groundwater, self.routing, self._modelTime
        )
        self.groundwater.update(self.landSurface, self.routing, self._modelTime)
        self.routing.update(
            self.landSurface, self.groundwater, self._modelTime, self.meteo
        )

        # save states at the end of the year or simulation, optionally also at the end of each month
        save_monthly_end_states = self.save_monthly_end_states
        if (
            self._modelTime.isLastDayOfYear()
            or self._modelTime.isLastTimeStep()
            or (self._modelTime.isLastDayOfMonth() and save_monthly_end_states)
        ):
            logger.info(
                "Saving/dumping states to pcraster maps for time %s to the directory %s",
                self._modelTime,
                self._configuration.endStateDir,
            )
            self.dumpState(self._configuration.endStateDir)

        # monthly values for the online coupling with MODFLOW
        if self._configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.calculateAndDumpMonthlyValuesForMODFLOW(self._configuration.mapsDir)

        if report_water_balance:
            # excluding surface water bodies
            landWaterStoresAtEnd = self.totalLandWaterStores()
            surfaceWaterStoresAtEnd = self.totalSurfaceWaterStores()

            # land surface water balance check
            self.checkLandSurfaceWaterBalance(
                landWaterStoresAtBeginning, landWaterStoresAtEnd
            )

            # TODO: include water balance checks for the surface water part and for land surface and surface water combined

            self.report_summary(
                landWaterStoresAtBeginning,
                landWaterStoresAtEnd,
                surfaceWaterStoresAtBeginning,
                surfaceWaterStoresAtEnd,
            )

        if self._modelTime.isLastDayOfMonth():
            # create an empty file to indicate that this month is done;
            # only needed for runs with merging and MODFLOW (skipped for spin-up runs)
            if self.spinUpRun is not None and self.spinUpRun == False:
                filename = (
                    self._configuration.mapsDir
                    + "/pcrglobwb_files_for_"
                    + str(self._modelTime.fulldate)
                    + "_are_ready.txt"
                )
                if os.path.exists(filename):
                    os.remove(filename)
                open(filename, "w").close()
