import logging
import math

import pcraster as pcr
from pcraster.framework import *

logger = logging.getLogger(__name__)

from pcrglobwb.common import virtualOS as vos
from pcrglobwb.ncConverter import *


class Groundwater(object):

    def getState(self):
        result = {}
        # (m)
        result["storGroundwater"] = self.storGroundwater
        # (m)
        result["storGroundwaterFossil"] = self.storGroundwaterFossil
        # (m/day)
        result["avgTotalGroundwaterAbstraction"] = self.avgAbstraction
        # (m/day)
        result["avgTotalGroundwaterAllocationLong"] = self.avgAllocation
        # (m/day)
        result["avgTotalGroundwaterAllocationShort"] = self.avgAllocationShort
        # (m/day)
        result["avgNonFossilGroundwaterAllocationLong"] = self.avgNonFossilAllocation
        # (m/day)
        result["avgNonFossilGroundwaterAllocationShort"] = (
            self.avgNonFossilAllocationShort
        )

        # states needed for coupling with MODFLOW
        # (m)
        result["relativeGroundwaterHead"] = self.relativeGroundwaterHead
        # (m/day)
        result["baseflow"] = self.baseflow

        # states needed for coupling with QUAlloc
        # (m/day)
        result["gwRecharge"] = self.gwRecharge
        # (m)
        result["avgStorGroundwater"] = self.avgStorGroundwater

        return result

    def getPseudoState(self):
        result = {}

        return result

    def __init__(self, iniItems, landmask, spinUp):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        self.iniItems = iniItems

        # option to activate the water balance check
        self.debugWaterBalance = True
        if iniItems.routingOptions["debugWaterBalance"] == "False":
            self.debugWaterBalance = False

        self.useMODFLOW = False
        if iniItems.groundwaterOptions["useMODFLOW"] == "True":
            self.useMODFLOW = True

        # exponent of the baseflow reservoir formula (default one)
        if "baseflow_exponent" in list(iniItems.groundwaterOptions.keys()):
            msg = "The exponent for the groundwater reservoir formula is set according to the baseflow_exponent values in the groundwaterOptions of the configuration file."
            logger.info(msg)
            self.baseflow_exponent = vos.readPCRmapClone(
                iniItems.groundwaterOptions["baseflow_exponent"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        else:
            self.baseflow_exponent = pcr.spatial(pcr.scalar(1.0))
        self.baseflow_exponent = pcr.ifthen(self.landmask, self.baseflow_exponent)

        # whether QUAlloc is used
        self.using_qualloc = False
        if "using_qualloc" in iniItems.waterManagementOptions.keys():
            if iniItems.waterManagementOptions["using_qualloc"] == "True":
                self.using_qualloc = True

        # option to limit groundwater use to renewable sources
        self.limitAbstraction = False
        if (
            not self.using_qualloc
            and iniItems.waterManagementOptions["limitAbstraction"] == "True"
        ):
            self.limitAbstraction = True

        # option to limit fossil groundwater abstraction to the aquifer thickness
        self.limitFossilGroundwaterAbstraction = False
        if (
            not self.using_qualloc
            or iniItems.waterManagementOptions["limitFossilGroundWaterAbstraction"]
            == "True"
        ):
            self.limitFossilGroundwaterAbstraction = True

        # with MODFLOW, limitAbstraction must be True (abstraction cannot exceed storGroundwater; no fossil groundwater)
        if self.useMODFLOW:
            self.limitAbstraction = True
            self.limitFossilGroundwaterAbstraction = False

        # option to limit regional groundwater abstraction
        if not self.using_qualloc:
            if iniItems.waterManagementOptions["pumpingCapacityNC"] != "None":
                logger.info(
                    "Limit for annual regional groundwater abstraction is used."
                )
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

        # netCDF file with the groundwater properties
        if iniItems.groundwaterOptions["groundwaterPropertiesNC"] != "None":
            groundwaterPropertiesNC = vos.getFullPath(
                iniItems.groundwaterOptions["groundwaterPropertiesNC"], self.inputDir
            )
        else:
            groundwaterPropertiesNC = iniItems.groundwaterOptions[
                "groundwaterPropertiesNC"
            ]

        # aquifer specific yield (-)
        if iniItems.groundwaterOptions[
            "groundwaterPropertiesNC"
        ] == "None" or "specificYield" in list(iniItems.groundwaterOptions.keys()):
            self.specificYield = vos.readPCRmapClone(
                iniItems.groundwaterOptions["specificYield"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        else:
            self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(
                groundwaterPropertiesNC, "specificYield", self.cloneMap
            )
        self.specificYield = pcr.cover(self.specificYield, 0.0)
        # TODO: set the minimum values of specific yield
        self.specificYield = pcr.max(0.010, self.specificYield)
        self.specificYield = pcr.min(1.000, self.specificYield)

        # aquifer hydraulic conductivity (m/day)
        if iniItems.groundwaterOptions[
            "groundwaterPropertiesNC"
        ] == "None" or "kSatAquifer" in list(iniItems.groundwaterOptions.keys()):
            self.kSatAquifer = vos.readPCRmapClone(
                iniItems.groundwaterOptions["kSatAquifer"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        else:
            self.kSatAquifer = vos.netcdf2PCRobjCloneWithoutTime(
                groundwaterPropertiesNC, "kSatAquifer", self.cloneMap
            )
        self.kSatAquifer = pcr.cover(self.kSatAquifer, 0.0)
        self.kSatAquifer = pcr.max(0.010, self.kSatAquifer)

        # try to read the recession coefficient (day-1) from groundwaterPropertiesNC
        try:
            if groundwaterPropertiesNC == "None":
                self.recessionCoeff = None
            else:
                msg = (
                    "The 'recessionCoeff' will be obtained from the file: "
                    + groundwaterPropertiesNC
                )
                logger.info(msg)
                self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(
                    groundwaterPropertiesNC,
                    "recessionCoeff",
                    cloneMapFileName=self.cloneMap,
                )
        except:
            self.recessionCoeff = None
            msg = (
                "The 'recessionCoeff' cannot be read from the file: "
                + groundwaterPropertiesNC
            )
            logger.warning(msg)
        # TODO: remove try/except

        # recession coefficient from the given PCRaster file
        if "recessionCoeff" in list(iniItems.groundwaterOptions.keys()):
            if iniItems.groundwaterOptions["recessionCoeff"] != "None":
                self.recessionCoeff = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["recessionCoeff"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

        # calculate the recession coefficient from the given parameters
        if self.recessionCoeff is None and "recessionCoeff" not in list(
            iniItems.groundwaterOptions.keys()
        ):

            msg = "Calculating the groundwater linear reccesion coefficient based on the given parameters."
            logger.info(msg)

            # aquifer width from the landSurfaceOptions (slopeLength)
            if iniItems.landSurfaceOptions["topographyNC"] == None:
                aquiferWidth = vos.readPCRmapClone(
                    iniItems.landSurfaceOptions["slopeLength"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                topoPropertiesNC = vos.getFullPath(
                    iniItems.landSurfaceOptions["topographyNC"], self.inputDir
                )
                aquiferWidth = vos.netcdf2PCRobjCloneWithoutTime(
                    topoPropertiesNC, "slopeLength", self.cloneMap
                )
            # fill missing aquiferWidth with its maximum value
            aquiferWidth = pcr.ifthen(
                self.landmask, pcr.cover(aquiferWidth, pcr.mapmaximum(aquiferWidth))
            )

            # aquifer thickness (m) for the recession coefficient
            aquiferThicknessForRecessionCoeff = vos.readPCRmapClone(
                iniItems.groundwaterOptions["aquiferThicknessForRecessionCoeff"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # recession coefficient (day-1)
            self.recessionCoeff = (
                (math.pi**2.0)
                * aquiferThicknessForRecessionCoeff
                / (4.0 * self.specificYield * (aquiferWidth**2.0))
            )

        # recession coefficient from the given PCRaster file
        if "recessionCoeff" in list(iniItems.groundwaterOptions.keys()):
            if iniItems.groundwaterOptions["recessionCoeff"] != "None":
                self.recessionCoeff = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["recessionCoeff"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

        # minimum and maximum groundwater recession coefficient (day-1)
        self.recessionCoeff = pcr.cover(self.recessionCoeff, 0.00)
        self.recessionCoeff = pcr.min(0.9999, self.recessionCoeff)
        if "minRecessionCoeff" in list(iniItems.groundwaterOptions.keys()):
            minRecessionCoeff = float(iniItems.groundwaterOptions["minRecessionCoeff"])
        else:
            minRecessionCoeff = (
                # minimum value used in Van Beek et al. (2011)
                1.0e-4
            )
        self.recessionCoeff = pcr.max(minRecessionCoeff, self.recessionCoeff)

        # river bed conductivity (default: kSatAquifer)
        self.riverBedConductivity = self.kSatAquifer
        # from the given PCRaster file
        if "riverBedConductivity" in list(iniItems.groundwaterOptions.keys()):
            if iniItems.groundwaterOptions["riverBedConductivity"] != "None":
                self.riverBedConductivity = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["riverBedConductivity"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

        # total groundwater thickness (m), used to estimate the fossil groundwater capacity (only for
        # runs without MODFLOW) and the productive aquifer areas, where capillary rise and groundwater
        # depletion can occur; for runs with MODFLOW, we want to minimize large drawdowns in
        # non-productive aquifer areas
        totalGroundwaterThickness = None
        if "estimateOfTotalGroundwaterThickness" in list(
            iniItems.groundwaterOptions.keys()
        ) and (self.limitFossilGroundwaterAbstraction or self.useMODFLOW):

            totalGroundwaterThickness = vos.readPCRmapClone(
                iniItems.groundwaterOptions["estimateOfTotalGroundwaterThickness"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            extrapolateGroundwaterThickness = True
            if (
                "doNotExtrapolateThickness" in iniItems.groundwaterOptions.keys()
                and iniItems.groundwaterOptions["doNotExtrapolateThickness"] == "True"
            ):
                extrapolateGroundwaterThickness = False

            if (
                "noParameterExtrapolation" in iniItems.groundwaterOptions.keys()
                and iniItems.groundwaterOptions["noParameterExtrapolation"] == "True"
            ):
                extrapolateGroundwaterThickness = False

            if extrapolateGroundwaterThickness:
                # extrapolate totalGroundwaterThickness; TODO: make a general extrapolation function in virtualOS.py
                totalGroundwaterThickness = pcr.cover(
                    totalGroundwaterThickness,
                    pcr.windowaverage(totalGroundwaterThickness, 0.75),
                )
                totalGroundwaterThickness = pcr.cover(
                    totalGroundwaterThickness,
                    pcr.windowaverage(totalGroundwaterThickness, 0.75),
                )
                totalGroundwaterThickness = pcr.cover(
                    totalGroundwaterThickness,
                    pcr.windowaverage(totalGroundwaterThickness, 0.75),
                )
                totalGroundwaterThickness = pcr.cover(
                    totalGroundwaterThickness,
                    pcr.windowaverage(totalGroundwaterThickness, 1.00),
                )

            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness, 0.0)

            # minimum thickness
            if "minimumTotalGroundwaterThickness" in list(
                iniItems.groundwaterOptions.keys()
            ):
                minimumThickness = pcr.scalar(
                    float(
                        iniItems.groundwaterOptions["minimumTotalGroundwaterThickness"]
                    )
                )
                totalGroundwaterThickness = pcr.max(
                    minimumThickness, totalGroundwaterThickness
                )

            # maximum thickness
            if "maximumTotalGroundwaterThickness" in list(
                iniItems.groundwaterOptions.keys()
            ) and (
                iniItems.groundwaterOptions["maximumTotalGroundwaterThickness"]
                != "None"
            ):
                maximumThickness = float(
                    iniItems.groundwaterOptions["maximumTotalGroundwaterThickness"]
                )
                totalGroundwaterThickness = pcr.min(
                    maximumThickness, totalGroundwaterThickness
                )

            self.totalGroundwaterThickness = totalGroundwaterThickness

        # extent of the productive aquifer (boolean); outside it, there is no capillary rise and
        # groundwater abstraction should not exceed recharge
        self.productive_aquifer = pcr.ifthen(
            self.landmask, pcr.spatial(pcr.boolean(1.0))
        )
        excludeUnproductiveAquifer = True
        if excludeUnproductiveAquifer:
            if "minimumTransmissivityForProductiveAquifer" in list(
                iniItems.groundwaterOptions.keys()
            ) and (
                iniItems.groundwaterOptions["minimumTransmissivityForProductiveAquifer"]
                != "None"
                or iniItems.groundwaterOptions[
                    "minimumTransmissivityForProductiveAquifer"
                ]
                != "False"
            ):
                minimumTransmissivityForProductiveAquifer = vos.readPCRmapClone(
                    iniItems.groundwaterOptions[
                        "minimumTransmissivityForProductiveAquifer"
                    ],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                self.productive_aquifer = pcr.cover(
                    pcr.ifthen(
                        self.kSatAquifer * totalGroundwaterThickness
                        > minimumTransmissivityForProductiveAquifer,
                        pcr.boolean(1.0),
                    ),
                    pcr.boolean(0.0),
                )
        self.productive_aquifer = pcr.cover(self.productive_aquifer, pcr.boolean(0.0))
        # TODO: check and recalculate the GLHYMPS map to confirm kSatAquifer in groundwaterPropertiesNC (e.g. parts of the HPA are missing)

        # fossil groundwater capacity, based on aquifer thickness and specific yield
        if (
            self.limitFossilGroundwaterAbstraction == True
            and self.limitAbstraction == False
        ):

            logger.info("Fossil groundwater abstractions are allowed with LIMIT.")

            logger.info(
                "Estimating fossil groundwater capacities based on aquifer thicknesses and specific yield."
            )
            # TODO: use this aquifer thickness to define the extent of the productive aquifer

            # capacity (m) of renewable groundwater, to correct the initial fossil groundwater capacity;
            # not relevant, but requested in the IWMI project
            if "estimateOfRenewableGroundwaterCapacity" not in list(
                iniItems.groundwaterOptions.keys()
            ):
                iniItems.groundwaterOptions[
                    "estimateOfRenewableGroundwaterCapacity"
                ] = 0.0
            storGroundwaterCap = pcr.cover(
                vos.readPCRmapClone(
                    iniItems.groundwaterOptions[
                        "estimateOfRenewableGroundwaterCapacity"
                    ],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                0.0,
            )
            # fossil groundwater capacity (m)
            self.fossilWaterCap = pcr.ifthen(
                self.landmask,
                pcr.max(
                    0.0,
                    totalGroundwaterThickness * self.specificYield - storGroundwaterCap,
                ),
            )

        self.getICs(iniItems, spinUp)

        # old-style reporting (useful for debugging)
        self.initiate_old_style_groundwater_reporting(iniItems)

    def initiate_old_style_groundwater_reporting(self, iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.groundwaterOptions["outDailyTotNC"].split(",")
            self.outMonthTotNC = iniItems.groundwaterOptions["outMonthTotNC"].split(",")
            self.outMonthAvgNC = iniItems.groundwaterOptions["outMonthAvgNC"].split(",")
            self.outMonthEndNC = iniItems.groundwaterOptions["outMonthEndNC"].split(",")
            self.outAnnuaTotNC = iniItems.groundwaterOptions["outAnnuaTotNC"].split(",")
            self.outAnnuaAvgNC = iniItems.groundwaterOptions["outAnnuaAvgNC"].split(",")
            self.outAnnuaEndNC = iniItems.groundwaterOptions["outAnnuaEndNC"].split(",")
        except:
            self.report = False
        if self.report == True:
            self.outNCDir = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            # daily netCDF output
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_dailyTot.nc",
                        var,
                        "undefined",
                    )
            # monthly netCDF output: totals
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # accumulator
                    vars(self)[var + "MonthTot"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_monthTot.nc",
                        var,
                        "undefined",
                    )
            # averages
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # accumulator
                    vars(self)[var + "MonthTot"] = None
                    vars(self)[var + "MonthAvg"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_monthAvg.nc",
                        var,
                        "undefined",
                    )
            # end of month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_monthEnd.nc",
                        var,
                        "undefined",
                    )
            # yearly netCDF output: totals
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:
                    # accumulator
                    vars(self)[var + "AnnuaTot"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_annuaTot.nc",
                        var,
                        "undefined",
                    )
            # averages
            if self.outAnnuaAvgNC[0] != "None":
                for var in self.outAnnuaAvgNC:
                    vars(self)[var + "AnnuaAvg"] = None
                    # accumulator
                    vars(self)[var + "AnnuaTot"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_annuaAvg.nc",
                        var,
                        "undefined",
                    )
            # end of year
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_annuaEnd.nc",
                        var,
                        "undefined",
                    )

    def getICs(self, iniItems, iniConditions=None):

        self.initialize_states(iniItems, iniConditions)

    def initialize_states(self, iniItems, iniConditions):

        # initial conditions (m) at the start of the model (read from file)
        if iniConditions == None:

            if (
                "estimateStorGroundwaterIniFromRecharge"
                in iniItems.groundwaterOptions.keys()
                and iniItems.groundwaterOptions[
                    "estimateStorGroundwaterIniFromRecharge"
                ]
                == "True"
            ):
                iniItems.groundwaterOptions["storGroundwaterIni"] = (
                    "ESTIMATE_FROM_GROUNDWATER_RECHARGE_RATE"
                )
                self.iniItems.groundwaterOptions["storGroundwaterIni"] = (
                    "ESTIMATE_FROM_GROUNDWATER_RECHARGE_RATE"
                )

            if (
                iniItems.groundwaterOptions["storGroundwaterIni"]
                != "ESTIMATE_FROM_GROUNDWATER_RECHARGE_RATE"
            ):
                self.storGroundwater = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["storGroundwaterIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                msg = "Estimating initial conditions of storGroundwater based on the daily groundwater recharge rate given in the configuration file."
                logger.info(msg)
                daily_gw_recharge = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["dailyGroundwaterRechargeIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                daily_gw_recharge = pcr.max(
                    0.0, pcr.ifthen(self.landmask, pcr.cover(daily_gw_recharge, 0.0))
                )
                pcr.report(
                    daily_gw_recharge,
                    "daily_gw_recharge_m_per_day_used_to_estimate_initial_stor_groundwater_when_the_model_just_start_without_spinup.map",
                )
                pcr.report(
                    self.recessionCoeff,
                    "gw_recession_coeff_day-1_used_to_estimate_initial_stor_groundwater_when_the_model_just_start_without_spinup.map",
                )
                self.storGroundwater = daily_gw_recharge / self.recessionCoeff
                self.storGroundwater = pcr.max(0.0, self.storGroundwater)

            self.storGroundwater = pcr.cover(self.storGroundwater, 0.0)
            self.storGroundwater = pcr.max(0.0, self.storGroundwater)
            self.storGroundwater = pcr.ifthen(self.landmask, self.storGroundwater)
            pcr.report(
                self.storGroundwater,
                "initial_stor_groundwater_when_the_model_just_start_without_spinup.map",
            )

            self.avgAbstraction = vos.readPCRmapClone(
                iniItems.groundwaterOptions["avgTotalGroundwaterAbstractionIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgAllocation = vos.readPCRmapClone(
                iniItems.groundwaterOptions["avgTotalGroundwaterAllocationLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgAllocationShort = vos.readPCRmapClone(
                iniItems.groundwaterOptions["avgTotalGroundwaterAllocationShortIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgNonFossilAllocation = vos.readPCRmapClone(
                iniItems.groundwaterOptions["avgNonFossilGroundwaterAllocationLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgNonFossilAllocationShort = vos.readPCRmapClone(
                iniItems.groundwaterOptions[
                    "avgNonFossilGroundwaterAllocationShortIni"
                ],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # additional initial conditions, only needed for the online coupling with MODFLOW
            if iniItems.groundwaterOptions["relativeGroundwaterHeadIni"] != "None":
                self.relativeGroundwaterHead = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["relativeGroundwaterHeadIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                self.relativeGroundwaterHead = self.storGroundwater / self.specificYield
            self.baseflow = vos.readPCRmapClone(
                iniItems.groundwaterOptions["baseflowIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # initial avgStorGroundwater (m), only relevant for a non-linear groundwater reservoir
            if "avgStorGroundwaterIni" in list(iniItems.groundwaterOptions.keys()):
                self.avgStorGroundwater = vos.readPCRmapClone(
                    iniItems.groundwaterOptions["avgStorGroundwaterIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                msg = "The initial state of avgStorGroundwaterIni is not defined in the configuration file. Yet, this is only relevant if non linear grdundwater reservoir is used."
                logger.warning(msg)
                msg = "This run uses storGroundwaterIni = avgStorGroundwaterIni."
                logger.warning(msg)
                self.avgStorGroundwater = self.storGroundwater

            self.gwRecharge = vos.readPCRmapClone(
                iniItems.groundwaterOptions["gwRechargeIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

        # during/after spin-up
        else:
            self.storGroundwater = iniConditions["groundwater"]["storGroundwater"]
            self.avgAbstraction = iniConditions["groundwater"][
                "avgTotalGroundwaterAbstraction"
            ]
            self.avgAllocation = iniConditions["groundwater"][
                "avgTotalGroundwaterAllocationLong"
            ]
            self.avgAllocationShort = iniConditions["groundwater"][
                "avgTotalGroundwaterAllocationShort"
            ]
            self.avgNonFossilAllocation = iniConditions["groundwater"][
                "avgNonFossilGroundwaterAllocationLong"
            ]
            self.avgNonFossilAllocationShort = iniConditions["groundwater"][
                "avgNonFossilGroundwaterAllocationShort"
            ]

            self.relativeGroundwaterHead = iniConditions["groundwater"][
                "relativeGroundwaterHead"
            ]
            self.baseflow = iniConditions["groundwater"]["baseflow"]

            self.avgStorGroundwater = iniConditions["groundwater"]["avgStorGroundwater"]
            self.gwRecharge = iniConditions["groundwater"]["gwRecharge"]

        # initial storGroundwaterFossil (m)
        if (
            "useMaximumStorGroundwaterFossilIni" in iniItems.groundwaterOptions.keys()
            and iniItems.groundwaterOptions["storGroundwaterFossilIni"] == "True"
        ):
            iniItems.groundwaterOptions["storGroundwaterFossilIni"] == "Maximum"
            self.iniItems.groundwaterOptions["storGroundwaterFossilIni"] == "Maximum"
        # storGroundwaterFossil should not be depleted during spin-up
        if (
            iniItems.groundwaterOptions["storGroundwaterFossilIni"] == "Maximum"
            and self.limitFossilGroundwaterAbstraction
            and self.limitAbstraction == False
        ):
            logger.info(
                "Assuming 'full' fossilWaterCap as the initial condition for fossil groundwater storage."
            )
            self.storGroundwaterFossil = self.fossilWaterCap
        if iniItems.groundwaterOptions["storGroundwaterFossilIni"] != "Maximum":
            logger.info(
                "Using a pre-defined initial condition for fossil groundwater storage."
            )
            self.storGroundwaterFossil = vos.readPCRmapClone(
                iniItems.groundwaterOptions["storGroundwaterFossilIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        if (
            iniItems.groundwaterOptions["storGroundwaterFossilIni"] != "Maximum"
            and self.limitFossilGroundwaterAbstraction
            and self.limitAbstraction == False
        ):
            logger.info(
                "The pre-defined initial condition for fossil groundwater is limited by fossilWaterCap (full capacity)."
            )
            self.storGroundwaterFossil = pcr.min(
                self.storGroundwaterFossil, self.fossilWaterCap
            )
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)

        # storGroundwater, avgAbstraction and avgNonFossilAllocation cannot be negative
        self.storGroundwater = pcr.cover(self.storGroundwater, 0.0)
        self.storGroundwater = pcr.max(0.0, self.storGroundwater)
        self.storGroundwater = pcr.ifthen(self.landmask, self.storGroundwater)
        self.avgStorGroundwater = pcr.cover(self.avgStorGroundwater, 0.0)
        self.avgStorGroundwater = pcr.max(0.0, self.avgStorGroundwater)
        self.avgStorGroundwater = pcr.ifthen(self.landmask, self.avgStorGroundwater)
        self.avgAbstraction = pcr.cover(self.avgAbstraction, 0.0)
        self.avgAbstraction = pcr.max(0.0, self.avgAbstraction)
        self.avgAbstraction = pcr.ifthen(self.landmask, self.avgAbstraction)
        self.avgAllocation = pcr.cover(self.avgAllocation, 0.0)
        self.avgAllocation = pcr.max(0.0, self.avgAllocation)
        self.avgAllocation = pcr.ifthen(self.landmask, self.avgAllocation)
        self.avgAllocationShort = pcr.cover(self.avgAllocationShort, 0.0)
        self.avgAllocationShort = pcr.max(0.0, self.avgAllocationShort)
        self.avgAllocationShort = pcr.ifthen(self.landmask, self.avgAllocationShort)
        self.avgNonFossilAllocation = pcr.cover(self.avgNonFossilAllocation, 0.0)
        self.avgNonFossilAllocation = pcr.max(0.0, self.avgNonFossilAllocation)
        self.avgNonFossilAllocation = pcr.ifthen(
            self.landmask, self.avgNonFossilAllocation
        )
        self.avgNonFossilAllocationShort = pcr.cover(
            self.avgNonFossilAllocationShort, 0.0
        )
        self.avgNonFossilAllocationShort = pcr.max(
            0.0, self.avgNonFossilAllocationShort
        )
        self.avgNonFossilAllocationShort = pcr.ifthen(
            self.landmask, self.avgNonFossilAllocationShort
        )

        self.relativeGroundwaterHead = pcr.cover(self.relativeGroundwaterHead, 0.0)
        self.relativeGroundwaterHead = pcr.ifthen(
            self.landmask, self.relativeGroundwaterHead
        )

        self.baseflow = pcr.cover(self.baseflow, 0.0)
        self.baseflow = pcr.ifthen(self.landmask, self.baseflow)

        self.gwRecharge = pcr.ifthen(self.landmask, pcr.cover(self.gwRecharge, 0.0))

        # storGroundwaterFossil can be negative (particularly if limitFossilGroundwaterAbstraction is False)
        self.storGroundwaterFossil = pcr.cover(self.storGroundwaterFossil, 0.0)
        self.storGroundwaterFossil = pcr.ifthen(
            self.landmask, self.storGroundwaterFossil
        )
        pcr.report(self.storGroundwaterFossil, "initial_fossil_gw_water.map")

    def perturb(self, name, **parameters):

        if name == "groundwater":

            # factor to perturb the initial storGroundwater
            self.storGroundwater = self.storGroundwater * (
                mapnormal() * parameters["standard_deviation"] + 1
            )
            self.storGroundwater = pcr.max(0.0, self.storGroundwater)

        else:
            print("Error: only groundwater may be updated at this time")
            return -1

    def update(self, landSurface, routing, currTimeStep):

        if self.useMODFLOW:
            self.update_with_MODFLOW(landSurface, routing, currTimeStep)
        else:
            self.update_without_MODFLOW(landSurface, routing, currTimeStep)

        self.calculate_statistics(routing)

        self.gwRecharge = landSurface.gwRecharge

        # old-style reporting; TODO: remove
        self.old_style_groundwater_reporting(currTimeStep)

    def update_with_MODFLOW(self, landSurface, routing, currTimeStep):

        logger.info("Updating groundwater based on the MODFLOW output.")

        # relativeGroundwaterHead, storGroundwater and baseflow are assumed to be constant
        self.relativeGroundwaterHead = self.relativeGroundwaterHead
        self.storGroundwater = self.storGroundwater
        self.baseflow = self.baseflow

        if currTimeStep.day == 1 and currTimeStep.timeStepPCR > 1:

            # online coupling: read the PCRaster maps of the previous day
            directory = self.iniItems.main_output_directory + "/modflow/transient/maps/"
            yesterday = str(currTimeStep.yesterday())

            filename = directory + "relativeGroundwaterHead_" + str(yesterday) + ".map"
            self.relativeGroundwaterHead = pcr.ifthen(
                self.landmask,
                pcr.cover(
                    vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0
                ),
            )

            filename = directory + "storGroundwater_" + str(yesterday) + ".map"
            self.storGroundwater = pcr.ifthen(
                self.landmask,
                pcr.cover(
                    vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0
                ),
            )

            filename = directory + "baseflow_" + str(yesterday) + ".map"
            self.baseflow = pcr.ifthen(
                self.landmask,
                pcr.cover(
                    vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0
                ),
            )

        # river bed exchange is included in the baseflow (via the MODFLOW river and drain packages)
        self.surfaceWaterInf = pcr.scalar(0.0)

        self.nonFossilGroundwaterAbs = landSurface.nonFossilGroundwaterAbs

        # fossil groundwater abstraction (must be zero)
        self.fossilGroundwaterAbstr = landSurface.fossilGroundwaterAbstr

        # groundwater allocation (done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc = landSurface.fossilGroundwaterAlloc

        # groundwater allocation (done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc = landSurface.fossilGroundwaterAlloc

        # note: unmetDemand is a misnomer; it is the demand satisfied from fossil groundwater
        self.unmetDemand = self.fossilGroundwaterAlloc

    def update_without_MODFLOW(self, landSurface, routing, currTimeStep):

        logger.info("Updating groundwater")

        if self.debugWaterBalance:
            preStorGroundwater = self.storGroundwater
            preStorGroundwaterFossil = self.storGroundwaterFossil

        # riverbed infiltration from the previous time step (from routing) (m)
        self.surfaceWaterInf = routing.riverbedExchange / routing.cellArea
        self.storGroundwater += self.surfaceWaterInf

        # net recharge (percolation - capillary rise) and storage update
        self.storGroundwater = pcr.max(
            0.0, self.storGroundwater + landSurface.gwRecharge
        )

        self.nonFossilGroundwaterAbs = landSurface.nonFossilGroundwaterAbs
        self.storGroundwater = pcr.max(
            0.0, self.storGroundwater - self.nonFossilGroundwaterAbs
        )

        # baseflow (m/day): baseflow = (1/J)*<S3>*(S3/<S3>)^gamma
        baseflow = (
            self.recessionCoeff
            * self.avgStorGroundwater
            * (
                (vos.getValDivZero(self.storGroundwater, self.avgStorGroundwater))
                ** self.baseflow_exponent
            )
        )
        # use a linear reservoir if avgStorGroundwater < 5 mm
        baseflow = pcr.ifthenelse(
            self.avgStorGroundwater < 0.005,
            self.recessionCoeff * self.storGroundwater,
            baseflow,
        )
        # the minimum is the linear reservoir value
        min_baseflow = self.recessionCoeff * self.storGroundwater
        baseflow = pcr.max(min_baseflow, baseflow)
        # make sure baseflow is always positive
        self.baseflow = pcr.max(0.0, pcr.min(self.storGroundwater, baseflow))

        self.storGroundwater = pcr.max(0.0, self.storGroundwater - self.baseflow)
        # baseflow must be calculated last (so storGroundwater is available for nonFossilGroundwaterAbs)

        self.fossilGroundwaterAbstr = landSurface.fossilGroundwaterAbstr
        self.storGroundwaterFossil -= self.fossilGroundwaterAbstr

        # fossil groundwater cannot be negative if limitFossilGroundwaterAbstraction is used
        if self.limitFossilGroundwaterAbstraction:
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)

        # groundwater allocation (done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc = landSurface.fossilGroundwaterAlloc

        # note: unmetDemand is a misnomer; it is the demand satisfied from fossil groundwater
        self.unmetDemand = self.fossilGroundwaterAlloc

        # relative groundwater head above the minimum level (m), needed to estimate the areas with capillary rise
        self.relativeGroundwaterHead = self.storGroundwater / self.specificYield

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.surfaceWaterInf, landSurface.gwRecharge],
                [self.baseflow, self.nonFossilGroundwaterAbs],
                [preStorGroundwater],
                [self.storGroundwater],
                "storGroundwater",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [pcr.scalar(0.0)],
                [self.fossilGroundwaterAbstr],
                [preStorGroundwaterFossil],
                [self.storGroundwaterFossil],
                "storGroundwaterFossil",
                True,
                currTimeStep.fulldate,
                threshold=1e-3,
            )

    def calculate_statistics(self, routing):

        # average total groundwater abstraction (m/day) over the last 365 days
        totalAbstraction = self.fossilGroundwaterAbstr + self.nonFossilGroundwaterAbs
        deltaAbstraction = totalAbstraction - self.avgAbstraction
        self.avgAbstraction = self.avgAbstraction + deltaAbstraction / pcr.min(
            365.0, pcr.max(1.0, routing.timestepsToAvgDischarge)
        )
        self.avgAbstraction = pcr.max(0.0, self.avgAbstraction)

        # average non-fossil groundwater allocation (m/day) over the last 365 days
        deltaAllocation = self.allocNonFossilGroundwater - self.avgNonFossilAllocation
        self.avgNonFossilAllocation = (
            self.avgNonFossilAllocation
            + deltaAllocation
            / pcr.min(365.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgNonFossilAllocation = pcr.max(0.0, self.avgNonFossilAllocation)
        # over the last 7 days
        deltaAllocationShort = (
            self.allocNonFossilGroundwater - self.avgNonFossilAllocationShort
        )
        self.avgNonFossilAllocationShort = (
            self.avgNonFossilAllocationShort
            + deltaAllocationShort
            / pcr.min(7.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgNonFossilAllocationShort = pcr.max(
            0.0, self.avgNonFossilAllocationShort
        )

        # average total (fossil and non-fossil) groundwater allocation (m/day)
        totalGroundwaterAllocation = (
            self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
        )
        # over the last 365 days
        deltaAllocation = totalGroundwaterAllocation - self.avgAllocation
        self.avgAllocation = self.avgAllocation + deltaAllocation / pcr.min(
            365.0, pcr.max(1.0, routing.timestepsToAvgDischarge)
        )
        self.avgAllocation = pcr.max(0.0, self.avgAllocation)
        # over the last 7 days
        deltaAllocationShort = totalGroundwaterAllocation - self.avgAllocationShort
        self.avgAllocationShort = (
            self.avgAllocationShort
            + deltaAllocationShort
            / pcr.min(7.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgAllocationShort = pcr.max(0.0, self.avgAllocationShort)

        # average storGroundwater (S3, m) over the last 5 x 365 days
        deltaStorGroundwater = self.storGroundwater - self.avgStorGroundwater
        self.avgStorGroundwater = (
            self.avgStorGroundwater
            + deltaStorGroundwater
            / pcr.min(5.0 * 365.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgStorGroundwater = pcr.max(0.0, self.avgStorGroundwater)

    def old_style_groundwater_reporting(self, currTimeStep):

        if self.report == True:
            timeStamp = datetime.datetime(
                currTimeStep.year, currTimeStep.month, currTimeStep.day, 0
            )
            # daily netCDF output
            timestepPCR = currTimeStep.timeStepPCR
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.data2NetCDF(
                        str(self.outNCDir) + "/" + str(var) + "_dailyTot.nc",
                        var,
                        pcr2numpy(self.__getattribute__(var), vos.MV),
                        timeStamp,
                        timestepPCR - 1,
                    )

            # monthly netCDF output: totals
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:

                    # initialize at the start of the simulation or reset at the start of the month
                    if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
                        vars(self)[var + "MonthTot"] = pcr.scalar(0.0)

                    vars(self)[var + "MonthTot"] += vars(self)[var]

                    if currTimeStep.endMonth == True:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_monthTot.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var + "MonthTot"), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )
            # averages
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # only if no accumulator is defined
                    if var not in self.outMonthTotNC:

                        # initialize at the start of the simulation or reset at the start of the month
                        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
                            vars(self)[var + "MonthTot"] = pcr.scalar(0.0)
                        vars(self)[var + "MonthTot"] += vars(self)[var]

                    if currTimeStep.endMonth == True:
                        vars(self)[var + "MonthAvg"] = (
                            vars(self)[var + "MonthTot"] / currTimeStep.day
                        )
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_monthAvg.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var + "MonthAvg"), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )
            # end of month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    if currTimeStep.endMonth == True:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_monthEnd.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )

            # yearly netCDF output: totals
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:

                    # initialize at the start of the simulation or reset at the start of the year
                    if currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1:
                        vars(self)[var + "AnnuaTot"] = pcr.scalar(0.0)

                    vars(self)[var + "AnnuaTot"] += vars(self)[var]

                    if currTimeStep.endYear == True:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_annuaTot.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var + "AnnuaTot"), vos.MV),
                            timeStamp,
                            currTimeStep.annuaIdx - 1,
                        )
            # averages
            if self.outAnnuaAvgNC[0] != "None":
                for var in self.outAnnuaAvgNC:
                    # only if no accumulator is defined
                    if var not in self.outAnnuaTotNC:
                        # initialize at the start of the simulation or reset at the start of the year
                        if currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1:
                            vars(self)[var + "AnnuaTot"] = pcr.scalar(0.0)
                        vars(self)[var + "AnnuaTot"] += vars(self)[var]
                    if currTimeStep.endYear == True:
                        vars(self)[var + "AnnuaAvg"] = (
                            vars(self)[var + "AnnuaTot"] / currTimeStep.doy
                        )
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_annuaAvg.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var + "AnnuaAvg"), vos.MV),
                            timeStamp,
                            currTimeStep.annuaIdx - 1,
                        )
            # end of year
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                    if currTimeStep.endYear == True:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_annuaEnd.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var), vos.MV),
                            timeStamp,
                            currTimeStep.annuaIdx - 1,
                        )
