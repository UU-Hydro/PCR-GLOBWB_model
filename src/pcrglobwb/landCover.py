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
        except:
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
        if get_only_fracVegCover == False:
            for var in landCovParams + ["arnoBeta"]:
                lc_parameters[var] = None

        # parameters that are fixed for the entire simulation
        if date_in_string == None:

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
                and get_only_fracVegCover == False
            ):
                self.iniItemsLC["arnoBeta"] = "None"

            # option 1 (top priority): a PCRaster file
            if self.iniItemsLC["arnoBeta"] != "None" and get_only_fracVegCover == False:

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
        if date_in_string != None:

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
                    except:
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

        if self.numberOfLayers == 2 and get_only_fracVegCover == False:

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
        if self.numberOfLayers == 3 and get_only_fracVegCover == False:

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
            if self.usingOriginalOldCalcRootTranspirationPartitioningMethod == False:
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
            if self.usingOriginalOldCalcRootTranspirationPartitioningMethod == False:
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

    def scaleRootFractionsOLD(self):

        if self.numberOfLayers == 2:
            # root fractions
            rootFracUpp = (0.30 / 0.30) * self.rootFraction1
            rootFracLow = (1.20 / 1.20) * self.rootFraction2
            # Rens: RFW1[TYPE]= RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])
            self.adjRootFrUpp = rootFracUpp / (rootFracUpp + rootFracLow)
            # Rens: RFW2[TYPE]= RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])
            self.adjRootFrLow = rootFracLow / (rootFracUpp + rootFracLow)
            # if not defined, put everything in the first layer
            self.adjRootFrUpp = pcr.min(1.0, pcr.cover(self.adjRootFrUpp, 1.0))
            self.adjRootFrLow = pcr.scalar(1.0) - self.adjRootFrUpp

        if self.numberOfLayers == 3:
            # root fractions
            rootFracUpp000005 = 0.05 / 0.30 * self.rootFraction1
            rootFracUpp005030 = 0.25 / 0.30 * self.rootFraction1
            rootFracLow030150 = 1.20 / 1.20 * self.rootFraction2
            self.adjRootFrUpp000005 = rootFracUpp000005 / (
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150
            )
            self.adjRootFrUpp005030 = rootFracUpp005030 / (
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150
            )
            self.adjRootFrLow030150 = rootFracLow030150 / (
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150
            )
            # if not defined, put everything in the first layer
            self.adjRootFrUpp000005 = pcr.min(
                1.0, pcr.cover(self.adjRootFrUpp000005, 1.0)
            )
            self.adjRootFrUpp005030 = pcr.ifthenelse(
                self.adjRootFrUpp000005 < 1.0, self.adjRootFrUpp005030, 0.0
            )
            self.adjRootFrLow030150 = pcr.scalar(1.0) - (
                self.adjRootFrUpp000005 + self.adjRootFrUpp005030
            )

    def scaleRootFractionsAlternativeOLD(self):

        if self.numberOfLayers == 2:
            # root fractions
            rootFracUpp = (0.30 / 0.30) * self.rootFraction1
            rootFracLow = (1.20 / 1.20) * self.rootFraction2
            self.adjRootFrUpp = pcr.ifthenelse(
                rootFracUpp + rootFracLow > 0.0,
                pcr.min(1.0, rootFracUpp / (rootFracUpp + rootFracLow)),
                0.0,
            )
            self.adjRootFrLow = pcr.ifthenelse(
                rootFracUpp + rootFracLow > 0.0,
                pcr.min(1.0, rootFracLow / (rootFracUpp + rootFracLow)),
                0.0,
            )

            # Rens (weighted root fractions): RFW1[TYPE]= if(RFRAC1[TYPE]+RFRAC2[TYPE] > 0,min(1.0,RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])),0.0)
            # RFW2[TYPE]= if(RFRAC1[TYPE]+RFRAC2[TYPE] > 0.0,min(1.0,RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])),0.0)

        if self.numberOfLayers == 3:
            # root fractions
            rootFracUpp000005 = 0.05 / 0.30 * self.rootFraction1
            rootFracUpp005030 = 0.25 / 0.30 * self.rootFraction1
            rootFracLow030150 = 1.20 / 1.20 * self.rootFraction2
            self.adjRootFrUpp000005 = pcr.ifthenelse(
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0,
                pcr.min(
                    1.0,
                    rootFracUpp000005
                    / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
                ),
                0.0,
            )
            self.adjRootFrUpp005030 = pcr.ifthenelse(
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0,
                pcr.min(
                    1.0,
                    rootFracUpp005030
                    / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
                ),
                0.0,
            )
            self.adjRootFrLow030150 = pcr.ifthenelse(
                rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0,
                pcr.min(
                    1.0,
                    rootFracLow030150
                    / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150),
                ),
                0.0,
            )

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
                if iniConditions == None:
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
                if iniConditions == None:
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
        if self.noAnnualChangesInLandCoverParameter == False and (
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
        if self.interceptCapNC != None and self.coverFractionNC != None:
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

        if self.report == True:
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
                    if currTimeStep.endMonth == True:
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
                    if currTimeStep.endMonth == True:
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
                    if currTimeStep.endMonth == True:
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

        if self.transport_water == True:
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
        if self.transport_water == True:
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

    def OLD_calculateWaterDemand(
        self,
        nonIrrGrossDemandDict,
        swAbstractionFractionDict,
        groundwater,
        routing,
        allocSegments,
        currTimeStep,
        desalinationWaterUse,
        groundwater_pumping_region_ids,
        regionalAnnualGroundwaterAbstractionLimit,
    ):

        # irrigation water demand (m/day) for paddy and non-paddy fields
        self.irrGrossDemand = pcr.scalar(0.0)
        if (
            self.name == "irrPaddy" or self.name == "irr_paddy"
        ) and self.includeIrrigation:
            # function of cropKC (evaporation and transpiration) and topWaterLayer (water in the field)
            self.irrGrossDemand = pcr.ifthenelse(
                self.cropKC > 0.75,
                pcr.max(0.0, self.minTopWaterLayer - (self.topWaterLayer)),
                0.0,
            )

        if (
            self.name == "irrNonPaddy"
            or self.name == "irr_non_paddy"
            or self.name == "irr_non_paddy_crops"
        ) and self.includeIrrigation:

            # original formula from Allen et al. (1998); see http://www.fao.org/docrep/x0490e/x0490e0e.htm
            adjDeplFactor = pcr.max(
                0.1,
                pcr.min(
                    0.8, (self.cropDeplFactor + 0.04 * (5.0 - self.totalPotET * 1000.0))
                ),
            )

            # irrigation demand to fill totAvlWater (maintaining field capacity), corrected for rooting depth
            # with the crop coefficient as a proxy
            self.irrigation_factor = pcr.ifthenelse(
                self.cropKC > 0.0, pcr.min(1.0, self.cropKC / 1.0), 0.0
            )
            self.irrGrossDemand = pcr.ifthenelse(
                self.cropKC > 0.20,
                pcr.ifthenelse(
                    self.readAvlWater
                    < adjDeplFactor * self.irrigation_factor * self.totAvlWater,
                    pcr.max(
                        0.0,
                        self.totAvlWater * self.irrigation_factor - self.readAvlWater,
                    ),
                    0.0,
                ),
                0.0,
            )

            # irrigate only if there is a deficit in transpiration and/or evaporation
            deficit_factor = 1.00
            evaporationDeficit = pcr.max(
                0.0,
                (self.potBareSoilEvap + self.potTranspiration) * deficit_factor
                - self.estimateTranspirationAndBareSoilEvap(returnTotalEstimation=True),
            )
            transpirationDeficit = pcr.max(
                0.0,
                self.potTranspiration * deficit_factor
                - self.estimateTranspirationAndBareSoilEvap(
                    returnTotalEstimation=True, returnTotalTranspirationOnly=True
                ),
            )
            deficit = pcr.max(evaporationDeficit, transpirationDeficit)
            # threshold to start irrigating
            deficit_treshold = 0.20 * self.totalPotET
            need_irrigation = pcr.ifthenelse(
                deficit > deficit_treshold,
                pcr.boolean(1),
                pcr.ifthenelse(
                    self.soilWaterStorage == 0.000, pcr.boolean(1), pcr.boolean(0)
                ),
            )
            need_irrigation = pcr.cover(need_irrigation, pcr.boolean(0.0))
            self.irrGrossDemand = pcr.ifthenelse(
                need_irrigation, self.irrGrossDemand, 0.0
            )

            # limit the demand by the potential evaporation of the coming days, to avoid unrealistically high demands
            max_irrigation_interval = 15.0
            min_irrigation_interval = 7.0
            irrigation_interval = pcr.min(
                max_irrigation_interval,
                pcr.max(
                    min_irrigation_interval,
                    pcr.ifthenelse(
                        self.totalPotET > 0.0,
                        pcr.roundup(
                            (
                                self.irrGrossDemand
                                + pcr.max(self.readAvlWater, self.soilWaterStorage)
                            )
                            / self.totalPotET
                        ),
                        1.0,
                    ),
                ),
            )
            # irrigation demand, limited by the potential evaporation of the coming days
            self.irrGrossDemand = pcr.min(
                pcr.max(
                    0.0,
                    self.totalPotET * irrigation_interval
                    - pcr.max(self.readAvlWater, self.soilWaterStorage),
                ),
                self.irrGrossDemand,
            )

            # assume that smart farmers do not irrigate more than the infiltration capacity
            if self.numberOfLayers == 2:
                self.irrGrossDemand = pcr.min(
                    self.irrGrossDemand, self.parameters.kSatUpp
                )
            if self.numberOfLayers == 3:
                self.irrGrossDemand = pcr.min(
                    self.irrGrossDemand, self.parameters.kSatUpp000005
                )

        # irrigation efficiency, minimum demand to start irrigating and maximum demand
        if self.includeIrrigation:

            # irrigation efficiency; TODO: improve the concept of irrigation efficiency
            self.irrigationEfficiencyUsed = pcr.min(
                1.0, pcr.max(0.10, self.irrigationEfficiency)
            )
            # demand including inefficiency
            self.irrGrossDemand = pcr.cover(
                self.irrGrossDemand / pcr.min(1.0, self.irrigationEfficiencyUsed), 0.0
            )

            # this demand is not limited by the available water
            self.irrGrossDemand = pcr.ifthen(self.landmask, self.irrGrossDemand)

            # reduce irrGrossDemand by netLqWaterToSoil
            self.irrGrossDemand = pcr.max(
                0.0, self.irrGrossDemand - self.netLqWaterToSoil
            )

            # minimum demand to start irrigating (m/day); TODO: set in the ini file
            minimum_demand = 0.005
            if self.name == "irrPaddy" or self.name == "irr_paddy":
                minimum_demand = pcr.min(self.minTopWaterLayer, 0.025)
            self.irrGrossDemand = pcr.ifthenelse(
                self.irrGrossDemand > minimum_demand, self.irrGrossDemand, 0.0
            )

            # maximum demand (m/day); TODO: set in the ini file
            maximum_demand = 0.025
            if self.name == "irrPaddy" or self.name == "irr_paddy":
                maximum_demand = pcr.min(self.minTopWaterLayer, 0.025)
            self.irrGrossDemand = pcr.min(maximum_demand, self.irrGrossDemand)

            # ignore small demands (less than 1 mm)
            self.irrGrossDemand = pcr.rounddown(self.irrGrossDemand * 1000.0) / 1000.0

            # only for areas with fracVegCover > 0; TODO: check whether this is needed
            self.irrGrossDemand = pcr.ifthenelse(
                self.fracVegCover > 0.0, self.irrGrossDemand, 0.0
            )

        # total gross irrigation demand (m) per cover type (not limited by available water)
        self.totalPotentialMaximumIrrGrossDemandPaddy = 0.0
        self.totalPotentialMaximumIrrGrossDemandNonPaddy = 0.0
        if self.name == "irrPaddy" or self.name == "irr_paddy":
            self.totalPotentialMaximumIrrGrossDemandPaddy = self.irrGrossDemand
        if (
            self.name == "irrNonPaddy"
            or self.name == "irr_non_paddy"
            or self.name == "irr_non_paddy_crops"
        ):
            self.totalPotentialMaximumIrrGrossDemandNonPaddy = self.irrGrossDemand

        # only for areas with fracVegCover > 0; TODO: check whether this is needed
        nonIrrGrossDemandDict["potential_demand"]["domestic"] = pcr.ifthenelse(
            self.fracVegCover > 0.0,
            nonIrrGrossDemandDict["potential_demand"]["domestic"],
            0.0,
        )
        nonIrrGrossDemandDict["potential_demand"]["industry"] = pcr.ifthenelse(
            self.fracVegCover > 0.0,
            nonIrrGrossDemandDict["potential_demand"]["industry"],
            0.0,
        )
        nonIrrGrossDemandDict["potential_demand"]["livestock"] = pcr.ifthenelse(
            self.fracVegCover > 0.0,
            nonIrrGrossDemandDict["potential_demand"]["livestock"],
            0.0,
        )

        # non-irrigation water demand, including livestock (not limited by available water)
        self.nonIrrGrossDemand = (
            nonIrrGrossDemandDict["potential_demand"]["domestic"]
            + nonIrrGrossDemandDict["potential_demand"]["industry"]
            + nonIrrGrossDemandDict["potential_demand"]["livestock"]
        )

        # total irrigation and livestock demand (not limited by available water)
        totalIrrigationLivestockDemand = (
            self.irrGrossDemand + nonIrrGrossDemandDict["potential_demand"]["livestock"]
        )

        # total gross demand (m) of irrigation and non-irrigation (not limited by available water, not reduced)
        self.totalPotentialMaximumGrossDemand = (
            self.irrGrossDemand + self.nonIrrGrossDemand
        )
        # irrigation (excluding livestock)
        self.totalPotentialMaximumIrrGrossDemand = self.irrGrossDemand
        # non-irrigation (including livestock)
        self.totalPotentialMaximumNonIrrGrossDemand = self.nonIrrGrossDemand

        # reduced by the available/accessible water
        self.totalPotentialGrossDemand = self.totalPotentialMaximumGrossDemand

        # abstraction and allocation of desalinated water, using the allocation zones defined in the
        # landSurface options
        if self.usingAllocSegments:
            logger.debug("Allocation of supply from desalination water.")
            volDesalinationAbstraction, volDesalinationAllocation = (
                vos.waterAbstractionAndAllocation(
                    water_demand_volume=self.totalPotentialGrossDemand
                    * routing.cellArea,
                    available_water_volume=pcr.max(
                        0.00, desalinationWaterUse * routing.cellArea
                    ),
                    allocation_zones=allocSegments,
                    zone_area=self.segmentArea,
                    high_volume_treshold=None,
                    debug_water_balance=True,
                    extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                    landmask=self.landmask,
                    ignore_small_values=False,
                    prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
                )
            )
            self.desalinationAbstraction = volDesalinationAbstraction / routing.cellArea
            self.desalinationAllocation = volDesalinationAllocation / routing.cellArea
        else:
            logger.debug(
                "Supply from desalination water is only for satisfying local demand (no network)."
            )
            self.desalinationAbstraction = pcr.min(
                desalinationWaterUse, self.totalPotentialGrossDemand
            )
            self.desalinationAllocation = self.desalinationAbstraction
        self.desalinationAbstraction = pcr.ifthen(
            self.landmask, self.desalinationAbstraction
        )
        self.desalinationAllocation = pcr.ifthen(
            self.landmask, self.desalinationAllocation
        )

        # water demand satisfied after desalination (m/day): irrigation (excluding livestock)
        satisfiedIrrigationDemand = (
            vos.getValDivZero(self.irrGrossDemand, self.totalPotentialGrossDemand)
            * self.desalinationAllocation
        )
        # domestic, industry and livestock
        satisfiedNonIrrDemand = pcr.max(
            0.00, self.desalinationAllocation - satisfiedIrrigationDemand
        )
        # domestic
        satisfiedDomesticDemand = satisfiedNonIrrDemand * vos.getValDivZero(
            nonIrrGrossDemandDict["potential_demand"]["domestic"],
            self.totalPotentialMaximumNonIrrGrossDemand,
        )
        # industry
        satisfiedIndustryDemand = satisfiedNonIrrDemand * vos.getValDivZero(
            nonIrrGrossDemandDict["potential_demand"]["industry"],
            self.totalPotentialMaximumNonIrrGrossDemand,
        )
        # livestock
        satisfiedLivestockDemand = pcr.max(
            0.0,
            satisfiedNonIrrDemand - satisfiedDomesticDemand - satisfiedIndustryDemand,
        )

        # total remaining gross demand after desalination (m/day)
        self.totalGrossDemandAfterDesalination = pcr.max(
            0.0, self.totalPotentialGrossDemand - self.desalinationAllocation
        )
        # remaining water demand per sector: domestic
        remainingDomestic = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["domestic"]
            - satisfiedDomesticDemand,
        )
        # industry
        remainingIndustry = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["industry"]
            - satisfiedIndustryDemand,
        )
        # livestock
        remainingLivestock = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["livestock"]
            - satisfiedLivestockDemand,
        )
        # irrigation (excluding livestock)
        remainingIrrigation = pcr.max(
            0.0, self.irrGrossDemand - satisfiedIrrigationDemand
        )
        # livestock and irrigation
        remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
        # industrial and domestic (excluding livestock)
        remainingIndustrialDomestic = pcr.max(
            0.0, self.totalGrossDemandAfterDesalination - remainingIrrigationLivestock
        )

        # abstraction and allocation of surface water, with the surface water demand estimated from
        # swAbstractionFractionDict: industrial and domestic
        swAbstractionFraction_industrial_domestic = pcr.min(
            swAbstractionFractionDict["max_for_non_irrigation"],
            swAbstractionFractionDict["estimate"],
        )
        if swAbstractionFractionDict["non_irrigation"] is not None:
            swAbstractionFraction_industrial_domestic = swAbstractionFractionDict[
                "non_irrigation"
            ]

        surface_water_demand_estimate = (
            swAbstractionFraction_industrial_domestic * remainingIndustrialDomestic
        )
        # irrigation and livestock
        surface_water_irrigation_demand_estimate = (
            swAbstractionFractionDict["irrigation"] * remainingIrrigationLivestock
        )
        # prioritize surface water if the groundwater irrigation fraction is relatively low
        surface_water_irrigation_demand_estimate = pcr.ifthenelse(
            swAbstractionFractionDict["irrigation"]
            >= swAbstractionFractionDict[
                "treshold_to_maximize_irrigation_surface_water"
            ],
            remainingIrrigationLivestock,
            surface_water_irrigation_demand_estimate,
        )
        # update the estimate of the surface water demand (m/day)
        surface_water_demand_estimate += surface_water_irrigation_demand_estimate
        # prioritize surface water in non-productive aquifers with limited groundwater supply
        surface_water_demand_estimate = pcr.ifthenelse(
            groundwater.productive_aquifer,
            surface_water_demand_estimate,
            pcr.max(
                0.0,
                remainingIrrigationLivestock
                - pcr.min(groundwater.avgAllocationShort, groundwater.avgAllocation),
            ),
        )
        # maximize surface water use in areas where groundwater supply is overestimated
        surface_water_demand_estimate += pcr.max(
            0.0,
            pcr.max(groundwater.avgAllocationShort, groundwater.avgAllocation)
            - (1.0 - swAbstractionFractionDict["irrigation"])
            * totalIrrigationLivestockDemand
            - (1.0 - swAbstractionFraction_industrial_domestic)
            * (self.totalPotentialMaximumGrossDemand - totalIrrigationLivestockDemand),
        )
        # total demand to allocate from surface water (m/day), limited by swAbstractionFractionDict and the
        # remaining demand
        surface_water_demand_estimate = pcr.min(
            self.totalGrossDemandAfterDesalination, surface_water_demand_estimate
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
            surface_water_demand = self.totalGrossDemandAfterDesalination
        # using the allocation zones of the supply network
        if self.usingAllocSegments:
            logger.debug("Allocation of surface water abstraction.")
            volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = (
                vos.waterAbstractionAndAllocation(
                    water_demand_volume=surface_water_demand * routing.cellArea,
                    available_water_volume=pcr.max(0.00, routing.readAvlChannelStorage),
                    allocation_zones=allocSegments,
                    zone_area=self.segmentArea,
                    high_volume_treshold=None,
                    debug_water_balance=True,
                    extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                    landmask=self.landmask,
                    ignore_small_values=False,
                    prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
                )
            )

            self.actSurfaceWaterAbstract = volActSurfaceWaterAbstract / routing.cellArea
            self.allocSurfaceWaterAbstract = (
                volAllocSurfaceWaterAbstract / routing.cellArea
            )
        else:
            logger.debug(
                "Surface water abstraction is only to satisfy local demand (no surface water network)."
            )
            # (m)
            self.actSurfaceWaterAbstract = pcr.min(
                routing.readAvlChannelStorage / routing.cellArea, surface_water_demand
            )
            # (m)
            self.allocSurfaceWaterAbstract = self.actSurfaceWaterAbstract
        self.actSurfaceWaterAbstract = pcr.ifthen(
            self.landmask, self.actSurfaceWaterAbstract
        )
        self.allocSurfaceWaterAbstract = pcr.ifthen(
            self.landmask, self.allocSurfaceWaterAbstract
        )

        # water demand satisfied after desalination and surface water supply (m/day): irrigation and livestock
        satisfiedIrrigationLivestockDemandFromSurfaceWater = (
            self.allocSurfaceWaterAbstract
            * vos.getValDivZero(
                correctedRemainingIrrigationLivestock,
                correctedSurfaceWaterDemandEstimate,
            )
        )
        # irrigation (excluding livestock)
        satisfiedIrrigationDemandFromSurfaceWater = (
            satisfiedIrrigationLivestockDemandFromSurfaceWater
            * vos.getValDivZero(remainingIrrigation, remainingIrrigationLivestock)
        )
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromSurfaceWater
        # non-irrigation: livestock, domestic and industry
        satisfiedNonIrrDemandFromSurfaceWater = pcr.max(
            0.0,
            self.allocSurfaceWaterAbstract - satisfiedIrrigationDemandFromSurfaceWater,
        )
        satisfiedNonIrrDemand += satisfiedNonIrrDemandFromSurfaceWater
        # livestock
        satisfiedLivestockDemand += pcr.max(
            0.0,
            satisfiedIrrigationLivestockDemandFromSurfaceWater
            - satisfiedIrrigationDemandFromSurfaceWater,
        )
        # industrial and domestic (excluding livestock)
        satisfiedIndustrialDomesticDemandFromSurfaceWater = pcr.max(
            0.0,
            self.allocSurfaceWaterAbstract
            - satisfiedIrrigationLivestockDemandFromSurfaceWater,
        )
        # domestic
        satisfiedDomesticDemand += (
            satisfiedIndustrialDomesticDemandFromSurfaceWater
            * vos.getValDivZero(remainingDomestic, remainingIndustrialDomestic)
        )
        # industry
        satisfiedIndustryDemand += (
            satisfiedIndustrialDomesticDemandFromSurfaceWater
            * vos.getValDivZero(remainingIndustry, remainingIndustrialDomestic)
        )

        # demand to be satisfied by groundwater abstraction (m), not limited by available water
        self.potGroundwaterAbstract = pcr.max(
            0.0, self.totalGrossDemandAfterDesalination - self.allocSurfaceWaterAbstract
        )
        # water demand per sector: domestic
        remainingDomestic = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["domestic"]
            - satisfiedDomesticDemand,
        )
        # industry
        remainingIndustry = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["industry"]
            - satisfiedIndustryDemand,
        )
        # livestock
        remainingLivestock = pcr.max(
            0.0,
            nonIrrGrossDemandDict["potential_demand"]["livestock"]
            - satisfiedLivestockDemand,
        )
        # irrigation (excluding livestock)
        remainingIrrigation = pcr.max(
            0.0, self.irrGrossDemand - satisfiedIrrigationDemand
        )
        # livestock and irrigation
        remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
        # industrial and domestic (excluding livestock)
        remainingIndustrialDomestic = remainingIndustry + remainingDomestic

        # abstraction and allocation of groundwater (fossil and non-fossil); groundwater demand of the
        # industrial and domestic sectors (all remaining demand must be satisfied)
        groundwater_demand_estimate = remainingIndustrialDomestic
        # demand of the irrigation and livestock sectors (only partly satisfied, as it may be too high due
        # to the uncertainty in the irrigation scheme)
        irrigationLivestockGroundwaterDemand = pcr.min(
            remainingIrrigationLivestock,
            pcr.max(
                0.0,
                (1.0 - swAbstractionFractionDict["irrigation"])
                * totalIrrigationLivestockDemand,
            ),
        )
        groundwater_demand_estimate += irrigationLivestockGroundwaterDemand

        # demand to be satisfied by groundwater abstraction, not limited by available water
        self.potGroundwaterAbstract = pcr.min(
            self.potGroundwaterAbstract, groundwater_demand_estimate
        )

        # constrain groundwater abstraction with the regional annual pumping capacity
        if groundwater.limitRegionalAnnualGroundwaterAbstraction:

            logger.debug(
                "Total groundwater abstraction is limited by regional annual pumping capacity."
            )

            # total groundwater abstraction over the last 365 days (m3)
            tolerating_days = 0.0
            annualGroundwaterAbstraction = (
                groundwater.avgAbstraction
                * routing.cellArea
                * pcr.min(
                    pcr.max(0.0, 365.0 - tolerating_days),
                    routing.timestepsToAvgDischarge,
                )
            )
            # total regional groundwater abstraction over the last 365 days (m3)
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(
                pcr.cover(annualGroundwaterAbstraction, 0.0),
                groundwater_pumping_region_ids,
            )

            # new method (still under development)
            # remaining regional pumping capacity (m3)
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.max(
                0.0,
                regionalAnnualGroundwaterAbstractionLimit
                - regionalAnnualGroundwaterAbstraction,
            )
            # safety factor (residence time, day-1)
            remainingRegionalAnnualGroundwaterAbstractionLimit *= 0.33

            # remaining regional pumping capacity (m3), limited by potGroundwaterAbstract
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.min(
                remainingRegionalAnnualGroundwaterAbstractionLimit,
                pcr.areatotal(
                    self.potGroundwaterAbstract * routing.cellArea,
                    groundwater_pumping_region_ids,
                ),
            )

            # remaining pumping capacity per cell (m3), downscaled using potGroundwaterAbstract
            remainingPixelAnnualGroundwaterAbstractionLimit = (
                remainingRegionalAnnualGroundwaterAbstractionLimit
                * vos.getValDivZero(
                    self.potGroundwaterAbstract * routing.cellArea,
                    pcr.areatotal(
                        self.potGroundwaterAbstract * routing.cellArea,
                        groundwater_pumping_region_ids,
                    ),
                )
            )

            # reduced potential groundwater abstraction (m), considering the pumping capacity and average recharge (baseflow)
            self.potGroundwaterAbstract = pcr.min(
                self.potGroundwaterAbstract,
                remainingPixelAnnualGroundwaterAbstractionLimit / routing.cellArea
                + pcr.max(0.0, routing.avgBaseflow / routing.cellArea),
            )

        else:
            logger.debug(
                "NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction."
            )

        # abstraction and allocation of non-fossil groundwater;
        # accessible non-fossil groundwater storage (m)
        readAvlStorGroundwater = pcr.cover(
            pcr.max(0.00, groundwater.storGroundwater), 0.0
        )
        # maximum daily groundwater abstraction
        readAvlStorGroundwater = pcr.min(
            readAvlStorGroundwater, groundwater.maximumDailyGroundwaterAbstraction
        )
        # ignore groundwater storage in non-productive aquifers
        readAvlStorGroundwater = pcr.ifthenelse(
            groundwater.productive_aquifer, readAvlStorGroundwater, 0.0
        )

        # in non-productive aquifers, limit readAvlStorGroundwater to the current recharge (baseflow)
        readAvlStorGroundwater = pcr.ifthenelse(
            groundwater.productive_aquifer,
            readAvlStorGroundwater,
            pcr.min(readAvlStorGroundwater, pcr.max(routing.avgBaseflow, 0.0)),
        )

        # avoid abstracting the entire groundwater volume at once
        readAvlStorGroundwater *= 0.75

        if groundwater.usingAllocSegments:

            logger.debug("Allocation of non fossil groundwater abstraction.")

            # TODO: consider aquifer productivity in the allocation (e.g. using aquifer transmissivity/conductivity)

            # non-fossil groundwater abstraction and allocation (m3)
            volActGroundwaterAbstract, volAllocGroundwaterAbstract = (
                vos.waterAbstractionAndAllocation(
                    water_demand_volume=self.potGroundwaterAbstract * routing.cellArea,
                    available_water_volume=pcr.max(
                        0.00, readAvlStorGroundwater * routing.cellArea
                    ),
                    allocation_zones=groundwater.allocSegments,
                    zone_area=groundwater.segmentArea,
                    high_volume_treshold=None,
                    debug_water_balance=True,
                    extra_info_for_water_balance_reporting=str(currTimeStep.fulldate),
                    landmask=self.landmask,
                    ignore_small_values=False,
                    prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
                )
            )

            # (m)
            self.nonFossilGroundwaterAbs = volActGroundwaterAbstract / routing.cellArea
            self.allocNonFossilGroundwater = (
                volAllocGroundwaterAbstract / routing.cellArea
            )

        else:

            logger.debug(
                "Non fossil groundwater abstraction is only for satisfying local demand."
            )
            self.nonFossilGroundwaterAbs = pcr.min(
                readAvlStorGroundwater, self.potGroundwaterAbstract
            )
            self.allocNonFossilGroundwater = self.nonFossilGroundwaterAbs

        # reduce capillary rise so there is always enough water for non-fossil groundwater abstraction
        self.reducedCapRise = self.nonFossilGroundwaterAbs
        # TODO: check whether this is needed for runs with MODFLOW

        # water demand satisfied after desalination, surface water and non-fossil groundwater supply (m/day):
        # irrigation and livestock
        satisfiedIrrigationLivestockDemandFromNonFossilGroundwater = (
            self.allocNonFossilGroundwater
            * vos.getValDivZero(
                irrigationLivestockGroundwaterDemand, groundwater_demand_estimate
            )
        )
        # irrigation (excluding livestock)
        satisfiedIrrigationDemandFromNonFossilGroundwater = (
            satisfiedIrrigationLivestockDemandFromNonFossilGroundwater
            * vos.getValDivZero(remainingIrrigation, remainingIrrigationLivestock)
        )
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromNonFossilGroundwater
        # non-irrigation: livestock, domestic and industry
        satisfiedNonIrrDemandFromNonFossilGroundwater = pcr.max(
            0.0,
            self.allocNonFossilGroundwater
            - satisfiedIrrigationLivestockDemandFromNonFossilGroundwater,
        )
        satisfiedNonIrrDemand += satisfiedNonIrrDemandFromNonFossilGroundwater
        # livestock
        satisfiedLivestockDemand += pcr.max(
            0.0,
            satisfiedIrrigationLivestockDemandFromNonFossilGroundwater
            - satisfiedIrrigationDemandFromNonFossilGroundwater,
        )
        # industrial and domestic (excluding livestock)
        satisfiedIndustrialDomesticDemandFromNonFossilGroundwater = pcr.max(
            0.0,
            self.allocNonFossilGroundwater
            - satisfiedIrrigationLivestockDemandFromNonFossilGroundwater,
        )
        # domestic
        satisfiedDomesticDemand += (
            satisfiedIndustrialDomesticDemandFromNonFossilGroundwater
            * vos.getValDivZero(remainingDomestic, remainingIndustrialDomestic)
        )
        # industry
        satisfiedIndustryDemand += (
            satisfiedIndustrialDomesticDemandFromNonFossilGroundwater
            * vos.getValDivZero(remainingIndustry, remainingIndustrialDomestic)
        )

        # demand to be satisfied by fossil groundwater abstraction (m), not limited by available water
        self.potFossilGroundwaterAbstract = pcr.max(
            0.0, self.potGroundwaterAbstract - self.allocNonFossilGroundwater
        )

        # with MODFLOW (limitAbstraction), there is no fossil groundwater abstraction
        if groundwater.useMODFLOW or self.limitAbstraction:
            logger.debug("Fossil groundwater abstractions are NOT allowed")
            self.fossilGroundwaterAbstr = pcr.scalar(0.0)
            self.fossilGroundwaterAlloc = pcr.scalar(0.0)

        # abstraction and allocation of fossil groundwater; TODO: skip this for runs without water use

        if self.limitAbstraction == False:

            logger.debug("Fossil groundwater abstractions are allowed.")

            # remaining water demand per sector (m/day), not limited by potFossilGroundwaterAbstract: domestic
            remainingDomestic = pcr.max(
                0.0,
                nonIrrGrossDemandDict["potential_demand"]["domestic"]
                - satisfiedDomesticDemand,
            )
            # industry
            remainingIndustry = pcr.max(
                0.0,
                nonIrrGrossDemandDict["potential_demand"]["industry"]
                - satisfiedIndustryDemand,
            )
            # livestock
            remainingLivestock = pcr.max(
                0.0,
                nonIrrGrossDemandDict["potential_demand"]["livestock"]
                - satisfiedLivestockDemand,
            )
            # irrigation (excluding livestock)
            remainingIrrigation = pcr.max(
                0.0, self.irrGrossDemand - satisfiedIrrigationDemand
            )
            # livestock and irrigation
            remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
            # industrial and domestic (excluding livestock)
            remainingIndustrialDomestic = remainingIndustry + remainingDomestic
            # total
            remainingTotalDemand = (
                remainingIrrigationLivestock + remainingIndustrialDomestic
            )

        # constrain fossil groundwater abstraction with the regional pumping capacity
        if (
            groundwater.limitRegionalAnnualGroundwaterAbstraction
            and self.limitAbstraction == False
        ):

            logger.debug(
                "Fossil groundwater abstraction is allowed, BUT limited by the regional annual pumping capacity."
            )

            # total groundwater abstraction over the last 365 days (m3), including non-fossil groundwater
            annualGroundwaterAbstraction += (
                self.nonFossilGroundwaterAbs * routing.cellArea
            )
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(
                pcr.cover(annualGroundwaterAbstraction, 0.0),
                groundwater_pumping_region_ids,
            )

            # fossil groundwater demand reduced by the pumping capacity (m/day); the safety factor avoids
            # abstracting the remaining limit at once (due to overestimated groundwater demand)
            safety_factor_for_fossil_abstraction = 1.00
            self.potFossilGroundwaterAbstract *= pcr.min(
                1.00,
                pcr.cover(
                    pcr.ifthenelse(
                        regionalAnnualGroundwaterAbstractionLimit > 0.0,
                        pcr.max(
                            0.000,
                            regionalAnnualGroundwaterAbstractionLimit
                            * safety_factor_for_fossil_abstraction
                            - regionalAnnualGroundwaterAbstraction,
                        )
                        / regionalAnnualGroundwaterAbstractionLimit,
                        0.0,
                    ),
                    0.0,
                ),
            )

        # TODO: skip this for runs without water use
        if self.limitAbstraction == False:

            # remaining total demand limited by potFossilGroundwaterAbstract (m/day)

            correctedRemainingTotalDemand = pcr.min(
                self.potFossilGroundwaterAbstract, remainingTotalDemand
            )

            # remaining industrial, domestic and livestock demand limited by potFossilGroundwaterAbstract (m/day);
            # not corrected, as these demands are always satisfied first
            correctedRemainingIndustrialDomesticLivestock = pcr.min(
                remainingIndustrialDomestic + remainingLivestock,
                correctedRemainingTotalDemand,
            )

            # remaining irrigation demand limited by potFossilGroundwaterAbstract
            correctedRemainingIrrigation = pcr.min(
                remainingIrrigation,
                pcr.max(
                    0.0,
                    correctedRemainingTotalDemand
                    - correctedRemainingIndustrialDomesticLivestock,
                ),
            )
            # ignore small irrigation demands (less than 1 mm)
            correctedRemainingIrrigation = (
                pcr.rounddown(correctedRemainingIrrigation * 1000.0) / 1000.0
            )

            # corrected remaining total demand, limited by potFossilGroundwaterAbstract
            correctedRemainingTotalDemand = (
                correctedRemainingIndustrialDomesticLivestock
                + correctedRemainingIrrigation
            )

            # corrected remaining industrial and domestic demand (excluding livestock)
            correctedRemainingIndustrialDomestic = pcr.min(
                remainingIndustrialDomestic, correctedRemainingTotalDemand
            )

            # remaining irrigation and livestock demand limited by potFossilGroundwaterAbstract
            correctedRemainingIrrigationLivestock = pcr.min(
                remainingIrrigationLivestock,
                pcr.max(
                    0.0,
                    correctedRemainingTotalDemand
                    - correctedRemainingIndustrialDomestic,
                ),
            )

            # corrected remaining total demand limited by potFossilGroundwaterAbstract (m/day)
            correctedRemainingTotalDemand = (
                correctedRemainingIrrigationLivestock
                + correctedRemainingIndustrialDomestic
            )

            # TODO: check the water balance: correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic <= potFossilGroundwaterAbstract

            # constrain the irrigation groundwater demand with the groundwater source fraction
            correctedRemainingIrrigationLivestock = pcr.min(
                (1.0 - swAbstractionFractionDict["irrigation"])
                * remainingIrrigationLivestock,
                correctedRemainingIrrigationLivestock,
            )
            correctedRemainingIrrigationLivestock = pcr.max(
                0.0,
                pcr.min(
                    correctedRemainingIrrigationLivestock,
                    pcr.max(0.0, totalIrrigationLivestockDemand)
                    * (1.0 - swAbstractionFractionDict["irrigation"])
                    - satisfiedIrrigationDemandFromNonFossilGroundwater,
                ),
            )

            # no fossil groundwater abstraction in irrigation areas dominated by swAbstractionFractionDict['irrigation']
            correctedRemainingIrrigationLivestock = pcr.ifthenelse(
                swAbstractionFractionDict["irrigation"]
                >= swAbstractionFractionDict[
                    "treshold_to_minimize_fossil_groundwater_irrigation"
                ],
                0.0,
                correctedRemainingIrrigationLivestock,
            )

            # reduce the fossil irrigation and livestock demands where there is enough non-fossil groundwater (to
            # minimize unrealistic fossil groundwater abstraction): supply from the average recharge (baseflow) and non-fossil groundwater allocation
            nonFossilGroundwaterSupply = pcr.max(
                pcr.max(0.0, routing.avgBaseflow) / routing.cellArea,
                groundwater.avgNonFossilAllocationShort,
                groundwater.avgNonFossilAllocation,
            )
            # irrigation supply from non-fossil groundwater
            nonFossilIrrigationGroundwaterSupply = (
                nonFossilGroundwaterSupply
                * vos.getValDivZero(remainingIrrigationLivestock, remainingTotalDemand)
            )
            # corrected irrigation and livestock demand
            correctedRemainingIrrigationLivestock = pcr.max(
                0.0,
                correctedRemainingIrrigationLivestock
                - nonFossilIrrigationGroundwaterSupply,
            )

            # corrected remaining total demand (m/day)
            correctedRemainingTotalDemand = (
                correctedRemainingIndustrialDomestic
                + correctedRemainingIrrigationLivestock
            )

            # demand to be satisfied by fossil groundwater abstraction
            self.potFossilGroundwaterAbstract = pcr.min(
                self.potFossilGroundwaterAbstract, correctedRemainingTotalDemand
            )

            if (
                groundwater.limitFossilGroundwaterAbstraction == False
                and self.limitAbstraction == False
            ):

                # note: if limitFossilGroundwaterAbstraction is False, fossil groundwater allocation is not needed
                msg = "Fossil groundwater abstractions are without limit for satisfying local demand. "
                msg = "Allocation for fossil groundwater abstraction is NOT needed/implemented. "
                msg += "However, the fossil groundwater abstraction rate still consider the maximumDailyGroundwaterAbstraction."
                logger.debug(msg)

                # fossil groundwater abstraction (m/day)
                self.fossilGroundwaterAbstr = self.potFossilGroundwaterAbstract
                self.fossilGroundwaterAbstr = pcr.min(
                    pcr.max(
                        0.0,
                        groundwater.maximumDailyGroundwaterAbstraction
                        - self.nonFossilGroundwaterAbs,
                    ),
                    self.fossilGroundwaterAbstr,
                )

                # fossil groundwater allocation (m/day)
                self.fossilGroundwaterAlloc = self.fossilGroundwaterAbstr

            if (
                groundwater.limitFossilGroundwaterAbstraction
                and self.limitAbstraction == False
            ):

                logger.debug(
                    "Fossil groundwater abstractions are allowed, but with limit."
                )

                # accessible fossil groundwater (m/day)
                readAvlFossilGroundwater = pcr.ifthenelse(
                    groundwater.productive_aquifer,
                    groundwater.storGroundwaterFossil,
                    0.0,
                )
                # residence time (day-1) or safety factor (avoids 'unrealistic' zero fossil groundwater)
                readAvlFossilGroundwater *= 0.10
                # maximum daily groundwater abstraction
                readAvlFossilGroundwater = pcr.min(
                    readAvlFossilGroundwater,
                    groundwater.maximumDailyFossilGroundwaterAbstraction,
                    pcr.max(
                        0.0,
                        groundwater.maximumDailyGroundwaterAbstraction
                        - self.nonFossilGroundwaterAbs,
                    ),
                )
                readAvlFossilGroundwater = pcr.max(
                    pcr.cover(readAvlFossilGroundwater, 0.0), 0.0
                )

                if groundwater.usingAllocSegments:

                    logger.debug("Allocation of fossil groundwater abstraction.")

                    # TODO: consider aquifer productivity in the allocation

                    # fossil groundwater abstraction and allocation (m3)
                    volActGroundwaterAbstract, volAllocGroundwaterAbstract = (
                        vos.waterAbstractionAndAllocation(
                            water_demand_volume=self.potFossilGroundwaterAbstract
                            * routing.cellArea,
                            available_water_volume=pcr.max(
                                0.00, readAvlFossilGroundwater * routing.cellArea
                            ),
                            allocation_zones=groundwater.allocSegments,
                            zone_area=groundwater.segmentArea,
                            high_volume_treshold=None,
                            debug_water_balance=True,
                            extra_info_for_water_balance_reporting=str(
                                currTimeStep.fulldate
                            ),
                            landmask=self.landmask,
                            ignore_small_values=False,
                            prioritizing_local_source=self.prioritizeLocalSourceToMeetWaterDemand,
                        )
                    )

                    # (m)
                    self.fossilGroundwaterAbstr = (
                        volActGroundwaterAbstract / routing.cellArea
                    )
                    self.fossilGroundwaterAlloc = (
                        volAllocGroundwaterAbstract / routing.cellArea
                    )

                else:

                    logger.debug(
                        "Fossil groundwater abstraction is only for satisfying local demand. NO Allocation for fossil groundwater abstraction."
                    )

                    self.fossilGroundwaterAbstr = pcr.min(
                        pcr.max(0.0, readAvlFossilGroundwater),
                        self.potFossilGroundwaterAbstract,
                    )
                    self.fossilGroundwaterAlloc = self.fossilGroundwaterAbstr

            # water demand satisfied after desalination, surface water, non-fossil and fossil groundwater (m/day);

            # prioritize domestic and industrial demand for fossil groundwater
            prioritizeFossilGroundwaterForDomesticIndutrial = (
                # TODO: define this in the configuration file
                False
            )

            if prioritizeFossilGroundwaterForDomesticIndutrial:

                # first priority: industrial and domestic demand (excluding livestock)
                satisfiedIndustrialDomesticDemandFromFossilGroundwater = pcr.min(
                    self.fossilGroundwaterAlloc, remainingIndustrialDomestic
                )
                # domestic
                satisfiedDomesticDemand += (
                    satisfiedIndustrialDomesticDemandFromFossilGroundwater
                    * vos.getValDivZero(remainingDomestic, remainingIndustrialDomestic)
                )
                # industry
                satisfiedIndustryDemand += (
                    satisfiedIndustrialDomesticDemandFromFossilGroundwater
                    * vos.getValDivZero(remainingIndustry, remainingIndustrialDomestic)
                )
                # irrigation and livestock
                satisfiedIrrigationLivestockDemandFromFossilGroundwater = pcr.max(
                    0.0,
                    self.fossilGroundwaterAlloc
                    - satisfiedIndustrialDomesticDemandFromFossilGroundwater,
                )
                # irrigation
                satisfiedIrrigationDemand += (
                    satisfiedIrrigationLivestockDemandFromFossilGroundwater
                    * vos.getValDivZero(
                        remainingIrrigation, remainingIrrigationLivestock
                    )
                )
                # livestock
                satisfiedLivestockDemand += (
                    satisfiedIrrigationLivestockDemandFromFossilGroundwater
                    * vos.getValDivZero(
                        remainingLivestock, remainingIrrigationLivestock
                    )
                )

            else:

                # distribute fossil groundwater proportionally to the demand of each sector: irrigation and livestock

                satisfiedIrrigationLivestockDemandFromFossilGroundwater = (
                    self.fossilGroundwaterAlloc
                    * vos.getValDivZero(
                        correctedRemainingIrrigationLivestock,
                        correctedRemainingTotalDemand,
                    )
                )
                # irrigation (excluding livestock)
                satisfiedIrrigationDemandFromFossilGroundwater = (
                    satisfiedIrrigationLivestockDemandFromFossilGroundwater
                    * vos.getValDivZero(
                        remainingIrrigation, remainingIrrigationLivestock
                    )
                )
                satisfiedIrrigationDemand += (
                    satisfiedIrrigationDemandFromFossilGroundwater
                )
                # non-irrigation: livestock, domestic and industry
                satisfiedNonIrrDemandFromFossilGroundwater = pcr.max(
                    0.0,
                    self.fossilGroundwaterAlloc
                    - satisfiedIrrigationDemandFromFossilGroundwater,
                )
                satisfiedNonIrrDemand += satisfiedNonIrrDemandFromFossilGroundwater
                # livestock
                satisfiedLivestockDemand += pcr.max(
                    0.0,
                    satisfiedIrrigationLivestockDemandFromFossilGroundwater
                    - satisfiedIrrigationDemandFromFossilGroundwater,
                )
                # industrial and domestic (excluding livestock)
                satisfiedIndustrialDomesticDemandFromFossilGroundwater = pcr.max(
                    0.0,
                    self.fossilGroundwaterAlloc
                    - satisfiedIrrigationLivestockDemandFromFossilGroundwater,
                )
                # domestic
                satisfiedDomesticDemand += (
                    satisfiedIndustrialDomesticDemandFromFossilGroundwater
                    * vos.getValDivZero(remainingDomestic, remainingIndustrialDomestic)
                )
                # industry
                satisfiedIndustryDemand += (
                    satisfiedIndustrialDomesticDemandFromFossilGroundwater
                    * vos.getValDivZero(remainingIndustry, remainingIndustrialDomestic)
                )

        # water demand limited by the available/allocated water
        self.totalPotentialGrossDemand = (
            self.fossilGroundwaterAlloc
            + self.allocNonFossilGroundwater
            + self.allocSurfaceWaterAbstract
            + self.desalinationAllocation
        )

        # total groundwater abstraction and allocation (m/day)
        self.totalGroundwaterAllocation = (
            self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
        )
        self.totalGroundwaterAbstraction = (
            self.fossilGroundwaterAbstr + self.nonFossilGroundwaterAbs
        )

        # irrigation water demand (excluding livestock) limited by the available/allocated water (m/day)
        self.irrGrossDemand = satisfiedIrrigationDemand

        # gross irrigation demand (m) per cover type (limited by available water)
        self.irrGrossDemandPaddy = 0.0
        self.irrGrossDemandNonPaddy = 0.0
        if self.name == "irrPaddy" or self.name == "irr_paddy":
            self.irrGrossDemandPaddy = self.irrGrossDemand
        if (
            self.name == "irrNonPaddy"
            or self.name == "irr_non_paddy"
            or self.name == "irr_non_paddy_crops"
        ):
            self.irrGrossDemandNonPaddy = self.irrGrossDemand

        # non-irrigation water demand (livestock, domestic and industry) limited by the available/allocated water (m/day)
        self.nonIrrGrossDemand = pcr.max(
            0.0, self.totalPotentialGrossDemand - self.irrGrossDemand
        )
        self.domesticWaterWithdrawal = satisfiedDomesticDemand
        self.industryWaterWithdrawal = satisfiedIndustryDemand
        self.livestockWaterWithdrawal = satisfiedLivestockDemand

        # return flow (m/day) of non-irrigation withdrawal (domestic, industry and livestock)
        self.nonIrrReturnFlow = (
            nonIrrGrossDemandDict["return_flow_fraction"]["domestic"]
            * self.domesticWaterWithdrawal
            + nonIrrGrossDemandDict["return_flow_fraction"]["industry"]
            * self.industryWaterWithdrawal
            + nonIrrGrossDemandDict["return_flow_fraction"]["livestock"]
            * self.livestockWaterWithdrawal
        )
        # ignore very small return flows (less than 0.1 mm)
        self.nonIrrReturnFlow = pcr.rounddown(self.nonIrrReturnFlow * 10000.0) / 10000.0
        self.nonIrrReturnFlow = pcr.min(self.nonIrrReturnFlow, self.nonIrrGrossDemand)

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.irrGrossDemand, self.nonIrrGrossDemand],
                [self.totalPotentialGrossDemand],
                [pcr.scalar(0.0)],
                [pcr.scalar(0.0)],
                "waterAllocationForAllSectors",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )
            vos.waterBalanceCheck(
                [
                    self.domesticWaterWithdrawal,
                    self.industryWaterWithdrawal,
                    self.livestockWaterWithdrawal,
                ],
                [self.nonIrrGrossDemand],
                [pcr.scalar(0.0)],
                [pcr.scalar(0.0)],
                "waterAllocationForNonIrrigationSectors",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )
            vos.waterBalanceCheck(
                [
                    self.irrGrossDemand,
                    self.domesticWaterWithdrawal,
                    self.industryWaterWithdrawal,
                    self.livestockWaterWithdrawal,
                ],
                [self.totalPotentialGrossDemand],
                [pcr.scalar(0.0)],
                [pcr.scalar(0.0)],
                "waterAllocationPerSector",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )

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
        if returnTotalEstimation == False:
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
        if self.numberOfLayers == 2 and returnTotalEstimation == False:
            # Rens: ES_a[TYPE] = SATFRAC_L*min(ES_p[TYPE],KS1[TYPE]*Duration*timeslice())+(1-SATFRAC_L)*min(ES_p[TYPE],KTHEFF1*Duration*timeslice())
            actBareSoilEvap = self.satAreaFrac * pcr.min(
                self.potBareSoilEvap, self.parameters.kSatUpp
            ) + (1.0 - self.satAreaFrac) * pcr.min(self.potBareSoilEvap, self.kUnsatUpp)
        if self.numberOfLayers == 3 and returnTotalEstimation == False:
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

    def scaleAllFluxesOptimizeEvaporationTranspiration(self, groundwater):

        # rescale all fluxes based on the available water; in irrigated areas, evaporation fluxes have
        # priority and percolation and interflow losses depend on the remaining water

        # remaining total energy for evaporation fluxes
        remainingPotET = self.potBareSoilEvap + self.potTranspiration

        # scale all fluxes based on the available water

        if self.numberOfLayers == 2:

            # scale the fluxes of Upp; potential transpiration is used to boost transpiration
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storUpp + self.infiltration) / ADJUST),
                0.0,
            )
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.actTranspiUpp = ADJUST * self.potTranspiration
            # allow more transpiration
            remainingPotET = pcr.max(
                0.0, remainingPotET - (self.actBareSoilEvap + self.actTranspiUpp)
            )
            extraTranspiration = pcr.min(
                remainingPotET,
                pcr.max(
                    0.0,
                    self.storUpp
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp,
                ),
            )
            self.actTranspiUpp += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)
            # percolation depends on the remaining water
            self.percUpp = pcr.min(
                self.percUpp,
                pcr.max(
                    0.0,
                    self.storUpp
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp,
                ),
            )

            # scale the fluxes of Low; the remaining potential evaporation is used to boost transpiration
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storLow + self.percUpp) / ADJUST),
                0.0,
            )
            self.actTranspiLow = ADJUST * remainingPotET
            # percolation and interflow depend on the remaining water
            ADJUST = self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0,
                    pcr.max(0.0, self.storLow + self.percUpp - self.actTranspiLow)
                    / ADJUST,
                ),
                0.0,
            )
            self.percLow = ADJUST * self.percLow
            self.interflow = ADJUST * self.interflow

            # capillary rise to storLow is limited to the available storGroundwater and to reducedCapRise
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

            # scale the fluxes of Upp000005; potential transpiration is used to boost transpiration
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp000005 + self.infiltration) / ADJUST
                ),
                0.0,
            )
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.actTranspiUpp000005 = ADJUST * self.potTranspiration
            # allow more transpiration
            remainingPotET = pcr.max(
                0.0, remainingPotET - (self.actBareSoilEvap + self.actTranspiUpp000005)
            )
            extraTranspiration = pcr.min(
                remainingPotET,
                pcr.max(
                    0.0,
                    self.storUpp000005
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp000005,
                ),
            )
            self.actTranspiUpp000005 += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)
            # percolation depends on the remaining water
            self.percUpp000005 = pcr.min(
                self.percUpp000005,
                pcr.max(
                    0.0,
                    self.storUpp000005
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp000005,
                ),
            )

            # scale the fluxes of Upp005030; the remaining potential evaporation is used to boost transpiration
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp005030 + self.percUpp000005) / ADJUST
                ),
                0.0,
            )
            self.actTranspiUpp005030 = ADJUST * remainingPotET
            # percolation depends on the remaining water
            self.percUpp005030 = pcr.min(
                self.percUpp005030,
                pcr.max(
                    0.0,
                    self.storUpp005030 + self.percUpp000005 - self.actTranspiUpp005030,
                ),
            )

            # scale the fluxes of Low030150; the remaining potential evaporation is used to boost transpiration
            remainingPotET = pcr.max(0.0, remainingPotET - self.actTranspiUpp005030)
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storLow030150 + self.percUpp005030) / ADJUST
                ),
                0.0,
            )
            self.actTranspiLow030150 = ADJUST * remainingPotET
            # percolation and interflow depend on the remaining water
            ADJUST = self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0,
                    pcr.max(
                        0.0,
                        self.storLow030150
                        + self.percUpp005030
                        - self.actTranspiLow030150,
                    )
                    / ADJUST,
                ),
                0.0,
            )
            self.percLow030150 = ADJUST * self.percLow030150
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

    def scaleAllFluxesOptimizeEvaporationVersion27April2014(self, groundwater):

        # rescale all fluxes based on the available water; in irrigated areas, evaporation fluxes have
        # priority and percolation and interflow losses depend on the remaining water

        # remaining total energy for evaporation fluxes
        remainingPotET = self.potBareSoilEvap + self.potTranspiration

        # minimize interflow in irrigation areas
        if self.name.startswith("irr"):
            self.interflow = 0.0

        # idea: deep percolation should consider application losses in non-paddy areas
        if self.name == "irrNonPaddy":
            startingCropKC = 0.75
            minimum_deep_percolation = pcr.min(
                self.infiltration, self.potential_irrigation_loss
            )
            maxADJUST = 2.0
            if self.numberOfLayers == 2:
                deep_percolation = pcr.max(
                    minimum_deep_percolation, self.percLow + self.interflow
                )
                ADJUST = self.percLow + self.interflow
                ADJUST = pcr.ifthenelse(
                    ADJUST > 0.0,
                    pcr.min(maxADJUST, pcr.max(0.0, deep_percolation) / ADJUST),
                    0.0,
                )
                ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.0)
                self.percLow = ADJUST * self.percLow
                self.interflow = ADJUST * self.interflow
            if self.numberOfLayers == 3:
                deep_percolation = pcr.max(
                    minimum_deep_percolation, self.percLow030150 + self.interflow
                )
                ADJUST = self.percLow030150 + self.interflow
                ADJUST = pcr.ifthenelse(
                    ADJUST > 0.0,
                    pcr.min(maxADJUST, pcr.max(0.0, deep_percolation) / ADJUST),
                    0.0,
                )
                ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.0)
                self.percLow030150 = ADJUST * self.percLow030150
                self.interflow = ADJUST * self.interflow

        # scale all fluxes based on the available water

        if self.numberOfLayers == 2:

            # scale the fluxes of Upp; potential transpiration is used to boost transpiration
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storUpp + self.infiltration) / ADJUST),
                0.0,
            )
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.actTranspiUpp = ADJUST * self.potTranspiration
            # allow more transpiration
            remainingPotET = pcr.max(
                0.0, remainingPotET - (self.actBareSoilEvap + self.actTranspiUpp)
            )
            extraTranspiration = pcr.min(
                remainingPotET,
                pcr.max(
                    0.0,
                    self.storUpp
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp,
                ),
            )
            self.actTranspiUpp += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)
            # percolation depends on the remaining water
            self.percUpp = pcr.min(
                self.percUpp,
                pcr.max(
                    0.0,
                    self.storUpp
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp,
                ),
            )

            # scale the fluxes of Low; the remaining potential evaporation is used to boost transpiration
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(1.0, pcr.max(0.0, self.storLow + self.percUpp) / ADJUST),
                0.0,
            )
            self.actTranspiLow = ADJUST * remainingPotET
            # percolation and interflow depend on the remaining water
            ADJUST = self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0,
                    pcr.max(0.0, self.storLow + self.percUpp - self.actTranspiLow)
                    / ADJUST,
                ),
                0.0,
            )
            self.percLow = ADJUST * self.percLow
            self.interflow = ADJUST * self.interflow

            # capillary rise to storLow is limited to the available storGroundwater and to reducedCapRise
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

            # scale the fluxes of Upp000005; potential transpiration is used to boost transpiration
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp000005 + self.infiltration) / ADJUST
                ),
                0.0,
            )
            self.actBareSoilEvap = ADJUST * self.actBareSoilEvap
            self.actTranspiUpp000005 = ADJUST * self.potTranspiration
            # allow more transpiration
            remainingPotET = pcr.max(
                0.0, remainingPotET - (self.actBareSoilEvap + self.actTranspiUpp000005)
            )
            extraTranspiration = pcr.min(
                remainingPotET,
                pcr.max(
                    0.0,
                    self.storUpp000005
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp000005,
                ),
            )
            self.actTranspiUpp000005 += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)
            # percolation depends on the remaining water
            self.percUpp000005 = pcr.min(
                self.percUpp000005,
                pcr.max(
                    0.0,
                    self.storUpp000005
                    + self.infiltration
                    - self.actBareSoilEvap
                    - self.actTranspiUpp000005,
                ),
            )

            # scale the fluxes of Upp005030; the remaining potential evaporation is used to boost transpiration
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storUpp005030 + self.percUpp000005) / ADJUST
                ),
                0.0,
            )
            self.actTranspiUpp005030 = ADJUST * remainingPotET
            # percolation depends on the remaining water
            self.percUpp005030 = pcr.min(
                self.percUpp005030,
                pcr.max(
                    0.0,
                    self.storUpp005030 + self.percUpp000005 - self.actTranspiUpp005030,
                ),
            )

            # scale the fluxes of Low030150; the remaining potential evaporation is used to boost transpiration
            remainingPotET = pcr.max(0.0, remainingPotET - self.actTranspiUpp005030)
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0, pcr.max(0.0, self.storLow030150 + self.percUpp005030) / ADJUST
                ),
                0.0,
            )
            self.actTranspiLow030150 = ADJUST * remainingPotET
            # percolation and interflow depend on the remaining water
            ADJUST = self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(
                ADJUST > 0.0,
                pcr.min(
                    1.0,
                    pcr.max(
                        0.0,
                        self.storLow030150
                        + self.percUpp005030
                        - self.actTranspiLow030150,
                    )
                    / ADJUST,
                ),
                0.0,
            )
            self.percLow030150 = ADJUST * self.percLow030150
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

    def OLDupperSoilUpdate(
        self,
        meteo,
        groundwater,
        routing,
        capRiseFrac,
        nonIrrGrossDemandDict,
        swAbstractionFractionDict,
        currTimeStep,
        allocSegments,
        desalinationWaterUse,
        groundwater_pumping_region_ids,
        regionalAnnualGroundwaterAbstractionLimit,
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

        # water demand (including the partitioning over sources)
        self.calculateWaterDemand(
            nonIrrGrossDemandDict,
            swAbstractionFractionDict,
            groundwater,
            routing,
            allocSegments,
            currTimeStep,
            desalinationWaterUse,
            groundwater_pumping_region_ids,
            regionalAnnualGroundwaterAbstractionLimit,
        )

        # open water evaporation from paddy fields, and update topWaterLayer
        self.calculateOpenWaterEvap()

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
                [netLqWaterToSoil, self.irrGrossDemand, self.satExcess],
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
                    [netLqWaterToSoil, self.capRiseLow, self.irrGrossDemand],
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
                    [netLqWaterToSoil, self.capRiseLow030150, self.irrGrossDemand],
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
