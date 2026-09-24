import logging

import pcraster as pcr

logger = logging.getLogger(__name__)


from pcrglobwb.common import virtualOS as vos
from pcrglobwb.ncConverter import *


class LandCover(object):

    def __init__(
        self,
        iniItems,
        nameOfSectionInIniFile,
        soil_and_topo_parameters,
        landmask,
        irrigationEfficiency=None,
        usingAllocSegments=False,
    ):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        # number of soil layers
        self.numberOfSoilLayers = int(
            iniItems.landSurfaceOptions["numberOfUpperSoilLayers"]
        )

        self.parameters = soil_and_topo_parameters

        # configuration of this land cover type
        self.iniItemsLC = iniItems.__getattribute__(nameOfSectionInIniFile)
        self.name = self.iniItemsLC["name"]

        self.includeIrrigation = False
        if iniItems.waterDemandOptions["includeIrrigation"] == "True":
            self.includeIrrigation = True

        # irrigation efficiency map (-)
        self.irrigationEfficiency = irrigationEfficiency

        # interception module type: "Original" (default) is principally as in van Beek et al. (2014);
        # "Modified" is Edwin Sutanudjaja's extension of the interception definition, using totalPotET
        # as the available energy
        self.interceptionModuleType = "Original"
        if "interceptionModuleType" in list(self.iniItemsLC.keys()):
            if self.iniItemsLC["interceptionModuleType"] == "Modified":
                msg = 'Using the "Modified" version of the interception module (i.e. extending interception definition, using totalPotET for the available energy for the interception process).'
                logger.info(msg)
                self.interceptionModuleType = "Modified"
            else:
                if self.iniItemsLC["interceptionModuleType"] != "Original":
                    msg = (
                        "The interceptionModuleType "
                        + self.iniItemsLC["interceptionModuleType"]
                        + " is NOT known."
                    )
                    logger.info(msg)
                msg = 'The "Original" interceptionModuleType is used.'
                logger.info(msg)

        # minimum interception capacity (only for the "Modified" interception module)
        self.minInterceptCap = 0.0
        if self.interceptionModuleType == "Original" and "minInterceptCap" in list(
            self.iniItemsLC.keys()
        ):
            msg = 'As the "Original" interceptionModuleType is used, the "minInterceptCap" value is ignored. The interception scope is only "canopy".'
            logger.warning(msg)
        if self.interceptionModuleType == "Modified":
            self.minInterceptCap = vos.readPCRmapClone(
                self.iniItemsLC["minInterceptCap"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

        # option to use surface water as the first priority water source (not used)
        self.surfaceWaterPiority = False

        # option to activate the water balance check
        self.debugWaterBalance = True
        if self.iniItemsLC["debugWaterBalance"] == "False":
            self.debugWaterBalance = False

        # improved Arno scheme: the "Original" work of van Beek et al. (2011) has no directRunoff reduction;
        # Rens van Beek introduced it later (20 April 2011) to maintain soil saturation; this is the
        # current "Default" method
        self.improvedArnoSchemeMethod = "Default"
        if "improvedArnoSchemeMethod" in list(iniItems.landSurfaceOptions.keys()):
            self.improvedArnoSchemeMethod = iniItems.landSurfaceOptions[
                "improvedArnoSchemeMethod"
            ]
            if self.improvedArnoSchemeMethod == "Original":
                logger.warning(
                    "Using the old/original approach of Improved Arno Scheme. No reduction for directRunoff."
                )

        # in Rens's original oldcalc script (2-layer model), the percolation percUpp (P1) can be negative;
        # Edwin changed a few lines to avoid this (see updateSoilStates)
        self.allowNegativePercolation = False
        if (
            "allowNegativePercolation" in list(self.iniItemsLC.keys())
            and self.iniItemsLC["allowNegativePercolation"] == "True"
        ):
            msg = "Allowing negative values of percolation percUpp (P1), as done in the oldcalc script of PCR-GLOBWB 1.0. \n"
            msg += (
                "Note that this option is only relevant for the two layer soil model."
            )
            logger.warning(msg)
            self.allowNegativePercolation = True

        # in Rens's original oldcalc script, roots/transpiration may only be defined in the bottom layer
        # without roots in the upper layer(s); Edwin changed a few lines to avoid this (see
        # scaleRootFractionsFromTwoLayerSoilParameters and estimateTranspirationAndBareSoilEvap)
        self.usingOriginalOldCalcRootTranspirationPartitioningMethod = False
        if (
            "usingOriginalOldCalcRootTranspirationPartitioningMethod"
            in list(self.iniItemsLC.keys())
            and self.iniItemsLC[
                "usingOriginalOldCalcRootTranspirationPartitioningMethod"
            ]
            == "True"
        ):
            msg = "Using the original rootFraction/transpiration as defined in the oldcalc script of PCR-GLOBWB 1.0. \n"
            msg += "There is a possibility that rootFraction/transpiration is only defined in the bottom layer, while no root in upper layer(s)."
            logger.warning(msg)
            self.usingOriginalOldCalcRootTranspirationPartitioningMethod = True

        # snow module type and parameters
        self.snowModuleType = self.iniItemsLC["snowModuleType"]
        snowParams = [
            "freezingT",
            "degreeDayFactor",
            "snowWaterHoldingCap",
            "refreezingCoeff",
        ]
        for var in snowParams:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(
                input, self.cloneMap, self.tmpDir, self.inputDir
            )
            vars(self)[var] = pcr.spatial(pcr.scalar(vars(self)[var]))

        self.cellArea = vos.readPCRmapClone(
            iniItems.routingOptions["cellAreaMap"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )
        # added by Joren
        self.snowTransport = False
        if (
            "snowTransport" in list(self.iniItemsLC.keys())
            and self.iniItemsLC["snowTransport"] != "None"
        ):
            self.snowTransport = self.iniItemsLC["snowTransport"]
            for var in ["Hv", "frho"]:
                input = self.iniItemsLC[str(var)]
                vars(self)[var] = vos.readPCRmapClone(
                    input, self.cloneMap, self.tmpDir, self.inputDir
                )
                vars(self)[var] = pcr.spatial(pcr.scalar(vars(self)[var]))

            self.reverseLDD = pcr.ldd(
                vos.readPCRmapClone(
                    iniItems.landSurfaceOptions["invertedDEM"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            )

            self.downstreamCells = pcr.upstream(self.reverseLDD, pcr.scalar(1.0))
            self.downstreamCells = pcr.ifthenelse(
                self.downstreamCells == 0, 1.0, self.downstreamCells
            )
            logger.info("Using FreyAndHolzmann Snow Transport to prevent snow towers")

        # area (m2) of this land cover type; assigned by the landSurface module
        self.fractionArea = None
        # fraction (-) of natural area over the cell; assigned by the landSurface module
        self.naturalFracVegCover = None
        # fraction of this irrigation type over the total irrigation area; assigned by the landSurface module
        self.irrTypeFracOverIrr = None

        # previous land cover fractions (needed to transfer states when the fractions change annually)
        self.previousFracVegCover = None

        # number of soil layers (two or three)
        self.numberOfLayers = self.parameters.numberOfLayers

        # option to change the land cover parameters (not only fracVegCover)
        self.noAnnualChangesInLandCoverParameter = True
        if "annualChangesInLandCoverParameters" in list(
            iniItems.landSurfaceOptions.keys()
        ):
            if (
                iniItems.landSurfaceOptions["annualChangesInLandCoverParameters"]
                == "True"
            ):
                self.noAnnualChangesInLandCoverParameter = False

        # land cover parameters that are fixed for the entire simulation
        if self.noAnnualChangesInLandCoverParameter:
            if self.numberOfLayers == 2:
                (
                    self.fracVegCover,
                    self.arnoBeta,
                    self.rootZoneWaterStorageMin,
                    self.rootZoneWaterStorageRange,
                    self.maxRootDepth,
                    self.adjRootFrUpp,
                    self.adjRootFrLow,
                ) = self.get_land_cover_parameters()
            if self.numberOfLayers == 3:
                (
                    self.fracVegCover,
                    self.arnoBeta,
                    self.rootZoneWaterStorageMin,
                    self.rootZoneWaterStorageRange,
                    self.maxRootDepth,
                    self.adjRootFrUpp000005,
                    self.adjRootFrUpp005030,
                    self.adjRootFrLow030150,
                ) = self.get_land_cover_parameters()
            # parameters at which transpiration is halved
            self.calculateParametersAtHalfTranspiration()

        # additional land cover parameters (always fixed for the entire simulation)
        landCovParamsAdd = ["minTopWaterLayer", "minCropKC"]
        for var in landCovParamsAdd:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(
                input, self.cloneMap, self.tmpDir, self.inputDir
            )
            if input != "None":
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        # additional parameters for irrigation areas (always fixed): cropDeplFactor (-), the crop
        # depletion factor during irrigation, needed for non-paddy irrigation areas
        if self.iniItemsLC["name"].startswith("irr") and self.name != "irrPaddy":
            self.cropDeplFactor = vos.readPCRmapClone(
                self.iniItemsLC["cropDeplFactor"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        # infiltration/percolation losses of paddy fields
        if self.name == "irrPaddy" or self.name == "irr_paddy":
            self.design_percolation_loss = self.estimate_paddy_infiltration_loss(
                self.iniItemsLC
            )

        # crop coefficient files
        self.cropCoefficientNC = vos.getFullPath(
            self.iniItemsLC["cropCoefficientNC"], self.inputDir
        )

        # interception capacity and cover fraction files
        if "interceptCapNC" in list(
            self.iniItemsLC.keys()
        ) and "coverFractionNC" in list(self.iniItemsLC.keys()):
            self.interceptCapNC = vos.getFullPath(
                self.iniItemsLC["interceptCapNC"], self.inputDir
            )
            self.coverFractionNC = vos.getFullPath(
                self.iniItemsLC["coverFractionNC"], self.inputDir
            )
        else:
            msg = (
                "The netcdf files for interceptCapNC (interception capacity) and/or coverFraction (canopy cover fraction) are NOT defined for the landCover type: "
                + self.name
                + "\n"
            )
            msg = (
                "This run assumes zero canopy interception capacity for this run, UNLESS minInterceptCap (minimum interception capacity) is bigger than zero."
                + "\n"
            )
            logger.warning(msg)
            self.coverFractionNC = None
            self.interceptCapNC = None

        if (
            "coverFractionNC" in list(self.iniItemsLC.keys())
            and self.iniItemsLC["coverFractionNC"] == "None"
        ):
            self.coverFractionNC = None
        if (
            "interceptCapNC" in list(self.iniItemsLC.keys())
            and self.iniItemsLC["interceptCapNC"] == "None"
        ):
            self.interceptCapNC = None

        # netCDF output
        self.report = True
        try:
            self.outDailyTotNC = self.iniItemsLC["outDailyTotNC"].split(",")
            self.outMonthTotNC = self.iniItemsLC["outMonthTotNC"].split(",")
            self.outMonthAvgNC = self.iniItemsLC["outMonthAvgNC"].split(",")
            self.outMonthEndNC = self.iniItemsLC["outMonthEndNC"].split(",")
        except Exception:
            self.report = False
        if self.report:
            self.outNCDir = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            # prepare the netCDF objects and files
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir)
                        + "/"
                        + str(var)
                        + "_"
                        + str(self.iniItemsLC["name"])
                        + "_"
                        + "dailyTot.nc",
                        var,
                        "undefined",
                    )

            # monthly netCDF output: totals
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # accumulator
                    vars(self)[var + "Tot"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir)
                        + "/"
                        + str(var)
                        + "_"
                        + str(self.iniItemsLC["name"])
                        + "_"
                        + "monthTot.nc",
                        var,
                        "undefined",
                    )
            # averages
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    vars(self)[var + "Avg"] = None
                    # accumulator
                    vars(self)[var + "Tot"] = None
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir)
                        + "/"
                        + str(var)
                        + "_"
                        + str(self.iniItemsLC["name"])
                        + "_"
                        + "monthAvg.nc",
                        var,
                        "undefined",
                    )
            # end of month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    self.netcdfObj.createNetCDF(
                        str(self.outNCDir)
                        + "/"
                        + str(var)
                        + "_"
                        + str(self.iniItemsLC["name"])
                        + "_"
                        + "monthEnd.nc",
                        var,
                        "undefined",
                    )

    def get_land_cover_parameters(
        self, date_in_string=None, get_only_fracVegCover=False
    ):

        # land cover parameters to read

        landCovParams = [
            "minSoilDepthFrac",
            "maxSoilDepthFrac",
            "rootFraction1",
            "rootFraction2",
            "maxRootDepth",
            "fracVegCover",
        ]
        # and arnoBeta

        # option to only return fracVegCover
        if get_only_fracVegCover:
            landCovParams = ["fracVegCover"]

        # initial values: None
        lc_parameters = {}
        if not get_only_fracVegCover:
            for var in landCovParams + ["arnoBeta"]:
                lc_parameters[var] = None

        # parameters that are fixed for the entire simulation
        if date_in_string is None:

            msg = "Obtaining the land cover parameters that are fixed for the entire simulation."
            logger.debug(msg)

            if self.iniItemsLC["landCoverMapsNC"] == str(None):
                # PCRaster maps
                landCoverPropertiesNC = None
                for var in landCovParams:
                    input = self.iniItemsLC[str(var)]
                    lc_parameters[var] = vos.readPCRmapClone(
                        input, self.cloneMap, self.tmpDir, self.inputDir
                    )
                    if input != "None":
                        lc_parameters[var] = pcr.cover(lc_parameters[var], 0.0)
            else:
                # netCDF file
                landCoverPropertiesNC = vos.getFullPath(
                    self.iniItemsLC["landCoverMapsNC"], self.inputDir
                )
                for var in landCovParams:
                    lc_parameters[var] = pcr.cover(
                        vos.netcdf2PCRobjCloneWithoutTime(
                            landCoverPropertiesNC, var, cloneMapFileName=self.cloneMap
                        ),
                        0.0,
                    )

            # arnoBeta of the improved Arno scheme can be defined in three ways, in order of priority:
            # 1. a PCRaster map or uniform scalar value (self.iniItemsLC['arnoBeta']),
            # 2. in the netCDF file (self.iniItemsLC['landCoverMapsNC']),
            # 3. approximated from minSoilDepthFrac and maxSoilDepthFrac

            lc_parameters["arnoBeta"] = None
            if (
                "arnoBeta" not in list(self.iniItemsLC.keys())
                and not get_only_fracVegCover
            ):
                self.iniItemsLC["arnoBeta"] = "None"

            # option 1 (top priority): a PCRaster file
            if self.iniItemsLC["arnoBeta"] != "None" and not get_only_fracVegCover:

                logger.debug(
                    "The parameter arnoBeta: " + str(self.iniItemsLC["arnoBeta"])
                )
                lc_parameters["arnoBeta"] = vos.readPCRmapClone(
                    self.iniItemsLC["arnoBeta"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

            # option 2: in the netCDF file
            if (
                lc_parameters["arnoBeta"] is None
                and landCoverPropertiesNC is not None
                and not get_only_fracVegCover
            ):

                if vos.checkVariableInNC(landCoverPropertiesNC, "arnoBeta"):

                    logger.debug(
                        "The parameter arnoBeta is defined in the netcdf file "
                        + str(self.iniItemsLC["arnoBeta"])
                    )
                    lc_parameters["arnoBeta"] = vos.netcdf2PCRobjCloneWithoutTime(
                        landCoverPropertiesNC, "arnoBeta", self.cloneMap
                    )

            # option 3: approximated from minSoilDepthFrac and maxSoilDepthFrac
            if lc_parameters["arnoBeta"] is None and not get_only_fracVegCover:

                logger.debug(
                    "The parameter arnoBeta is approximated from the minSoilDepthFrac and maxSoilDepthFrac values."
                )

                # make sure maxSoilDepthFrac >= minSoilDepthFrac; maxSoilDepthFrac is only needed for arnoBeta,
                # minSoilDepthFrac also for rootZoneWaterStorageMin
                lc_parameters["maxSoilDepthFrac"] = pcr.max(
                    lc_parameters["maxSoilDepthFrac"], lc_parameters["minSoilDepthFrac"]
                )

                # estimate arnoBeta from maxSoilDepthFrac and minSoilDepthFrac;
                # Rens: BCF[TYPE]= max(0.001,(MAXFRAC[TYPE]-1)/(1-MINFRAC[TYPE])+B_ORO-0.01)
                lc_parameters["arnoBeta"] = pcr.max(
                    0.001,
                    (lc_parameters["maxSoilDepthFrac"] - 1.0)
                    / (1.0 - lc_parameters["minSoilDepthFrac"])
                    + self.parameters.orographyBeta
                    - 0.01,
                )

        # land cover parameters that change annually (netCDF files)
        if date_in_string is not None:

            msg = (
                "Obtaining the land cover parameters (from netcdf files) for the year/date: "
                + str(date_in_string)
            )
            logger.debug(msg)

            if get_only_fracVegCover:
                landCovParams = ["fracVegCover"]
            else:
                landCovParams += ["arnoBeta"]

            for var in landCovParams:

                # read the parameter from the netCDF file in the ini file
                ini_option = self.iniItemsLC[var + "NC"]

                if ini_option.endswith(vos.netcdf_suffixes):
                    netcdf_file = vos.getFullPath(ini_option, self.inputDir)
                    lc_parameters[var] = pcr.cover(
                        vos.netcdf2PCRobjClone(
                            netcdf_file,
                            var,
                            date_in_string,
                            useDoy="yearly",
                            cloneMapFileName=self.cloneMap,
                        ),
                        0.0,
                    )
                else:
                    # read the parameter from PCRaster maps or scalar values
                    try:
                        lc_parameters[var] = pcr.cover(
                            pcr.spatial(
                                vos.readPCRmapClone(
                                    ini_option,
                                    self.cloneMap,
                                    self.tmpDir,
                                    self.inputDir,
                                )
                            ),
                            0.0,
                        )
                    except Exception:
                        lc_parameters[var] = vos.readPCRmapClone(
                            ini_option, self.cloneMap, self.tmpDir, self.inputDir
                        )

            # if not defined, approximate arnoBeta from minSoilDepthFrac and maxSoilDepthFrac
            if not get_only_fracVegCover and lc_parameters["arnoBeta"] is None:

                logger.debug(
                    "The parameter arnoBeta is approximated from the minSoilDepthFrac and maxSoilDepthFrac values."
                )

                # make sure maxSoilDepthFrac >= minSoilDepthFrac; maxSoilDepthFrac is only needed for arnoBeta,
                # minSoilDepthFrac also for rootZoneWaterStorageMin
                lc_parameters["maxSoilDepthFrac"] = pcr.max(
                    lc_parameters["maxSoilDepthFrac"], lc_parameters["minSoilDepthFrac"]
                )

                # estimate arnoBeta from maxSoilDepthFrac and minSoilDepthFrac;
                # Rens: BCF[TYPE]= max(0.001,(MAXFRAC[TYPE]-1)/(1-MINFRAC[TYPE])+B_ORO-0.01)
                lc_parameters["arnoBeta"] = pcr.max(
                    0.001,
                    (lc_parameters["maxSoilDepthFrac"] - 1.0)
                    / (1.0 - lc_parameters["minSoilDepthFrac"])
                    + self.parameters.orographyBeta
                    - 0.01,
                )

        # limit fracVegCover to 0-1
        fracVegCover = pcr.cover(lc_parameters["fracVegCover"], 0.0)
        fracVegCover = pcr.max(0.0, fracVegCover)
        fracVegCover = pcr.min(1.0, fracVegCover)

        if get_only_fracVegCover:
            return pcr.ifthen(self.landmask, fracVegCover)

        # WMIN (m): minimum local soil water capacity within the cell (WMIN in the oldcalc script)
        rootZoneWaterStorageMin = (
            lc_parameters["minSoilDepthFrac"] * self.parameters.rootZoneWaterStorageCap
        )

        # WMAX - WMIN (m)
        rootZoneWaterStorageRange = (
            self.parameters.rootZoneWaterStorageCap - rootZoneWaterStorageMin
        )

        # arnoBeta (-)
        arnoBeta = pcr.max(0.001, lc_parameters["arnoBeta"])
        arnoBeta = pcr.cover(arnoBeta, 0.001)

        # maximum root depth
        maxRootDepth = lc_parameters["maxRootDepth"]

        # minSoilDepthFrac and maxSoilDepthFrac (only for debugging)
        self.minSoilDepthFrac = lc_parameters["minSoilDepthFrac"]
        self.maxSoilDepthFrac = lc_parameters["maxSoilDepthFrac"]

        # rootFraction1 and rootFraction2 (only for debugging)
        self.rootFraction1 = lc_parameters["rootFraction1"]
        self.rootFraction2 = lc_parameters["rootFraction2"]

        if self.numberOfLayers == 2 and not get_only_fracVegCover:

            # scale the root fractions
            adjRootFrUpp, adjRootFrLow = (
                self.scaleRootFractionsFromTwoLayerSoilParameters(
                    lc_parameters["rootFraction1"], lc_parameters["rootFraction2"]
                )
            )

            return (
                pcr.ifthen(self.landmask, fracVegCover),
                pcr.ifthen(self.landmask, arnoBeta),
                pcr.ifthen(self.landmask, rootZoneWaterStorageMin),
                pcr.ifthen(self.landmask, rootZoneWaterStorageRange),
                pcr.ifthen(self.landmask, maxRootDepth),
                pcr.ifthen(self.landmask, adjRootFrUpp),
                pcr.ifthen(self.landmask, adjRootFrLow),
            )
        if self.numberOfLayers == 3 and not get_only_fracVegCover:

            # scale the root fractions
            adjRootFrUpp000005, adjRootFrUpp005030, adjRootFrLow030150 = (
                self.scaleRootFractionsFromTwoLayerSoilParameters(
                    lc_parameters["rootFraction1"], lc_parameters["rootFraction2"]
                )
            )

            return (
                pcr.ifthen(self.landmask, fracVegCover),
                pcr.ifthen(self.landmask, arnoBeta),
                pcr.ifthen(self.landmask, rootZoneWaterStorageMin),
                pcr.ifthen(self.landmask, rootZoneWaterStorageRange),
                pcr.ifthen(self.landmask, maxRootDepth),
                pcr.ifthen(self.landmask, adjRootFrUpp000005),
                pcr.ifthen(self.landmask, adjRootFrUpp005030),
                pcr.ifthen(self.landmask, adjRootFrLow030150),
            )

    def estimate_paddy_infiltration_loss(self, iniPaddyOptions):

        # due to compaction, the infiltration/percolation loss rate can be much smaller than the saturated
        # conductivity; Wada et al. (2014) assume a factor 10
        if self.numberOfLayers == 2:
            # (m/day)
            design_percolation_loss = self.parameters.kSatUpp / 10.0
        if self.numberOfLayers == 3:
            # (m/day)
            design_percolation_loss = self.parameters.kSatUpp000005 / 10.0

        # it can be even smaller in well-puddled paddy fields, which avoids salinization; default minimum
        # and maximum percolation loss are FAO values (http://www.fao.org/docrep/s2022e/s2022e08.htm)
        min_percolation_loss = 0.006
        max_percolation_loss = 0.008
        # minimum and maximum percolation loss from the ini file
        if (
            "minPercolationLoss" in list(iniPaddyOptions.keys())
            and iniPaddyOptions["minPercolationLoss"] != "None"
        ):
            min_percolation_loss = vos.readPCRmapClone(
                iniPaddyOptions["minPercolationLoss"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        if (
            "maxPercolationLoss" in list(iniPaddyOptions.keys())
            and iniPaddyOptions["maxPercolationLoss"] != "None"
        ):
            min_percolation_loss = vos.readPCRmapClone(
                iniPaddyOptions["maxPercolationLoss"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        # percolation loss in paddy fields (m/day)
        design_percolation_loss = pcr.max(
            min_percolation_loss, pcr.min(max_percolation_loss, design_percolation_loss)
        )
        # if the soil is already 'good', use its original infiltration/percolation rate
        if self.numberOfLayers == 2:
            design_percolation_loss = pcr.min(
                self.parameters.kSatUpp, design_percolation_loss
            )
        if self.numberOfLayers == 3:
            design_percolation_loss = pcr.min(
                self.parameters.kSatUpp000005, design_percolation_loss
            )

        # design_percolation_loss is the maximum loss in paddy fields
        return design_percolation_loss

    def scaleRootFractionsFromTwoLayerSoilParameters(
        self, rootFraction1, rootFraction2
    ):

        # cover rootFraction1 and rootFraction2
        rootFraction1 = pcr.cover(rootFraction1, 0.0)
        rootFraction2 = pcr.cover(rootFraction2, 0.0)

        if self.numberOfLayers == 2:
            # root fractions
            rootFracUpp = (0.30 / 0.30) * rootFraction1
            rootFracLow = (1.20 / 1.20) * rootFraction2
            # Rens: RFW1[TYPE]= RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])
            adjRootFrUpp = vos.getValDivZero(rootFracUpp, (rootFracUpp + rootFracLow))
            # Rens: RFW2[TYPE]= RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])
            adjRootFrLow = vos.getValDivZero(rootFracLow, (rootFracUpp + rootFracLow))
            # if not defined, put everything in the first layer
            if not self.usingOriginalOldCalcRootTranspirationPartitioningMethod:
                adjRootFrUpp = pcr.max(0.0, pcr.min(1.0, pcr.cover(adjRootFrUpp, 1.0)))
                adjRootFrLow = pcr.max(0.0, pcr.scalar(1.0) - adjRootFrUpp)

            return adjRootFrUpp, adjRootFrLow

        if self.numberOfLayers == 3:
            # root fractions
            rootFracUpp000005 = 0.05 / 0.30 * rootFraction1
            rootFracUpp005030 = 0.25 / 0.30 * rootFraction1
            rootFracLow030150 = 1.20 / 1.20 * rootFraction2
            adjRootFrUpp000005 = vos.getValDivZero(
                rootFracUpp000005,
                (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
            )
            adjRootFrUpp005030 = vos.getValDivZero(
                rootFracUpp005030,
                (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
            )
            adjRootFrLow030150 = vos.getValDivZero(
                rootFracLow030150,
                (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
            )
            # if not defined, put everything in the first layer
            if not self.usingOriginalOldCalcRootTranspirationPartitioningMethod:
                adjRootFrUpp000005 = pcr.max(
                    0.0, pcr.min(1.0, pcr.cover(adjRootFrUpp000005, 1.0))
                )
                adjRootFrUpp005030 = pcr.max(
                    0.0,
                    pcr.ifthenelse(
                        adjRootFrUpp000005 < 1.0,
                        pcr.min(
                            adjRootFrUpp005030, pcr.scalar(1.0) - adjRootFrUpp000005
                        ),
                        0.0,
                    ),
                )
                adjRootFrLow030150 = pcr.max(
                    0.0, pcr.scalar(1.0) - (adjRootFrUpp000005 + adjRootFrUpp005030)
                )

            return adjRootFrUpp000005, adjRootFrUpp005030, adjRootFrLow030150

    def calculateParametersAtHalfTranspiration(self):

        # average soil parameters at which actual transpiration is halved

        if self.numberOfLayers == 2:

            # Rens (version 1.1): THEFF_50[TYPE]= (SC1[TYPE]*RFW1[TYPE]*(PSI_50/PSI_A1[TYPE])**(-1/BCH1[TYPE]) + SC2[TYPE]*RFW2[TYPE]*(PSI_50/PSI_A2[TYPE])**(-1/BCH2[TYPE])) / (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE])
            # Rens (version 1.2): THEFF_50[TYPE]= if(RFW1[TYPE]+RFW2[TYPE] > 0, (SC1[TYPE]*RFW1[TYPE]*(PSI_50/PSI_A1[TYPE])**(-1/BCH1[TYPE])+ SC2[TYPE]*RFW2[TYPE]*(PSI_50/PSI_A2[TYPE])**(-1/BCH2[TYPE]))/ (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]),0.5)

            # Rens (version 1.1): BCH_50 = (SC1[TYPE]*RFW1[TYPE]*BCH1[TYPE]+SC2[TYPE]*RFW2[TYPE]*BCH2[TYPE])/(SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE])
            # Rens (version 1.1): BCH_50= if(RFW1[TYPE]+RFW2[TYPE] > 0,(SC1[TYPE]*RFW1[TYPE]*BCH1[TYPE]+SC2[TYPE]*RFW2[TYPE]*BCH2[TYPE])/(SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]),0.5*(BCH1[TYPE]+BCH2[TYPE]))

            denominator = (
                self.parameters.storCapUpp * self.adjRootFrUpp
                + self.parameters.storCapLow * self.adjRootFrLow
            )

            self.effSatAt50 = pcr.ifthenelse(
                denominator > 0.0,
                (
                    self.parameters.storCapUpp
                    * self.adjRootFrUpp
                    * (
                        self.parameters.matricSuction50
                        / self.parameters.airEntryValueUpp
                    )
                    ** (-1.0 / self.parameters.poreSizeBetaUpp)
                    + self.parameters.storCapLow
                    * self.adjRootFrLow
                    * (
                        self.parameters.matricSuction50
                        / self.parameters.airEntryValueLow
                    )
                    ** (-1.0 / self.parameters.poreSizeBetaLow)
                )
                / (
                    self.parameters.storCapUpp * self.adjRootFrUpp
                    + self.parameters.storCapLow * self.adjRootFrLow
                ),
                0.5,
            )

            self.effPoreSizeBetaAt50 = pcr.ifthenelse(
                denominator > 0.0,
                (
                    self.parameters.storCapUpp
                    * self.adjRootFrUpp
                    * self.parameters.poreSizeBetaUpp
                    + self.parameters.storCapLow
                    * self.adjRootFrLow
                    * self.parameters.poreSizeBetaLow
                )
                / (
                    (
                        self.parameters.storCapUpp * self.adjRootFrUpp
                        + self.parameters.storCapLow * self.adjRootFrLow
                    )
                ),
                0.5
                * (self.parameters.poreSizeBetaUpp + self.parameters.poreSizeBetaLow),
            )

        if self.numberOfLayers == 3:

            denominator = (
                self.parameters.storCapUpp000005 * self.adjRootFrUpp000005
                + self.parameters.storCapUpp005030 * self.adjRootFrUpp005030
                + self.parameters.storCapLow030150 * self.adjRootFrLow030150
            )

            self.effSatAt50 = pcr.ifthenelse(
                denominator > 0.0,
                (
                    self.parameters.storCapUpp000005
                    * self.adjRootFrUpp000005
                    * (
                        self.parameters.matricSuction50
                        / self.parameters.airEntryValueUpp000005
                    )
                    ** (-1.0 / self.parameters.poreSizeBetaUpp000005)
                    + self.parameters.storCapUpp005030
                    * self.adjRootFrUpp005030
                    * (
                        self.parameters.matricSuction50
                        / self.parameters.airEntryValueUpp000005
                    )
                    ** (-1.0 / self.parameters.poreSizeBetaUpp000005)
                    + self.parameters.storCapLow030150
                    * self.adjRootFrLow030150
                    * (
                        self.parameters.matricSuction50
                        / self.parameters.airEntryValueLow030150
                    )
                    ** (-1.0 / self.parameters.poreSizeBetaLow030150)
                    / (
                        self.parameters.storCapUpp000005 * self.adjRootFrUpp000005
                        + self.parameters.storCapUpp005030 * self.adjRootFrUpp005030
                        + self.parameters.storCapLow030150 * self.adjRootFrLow030150
                    )
                ),
                0.5,
            )

            self.effPoreSizeBetaAt50 = pcr.ifthenelse(
                denominator > 0.0,
                (
                    self.parameters.storCapUpp000005
                    * self.adjRootFrUpp000005
                    * self.parameters.poreSizeBetaUpp000005
                    + self.parameters.storCapUpp005030
                    * self.adjRootFrUpp005030
                    * self.parameters.poreSizeBetaUpp005030
                    + self.parameters.storCapLow030150
                    * self.adjRootFrLow030150
                    * self.parameters.poreSizeBetaLow030150
                )
                / (
                    self.parameters.storCapUpp000005 * self.adjRootFrUpp000005
                    + self.parameters.storCapUpp005030 * self.adjRootFrUpp005030
                    + self.parameters.storCapLow030150 * self.adjRootFrLow030150
                ),
                0.5
                * (
                    0.5
                    * (
                        self.parameters.poreSizeBetaUpp000005
                        + self.parameters.poreSizeBetaUpp005030
                    )
                    + self.parameters.poreSizeBetaLow030150
                ),
            )

        # these items may not be needed
        self.effSatAt50 = pcr.cover(self.effSatAt50, 0.5)
        if self.numberOfLayers == 2:
            self.effPoreSizeBetaAt50 = pcr.cover(
                self.effPoreSizeBetaAt50,
                0.5
                * (self.parameters.poreSizeBetaUpp + self.parameters.poreSizeBetaLow),
            )
        if self.numberOfLayers == 3:
            self.effPoreSizeBetaAt50 = pcr.cover(
                self.effPoreSizeBetaAt50,
                0.5
                * (
                    0.5
                    * (
                        self.parameters.poreSizeBetaUpp000005
                        + self.parameters.poreSizeBetaUpp005030
                    )
                    + self.parameters.poreSizeBetaLow030150
                ),
            )

        # crop to the landmask
        self.effSatAt50 = pcr.ifthen(self.landmask, self.effSatAt50)
        self.effPoreSizeBetaAt50 = pcr.ifthen(self.landmask, self.effPoreSizeBetaAt50)

    def getICsLC(self, iniItems, iniConditions=None):

        if self.numberOfLayers == 2:

            # state and flux variables
            initialVars = [
                "interceptStor",
                "snowCoverSWE",
                "snowFreeWater",
                "topWaterLayer",
                "storUpp",
                "storLow",
                "interflow",
            ]
            for var in initialVars:
                if iniConditions is None:
                    input = self.iniItemsLC[str(var) + "Ini"]
                    vars(self)[var] = vos.readPCRmapClone(
                        input, self.cloneMap, self.tmpDir, self.inputDir
                    )
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask, vars(self)[var])

        if self.numberOfLayers == 3:

            # state and flux variables
            initialVars = [
                "interceptStor",
                "snowCoverSWE",
                "snowFreeWater",
                "topWaterLayer",
                "storUpp000005",
                "storUpp005030",
                "storLow030150",
                "interflow",
            ]
            for var in initialVars:
                if iniConditions is None:
                    input = self.iniItemsLC[str(var) + "Ini"]
                    vars(self)[var] = vos.readPCRmapClone(
                        input, self.cloneMap, self.tmpDir, self.inputDir, cover=0.0
                    )
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask, vars(self)[var])

    def set_land_cover_parameters(self, currTimeStep):

        # land cover parameters on the first day of the year or of the simulation
        if not self.noAnnualChangesInLandCoverParameter and (
            currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1
        ):
            if self.numberOfLayers == 2:
                (
                    self.fracVegCover,
                    self.arnoBeta,
                    self.rootZoneWaterStorageMin,
                    self.rootZoneWaterStorageRange,
                    self.maxRootDepth,
                    self.adjRootFrUpp,
                    self.adjRootFrLow,
                ) = self.get_land_cover_parameters(currTimeStep.fulldate)
            if self.numberOfLayers == 3:
                (
                    self.fracVegCover,
                    self.arnoBeta,
                    self.rootZoneWaterStorageMin,
                    self.rootZoneWaterStorageRange,
                    self.maxRootDepth,
                    self.adjRootFrUpp000005,
                    self.adjRootFrUpp005030,
                    self.adjRootFrLow030150,
                ) = self.get_land_cover_parameters(currTimeStep.fulldate)

            # parameters at which transpiration is halved (sets effSatAt50 and effPoreSizeBetaAt50)
            self.calculateParametersAtHalfTranspiration()

        # crop coefficient
        if self.iniItemsLC["cropCoefficientNC"] == "None":
            cropKC = pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0.0)))
        else:
            cropKC = pcr.cover(
                vos.netcdf2PCRobjClone(
                    self.cropCoefficientNC,
                    "kc",
                    currTimeStep.fulldate,
                    useDoy="daily_seasonal",
                    cloneMapFileName=self.cloneMap,
                ),
                0.0,
            )
        self.inputCropKC = (
            # needed for debugging; TODO: check whether this can be removed
            cropKC
        )
        self.cropKC = pcr.max(cropKC, self.minCropKC)

        # interception capacity and cover fraction
        interceptCap = pcr.scalar(self.minInterceptCap)
        coverFraction = pcr.scalar(1.0)
        if self.interceptCapNC is not None and self.coverFractionNC is not None:
            interceptCap = pcr.cover(
                vos.netcdf2PCRobjClone(
                    self.interceptCapNC,
                    "interceptCapInput",
                    currTimeStep.fulldate,
                    useDoy="daily_seasonal",
                    cloneMapFileName=self.cloneMap,
                ),
                0.0,
            )
            # needed for debugging
            self.interceptCapInput = interceptCap
            coverFraction = pcr.cover(
                vos.netcdf2PCRobjClone(
                    self.coverFractionNC,
                    "coverFractionInput",
                    currTimeStep.fulldate,
                    useDoy="daily_seasonal",
                    cloneMapFileName=self.cloneMap,
                ),
                0.0,
            )
            coverFraction = pcr.cover(coverFraction, 0.0)
            # Rens: ICC[TYPE] = CFRAC[TYPE]*INTCMAX[TYPE]
            interceptCap = coverFraction * interceptCap
        # canopy/cover fraction over the cell
        self.coverFraction = coverFraction
        # interception capacity (Edwin: extended interception definition)
        self.interceptCap = pcr.max(interceptCap, self.minInterceptCap)

        # note: some other land cover parameters (e.g. snow module parameters) are set in __init__ and are constant during the simulation

    def land_surface_hydrology_update_for_every_lc(
        self,
        capRiseFrac,
        currTimeStep,
        groundwater,
        satisfied_irrigation_water_height=0.0,
        reducedCapRise=0.0,
    ):

        # reduced capillary rise (e.g. due to non-fossil groundwater abstraction)
        self.reducedCapRise = reducedCapRise

        # qDR, qSF and q23 (and update the storages)
        self.upperSoilUpdate(
            capRiseFrac, currTimeStep, satisfied_irrigation_water_height, groundwater
        )

        # degrees of saturation (only needed for reporting)
        if self.numberOfSoilLayers == 2:
            self.satDegUpp = vos.getValDivZero(
                self.storUpp, self.parameters.storCapUpp, vos.smallNumber, 0.0
            )
            self.satDegUpp = pcr.ifthen(self.landmask, self.satDegUpp)
            self.satDegLow = vos.getValDivZero(
                self.storLow, self.parameters.storCapLow, vos.smallNumber, 0.0
            )
            self.satDegLow = pcr.ifthen(self.landmask, self.satDegLow)

            self.satDegUppTotal = self.satDegUpp
            self.satDegLowTotal = self.satDegLow

            self.satDegTotal = pcr.ifthen(
                self.landmask,
                vos.getValDivZero(
                    self.storUpp + self.storLow,
                    self.parameters.storCapUpp + self.parameters.storCapLow,
                    vos.smallNumber,
                    0.0,
                ),
            )

        if self.numberOfSoilLayers == 3:
            self.satDegUpp000005 = vos.getValDivZero(
                self.storUpp000005,
                self.parameters.storCapUpp000005,
                vos.smallNumber,
                0.0,
            )
            self.satDegUpp000005 = pcr.ifthen(self.landmask, self.satDegUpp000005)
            self.satDegUpp005030 = vos.getValDivZero(
                self.storUpp005030,
                self.parameters.storCapUpp005030,
                vos.smallNumber,
                0.0,
            )
            self.satDegUpp005030 = pcr.ifthen(self.landmask, self.satDegUpp005030)
            self.satDegLow030150 = vos.getValDivZero(
                self.storLow030150,
                self.parameters.storCapLow030150,
                vos.smallNumber,
                0.0,
            )
            self.satDegLow030150 = pcr.ifthen(self.landmask, self.satDegLow030150)

            self.satDegUppTotal = vos.getValDivZero(
                self.storUpp000005 + self.storUpp005030,
                self.parameters.storCapUpp000005 + self.parameters.storCapUpp005030,
                vos.smallNumber,
                0.0,
            )
            self.satDegUppTotal = pcr.ifthen(self.landmask, self.satDegUppTotal)
            self.satDegLowTotal = self.satDegLow030150

            self.satDegTotal = pcr.ifthen(
                self.landmask,
                vos.getValDivZero(
                    self.storUpp000005 + self.storUpp005030 + self.satDegLow030150,
                    self.parameters.storCapUpp000005
                    + self.parameters.storCapUpp005030
                    + self.parameters.storCapLow030150,
                    vos.smallNumber,
                    0.0,
                ),
            )

        if self.report:
            # netCDF output: daily
            timeStamp = datetime.datetime(
                currTimeStep.year, currTimeStep.month, currTimeStep.day, 0
            )
            timestepPCR = currTimeStep.timeStepPCR
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.data2NetCDF(
                        str(self.outNCDir)
                        + str(var)
                        + "_"
                        + str(self.iniItemsLC["name"])
                        + "_"
                        + "dailyTot.nc",
                        var,
                        pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                        timeStamp,
                        timestepPCR - 1,
                    )

            # monthly netCDF output: totals
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initialize at the start of the simulation
                    if currTimeStep.timeStepPCR == 1:
                        vars(self)[var + "Tot"] = pcr.scalar(0.0)
                    # reset at the start of the month
                    if currTimeStep.day == 1:
                        vars(self)[var + "Tot"] = pcr.scalar(0.0)
                    vars(self)[var + "Tot"] += vars(self)[var]
                    if currTimeStep.endMonth:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir)
                            + "/"
                            + str(var)
                            + "_"
                            + str(self.iniItemsLC["name"])
                            + "_"
                            + "monthTot.nc",
                            var,
                            pcr.pcr2numpy(self.__getattribute__(var + "Tot"), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )
            # averages
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # only if no accumulator is defined
                    if var not in self.outMonthTotNC:
                        # initialize at the start of the simulation
                        if currTimeStep.timeStepPCR == 1:
                            vars(self)[var + "Tot"] = pcr.scalar(0.0)
                        # reset at the start of the month
                        if currTimeStep.day == 1:
                            vars(self)[var + "Tot"] = pcr.scalar(0.0)
                        vars(self)[var + "Tot"] += vars(self)[var]
                    if currTimeStep.endMonth:
                        vars(self)[var + "Avg"] = (
                            vars(self)[var + "Tot"] / currTimeStep.day
                        )
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir)
                            + "/"
                            + str(var)
                            + "_"
                            + str(self.iniItemsLC["name"])
                            + "_"
                            + "monthAvg.nc",
                            var,
                            pcr.pcr2numpy(self.__getattribute__(var + "Avg"), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )
            # end of month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    if currTimeStep.endMonth:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir)
                            + "/"
                            + str(var)
                            + "_"
                            + str(self.iniItemsLC["name"])
                            + "_"
                            + "monthEnd.nc",
                            var,
                            pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                            timeStamp,
                            currTimeStep.monthIdx - 1,
                        )

    def getPotET(self, meteo, currTimeStep):

        # potential ET (m/day)
        self.totalPotET = pcr.ifthen(self.landmask, self.cropKC * meteo.referencePotET)

        # potential bare soil evaporation and transpiration (m/day)
        self.potBareSoilEvap = pcr.ifthen(
            self.landmask, self.minCropKC * meteo.referencePotET
        )
        self.potTranspiration = pcr.max(
            0.0, pcr.ifthen(self.landmask, self.totalPotET - self.potBareSoilEvap)
        )

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.totalPotET],
                [self.potBareSoilEvap, self.potTranspiration],
                [],
                [],
                "partitioning potential evaporation",
                True,
                currTimeStep.fulldate,
                threshold=5e-4,
            )

    def interceptionUpdate(self, meteo, currTimeStep):

        if self.debugWaterBalance:
            prevStates = [self.interceptStor]

        # throughfall: surplus above the interception storage threshold
        if self.interceptionModuleType == "Modified":
            # extended interception definition (not only canopy);
            # Rens: PRP = (1-CFRAC[TYPE])*PRPTOT+max(CFRAC[TYPE]*PRPTOT+INTS_L[TYPE]-ICC[TYPE],0)
            self.throughfall = pcr.max(
                0.0, self.interceptStor + meteo.precipitation - self.interceptCap
            )
            # Edwin modified this to extend the interception scope (not only canopy interception)
        if self.interceptionModuleType == "Original":
            # only canopy interception
            self.throughfall = (
                1.0 - self.coverFraction
            ) * meteo.precipitation + pcr.max(
                0.0,
                self.coverFraction * meteo.precipitation
                + self.interceptStor
                - self.interceptCap,
            )

        # update the interception storage after throughfall; Rens: INTS_L[TYPE] = max(0,INTS_L[TYPE]+PRPTOT-PRP)
        self.interceptStor = pcr.max(
            0.0, self.interceptStor + meteo.precipitation - self.throughfall
        )

        # partition throughfall into snowfall and liquid precipitation
        # Rens: SNOW = if(TA<TT,PRPTOT,0), done in his meteo module to allow for the snowfall correction factor (SFCF)
        estimSnowfall = pcr.ifthenelse(
            meteo.temperature < self.freezingT, meteo.precipitation, 0.0
        )
        # snowfall (m/day); Rens: SNOW = SNOW*if(PRPTOT>0,PRP/PRPTOT,0)
        self.snowfall = estimSnowfall * vos.getValDivZero(
            self.throughfall, meteo.precipitation, vos.smallNumber
        )
        # liquid precipitation (m/day); Rens: PRP = PRP-SNOW
        self.liquidPrecip = pcr.max(0.0, self.throughfall - self.snowfall)

        # potential interception flux (m/day), depending on interceptionModuleType
        if self.interceptionModuleType == "Original":
            # only canopy interception
            self.potInterceptionFlux = self.potTranspiration
        if self.interceptionModuleType == "Modified":
            # extended interception definition (not only canopy), added by Edwin
            self.potInterceptionFlux = self.totalPotET

        # evaporation from intercepted water (based on potInterceptionFlux), following Van Beek et al. (2011);
        # Rens: EACT_L[TYPE]= min(INTS_L[TYPE],(T_p[TYPE]*if(ICC[TYPE]>0,INTS_L[TYPE]/ICC[TYPE],0)**(2/3)))
        self.interceptEvap = pcr.min(
            self.interceptStor,
            self.potInterceptionFlux
            * (
                vos.getValDivZero(
                    self.interceptStor, self.interceptCap, vos.smallNumber, 0.0
                )
                ** (2.00 / 3.00)
            ),
        )

        # update the interception storage; Rens: INTS_L[TYPE]= INTS_L[TYPE]-EACT_L[TYPE]
        self.interceptStor = pcr.max(0.0, self.interceptStor - self.interceptEvap)

        # update potBareSoilEvap and potTranspiration after interceptEvap
        if self.interceptionModuleType == "Modified":
            # fractions of potential bare soil evaporation and transpiration
            fracPotBareSoilEvap = pcr.max(
                0.0,
                pcr.min(
                    1.0,
                    vos.getValDivZero(
                        self.potBareSoilEvap,
                        self.potBareSoilEvap + self.potTranspiration,
                        vos.smallNumber,
                    ),
                ),
            )
            fracPotTranspiration = pcr.scalar(1.0 - self.fracPotBareSoilEvap)
            # subtract interceptEvap from potBareSoilEvap and potTranspiration
            self.potBareSoilEvap = pcr.max(
                0.0, self.potBareSoilEvap - fracPotBareSoilEvap * self.interceptEvap
            )
            self.potTranspiration = pcr.max(
                0.0, self.potTranspiration - fracPotTranspiration * self.interceptEvap
            )
            # Rens: T_p[TYPE] = max(0,T_p[TYPE]-EACT_L[TYPE]); Edwin modified this to extend the interception
            # scope (not only canopy interception)
        if self.interceptionModuleType == "Original":
            self.potTranspiration = pcr.max(
                0.0, self.potTranspiration - self.interceptEvap
            )

        # update the actual evaporation after interceptEvap (the first flux in ET)
        self.actualET = 0.0
        self.actualET += self.interceptEvap

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.throughfall],
                [self.snowfall, self.liquidPrecip],
                [],
                [],
                "rain-snow-partitioning",
                True,
                currTimeStep.fulldate,
                threshold=1e-5,
            )
            vos.waterBalanceCheck(
                [meteo.precipitation],
                [self.throughfall, self.interceptEvap],
                prevStates,
                [self.interceptStor],
                "interceptStor",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )

    # TODO: rewrite this method as defined by Rens

    def snow_module_update(self, meteo, currTimeStep):

        if self.snowModuleType == "Simple":
            self.snowMeltHBVSimple(meteo, currTimeStep)
        # TODO: define other snow modules

    def snowMeltHBVSimple(self, meteo, currTimeStep):

        if self.debugWaterBalance:
            prevStates = [self.snowCoverSWE, self.snowFreeWater]
            prevSnowCoverSWE = self.snowCoverSWE
            prevSnowFreeWater = self.snowFreeWater

        # added by Joren: snow transport
        self.transportVolSnow = pcr.scalar(0.0)
        self.incomingVolSnow = pcr.scalar(0.0)

        # whether to transport snow free water as well
        self.transport_water = False
        self.transportFreeWater = pcr.scalar(0.0)
        self.incomingFreeWater = pcr.scalar(0.0)
        # kind of snow transport
        if self.snowTransport == "FreyAndHolzmann":
            self.simplifiedFreyAndHolzmann_pcraster(currTimeStep)

        else:
            logger.info("NO SnowTransport: who needs that anyway....?")

        # changes in snow cover: - melt, + gain in snow or refreezing;
        # Rens: DSC[TYPE] = if(TA<=TT,CFR*SCF_L[TYPE],-min(SC_L[TYPE],max(TA-TT,0)*CFMAX*Duration*timeslice()))
        deltaSnowCover = pcr.ifthenelse(
            meteo.temperature <= self.freezingT,
            self.refreezingCoeff * self.snowFreeWater,
            -pcr.min(
                self.snowCoverSWE,
                pcr.max(meteo.temperature - self.freezingT, 0.0) * self.degreeDayFactor,
            )
            * 1.0
            * 1.0,
        )

        # update snowCoverSWE; Rens: SC_L[TYPE] = max(0.0, SC_L[TYPE]+DSC[TYPE]+SNOW)
        self.snowCoverSWE = pcr.max(
            0.0, self.snowfall + deltaSnowCover + self.snowCoverSWE
        )

        # snow melt (m/day) for reporting
        self.snowMelt = pcr.ifthenelse(
            deltaSnowCover < 0.0, deltaSnowCover * pcr.scalar(-1.0), pcr.scalar(0.0)
        )

        # snowFreeWater: liquid water stored above snowCoverSWE; Rens: SCF_L[TYPE] = SCF_L[TYPE]-DSC[TYPE]+PRP
        self.snowFreeWater = self.snowFreeWater - deltaSnowCover + self.liquidPrecip

        # net liquid water transferred to the soil; Rens: Pn = max(0,SCF_L[TYPE]-CWH*SC_L[TYPE])
        self.netLqWaterToSoil = pcr.max(
            0.0, self.snowFreeWater - self.snowWaterHoldingCap * self.snowCoverSWE
        )

        # update snowFreeWater after netLqWaterToSoil; Rens: SCF_L[TYPE] = max(0,SCF_L[TYPE]-Pn)
        self.snowFreeWater = pcr.max(0.0, self.snowFreeWater - self.netLqWaterToSoil)

        # evaporation from snowFreeWater (based on potBareSoilEvap); Rens: ES_a[TYPE] = min(SCF_L[TYPE],ES_p[TYPE])
        self.actSnowFreeWaterEvap = pcr.min(self.snowFreeWater, self.potBareSoilEvap)

        # update snowFreeWater; Rens: SCF_L[TYPE]= SCF_L[TYPE]-ES_a[TYPE]
        self.snowFreeWater = pcr.max(
            0.0, self.snowFreeWater - self.actSnowFreeWaterEvap
        )
        # update potBareSoilEvap; Rens: ES_p[TYPE]= max(0,ES_p[TYPE]-ES_a[TYPE])
        self.potBareSoilEvap = pcr.max(
            0, self.potBareSoilEvap - self.actSnowFreeWaterEvap
        )

        # update the actual evaporation after evaporation from snowFreeWater; Rens: EACT_L[TYPE]= EACT_L[TYPE]+ES_a[TYPE]
        self.actualET += self.actSnowFreeWaterEvap
        # changed by Joren

        if self.transport_water:
            vos.waterBalanceCheck(
                [
                    self.snowfall,
                    self.liquidPrecip,
                    self.incomingVolSnow / self.cellArea,
                    self.incomingFreeWater / self.cellArea,
                ],
                [
                    self.netLqWaterToSoil,
                    self.actSnowFreeWaterEvap,
                    self.transportVolSnow / self.cellArea,
                    self.transportFreeWater / self.cellArea,
                ],
                prevStates,
                [self.snowCoverSWE, self.snowFreeWater],
                "snow module",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )
            vos.waterBalanceCheck(
                [self.snowfall, deltaSnowCover, self.incomingVolSnow / self.cellArea],
                [self.transportVolSnow / self.cellArea],
                [prevSnowCoverSWE],
                [self.snowCoverSWE],
                "snowCoverSWE",
                True,
                currTimeStep.fulldate,
                threshold=5e-4,
            )
            vos.waterBalanceCheck(
                [self.liquidPrecip, self.incomingFreeWater / self.cellArea],
                [
                    deltaSnowCover,
                    self.actSnowFreeWaterEvap,
                    self.netLqWaterToSoil,
                    self.transportFreeWater / self.cellArea,
                ],
                [prevSnowFreeWater],
                [self.snowFreeWater],
                "snowFreeWater",
                True,
                currTimeStep.fulldate,
                threshold=5e-4,
            )
        else:
            vos.waterBalanceCheck(
                [
                    self.snowfall,
                    self.liquidPrecip,
                    self.incomingVolSnow / self.cellArea,
                ],
                [
                    self.netLqWaterToSoil,
                    self.actSnowFreeWaterEvap,
                    self.transportVolSnow / self.cellArea,
                ],
                prevStates,
                [self.snowCoverSWE, self.snowFreeWater],
                "snow module",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )
            vos.waterBalanceCheck(
                [self.snowfall, deltaSnowCover, self.incomingVolSnow / self.cellArea],
                [self.transportVolSnow / self.cellArea],
                [prevSnowCoverSWE],
                [self.snowCoverSWE],
                "snowCoverSWE",
                True,
                currTimeStep.fulldate,
                threshold=5e-4,
            )
            vos.waterBalanceCheck(
                [self.liquidPrecip],
                [deltaSnowCover, self.actSnowFreeWaterEvap, self.netLqWaterToSoil],
                [prevSnowFreeWater],
                [self.snowFreeWater],
                "snowFreeWater",
                True,
                currTimeStep.fulldate,
                threshold=5e-4,
            )

    def simplifiedFreyAndHolzmann_pcraster(self, currTimeStep):
        # cells where snow exceeds the threshold
        self.reverseLDD_sub = pcr.ifthen(
            pcr.ifthenelse(self.snowCoverSWE != 0.0, pcr.scalar(1.0), pcr.scalar(0.0))
            != 0,
            self.reverseLDD,
        )
        # convert to volumes
        self.transportVolSnow = (
            pcr.max(self.snowCoverSWE - self.Hv, pcr.scalar(0.0)) * self.cellArea
        )
        # fraction to transport
        self.transportVolSnow = (
            self.transportVolSnow
            * vos.rad2deg(self.parameters.tanslope)
            / 90
            * self.frho
        )

        # divide by the number of downstream cells (downstream copies the value of the downstream cell,
        # so this is needed for the water balance) and transport the snow downstream (reverse LDD)
        self.incomingVolSnow = pcr.cover(
            pcr.downstream(
                self.reverseLDD_sub,
                pcr.cover(self.transportVolSnow / self.downstreamCells),
            ),
            0.0,
        )

        # transport snow free water
        if self.transport_water:
            frac_of_snow = (
                exceedingSnow * vos.rad2deg(self.parameters.tanslope) / 90 * self.frho
            ) / self.snowCoverSWE
            self.transportFreeWater = pcr.max(
                self.cellArea * self.snowFreeWater * frac_of_snow, 0.0
            )
            fractionWater = self.transportFreeWater / self.downstreamCells
            # transport the snow free water downstream (reverse LDD)
            self.incomingFreeWater = pcr.downstream(self.reverseLDD, fractionWater)
            self.snowFreeWater = (
                self.snowFreeWater
                - self.transportFreeWater / self.cellArea
                + self.incomingFreeWater / self.cellArea
            )

        # new snow cover
        self.snowCoverSWE = (
            self.snowCoverSWE
            - self.transportVolSnow / self.cellArea
            + self.incomingVolSnow / self.cellArea
        )

    def getSoilStates(self):

        if self.numberOfLayers == 2:

            # initial total soil water storage
            self.soilWaterStorage = pcr.max(0.0, self.storUpp + self.storLow)

            # effective degree of saturation (-); zero for zero storage capacities (not covered with 1)
            self.effSatUpp = vos.getValDivZero(self.storUpp, self.parameters.storCapUpp)
            self.effSatLow = vos.getValDivZero(self.storLow, self.parameters.storCapLow)
            self.effSatUpp = pcr.min(1.0, self.effSatUpp)
            self.effSatLow = pcr.min(1.0, self.effSatLow)

            # matric suction (m); Rens: PSI1= PSI_A1[TYPE]*max(0.01,THEFF1)**-BCH1[TYPE]
            self.matricSuctionUpp = self.parameters.airEntryValueUpp * (
                pcr.max(0.01, self.effSatUpp) ** -self.parameters.poreSizeBetaUpp
            )
            # Rens: PSI2= PSI_A2[TYPE]*max(0.01,THEFF2)**-BCH2[TYPE]
            self.matricSuctionLow = self.parameters.airEntryValueLow * (
                pcr.max(0.01, self.effSatLow) ** -self.parameters.poreSizeBetaLow
            )

            # unsaturated hydraulic conductivity kUnsat (m/day)
            # Rens: KTHEFF1= max(0,THEFF1**BCB1[TYPE]*KS1[TYPE])
            self.kUnsatUpp = pcr.max(
                0.0,
                (self.effSatUpp**self.parameters.campbellBetaUpp)
                * self.parameters.kSatUpp,
            )
            # Rens: KTHEFF2= max(0,THEFF2**BCB2[TYPE]*KS2[TYPE])
            self.kUnsatLow = pcr.max(
                0.0,
                (self.effSatLow**self.parameters.campbellBetaLow)
                * self.parameters.kSatLow,
            )
            self.kUnsatUpp = pcr.min(self.kUnsatUpp, self.parameters.kSatUpp)
            self.kUnsatLow = pcr.min(self.kUnsatLow, self.parameters.kSatLow)

            # kThVert (m/day): unsaturated conductivity capped at field capacity, for the exchange between layers;
            # Rens: KTHVERT = min(sqrt(KTHEFF1*KTHEFF2),(KTHEFF1*KTHEFF2*KTHEFF1_FC*KTHEFF2_FC)**0.25)
            self.kThVertUppLow = pcr.min(
                pcr.sqrt(self.kUnsatUpp * self.kUnsatLow),
                (
                    self.kUnsatUpp
                    * self.kUnsatLow
                    * self.parameters.kUnsatAtFieldCapUpp
                    * self.parameters.kUnsatAtFieldCapLow
                )
                ** 0.25,
            )

            # gradient for capillary rise (from the target store to the underlying store);
            # Rens: GRAD = max(0,2*(PSI1-PSI2)/(Z1[TYPE]+Z2[TYPE])-1)
            self.gradientUppLow = pcr.max(
                0.0,
                (self.matricSuctionUpp - self.matricSuctionLow)
                * 2.0
                / (self.parameters.thickUpp + self.parameters.thickLow)
                - pcr.scalar(1.0),
            )
            self.gradientUppLow = pcr.cover(self.gradientUppLow, 0.0)

            # readily available water in the root zone (upper soil layers); Edwin uses the soil thicknesses
            # thickUpp and thickLow instead of storCapUpp and storCapLow (supported by Rens)
            self.readAvlWater = (
                pcr.max(0.0, self.effSatUpp - self.parameters.effSatAtWiltPointUpp)
            ) * (
                self.parameters.satVolMoistContUpp - self.parameters.resVolMoistContUpp
            ) * pcr.min(
                self.parameters.thickUpp, self.maxRootDepth
            ) + (
                pcr.max(0.0, self.effSatLow - self.parameters.effSatAtWiltPointLow)
            ) * (
                self.parameters.satVolMoistContLow - self.parameters.resVolMoistContLow
            ) * pcr.min(
                self.parameters.thickLow,
                pcr.max(self.maxRootDepth - self.parameters.thickUpp, 0.0),
            )

        if self.numberOfLayers == 3:

            # initial total soil water storage
            self.soilWaterStorage = pcr.max(
                0.0, self.storUpp000005 + self.storUpp005030 + self.storLow030150
            )

            # effective degree of saturation (-)
            self.effSatUpp000005 = vos.getValDivZero(
                self.storUpp000005, self.parameters.storCapUpp000005
            )
            self.effSatUpp005030 = vos.getValDivZero(
                self.storUpp005030, self.parameters.storCapUpp005030
            )
            self.effSatLow030150 = vos.getValDivZero(
                self.storLow030150, self.parameters.storCapLow030150
            )
            self.effSatUpp000005 = pcr.min(1.0, self.effSatUpp000005)
            self.effSatUpp005030 = pcr.min(1.0, self.effSatUpp005030)
            self.effSatLow030150 = pcr.min(1.0, self.effSatLow030150)

            # matric suction (m)
            self.matricSuctionUpp000005 = self.parameters.airEntryValueUpp000005 * (
                pcr.max(0.01, self.effSatUpp000005)
                ** -self.parameters.poreSizeBetaUpp000005
            )
            self.matricSuctionUpp005030 = self.parameters.airEntryValueUpp005030 * (
                pcr.max(0.01, self.effSatUpp005030)
                ** -self.parameters.poreSizeBetaUpp005030
            )
            self.matricSuctionLow030150 = self.parameters.airEntryValueLow030150 * (
                pcr.max(0.01, self.effSatLow030150)
                ** -self.parameters.poreSizeBetaLow030150
            )

            # unsaturated hydraulic conductivity kUnsat (m/day)
            self.kUnsatUpp000005 = pcr.max(
                0.0,
                (self.effSatUpp000005**self.parameters.campbellBetaUpp000005)
                * self.parameters.kSatUpp000005,
            )
            self.kUnsatUpp005030 = pcr.max(
                0.0,
                (self.effSatUpp005030**self.parameters.campbellBetaUpp005030)
                * self.parameters.kSatUpp005030,
            )
            self.kUnsatLow030150 = pcr.max(
                0.0,
                (self.effSatLow030150**self.parameters.campbellBetaLow030150)
                * self.parameters.kSatLow030150,
            )

            self.kUnsatUpp000005 = pcr.min(
                self.kUnsatUpp000005, self.parameters.kSatUpp000005
            )
            self.kUnsatUpp005030 = pcr.min(
                self.kUnsatUpp005030, self.parameters.kSatUpp005030
            )
            self.kUnsatLow030150 = pcr.min(
                self.kUnsatLow030150, self.parameters.kSatLow030150
            )

            # kThVert (m/day): unsaturated conductivity capped at field capacity, for the exchange between layers:
            # between Upp000005 and Upp005030
            self.kThVertUpp000005Upp005030 = pcr.min(
                pcr.sqrt(self.kUnsatUpp000005 * self.kUnsatUpp005030),
                (
                    self.kUnsatUpp000005
                    * self.kUnsatUpp005030
                    * self.parameters.kUnsatAtFieldCapUpp000005
                    * self.parameters.kUnsatAtFieldCapUpp005030
                )
                ** 0.25,
            )
            # between Upp005030 and Low030150
            self.kThVertUpp005030Low030150 = pcr.min(
                pcr.sqrt(self.kUnsatUpp005030 * self.kUnsatLow030150),
                (
                    self.kUnsatUpp005030
                    * self.kUnsatLow030150
                    * self.parameters.kUnsatAtFieldCapUpp005030
                    * self.parameters.kUnsatAtFieldCapLow030150
                )
                ** 0.25,
            )

            # gradient for capillary rise (from the target store to the underlying store):
            # between Upp000005 and Upp005030
            self.gradientUpp000005Upp005030 = pcr.max(
                0.0,
                2.0
                * (self.matricSuctionUpp000005 - self.matricSuctionUpp005030)
                / (self.parameters.thickUpp000005 + self.parameters.thickUpp005030)
                - 1.0,
            )
            # between Upp005030 and Low030150
            self.gradientUpp005030Low030150 = pcr.max(
                0.0,
                2.0
                * (self.matricSuctionUpp005030 - self.matricSuctionLow030150)
                / (self.parameters.thickUpp005030 + self.parameters.thickLow030150)
                - 1.0,
            )

            # readily available water in the root zone (upper soil layers)
            self.readAvlWater = (
                (
                    pcr.max(
                        0.0,
                        self.effSatUpp000005
                        - self.parameters.effSatAtWiltPointUpp000005,
                    )
                )
                * (
                    self.parameters.satVolMoistContUpp000005
                    - self.parameters.resVolMoistContUpp000005
                )
                * pcr.min(self.parameters.thickUpp000005, self.maxRootDepth)
                + (
                    pcr.max(
                        0.0,
                        self.effSatUpp005030
                        - self.parameters.effSatAtWiltPointUpp005030,
                    )
                )
                * (
                    self.parameters.satVolMoistContUpp005030
                    - self.parameters.resVolMoistContUpp005030
                )
                * pcr.min(
                    self.parameters.thickUpp005030,
                    pcr.max(self.maxRootDepth - self.parameters.thickUpp000005),
                )
                + (
                    pcr.max(
                        0.0,
                        self.effSatLow030150
                        - self.parameters.effSatAtWiltPointLow030150,
                    )
                )
                * (
                    self.parameters.satVolMoistContLow030150
                    - self.parameters.resVolMoistContLow030150
                )
                * pcr.min(
                    self.parameters.thickLow030150,
                    pcr.max(self.maxRootDepth - self.parameters.thickUpp005030, 0.0),
                )
            )

        # RvB: initialize satAreaFrac
        self.satAreaFrac = None

        # TODO: check the water balance of all sources: desalination, surface water, non-fossil and fossil groundwater

    def calculateDirectRunoff(self):

        # partition topWaterLater into directRunoff and infiltration
        self.directRunoff = self.improvedArnoScheme(
            iniWaterStorage=self.soilWaterStorage,
            inputNetLqWaterToSoil=self.topWaterLayer,
            directRunoffReductionMethod=self.improvedArnoSchemeMethod,
        )
        self.directRunoff = pcr.min(self.topWaterLayer, self.directRunoff)

        # minimize directRunoff in irrigation areas
        if self.name.startswith("irr") and self.includeIrrigation:
            self.directRunoff = pcr.scalar(0.0)

        # update topWaterLayer after directRunoff
        self.topWaterLayer = pcr.max(0.0, self.topWaterLayer - self.directRunoff)

    def improvedArnoScheme(
        self,
        iniWaterStorage,
        inputNetLqWaterToSoil,
        directRunoffReductionMethod="Default",
    ):

        # arnoBeta = BCF = b coefficient of soil water storage capacity distribution
        # WMIN = root zone water storage capacity, minimum values
        # WMAX = root zone water storage capacity, area-averaged values
        # W    = actual water storage in root zone
        # WRANGE  = WMAX - WMIN
        # DW      = WMAX-W
        # WFRAC   = DW/WRANGE ; WFRAC capped at 1
        # WFRACB  = DW/WRANGE raised to the power (1/(b+1))
        # SATFRAC = fractional saturated area
        # WACT    = actual water storage within rootzone

        self.satAreaFracOld = self.satAreaFrac

        # Pn = W[TYPE]+Pn;
        Pn = iniWaterStorage + inputNetLqWaterToSoil
        # Pn = Pn-max(WMIN[TYPE],W[TYPE]);
        Pn = Pn - pcr.max(self.rootZoneWaterStorageMin, iniWaterStorage)
        # W[TYPE]= if(Pn<0,WMIN[TYPE]+Pn,max(W[TYPE],WMIN[TYPE]));
        soilWaterStorage = pcr.ifthenelse(
            Pn < 0.0,
            self.rootZoneWaterStorageMin + Pn,
            pcr.max(iniWaterStorage, self.rootZoneWaterStorageMin),
        )
        # Pn = max(0,Pn);
        Pn = pcr.max(0.0, Pn)
        # DW = max(0,WMAX[TYPE]-W[TYPE]);
        DW = pcr.max(0.0, self.parameters.rootZoneWaterStorageCap - soilWaterStorage)

        # modified by Edwin, to solve problems with rootZoneWaterStorageRange = 0
        WFRAC = pcr.ifthenelse(
            self.rootZoneWaterStorageRange > 0.0,
            pcr.min(1.0, DW / self.rootZoneWaterStorageRange),
            1.0,
        )

        # WFRACB = WFRAC**(1/(1+BCF[TYPE]));
        self.WFRACB = WFRAC ** (1.0 / (1.0 + self.arnoBeta))
        # SATFRAC_L = if(WFRACB>0,1-WFRACB**BCF[TYPE],1);
        self.satAreaFrac = pcr.ifthenelse(
            self.WFRACB > 0.0, 1.0 - self.WFRACB**self.arnoBeta, 1.0
        )
        # make sure 0 <= satAreaFrac <= 1
        self.satAreaFrac = pcr.min(self.satAreaFrac, 1.0)
        self.satAreaFrac = pcr.max(self.satAreaFrac, 0.0)

        # Rens: WACT_L = (BCF[TYPE]+1)*WMAX[TYPE]- BCF[TYPE]*WMIN[TYPE]- (BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB
        actualW = (
            (self.arnoBeta + 1.0) * self.parameters.rootZoneWaterStorageCap
            - self.arnoBeta * self.rootZoneWaterStorageMin
            - (self.arnoBeta + 1.0) * self.rootZoneWaterStorageRange * self.WFRACB
        )

        # as in the "Original" work of van Beek et al. (2011)
        directRunoffReduction = pcr.scalar(0.0)
        # Rens: to maintain full saturation and continuous groundwater recharge/percolation, directRunoff may be reduced;
        # for the 2-layer model, this reduction is percLow = min(KUnSatLow, sqrt(KUnSatFC2*KUnSatLow))
        if directRunoffReductionMethod == "Default":
            if self.numberOfLayers == 2:
                directRunoffReduction = pcr.min(
                    self.kUnsatLow,
                    pcr.sqrt(self.kUnsatLow * self.parameters.kUnsatAtFieldCapLow),
                )
            if self.numberOfLayers == 3:
                directRunoffReduction = pcr.min(
                    self.kUnsatLow030150,
                    pcr.sqrt(
                        self.kUnsatLow030150 * self.parameters.kUnsatAtFieldCapLow030150
                    ),
                )

        if directRunoffReductionMethod == "Modified":
            if self.numberOfLayers == 2:
                directRunoffReduction = pcr.min(
                    self.kUnsatLow,
                    pcr.sqrt(self.kUnsatLow * self.parameters.kUnsatAtFieldCapLow),
                )
            if self.numberOfLayers == 3:
                directRunoffReduction = pcr.min(
                    self.kUnsatLow030150,
                    pcr.sqrt(
                        self.kUnsatLow030150 * self.parameters.kUnsatAtFieldCapLow030150
                    ),
                )
            # directRunoff (preferential flow to groundwater) is only reduced if soilWaterStorage is near
            # saturation, to maintain saturation
            saturation_treshold = 0.999
            directRunoffReduction = pcr.ifthenelse(
                vos.getValDivZero(
                    soilWaterStorage, self.parameters.rootZoneWaterStorageCap
                )
                > saturation_treshold,
                directRunoffReduction,
                0.0,
            )

        # directRunoff; Rens: Q1_L[TYPE]= max(0,Pn-(WMAX[TYPE]+P2_L[TYPE]-W[TYPE])+
        # if(Pn>=(BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB, 0, WRANGE[TYPE]*(WFRACB-Pn/((BCF[TYPE]+1)*WRANGE[TYPE]))**(BCF[TYPE]+1)))
        condition = (
            (self.arnoBeta + pcr.scalar(1.0))
            * self.rootZoneWaterStorageRange
            * self.WFRACB
        )
        directRunoff = pcr.max(
            0.0,
            Pn
            - (
                self.parameters.rootZoneWaterStorageCap
                + directRunoffReduction
                - soilWaterStorage
            )
            + pcr.ifthenelse(
                Pn >= condition,
                pcr.scalar(0.0),
                self.rootZoneWaterStorageRange
                * (
                    self.WFRACB
                    - Pn / ((self.arnoBeta + 1.0) * self.rootZoneWaterStorageRange)
                )
                ** (self.arnoBeta + 1.0),
            ),
        )
        # make sure there is always a value
        directRunoff = pcr.cover(directRunoff, 0.0)

        return directRunoff

    def calculateOpenWaterEvap(self, satisfied_irrigation_water_height):

        # update topWaterLayer with netLqWaterToSoil and irrGrossDemand
        self.topWaterLayer += pcr.max(
            0.0, self.netLqWaterToSoil + satisfied_irrigation_water_height
        )

        # potential evaporation for openWaterEvap; Edwin's principle: LIMIT = potBareSoilEvap + potTranspiration
        remainingPotETP = self.potBareSoilEvap + self.potTranspiration

        # openWaterEvap is only for evaporation from paddy fields
        self.openWaterEvap = pcr.spatial(pcr.scalar(0.0))

        if self.name == "irrPaddy" or self.name == "irr_paddy":
            self.openWaterEvap = pcr.min(
                pcr.max(0.0, self.topWaterLayer), remainingPotETP
            )

        # update potBareSoilEvap and potTranspiration after openWaterEvap; Edwin replaced the cover by the following
        self.potBareSoilEvap = pcr.cover(
            pcr.max(
                0.0,
                self.potBareSoilEvap
                - vos.getValDivZero(self.potBareSoilEvap, remainingPotETP)
                * self.openWaterEvap,
            ),
            0.0,
        )
        self.potTranspiration = pcr.cover(
            pcr.max(
                0.0,
                self.potTranspiration
                - vos.getValDivZero(self.potTranspiration, remainingPotETP)
                * self.openWaterEvap,
            ),
            0.0,
        )

        # update topWaterLayer after openWaterEvap
        self.topWaterLayer = pcr.max(0.0, self.topWaterLayer - self.openWaterEvap)

    def calculateInfiltration(self):

        # infiltration, limited by KSat1 and the available water in topWaterLayer
        if self.numberOfLayers == 2:
            # Rens: P0_L = min(P0_L,KS1*Duration*timeslice())
            self.infiltration = pcr.min(self.topWaterLayer, self.parameters.kSatUpp)

        if self.numberOfLayers == 3:
            # Rens: P0_L = min(P0_L,KS1*Duration*timeslice())
            self.infiltration = pcr.min(
                self.topWaterLayer, self.parameters.kSatUpp000005
            )

        # for paddy fields, infiltration should consider percolation losses
        if (
            self.name == "irrPaddy" or self.name == "irr_paddy"
        ) and self.includeIrrigation:
            infiltration_loss = pcr.max(
                self.design_percolation_loss,
                ((1.0 / self.irrigationEfficiencyUsed) - 1.0) * self.topWaterLayer,
            )
            self.infiltration = pcr.min(infiltration_loss, self.infiltration)

        # update topWaterLayer after infiltration
        self.topWaterLayer = pcr.max(0.0, self.topWaterLayer - self.infiltration)

        # release the excess topWaterLayer above minTopWaterLayer as additional direct runoff
        self.directRunoff += pcr.max(0.0, self.topWaterLayer - self.minTopWaterLayer)

        # update topWaterLayer after the additional direct runoff
        self.topWaterLayer = pcr.min(self.topWaterLayer, self.minTopWaterLayer)

    def estimateTranspirationAndBareSoilEvap(
        self, returnTotalEstimation=False, returnTotalTranspirationOnly=False
    ):

        # transpiration: fractions based on root fractions and actual layer storages
        # Rens: WF1= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW1[TYPE]*S1_L[TYPE]/max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW1[TYPE])
        # Rens: WF2= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW2[TYPE]*S2_L[TYPE]/max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW2[TYPE])
        if self.numberOfLayers == 2:
            dividerTranspFracs = pcr.max(
                1e-9,
                self.adjRootFrUpp * self.storUpp + self.adjRootFrLow * self.storLow,
            )
            transpFracUpp = pcr.ifthenelse(
                (self.storUpp + self.storLow) > 0.0,
                self.adjRootFrUpp * self.storUpp / dividerTranspFracs,
                self.adjRootFrUpp,
            )
            transpFracLow = pcr.ifthenelse(
                (self.storUpp + self.storLow) > 0.0,
                self.adjRootFrLow * self.storLow / dividerTranspFracs,
                self.adjRootFrLow,
            )
        if self.numberOfLayers == 3:
            dividerTranspFracs = pcr.max(
                1e-9,
                self.adjRootFrUpp000005 * self.storUpp000005
                + self.adjRootFrUpp005030 * self.storUpp005030
                + self.adjRootFrLow030150 * self.storLow030150,
            )
            transpFracUpp000005 = pcr.ifthenelse(
                (self.storUpp000005 + self.storUpp005030 + self.storLow030150) > 0.0,
                self.adjRootFrUpp000005 * self.storUpp000005 / dividerTranspFracs,
                self.adjRootFrUpp000005,
            )
            transpFracUpp005030 = pcr.ifthenelse(
                (self.storUpp000005 + self.storUpp005030 + self.storLow030150) > 0.0,
                self.adjRootFrUpp005030 * self.storUpp005030 / dividerTranspFracs,
                self.adjRootFrUpp005030,
            )
            transpFracLow030150 = pcr.ifthenelse(
                (self.storUpp000005 + self.storUpp005030 + self.storLow030150) > 0.0,
                self.adjRootFrLow030150 * self.storLow030150 / dividerTranspFracs,
                self.adjRootFrLow030150,
            )

        # no reduction when returnTotalEstimation
        relActTranspiration = pcr.scalar(1.0)
        if not returnTotalEstimation:
            # reduction factor for transpiration (actual over potential transpiration)
            # Rens: FRACTA[TYPE] = (WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-(1+BCF[TYPE])/BCF[TYPE]*WFRACB))/(WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-WFRACB))
            relActTranspiration = (
                self.parameters.rootZoneWaterStorageCap
                + self.arnoBeta
                * self.rootZoneWaterStorageRange
                * (1.0 - (1.0 + self.arnoBeta) / self.arnoBeta * self.WFRACB)
            ) / (
                self.parameters.rootZoneWaterStorageCap
                + self.arnoBeta * self.rootZoneWaterStorageRange * (1.0 - self.WFRACB)
            )
            # Rens: FRACTA[TYPE] = (1-SATFRAC_L)/(1+(max(0.01,FRACTA[TYPE])/THEFF_50[TYPE])**(-3*BCH_50))
            relActTranspiration = (1.0 - self.satAreaFrac) / (
                1.0
                + (pcr.max(0.01, relActTranspiration) / self.effSatAt50)
                ** (self.effPoreSizeBetaAt50 * pcr.scalar(-3.0))
            )
        relActTranspiration = pcr.max(0.0, relActTranspiration)
        relActTranspiration = pcr.min(1.0, relActTranspiration)

        # Edwin (23 March 2015): no transpiration reduction in irrigated areas
        if self.name.startswith("irr") and self.includeIrrigation:
            relActTranspiration = pcr.scalar(1.0)

        # partition potential transpiration (based on Rens's oldcalc script of 30 July 2015)
        if self.numberOfLayers == 2:
            potTranspirationUpp = pcr.min(
                transpFracUpp * self.potTranspiration, self.potTranspiration
            )
            potTranspirationLow = pcr.max(
                0.0, self.potTranspiration - potTranspirationUpp
            )
        if self.numberOfLayers == 3:
            potTranspirationUpp000005 = pcr.min(
                transpFracUpp000005 * self.potTranspiration, self.potTranspiration
            )
            potTranspirationUpp005030 = pcr.min(
                transpFracUpp005030 * self.potTranspiration,
                pcr.max(0.0, self.potTranspiration - potTranspirationUpp000005),
            )
            potTranspirationLow030150 = pcr.max(
                0.0,
                self.potTranspiration
                - potTranspirationUpp000005
                - potTranspirationUpp005030,
            )

        # actual transpiration fluxes
        if self.numberOfLayers == 2:
            actTranspiUpp = pcr.cover(relActTranspiration * potTranspirationUpp, 0.0)
            actTranspiLow = pcr.cover(relActTranspiration * potTranspirationLow, 0.0)
        if self.numberOfLayers == 3:
            actTranspiUpp000005 = pcr.cover(
                relActTranspiration * potTranspirationUpp000005, 0.0
            )
            actTranspiUpp005030 = pcr.cover(
                relActTranspiration * potTranspirationUpp005030, 0.0
            )
            actTranspiLow030150 = pcr.cover(
                relActTranspiration * potTranspirationLow030150, 0.0
            )

        # bare soil evaporation (potential); no reduction when returnTotalEstimation
        actBareSoilEvap = self.potBareSoilEvap
        if self.numberOfLayers == 2 and not returnTotalEstimation:
            # Rens: ES_a[TYPE] = SATFRAC_L*min(ES_p[TYPE],KS1[TYPE]*Duration*timeslice())+(1-SATFRAC_L)*min(ES_p[TYPE],KTHEFF1*Duration*timeslice())
            actBareSoilEvap = self.satAreaFrac * pcr.min(
                self.potBareSoilEvap, self.parameters.kSatUpp
            ) + (1.0 - self.satAreaFrac) * pcr.min(self.potBareSoilEvap, self.kUnsatUpp)
        if self.numberOfLayers == 3 and not returnTotalEstimation:
            actBareSoilEvap = self.satAreaFrac * pcr.min(
                self.potBareSoilEvap, self.parameters.kSatUpp000005
            ) + (1.0 - self.satAreaFrac) * pcr.min(
                self.potBareSoilEvap, self.kUnsatUpp000005
            )
        actBareSoilEvap = pcr.max(0.0, actBareSoilEvap)
        actBareSoilEvap = pcr.min(actBareSoilEvap, self.potBareSoilEvap)
        actBareSoilEvap = pcr.cover(actBareSoilEvap, 0.0)

        # no bare soil evaporation in inundated paddy fields
        if self.name == "irrPaddy" or self.name == "irr_paddy":
            # no bare soil evaporation if topWaterLayer is above the threshold (Edwin, 23 March 2015)
            treshold = self.potBareSoilEvap + self.potTranspiration
            actBareSoilEvap = pcr.ifthenelse(
                self.topWaterLayer > treshold, 0.0, actBareSoilEvap
            )

        if self.numberOfLayers == 2:
            if returnTotalEstimation:
                if returnTotalTranspirationOnly:
                    return actTranspiUpp + actTranspiLow
                else:
                    return actBareSoilEvap + actTranspiUpp + actTranspiLow
            else:
                return actBareSoilEvap, actTranspiUpp, actTranspiLow
        if self.numberOfLayers == 3:
            if returnTotalEstimation:
                if returnTotalTranspirationOnly:
                    return (
                        actTranspiUpp000005 + actTranspiUpp005030 + actTranspiLow030150
                    )
                else:
                    return (
                        actBareSoilEvap
                        + actTranspiUpp000005
                        + actTranspiUpp005030
                        + actTranspiLow030150
                    )
            else:
                return (
                    actBareSoilEvap,
                    actTranspiUpp000005,
                    actTranspiUpp005030,
                    actTranspiLow030150,
                )

    def estimateSoilFluxes(self, capRiseFrac, groundwater):

        # estimate all fluxes from the given states

        if self.numberOfLayers == 2:

            # percolation from storUpp to storLow; Rens: P1_L[TYPE] = KTHVERT*Duration*timeslice()
            self.percUpp = self.kThVertUppLow * 1.0
            # Rens: P1_L[TYPE] = if(THEFF1 > THEFF1_FC[TYPE],min(max(0,THEFF1-THEFF1_FC[TYPE])*SC1[TYPE],P1_L[TYPE]),P1_L[TYPE])+max(0,P0_L[TYPE]-(SC1[TYPE]-S1_L[TYPE]))
            self.percUpp = pcr.ifthenelse(
                self.effSatUpp > self.parameters.effSatAtFieldCapUpp,
                pcr.min(
                    pcr.max(0.0, self.effSatUpp - self.parameters.effSatAtFieldCapUpp)
                    * self.parameters.storCapUpp,
                    self.percUpp,
                ),
                self.percUpp,
            ) + pcr.max(
                0.0, self.infiltration - (self.parameters.storCapUpp - self.storUpp)
            )
            # percolation from storLow to storGroundwater; Rens: P2_L[TYPE] = min(KTHEFF2,sqrt(KTHEFF2*KTHEFF2_FC[TYPE]))*Duration*timeslice()
            self.percLow = pcr.min(
                self.kUnsatLow,
                pcr.sqrt(self.kUnsatLow * self.parameters.kUnsatAtFieldCapLow),
            )

            # capillary rise to storUpp from storLow
            # Rens: CR1_L[TYPE] = min(max(0,THEFF1_FC[TYPE]-THEFF1)*SC1[TYPE],KTHVERT*GRAD*Duration*timeslice())
            self.capRiseUpp = pcr.min(
                pcr.max(0.0, self.parameters.effSatAtFieldCapUpp - self.effSatUpp)
                * self.parameters.storCapUpp,
                self.kThVertUppLow * self.gradientUppLow,
            )

            # capillary rise to storLow from storGroundwater (m)
            # Rens: CR2_L[TYPE] = 0.5*(SATFRAC_L+CRFRAC)*min((1-THEFF2)*sqrt(KS2[TYPE]*KTHEFF2)*Duration*timeslice(),max(0,THEFF2_FC[TYPE]-THEFF2)*SC2[TYPE])
            self.capRiseLow = (
                0.5
                * (self.satAreaFrac + capRiseFrac)
                * pcr.min(
                    (1.0 - self.effSatLow)
                    * pcr.sqrt(self.parameters.kSatLow * self.kUnsatLow),
                    pcr.max(0.0, self.parameters.effSatAtFieldCapLow - self.effSatLow)
                    * self.parameters.storCapLow,
                )
            )

            # no capillary rise from non-productive aquifers
            self.capRiseLow = pcr.ifthenelse(
                groundwater.productive_aquifer, self.capRiseLow, 0.0
            )

            # interflow (m)
            percToInterflow = self.parameters.percolationImp * (
                self.percUpp + self.capRiseLow - (self.percLow + self.capRiseUpp)
            )
            self.interflow = pcr.max(
                self.parameters.interflowConcTime * percToInterflow
                + (pcr.scalar(1.0) - self.parameters.interflowConcTime)
                * self.interflow,
                0.0,
            )

        if self.numberOfLayers == 3:

            # percolation from storUpp000005 to storUpp005030 (m)
            self.percUpp000005 = self.kThVertUpp000005Upp005030 * 1.0
            self.percUpp000005 = pcr.ifthenelse(
                self.effSatUpp000005 > self.parameters.effSatAtFieldCapUpp000005,
                pcr.min(
                    pcr.max(
                        0.0,
                        self.effSatUpp000005
                        - self.parameters.effSatAtFieldCapUpp000005,
                    )
                    * self.parameters.storCapUpp000005,
                    self.percUpp000005,
                ),
                self.percUpp000005,
            ) + pcr.max(
                0.0,
                self.infiltration
                - (self.parameters.storCapUpp000005 - self.storUpp000005),
            )

            # percolation from storUpp005030 to storLow030150 (m)
            self.percUpp005030 = self.kThVertUpp005030Low030150 * 1.0
            self.percUpp005030 = pcr.ifthenelse(
                self.effSatUpp005030 > self.parameters.effSatAtFieldCapUpp005030,
                pcr.min(
                    pcr.max(
                        0.0,
                        self.effSatUpp005030
                        - self.parameters.effSatAtFieldCapUpp005030,
                    )
                    * self.parameters.storCapUpp005030,
                    self.percUpp005030,
                ),
                self.percUpp005030,
            ) + pcr.max(
                0.0,
                self.percUpp000005
                - (self.parameters.storCapUpp005030 - self.storUpp005030),
            )

            # percolation from storLow030150 to storGroundwater (m)
            self.percLow030150 = pcr.min(
                self.kUnsatLow030150,
                pcr.sqrt(
                    self.parameters.kUnsatAtFieldCapLow030150 * self.kUnsatLow030150
                ),
            )

            # capillary rise to storUpp000005 from storUpp005030 (m)
            self.capRiseUpp000005 = pcr.min(
                pcr.max(
                    0.0,
                    self.parameters.effSatAtFieldCapUpp000005 - self.effSatUpp000005,
                )
                * self.parameters.storCapUpp000005,
                self.kThVertUpp000005Upp005030 * self.gradientUpp000005Upp005030,
            )

            # capillary rise to storUpp005030 from storLow030150 (m)
            self.capRiseUpp005030 = pcr.min(
                pcr.max(
                    0.0,
                    self.parameters.effSatAtFieldCapUpp005030 - self.effSatUpp005030,
                )
                * self.parameters.storCapUpp005030,
                self.kThVertUpp005030Low030150 * self.gradientUpp005030Low030150,
            )

            # capillary rise to storLow030150 from storGroundwater (m)
            self.capRiseLow030150 = (
                0.5
                * (self.satAreaFrac + capRiseFrac)
                * pcr.min(
                    (1.0 - self.effSatLow030150)
                    * pcr.sqrt(self.parameters.kSatLow030150 * self.kUnsatLow030150),
                    pcr.max(
                        0.0,
                        self.parameters.effSatAtFieldCapLow030150
                        - self.effSatLow030150,
                    )
                    * self.parameters.storCapLow030150,
                )
            )

            # no capillary rise from non-productive aquifers
            self.capRiseLow030150 = pcr.ifthenelse(
                groundwater.productive_aquifer, self.capRiseLow030150, 0.0
            )

            # interflow (m)
            percToInterflow = self.parameters.percolationImp * (
                self.percUpp005030
                + self.capRiseLow030150
                - (self.percLow030150 + self.capRiseUpp005030)
            )
            self.interflow = pcr.max(
                self.parameters.interflowConcTime * percToInterflow
                + (pcr.scalar(1.0) - self.parameters.interflowConcTime)
                * self.interflow,
                0.0,
            )

    def scaleAllFluxes(self, groundwater):

        # rescale all fluxes based on the available water

        if self.numberOfLayers == 2:

            # scale the fluxes of Upp; Rens: ADJUST = ES_a[TYPE]+T_a1[TYPE]+P1_L[TYPE];
            # ADJUST = if(ADJUST>0,min(1,(max(0,S1_L[TYPE]+P0_L[TYPE]))/ADJUST),0); ES_a, T_a1 and P1_L are multiplied by ADJUST
            ADJUST = self.actBareSoilEvap + self.actTranspiUpp + self.percUpp
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storUpp + self.infiltration) / ADJUST),
                0.0,
            )
            ADJUST = pcr.cover(ADJUST, 0.0)
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.percUpp = ADJUST * self.percUpp
            self.actTranspiUpp = ADJUST * self.actTranspiUpp

            # scale the fluxes of Low; Rens: ADJUST = T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE];
            # ADJUST = if(ADJUST>0,min(1,max(S2_L[TYPE]+P1_L[TYPE],0)/ADJUST),0); T_a2, P2_L and Q2_L are multiplied by ADJUST
            ADJUST = self.actTranspiLow + self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storLow + self.percUpp) / ADJUST),
                0.0,
            )
            ADJUST = pcr.cover(ADJUST, 0.0)
            self.percLow = ADJUST * self.percLow
            self.actTranspiLow = ADJUST * self.actTranspiLow
            self.interflow = ADJUST * self.interflow

            # capillary rise to storLow is limited to the available storGroundwater and to reducedCapRise;
            # Rens used fracVegCover as a safety factor for a conservative approach (EHS, 2 Sep 2013: not needed)
            self.capRiseLow = pcr.max(
                0.0,
                pcr.min(
                    pcr.max(0.0, groundwater.storGroundwater - self.reducedCapRise),
                    self.capRiseLow,
                ),
            )

            # capillary rise to storUpp is limited to the available storLow
            estimateStorLowBeforeCapRise = pcr.max(
                0,
                self.storLow
                + self.percUpp
                - (self.actTranspiLow + self.percLow + self.interflow),
            )
            # Rens: CR1_L[TYPE] = min(max(0,S2_L[TYPE]+P1_L[TYPE]-(T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE])),CR1_L[TYPE])
            self.capRiseUpp = pcr.min(estimateStorLowBeforeCapRise, self.capRiseUpp)

        if self.numberOfLayers == 3:

            # scale the fluxes of Upp000005
            ADJUST = (
                self.actBareSoilEvap + self.actTranspiUpp000005 + self.percUpp000005
            )
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp000005 + self.infiltration) / ADJUST
                ),
                0.0,
            )
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.percUpp000005 = ADJUST * self.percUpp000005
            self.actTranspiUpp000005 = ADJUST * self.actTranspiUpp000005

            # scale the fluxes of Upp005030
            ADJUST = self.actTranspiUpp005030 + self.percUpp005030
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp005030 + self.percUpp000005) / ADJUST
                ),
                0.0,
            )
            self.percUpp005030 = ADJUST * self.percUpp005030
            self.actTranspiUpp005030 = ADJUST * self.actTranspiUpp005030

            # scale the fluxes of Low030150
            ADJUST = self.actTranspiLow030150 + self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storLow030150 + self.percUpp005030) / ADJUST
                ),
                0.0,
            )
            self.percLow030150 = ADJUST * self.percLow030150
            self.actTranspiLow030150 = ADJUST * self.actTranspiLow030150
            self.interflow = ADJUST * self.interflow

            # capillary rise to storLow is limited to the available storGroundwater and to reducedCapRise
            self.capRiseLow030150 = pcr.max(
                0.0,
                pcr.min(
                    pcr.max(0.0, groundwater.storGroundwater - self.reducedCapRise),
                    self.capRiseLow030150,
                ),
            )

            # capillary rise to storUpp005030 is limited to the available storLow030150
            estimateStorLow030150BeforeCapRise = pcr.max(
                0,
                self.storLow030150
                + self.percUpp005030
                - (self.actTranspiLow030150 + self.percLow030150 + self.interflow),
            )
            self.capRiseUpp005030 = pcr.min(
                estimateStorLow030150BeforeCapRise, self.capRiseUpp005030
            )

            # capillary rise to storUpp000005 is limited to the available storUpp005030
            estimateStorUpp005030BeforeCapRise = pcr.max(
                0,
                self.storUpp005030
                + self.percUpp000005
                - (self.actTranspiUpp005030 + self.percUpp005030),
            )
            self.capRiseUpp000005 = pcr.min(
                estimateStorUpp005030BeforeCapRise, self.capRiseUpp000005
            )

    def scaleAllFluxesForIrrigatedAreas(self, groundwater):

        # minimize interflow in irrigation areas
        if self.name.startswith("irr"):
            self.interflow = 0.0

        # idea of 16 June 2015: deep percolation should consider irrigation application losses
        if self.name.startswith("irr"):

            # the starting crop coefficient indicates the growing season
            startingKC = 0.20

            if self.numberOfLayers == 2:
                deep_percolation_loss = self.percLow
                deep_percolation_loss = pcr.max(
                    deep_percolation_loss,
                    pcr.max(0.0, self.storLow)
                    * ((1.0 / self.irrigationEfficiencyUsed) - 1.0),
                )
                self.percLow = pcr.ifthenelse(
                    self.cropKC > startingKC, deep_percolation_loss, self.percLow
                )

            if self.numberOfLayers == 3:
                deep_percolation_loss = self.percLow030150
                deep_percolation_loss = pcr.max(
                    deep_percolation_loss,
                    pcr.max(0.0, self.storLow030150)
                    * ((1.0 / self.irrigationEfficiencyUsed) - 1.0),
                )
                self.percLow030150 = pcr.ifthenelse(
                    self.cropKC > startingKC, deep_percolation_loss, self.percLow030150
                )

        # scale all fluxes based on the available water (alternative 1)
        self.scaleAllFluxes(groundwater)

    def updateSoilStates(self):

        # update the states, making sure no storage capacity is exceeded

        if self.numberOfLayers == 2:

            # update storLow: + percUpp + capRiseLow - percLow - interflow - actTranspiLow - capRiseUpp;
            # Rens: S2_L[TYPE]= max(0,S2_L[TYPE]+P1_L[TYPE]+CR2_L[TYPE]-(P2_L[TYPE]+Q2_L[TYPE]+CR1_L[TYPE]+T_a2[TYPE]))
            self.storLow = pcr.max(
                0.0,
                self.storLow
                + self.percUpp
                + self.capRiseLow
                - (
                    self.percLow + self.interflow + self.actTranspiLow + self.capRiseUpp
                ),
            )
            # if necessary, reduce the percolation input
            percUpp = self.percUpp

            if self.allowNegativePercolation:
                # as in Rens's oldcalc script, where P1 can be negative: P1_L[TYPE] = P1_L[TYPE]-max(0,S2_L[TYPE]-SC2[TYPE])
                self.percUpp = percUpp - pcr.max(
                    0.0, self.storLow - self.parameters.storCapLow
                )
            else:
                # alternative proposed by Edwin: avoid negative percolation
                self.percUpp = pcr.max(
                    0.0,
                    percUpp - pcr.max(0.0, self.storLow - self.parameters.storCapLow),
                )
                self.storLow = self.storLow - percUpp + self.percUpp
                # if necessary, reduce the capillary rise input
                capRiseLow = self.capRiseLow
                self.capRiseLow = pcr.max(
                    0.0,
                    capRiseLow
                    - pcr.max(0.0, self.storLow - self.parameters.storCapLow),
                )
                self.storLow = self.storLow - capRiseLow + self.capRiseLow
                # if necessary, increase the interflow outflow
                addInterflow = pcr.max(0.0, self.storLow - self.parameters.storCapLow)
                self.interflow += addInterflow
                self.storLow -= addInterflow
                self.storLow = pcr.min(self.storLow, self.parameters.storCapLow)

            # update storUpp: + infiltration + capRiseUpp - percUpp - actTranspiUpp - actBareSoilEvap;
            # Rens: S1_L[TYPE]= max(0,S1_L[TYPE]+P0_L[TYPE]+CR1_L[TYPE]-(P1_L[TYPE]+T_a1[TYPE]+ES_a[TYPE]))
            self.storUpp = pcr.max(
                0.0,
                self.storUpp
                + self.infiltration
                + self.capRiseUpp
                - (self.percUpp + self.actTranspiUpp + self.actBareSoilEvap),
            )
            # any excess above storCapUpp goes to topWaterLayer
            self.satExcess = pcr.max(0.0, self.storUpp - self.parameters.storCapUpp)
            self.topWaterLayer = self.topWaterLayer + self.satExcess

            # any excess above minTopWaterLayer is released as directRunoff
            self.directRunoff = self.directRunoff + pcr.max(
                0.0, self.topWaterLayer - self.minTopWaterLayer
            )

            # make sure storage capacities are not exceeded
            self.topWaterLayer = pcr.min(self.topWaterLayer, self.minTopWaterLayer)
            self.storUpp = pcr.min(self.storUpp, self.parameters.storCapUpp)
            self.storLow = pcr.min(self.storLow, self.parameters.storCapLow)

            # total actual evaporation and transpiration
            self.actualET += (
                self.actBareSoilEvap
                + self.openWaterEvap
                + self.actTranspiUpp
                + self.actTranspiLow
            )

            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUpp + self.actTranspiLow

            # net percolation between the upper soil stores (positive downward)
            self.netPercUpp = self.percUpp - self.capRiseUpp

            # groundwater recharge (positive downward)
            self.gwRecharge = self.percLow - self.capRiseLow

            # for comparison with the 3-layer model output
            self.storUppTotal = self.storUpp
            self.storLowTotal = self.storLow
            self.actTranspiUppTotal = self.actTranspiUpp
            self.actTranspiLowTotal = self.actTranspiLow
            self.interflowTotal = self.interflow

        if self.numberOfLayers == 3:

            # update storLow030150: + percUpp005030 + capRiseLow030150 - percLow030150 - interflow - actTranspiLow030150 - capRiseUpp005030
            self.storLow030150 = pcr.max(
                0.0,
                self.storLow030150
                + self.percUpp005030
                + self.capRiseLow030150
                - (
                    self.percLow030150
                    + self.interflow
                    + self.actTranspiLow030150
                    + self.capRiseUpp005030
                ),
            )
            # if necessary, reduce the percolation input
            percUpp005030 = self.percUpp005030
            self.percUpp005030 = pcr.max(
                0.0,
                percUpp005030
                - pcr.max(0.0, self.storLow030150 - self.parameters.storCapLow030150),
            )
            self.storLow030150 = self.storLow030150 - percUpp005030 + self.percUpp005030
            # if necessary, reduce the capillary rise input
            capRiseLow030150 = self.capRiseLow030150
            self.capRiseLow030150 = pcr.max(
                0.0,
                capRiseLow030150
                - pcr.max(0.0, self.storLow030150 - self.parameters.storCapLow030150),
            )
            self.storLow030150 = (
                self.storLow030150 - capRiseLow030150 + self.capRiseLow030150
            )
            # if necessary, increase the interflow outflow
            addInterflow = pcr.max(
                0.0, self.storLow030150 - self.parameters.storCapLow030150
            )
            self.interflow += addInterflow
            self.storLow030150 -= addInterflow

            self.storLow030150 = pcr.min(
                self.storLow030150, self.parameters.storCapLow030150
            )

            # update storUpp005030: + percUpp000005 + capRiseUpp005030 - percUpp005030 - actTranspiUpp005030 - capRiseUpp000005
            self.storUpp005030 = pcr.max(
                0.0,
                self.storUpp005030
                + self.percUpp000005
                + self.capRiseUpp005030
                - (
                    self.percUpp005030
                    + self.actTranspiUpp005030
                    + self.capRiseUpp000005
                ),
            )
            # if necessary, reduce the percolation input
            percUpp000005 = self.percUpp000005
            self.percUpp000005 = pcr.max(
                0.0,
                percUpp000005
                - pcr.max(0.0, self.storUpp005030 - self.parameters.storCapUpp005030),
            )
            self.storUpp005030 = self.storUpp005030 - percUpp000005 + self.percUpp000005
            # if necessary, reduce the capillary rise input
            capRiseUpp005030 = self.capRiseUpp005030
            self.capRiseUpp005030 = pcr.max(
                0.0,
                capRiseUpp005030
                - pcr.max(0.0, self.storUpp005030 - self.parameters.storCapUpp005030),
            )
            self.storUpp005030 = (
                self.storUpp005030 - capRiseUpp005030 + self.capRiseUpp005030
            )
            # if necessary, introduce interflow outflow
            self.interflowUpp005030 = pcr.max(
                0.0, self.storUpp005030 - self.parameters.storCapUpp005030
            )
            self.storUpp005030 = self.storUpp005030 - self.interflowUpp005030

            # update storUpp000005: + infiltration + capRiseUpp000005 - percUpp000005 - actTranspiUpp000005 - actBareSoilEvap
            self.storUpp000005 = pcr.max(
                0.0,
                self.storUpp000005
                + self.infiltration
                + self.capRiseUpp000005
                - (
                    self.percUpp000005 + self.actTranspiUpp000005 + self.actBareSoilEvap
                ),
            )
            # any excess above storCapUpp goes to topWaterLayer
            self.satExcess = pcr.max(
                0.0, self.storUpp000005 - self.parameters.storCapUpp000005
            )
            self.topWaterLayer = self.topWaterLayer + self.satExcess

            # any excess above minTopWaterLayer is released as directRunoff
            self.directRunoff = self.directRunoff + pcr.max(
                0.0, self.topWaterLayer - self.minTopWaterLayer
            )

            # make sure storage capacities are not exceeded
            self.topWaterLayer = pcr.min(self.topWaterLayer, self.minTopWaterLayer)
            self.storUpp000005 = pcr.min(
                self.storUpp000005, self.parameters.storCapUpp000005
            )
            self.storUpp005030 = pcr.min(
                self.storUpp005030, self.parameters.storCapUpp005030
            )
            self.storLow030150 = pcr.min(
                self.storLow030150, self.parameters.storCapLow030150
            )

            # total actual evaporation and transpiration
            self.actualET += (
                self.actBareSoilEvap
                + self.openWaterEvap
                + self.actTranspiUpp000005
                + self.actTranspiUpp005030
                + self.actTranspiLow030150
            )

            # total actual transpiration
            self.actTranspiUppTotal = (
                self.actTranspiUpp000005 + self.actTranspiUpp005030
            )

            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUppTotal + self.actTranspiLow030150

            # net percolation between the upper soil stores (positive downward)
            self.netPercUpp000005 = self.percUpp000005 - self.capRiseUpp000005
            self.netPercUpp005030 = self.percUpp005030 - self.capRiseUpp005030

            # groundwater recharge
            self.gwRecharge = self.percLow030150 - self.capRiseLow030150

            # for comparison with the 2-layer model output
            self.storUppTotal = self.storUpp000005 + self.storUpp005030
            self.storLowTotal = self.storLow030150
            self.actTranspiUppTotal = (
                self.actTranspiUpp000005 + self.actTranspiUpp005030
            )
            self.actTranspiLowTotal = self.actTranspiLow030150
            self.interflowTotal = self.interflow + self.interflowUpp005030

        # variables/states defined in both the 2- and 3-layer models

        # landSurfaceRunoff (needed for routing)
        self.landSurfaceRunoff = self.directRunoff + self.interflowTotal

    def upperSoilUpdate(
        self, capRiseFrac, currTimeStep, satisfied_irrigation_water_height, groundwater
    ):

        if self.debugWaterBalance:
            netLqWaterToSoil = self.netLqWaterToSoil
            preTopWaterLayer = self.topWaterLayer
            if self.numberOfLayers == 2:
                preStorUpp = self.storUpp
                preStorLow = self.storLow
            if self.numberOfLayers == 3:
                preStorUpp000005 = self.storUpp000005
                preStorUpp005030 = self.storUpp005030
                preStorLow030150 = self.storLow030150

        # derived states from the soil storages: effective degree of saturation, unsaturated hydraulic
        # conductivity and readily available water within the root zone
        self.getSoilStates()

        # open water evaporation from paddy fields, and update topWaterLayer (including irrigation water)
        self.calculateOpenWaterEvap(satisfied_irrigation_water_height)

        # directRunoff and infiltration with the improved Arno scheme (Hageman and Gates, 2003), and update topWaterLayer
        self.calculateDirectRunoff()
        self.calculateInfiltration()

        # bare soil evaporation and transpiration
        if self.numberOfLayers == 2:
            self.actBareSoilEvap, self.actTranspiUpp, self.actTranspiLow = (
                self.estimateTranspirationAndBareSoilEvap()
            )
        if self.numberOfLayers == 3:
            (
                self.actBareSoilEvap,
                self.actTranspiUpp000005,
                self.actTranspiUpp005030,
                self.actTranspiLow030150,
            ) = self.estimateTranspirationAndBareSoilEvap()

        # percolation, capillary rise and interflow
        self.estimateSoilFluxes(capRiseFrac, groundwater)

        # limit all fluxes to the available (source) storage
        if self.name.startswith("irr") and self.includeIrrigation:
            self.scaleAllFluxesForIrrigatedAreas(groundwater)
        else:
            self.scaleAllFluxes(groundwater)

        # update all soil states (including the final/corrected fluxes)
        self.updateSoilStates()

        # irrigation transpiration deficit for reporting
        self.irrigationTranspirationDeficit = 0.0
        if self.name.startswith("irr"):
            self.irrigationTranspirationDeficit = pcr.max(
                0.0, self.potTranspiration - self.actTranspiTotal
            )

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [netLqWaterToSoil, satisfied_irrigation_water_height, self.satExcess],
                [self.directRunoff, self.openWaterEvap, self.infiltration],
                [preTopWaterLayer],
                [self.topWaterLayer],
                "topWaterLayer",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )

            if self.numberOfLayers == 2:
                vos.waterBalanceCheck(
                    [self.infiltration, self.capRiseUpp],
                    [
                        self.actTranspiUpp,
                        self.percUpp,
                        self.actBareSoilEvap,
                        self.satExcess,
                    ],
                    [preStorUpp],
                    [self.storUpp],
                    "storUpp",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-5,
                )
                vos.waterBalanceCheck(
                    [self.percUpp],
                    [
                        self.actTranspiLow,
                        self.gwRecharge,
                        self.interflow,
                        self.capRiseUpp,
                    ],
                    [preStorLow],
                    [self.storLow],
                    "storLow",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-5,
                )
                vos.waterBalanceCheck(
                    [self.infiltration, self.capRiseLow],
                    [
                        self.satExcess,
                        self.interflow,
                        self.percLow,
                        self.actTranspiUpp,
                        self.actTranspiLow,
                        self.actBareSoilEvap,
                    ],
                    [preStorUpp, preStorLow],
                    [self.storUpp, self.storLow],
                    "entireSoilLayers",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-4,
                )
                vos.waterBalanceCheck(
                    [
                        netLqWaterToSoil,
                        self.capRiseLow,
                        satisfied_irrigation_water_height,
                    ],
                    [
                        self.directRunoff,
                        self.interflow,
                        self.percLow,
                        self.actTranspiUpp,
                        self.actTranspiLow,
                        self.actBareSoilEvap,
                        self.openWaterEvap,
                    ],
                    [preTopWaterLayer, preStorUpp, preStorLow],
                    [self.topWaterLayer, self.storUpp, self.storLow],
                    "allLayers",
                    True,
                    currTimeStep.fulldate,
                    threshold=5e-4,
                )

            if self.numberOfLayers == 3:
                vos.waterBalanceCheck(
                    [self.infiltration, self.capRiseUpp000005],
                    [
                        self.actTranspiUpp000005,
                        self.percUpp000005,
                        self.actBareSoilEvap,
                        self.satExcess,
                    ],
                    [preStorUpp000005],
                    [self.storUpp000005],
                    "storUpp000005",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-5,
                )

                vos.waterBalanceCheck(
                    [self.percUpp000005, self.capRiseUpp005030],
                    [
                        self.actTranspiUpp005030,
                        self.percUpp005030,
                        self.interflowUpp005030,
                        self.capRiseUpp000005,
                    ],
                    [preStorUpp005030],
                    [self.storUpp005030],
                    "storUpp005030",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-5,
                )
                vos.waterBalanceCheck(
                    [self.percUpp005030],
                    [
                        self.actTranspiLow030150,
                        self.gwRecharge,
                        self.interflow,
                        self.capRiseUpp005030,
                    ],
                    [preStorLow030150],
                    [self.storLow030150],
                    "storLow030150",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-5,
                )
                vos.waterBalanceCheck(
                    [self.infiltration, self.capRiseLow030150],
                    [
                        self.satExcess,
                        self.interflow,
                        self.interflowUpp005030,
                        self.percLow030150,
                        self.actTranspiUpp000005,
                        self.actTranspiUpp005030,
                        self.actTranspiLow030150,
                        self.actBareSoilEvap,
                    ],
                    [preStorUpp000005, preStorUpp005030, preStorLow030150],
                    [self.storUpp000005, self.storUpp005030, self.storLow030150],
                    "entireSoilLayers",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-4,
                )
                vos.waterBalanceCheck(
                    [
                        netLqWaterToSoil,
                        self.capRiseLow030150,
                        satisfied_irrigation_water_height,
                    ],
                    [
                        self.directRunoff,
                        self.interflow,
                        self.interflowUpp005030,
                        self.percLow030150,
                        self.actTranspiUpp000005,
                        self.actTranspiUpp005030,
                        self.actTranspiLow030150,
                        self.actBareSoilEvap,
                        self.openWaterEvap,
                    ],
                    [
                        preTopWaterLayer,
                        preStorUpp000005,
                        preStorUpp005030,
                        preStorLow030150,
                    ],
                    [
                        self.topWaterLayer,
                        self.storUpp000005,
                        self.storUpp005030,
                        self.storLow030150,
                    ],
                    "allLayers",
                    True,
                    currTimeStep.fulldate,
                    threshold=1e-4,
                )
