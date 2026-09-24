import logging

import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)

from copy import deepcopy

from pcrglobwb import landCover as lc
from pcrglobwb import parameterSoilAndTopo as parSoilAndTopo
from pcrglobwb.ncConverter import *
from pcrglobwb.water_demand import main_water_demand as water_demand
from pcrglobwb.water_management import main_water_management as water_management
from qualloc.model_configuration import configuration_parser
from qualloc.model_time import model_time
from qualloc.qualloc_main import qualloc_model
from qualloc.qualloc_reporting import qualloc_reporting


class LandSurface(object):

    def getState(self):
        result = {}

        if self.numberOfSoilLayers == 2:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]["interceptStor"] = self.landCoverObj[
                    coverType
                ].interceptStor
                result[coverType]["snowCoverSWE"] = self.landCoverObj[
                    coverType
                ].snowCoverSWE
                result[coverType]["snowFreeWater"] = self.landCoverObj[
                    coverType
                ].snowFreeWater
                result[coverType]["topWaterLayer"] = self.landCoverObj[
                    coverType
                ].topWaterLayer
                result[coverType]["storUpp"] = self.landCoverObj[coverType].storUpp
                result[coverType]["storLow"] = self.landCoverObj[coverType].storLow
                result[coverType]["interflow"] = self.landCoverObj[coverType].interflow

        if self.numberOfSoilLayers == 3:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]["interceptStor"] = self.landCoverObj[
                    coverType
                ].interceptStor
                result[coverType]["snowCoverSWE"] = self.landCoverObj[
                    coverType
                ].snowCoverSWE
                result[coverType]["snowFreeWater"] = self.landCoverObj[
                    coverType
                ].snowFreeWater
                result[coverType]["topWaterLayer"] = self.landCoverObj[
                    coverType
                ].topWaterLayer
                result[coverType]["storUpp000005"] = self.landCoverObj[
                    coverType
                ].storUpp000005
                result[coverType]["storUpp005030"] = self.landCoverObj[
                    coverType
                ].storUpp005030
                result[coverType]["storLow030150"] = self.landCoverObj[
                    coverType
                ].storLow030150
                result[coverType]["interflow"] = self.landCoverObj[coverType].interflow

        return result

    def getPseudoState(self):
        result = {}

        if self.numberOfSoilLayers == 2:
            result["interceptStor"] = self.interceptStor
            result["snowCoverSWE"] = self.snowCoverSWE
            result["snowFreeWater"] = self.snowFreeWater
            result["topWaterLayer"] = self.topWaterLayer
            result["storUpp"] = self.storUpp
            result["storLow"] = self.storLow

        if self.numberOfSoilLayers == 3:
            result["interceptStor"] = self.interceptStor
            result["snowCoverSWE"] = self.snowCoverSWE
            result["snowFreeWater"] = self.snowFreeWater
            result["topWaterLayer"] = self.topWaterLayer
            result["storUpp000005"] = self.storUpp000005
            result["storUpp005030"] = self.storUpp005030
            result["storLow030150"] = self.storLow030150

        return result

    def __init__(self, iniItems, landmask, initialState=None):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        self.iniItems = iniItems

        # cell area (m2)
        self.cellArea = vos.readPCRmapClone(
            iniItems.routingOptions["cellAreaMap"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )
        self.cellArea = pcr.ifthen(self.landmask, self.cellArea)

        # number of soil layers
        self.numberOfSoilLayers = int(
            iniItems.landSurfaceOptions["numberOfUpperSoilLayers"]
        )

        # aggregated variables (from the landCover modules) that must be defined in this module; needed
        # for water balance checks, initial conditions and other modules (e.g. routing, groundwater)

        # main state variables (m)
        self.mainStates = [
            "interceptStor",
            "snowCoverSWE",
            "snowFreeWater",
            "topWaterLayer",
        ]

        # state variables (m)
        self.stateVars = [
            "storUppTotal",
            "storLowTotal",
            "satDegUppTotal",
            "satDegLowTotal",
            "satDegTotal",
        ]

        # flux variables (m/day)
        self.fluxVars = [
            "infiltration",
            "gwRecharge",
            "netLqWaterToSoil",
            "totalPotET",
            "actualET",
            "interceptEvap",
            "openWaterEvap",
            "actSnowFreeWaterEvap",
            "actBareSoilEvap",
            "actTranspiUppTotal",
            "actTranspiLowTotal",
            "actTranspiTotal",
            "directRunoff",
            "interflow",
            "interflowTotal",
            "landSurfaceRunoff",
            "satExcess",
            "snowMelt",
            "irrigationTranspirationDeficit",
        ]

        # added by Joren
        self.fluxVars += [
            "incomingVolSnow",
            "transportVolSnow",
            "incomingFreeWater",
            "transportFreeWater",
        ]

        # specific variables for the 2- and 3-layer soil models
        if self.numberOfSoilLayers == 2:
            self.mainStates += ["storUpp", "storLow"]
            self.stateVars += self.mainStates
            self.fluxVars += ["actTranspiUpp", "actTranspiLow", "netPercUpp"]

        if self.numberOfSoilLayers == 3:
            self.mainStates += ["storUpp000005", "storUpp005030", "storLow030150"]
            self.stateVars += self.mainStates
            self.fluxVars += [
                "actTranspiUpp000005",
                "actTranspiUpp005030",
                "actTranspiLow030150",
                "netPercUpp000005",
                "netPercUpp005030",
                "interflowUpp005030",
            ]

        # all variables calculated/reported in landSurface.py
        self.aggrVars = self.stateVars + self.fluxVars
        if self.numberOfSoilLayers == 2:
            self.aggrVars += ["satDegUpp", "satDegLow"]
        if self.numberOfSoilLayers == 3:
            self.aggrVars += ["satDegUpp000005", "satDegUpp005030", "satDegLow030150"]

        # option to check the water balance
        self.debugWaterBalance = iniItems.landSurfaceOptions["debugWaterBalance"]

        # land cover types included in the simulation
        self.coverTypes = ["forest", "grassland"]

        # option to include irrigation per land cover type
        self.includeIrrigation = False
        if iniItems.waterDemandOptions["includeIrrigation"] == "True":
            self.includeIrrigation = True
            self.coverTypes += ["irrPaddy", "irrNonPaddy"]
            logger.info("Irrigation is included/considered in this run.")
        else:
            logger.info("Irrigation is NOT included/considered in this run.")

        # land cover types defined by the user
        if "landCoverTypes" in list(iniItems.landSurfaceOptions.keys()):
            self.coverTypes = iniItems.landSurfaceOptions["landCoverTypes"].split(",")

        # water demand options: irrigation efficiency, non-irrigation water demand and desalination supply;
        # TODO: deactivate due to the new water_demand and water_management modules
        self.waterDemandOptions(iniItems)

        # TODO: add an option for natural runs (without water use and reservoirs)

        # topography and soil parameters
        self.soil_topo_parameters = {}
        # default values for all land cover types
        self.soil_topo_parameters["default"] = parSoilAndTopo.SoilAndTopoParameters(
            iniItems, self.landmask
        )
        self.soil_topo_parameters["default"].read(iniItems)
        # soil and topography parameters per land cover type
        for coverType in self.coverTypes:
            name_of_section_given_in_ini_file = str(coverType) + "Options"
            dictionary_of_land_cover_settings = iniItems.__getattribute__(
                name_of_section_given_in_ini_file
            )

            if "usingSpecificSoilTopo" not in list(
                dictionary_of_land_cover_settings.keys()
            ):
                dictionary_of_land_cover_settings["usingSpecificSoilTopo"] = "False"
            if dictionary_of_land_cover_settings["usingSpecificSoilTopo"] == "True":

                msg = "Using a specific set of soil and topo parameters "
                msg += (
                    "as defined in the "
                    + name_of_section_given_in_ini_file
                    + " of the ini/configuration file."
                )

                self.soil_topo_parameters[coverType] = (
                    parSoilAndTopo.SoilAndTopoParameters(iniItems, self.landmask)
                )
                self.soil_topo_parameters[coverType].read(
                    iniItems, dictionary_of_land_cover_settings
                )
            else:

                msg = "Using the default set of soil and topo parameters "
                msg += "as defined in the landSurfaceOptions of the ini/configuration file."

                self.soil_topo_parameters[coverType] = self.soil_topo_parameters[
                    "default"
                ]
            logger.info(msg)

        self.landCoverObj = {}
        for coverType in self.coverTypes:
            self.landCoverObj[coverType] = lc.LandCover(
                iniItems,
                str(coverType) + "Options",
                self.soil_topo_parameters[coverType],
                self.landmask,
            )

        # rescale the land cover fractions; by default they are always corrected (total of all fractions = 1)
        self.noLandCoverFractionCorrection = False
        if "noLandCoverFractionCorrection" in list(iniItems.landSurfaceOptions.keys()):
            if iniItems.landSurfaceOptions["noLandCoverFractionCorrection"] == "True":
                self.noLandCoverFractionCorrection = True
        if self.noLandCoverFractionCorrection == False:
            self.scaleNaturalLandCoverFractions()
            if self.includeIrrigation:
                self.scaleModifiedLandCoverFractions()

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

        # dynamicIrrigationArea cannot be combined with noLandCoverFractionCorrection
        if self.noLandCoverFractionCorrection:
            self.dynamicIrrigationArea = False

        # noAnnualChangesInLandCoverParameter = False requires noLandCoverFractionCorrection
        if (
            self.noAnnualChangesInLandCoverParameter == False
            and self.noLandCoverFractionCorrection == False
        ):
            self.noLandCoverFractionCorrection = True
            msg = "WARNING! No land cover fraction correction will be performed. Please make sure that the 'total' of all fracVegCover adds to one."
            logger.warning(msg)
            logger.warning(msg)
            logger.warning(msg)
            logger.warning(msg)
            logger.warning(msg)

        self.using_qualloc = False
        if "using_qualloc" in iniItems.waterManagementOptions.keys():
            if iniItems.waterManagementOptions["using_qualloc"] == "True":
                self.using_qualloc = True

        self.using_dynqual = False
        if "quality" in iniItems.routingOptions.keys():
            if iniItems.routingOptions["quality"] == "True":
                self.using_dynqual = True

        # with a historical/dynamic irrigation file (changing every year), we need the fraction over the
        # irrigation area to calculate the irrigation area per irrigation type:
        # totalIrrAreaFrac: fraction of irrigated area (e.g. paddy + non-paddy) over the cell (-), changes if dynamicIrrigationArea
        # irrTypeFracOverIrr: fraction of each irrigation type over the irrigation area (-), constant over the simulation
        if self.dynamicIrrigationArea:

            logger.info("Determining fraction of total irrigated areas over each cell")
            # only needed if historical irrigation areas are used (dynamicIrrigationArea)

            # total irrigated area fraction (over the cell)
            totalIrrAreaFrac = 0.0
            for coverType in self.coverTypes:
                if coverType.startswith("irr"):
                    totalIrrAreaFrac += self.landCoverObj[coverType].fracVegCover

            # fraction over the irrigation area
            for coverType in self.coverTypes:
                if coverType.startswith("irr"):
                    self.landCoverObj[coverType].irrTypeFracOverIrr = vos.getValDivZero(
                        self.landCoverObj[coverType].fracVegCover,
                        totalIrrAreaFrac,
                        vos.smallNumber,
                    )

        # initial conditions (per land cover type)
        self.getInitialConditions(iniItems, initialState)

        self.water_demand = water_demand.WaterDemand(
            iniItems, landmask, self.coverTypes, self.landCoverObj
        )

        if self.using_qualloc:
            qualloc_config_file = iniItems.waterManagementOptions[
                "configuration_file_for_qualloc"
            ]

            # configuration object
            sections = [
                "general",
                "time",
                "forcing",
                "groundwater",
                "surfacewater",
                "water_management",
                "water_quality",
            ]
            groups = []
            subst_args = []

            # the placeholders in the QUAlloc cfg are filled from this ini, which run-with-arguments has
            # already substituted with the same values, so both models are driven by one set of arguments
            replacements = {}
            for token, option in [
                ("MAIN_INPUT_DIR", "main_input_dir_for_qualloc"),
                ("MAIN_OUTPUT_DIR", "main_output_dir_for_qualloc"),
                ("CLONEMAP", "clonemap_for_qualloc"),
            ]:
                if option in iniItems.waterManagementOptions:
                    replacements[token] = iniItems.waterManagementOptions[option]

            self.qualloc_model_configuration = configuration_parser(
                cfgfilename=qualloc_config_file,
                sections=sections,
                groups=groups,
                subst_args=subst_args,
                replacements=replacements,
            )

            time_increment = "daily"
            startyear = int(self.qualloc_model_configuration.time["startyear"])
            endyear = int(self.qualloc_model_configuration.time["endyear"])
            self.qualloc_model_time = model_time(startyear, endyear, time_increment)

            # dummy model flags and initial conditions; initial conditions are read from the configuration
            # file if None, otherwise the existing warm states are used
            model_flags = {}
            initial_conditions = None

            self.qualloc_model = qualloc_model(
                self.qualloc_model_configuration,
                self.qualloc_model_time,
                model_flags,
                initial_conditions,
            )
            self.qualloc_model.initialize(online_coupling=self.using_qualloc)

            self.qualloc_reporting = qualloc_reporting(self.qualloc_model_configuration)
            self.qualloc_reporting.initialize()

        else:
            self.water_management = water_management.WaterManagement(iniItems, landmask)

        # old-style reporting (useful for debugging)
        self.initiate_old_style_land_surface_reporting(iniItems)

    def initiate_old_style_land_surface_reporting(self, iniItems):
        self.report = True
        try:
            self.outDailyTotNC = iniItems.landSurfaceOptions["outDailyTotNC"].split(",")
            self.outMonthTotNC = iniItems.landSurfaceOptions["outMonthTotNC"].split(",")
            self.outMonthAvgNC = iniItems.landSurfaceOptions["outMonthAvgNC"].split(",")
            self.outMonthEndNC = iniItems.landSurfaceOptions["outMonthEndNC"].split(",")
            self.outAnnuaTotNC = iniItems.landSurfaceOptions["outAnnuaTotNC"].split(",")
            self.outAnnuaAvgNC = iniItems.landSurfaceOptions["outAnnuaAvgNC"].split(",")
            self.outAnnuaEndNC = iniItems.landSurfaceOptions["outAnnuaEndNC"].split(",")
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

    def getInitialConditions(self, iniItems, iniConditions=None):

        starting_year = int(iniItems.globalOptions["startTime"][0:4])

        # check whether the run starts on 1 January
        start_on_1_Jan = False
        if iniItems.globalOptions["startTime"][-5:] == "01-01":
            start_on_1_Jan = True

        # whether to consider the land cover fractions of the previous year
        consider_previous_year_land_cover_fraction = False

        # initial land cover fractions for runs with dynamicIrrigationArea: non-spin-up runs that start on
        # 1 January must consider the land cover fractions of the previous year
        if (
            iniConditions == None
            and start_on_1_Jan == True
            and self.dynamicIrrigationArea
            and self.noLandCoverFractionCorrection == False
        ):
            # land cover fractions of the previous year
            self.scaleDynamicIrrigation(starting_year - 1)
            consider_previous_year_land_cover_fraction = True
        # spin-up runs or runs that start after 1 January use the land cover fractions of the current year
        if (
            consider_previous_year_land_cover_fraction == False
            and self.dynamicIrrigationArea
            and self.noLandCoverFractionCorrection == False
        ):
            self.scaleDynamicIrrigation(starting_year)

        # initial land cover fractions for runs with noLandCoverFractionCorrection and annual changes in the
        # land cover parameters: non-spin-up runs that start on 1 January must consider the previous year
        if (
            iniConditions == None
            and start_on_1_Jan == True
            and self.noLandCoverFractionCorrection
            and self.noAnnualChangesInLandCoverParameter == False
        ):
            # land cover fractions of the previous year
            previous_year = starting_year - 1
            one_january_prev_year = str(previous_year) + "-01-01"
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[
                    coverType
                ].get_land_cover_parameters(
                    date_in_string=one_january_prev_year, get_only_fracVegCover=True
                )

            # correct the land cover fractions
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover

            if "grassland" in list(self.landCoverObj.keys()):
                self.landCoverObj["grassland"].previousFracVegCover = pcr.ifthenelse(
                    total_fractions > 0.1,
                    self.landCoverObj["grassland"].previousFracVegCover,
                    1.0,
                )

            if "short_natural" in list(self.landCoverObj.keys()):
                self.landCoverObj["short_natural"].previousFracVegCover = (
                    pcr.ifthenelse(
                        total_fractions > 0.1,
                        self.landCoverObj["short_natural"].previousFracVegCover,
                        1.0,
                    )
                )

            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover

            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = (
                    self.landCoverObj[coverType].previousFracVegCover / total_fractions
                )

            consider_previous_year_land_cover_fraction = True

        # spin-up runs or runs that start after 1 January use the land cover fractions of the current year
        if (
            consider_previous_year_land_cover_fraction == False
            and self.noLandCoverFractionCorrection
            and self.noAnnualChangesInLandCoverParameter == False
        ):
            # land cover fractions of the current year
            one_january_this_year = str(starting_year) + "-01-01"
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[
                    coverType
                ].get_land_cover_parameters(
                    date_in_string=one_january_this_year, get_only_fracVegCover=True
                )

            # correct the land cover fractions
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover

            if "grassland" in list(self.landCoverObj.keys()):
                self.landCoverObj["grassland"].previousFracVegCover = pcr.ifthenelse(
                    total_fractions > 0.1,
                    self.landCoverObj["grassland"].previousFracVegCover,
                    1.0,
                )

            if "short_natural" in list(self.landCoverObj.keys()):
                self.landCoverObj["short_natural"].previousFracVegCover = (
                    pcr.ifthenelse(
                        total_fractions > 0.1,
                        self.landCoverObj["short_natural"].previousFracVegCover,
                        1.0,
                    )
                )

            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover

            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = (
                    self.landCoverObj[coverType].previousFracVegCover / total_fractions
                )

        # initial conditions: first set all aggregated main states to zero, then initialize them per land cover type
        for var in self.mainStates:
            vars(self)[var] = pcr.scalar(0.0)
        for coverType in self.coverTypes:
            if iniConditions != None:
                self.landCoverObj[coverType].getICsLC(
                    iniItems, iniConditions["landSurface"][coverType]
                )
            else:
                self.landCoverObj[coverType].getICsLC(iniItems)
            # aggregate the initial states using the initial land cover fractions (previousFracVegCover)
            for var in self.mainStates:
                # initial land cover fractions (-)
                if self.landCoverObj[coverType].previousFracVegCover is None:
                    self.landCoverObj[coverType].previousFracVegCover = (
                        self.landCoverObj[coverType].fracVegCover
                    )
                land_cover_fraction = self.landCoverObj[coverType].previousFracVegCover
                # initial land cover states (m)
                land_cover_states = vars(self.landCoverObj[coverType])[var]
                vars(self)[var] += land_cover_states * land_cover_fraction

    def waterDemandOptions(self, iniItems):
        # historical irrigation area (ha)
        self.dynamicIrrigationArea = False
        if iniItems.landSurfaceOptions["historicalIrrigationArea"] != "None":
            logger.info(
                "Using the dynamicIrrigationArea option. Extent of irrigation areas is based on the file provided in the 'historicalIrrigationArea'."
            )
            self.dynamicIrrigationArea = True

        if self.dynamicIrrigationArea:
            self.dynamicIrrigationAreaFile = vos.getFullPath(
                iniItems.landSurfaceOptions["historicalIrrigationArea"],
                self.inputDir,
                False,
            )

    def scaleNaturalLandCoverFractions(self):
        """rescales natural land cover fractions (make sure the total = 1)"""

        # total land cover fraction
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                pristineAreaFrac += pcr.cover(
                    self.landCoverObj[coverType].fracVegCover, 0.0
                )
                numb_of_lc_types += 1.0

        # fill cells with pristineAreaFrac < 0 with the window average within 0.5 and 1.5 degrees
        for coverType in self.coverTypes:

            if not coverType.startswith("irr"):
                extrapolate = True
                if (
                    "noParameterExtrapolation"
                    in self.iniItems.landSurfaceOptions.keys()
                    and self.iniItems.landSurfaceOptions["noParameterExtrapolation"]
                    == "True"
                ):
                    extrapolate = False

                if extrapolate:
                    filled_fractions = pcr.windowaverage(
                        self.landCoverObj[coverType].fracVegCover, 0.5
                    )
                    filled_fractions = pcr.cover(
                        filled_fractions,
                        pcr.windowaverage(
                            self.landCoverObj[coverType].fracVegCover, 1.5
                        ),
                    )
                    filled_fractions = pcr.max(0.0, filled_fractions)
                    filled_fractions = pcr.min(1.0, filled_fractions)

                    self.landCoverObj[coverType].fracVegCover = pcr.ifthen(
                        pristineAreaFrac >= 0.0,
                        self.landCoverObj[coverType].fracVegCover,
                    )
                    self.landCoverObj[coverType].fracVegCover = pcr.cover(
                        self.landCoverObj[coverType].fracVegCover, filled_fractions
                    )
                    self.landCoverObj[coverType].fracVegCover = pcr.ifthen(
                        self.landmask, self.landCoverObj[coverType].fracVegCover
                    )

        # recheck the total land cover fraction
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                pristineAreaFrac += pcr.cover(
                    self.landCoverObj[coverType].fracVegCover, 0.0
                )
                numb_of_lc_types += 1.0

        # fill cells with pristineAreaFrac = 0; TODO: this only works for certain land cover names
        try:
            self.landCoverObj["forest"].fracVegCover = pcr.ifthenelse(
                pristineAreaFrac > 0.0, self.landCoverObj["forest"].fracVegCover, 0.0
            )
            self.landCoverObj["forest"].fracVegCover = pcr.min(
                1.0, self.landCoverObj["forest"].fracVegCover
            )
            self.landCoverObj["grassland"].fracVegCover = (
                1.0 - self.landCoverObj["forest"].fracVegCover
            )
        except:
            pass

        # recalculate the total land cover fraction
        pristineAreaFrac = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                pristineAreaFrac += pcr.cover(
                    self.landCoverObj[coverType].fracVegCover, 0.0
                )

        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                self.landCoverObj[coverType].fracVegCover = (
                    self.landCoverObj[coverType].fracVegCover / pristineAreaFrac
                )

        pristineAreaFrac = 0.0
        # check pristineAreaFrac (must be 1)
        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                pristineAreaFrac += self.landCoverObj[coverType].fracVegCover
                self.landCoverObj[coverType].naturalFracVegCover = self.landCoverObj[
                    coverType
                ].fracVegCover

        # make sure totalArea = 1 for all cells
        totalArea = pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask, totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        check_map = totalArea - pcr.scalar(1.0)
        a, b, c = vos.getMinMaxMean(check_map)
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error(
                "total of 'Natural Area' fractions is not equal to 1.0 ... Min %f Max %f Mean %f"
                % (a, b, c)
            )

    def scaleModifiedLandCoverFractions(self):
        """rescales the land cover fractions with irrigation areas"""

        # fraction of irrigated area
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                irrigatedAreaFrac = (
                    irrigatedAreaFrac + self.landCoverObj[coverType].fracVegCover
                )

        # scale fracVegCover of the irrigation types if irrigatedAreaFrac > 1
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                self.landCoverObj[coverType].fracVegCover = pcr.ifthenelse(
                    irrigatedAreaFrac > 1.0,
                    self.landCoverObj[coverType].fracVegCover / irrigatedAreaFrac,
                    self.landCoverObj[coverType].fracVegCover,
                )

        # corrected irrigated area fraction
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                irrigatedAreaFrac += self.landCoverObj[coverType].fracVegCover

        totalArea = pcr.spatial(pcr.scalar(0.0))
        totalArea += irrigatedAreaFrac

        # correction factor for forest and grassland (pristine areas)
        lcFrac = pcr.max(0.0, 1.0 - totalArea)
        pristineAreaFrac = pcr.spatial(pcr.scalar(0.0))

        for coverType in self.coverTypes:
            if not coverType.startswith("irr"):
                self.landCoverObj[coverType].fracVegCover = 0.0
                self.landCoverObj[coverType].fracVegCover = (
                    self.landCoverObj[coverType].naturalFracVegCover * lcFrac
                )
                pristineAreaFrac += pcr.cover(
                    self.landCoverObj[coverType].fracVegCover, 0.0
                )

        # make sure totalArea = 1 for all cells
        totalArea += pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask, totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        totalArea = pcr.ifthen(self.landmask, totalArea)
        a, b, c = vos.getMinMaxMean(totalArea - pcr.scalar(1.0))
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error(
                "fraction total (from all land cover types) is not equal to 1.0 ... Min %f Max %f Mean %f"
                % (a, b, c)
            )

    def calculateCapRiseFrac(self, groundwater, routing, currTimeStep):
        # cell fraction influenced by capillary rise, from the relative groundwater head (m) above the
        # minimum elevation within the cell
        dzGroundwater = groundwater.storGroundwater / groundwater.specificYield

        # add a tolerance/influence level (m)
        dzGroundwater += self.soil_topo_parameters["default"].maxGWCapRise

        # minimum zero (zero relativeGroundwaterHead means no capRiseFrac)
        dzGroundwater = pcr.max(0.0, dzGroundwater)

        # approximate cell fraction influenced by capillary rise
        FRACWAT = pcr.spatial(pcr.scalar(0.0))
        if currTimeStep.timeStepPCR > 1:
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0)
        else:
            if routing.includeWaterBodies:
                if routing.WaterBodies.useNetCDF:
                    routing.WaterBodies.fracWat = vos.netcdf2PCRobjClone(
                        routing.WaterBodies.ncFileInp,
                        "fracWaterInp",
                        currTimeStep.fulldate,
                        useDoy="yearly",
                        cloneMapFileName=self.cloneMap,
                    )
                else:
                    if routing.WaterBodies.fracWaterInp != "None":
                        routing.WaterBodies.fracWat = vos.readPCRmapClone(
                            routing.WaterBodies.fracWaterInp
                            + str(currTimeStep.year)
                            + ".map",
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                    else:
                        routing.WaterBodies.fracWat = pcr.spatial(pcr.scalar(0.0))
            else:
                if routing.WaterBodies.useNetCDF:
                    routing.WaterBodies.fracWat = vos.netcdf2PCRobjClone(
                        routing.WaterBodies.ncFileInp,
                        "fracWaterInp",
                        currTimeStep.fulldate,
                        useDoy="yearly",
                        cloneMapFileName=self.cloneMap,
                    )
                else:
                    if routing.WaterBodies.fracWaterInp != "None":
                        routing.WaterBodies.fracWat = vos.readPCRmapClone(
                            routing.WaterBodies.fracWaterInp,
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                    else:
                        routing.WaterBodies.fracWat = pcr.spatial(pcr.scalar(0.0))
            # note: FRACWAT is used here (possibly a small bug fix relative to the GMD paper version)
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0)
        FRACWAT = pcr.cover(FRACWAT, 0.0)

        CRFRAC = pcr.min(
            1.0,
            1.0
            - (self.soil_topo_parameters["default"].dzRel0100 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0100
                - self.soil_topo_parameters["default"].dzRel0090,
            ),
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0090,
            0.9
            - (self.soil_topo_parameters["default"].dzRel0090 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0090
                - self.soil_topo_parameters["default"].dzRel0080,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0080,
            0.8
            - (self.soil_topo_parameters["default"].dzRel0080 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0080
                - self.soil_topo_parameters["default"].dzRel0070,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0070,
            0.7
            - (self.soil_topo_parameters["default"].dzRel0070 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0070
                - self.soil_topo_parameters["default"].dzRel0060,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0060,
            0.6
            - (self.soil_topo_parameters["default"].dzRel0060 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0060
                - self.soil_topo_parameters["default"].dzRel0050,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0050,
            0.5
            - (self.soil_topo_parameters["default"].dzRel0050 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0050
                - self.soil_topo_parameters["default"].dzRel0040,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0040,
            0.4
            - (self.soil_topo_parameters["default"].dzRel0040 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0040
                - self.soil_topo_parameters["default"].dzRel0030,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0030,
            0.3
            - (self.soil_topo_parameters["default"].dzRel0030 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0030
                - self.soil_topo_parameters["default"].dzRel0020,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0020,
            0.2
            - (self.soil_topo_parameters["default"].dzRel0020 - dzGroundwater)
            * 0.1
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0020
                - self.soil_topo_parameters["default"].dzRel0010,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0010,
            0.1
            - (self.soil_topo_parameters["default"].dzRel0010 - dzGroundwater)
            * 0.05
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0010
                - self.soil_topo_parameters["default"].dzRel0005,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0005,
            0.05
            - (self.soil_topo_parameters["default"].dzRel0005 - dzGroundwater)
            * 0.04
            / pcr.max(
                0.001,
                self.soil_topo_parameters["default"].dzRel0005
                - self.soil_topo_parameters["default"].dzRel0001,
            ),
            CRFRAC,
        )
        CRFRAC = pcr.ifthenelse(
            dzGroundwater < self.soil_topo_parameters["default"].dzRel0001,
            0.01
            - (self.soil_topo_parameters["default"].dzRel0001 - dzGroundwater)
            * 0.01
            / pcr.max(0.001, self.soil_topo_parameters["default"].dzRel0001),
            CRFRAC,
        )

        CRFRAC = pcr.ifthenelse(
            FRACWAT < 1.0, pcr.max(0.0, CRFRAC - FRACWAT) / (1.0 - FRACWAT), 0.0
        )

        capRiseFrac = pcr.max(0.0, pcr.min(1.0, CRFRAC))

        return capRiseFrac

    def scaleDynamicIrrigation(self, yearInInteger):
        # update fracVegCover for historical irrigation areas (yearly)

        yearInString = str(yearInInteger)

        if self.dynamicIrrigationAreaFile.endswith((".nc4", ".nc")):
            fulldateInString = yearInString + "-01" + "-01"
            # (m2; the input file is in hectare)
            self.irrigationArea = 10000.0 * pcr.cover(
                vos.netcdf2PCRobjClone(
                    self.dynamicIrrigationAreaFile,
                    "irrigationArea",
                    fulldateInString,
                    useDoy="yearly",
                    cloneMapFileName=self.cloneMap,
                ),
                0.0,
            )
        else:
            irrigation_pcraster_file = (
                self.dynamicIrrigationAreaFile + yearInString + ".map"
            )
            logger.debug(
                "reading irrigation area map from : " + irrigation_pcraster_file
            )
            # (m2; the input file is in hectare)
            self.irrigationArea = 10000.0 * pcr.cover(
                vos.readPCRmapClone(
                    irrigation_pcraster_file, self.cloneMap, self.tmpDir
                ),
                0.0,
            )

        # TODO: convert the input file from hectare to percentage, to avoid errors when 30 arcmin input
        # is used for a 5 arcmin model

        # irrigation area is limited by the cell area
        self.irrigationArea = pcr.max(self.irrigationArea, 0.0)
        self.irrigationArea = pcr.min(self.irrigationArea, self.cellArea)

        # fracVegCover (irrigation only)
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):

                self.landCoverObj[coverType].fractionArea = 0.0
                # (m2)
                self.landCoverObj[coverType].fractionArea = (
                    self.landCoverObj[coverType].irrTypeFracOverIrr
                    * self.irrigationArea
                )
                self.landCoverObj[coverType].fracVegCover = pcr.min(
                    1.0, self.landCoverObj[coverType].fractionArea / self.cellArea
                )

                # avoid small values
                self.landCoverObj[coverType].fracVegCover = (
                    pcr.rounddown(self.landCoverObj[coverType].fracVegCover * 1000.0)
                    / 1000.0
                )

        # rescale the land cover fractions (for all land cover types)
        self.scaleModifiedLandCoverFractions()

    def update(self, meteo, groundwater, routing, currTimeStep):
        # set the land cover parameters per land cover type: fracVegCover, arnoBeta, rootZoneWaterStorageMin,
        # rootZoneWaterStorageRange, maxRootDepth, adjRootFrUpp, adjRootFrLow, effSatAt50, effPoreSizeBetaAt50,
        # cropKc, coverFraction and interceptCap

        for coverType in self.coverTypes:
            logger.info("Setting land cover parameters: " + str(coverType))
            self.landCoverObj[coverType].set_land_cover_parameters(currTimeStep)

        # transfer states between land cover types due to dynamic irrigation areas (expansion/reduction);
        # done at the start of each year, including the first time step
        self.state_transfer_among_land_cover(currTimeStep)

        # total potential evaporation per land cover type, partitioned into bare soil evaporation and
        # transpiration (totalPotET, potBareSoilEvap, potTranspiration)
        for coverType in self.coverTypes:
            logger.info(
                "Calculate potential evaporation and partition this to bare soil evaporation and transpiration: "
                + str(coverType)
            )
            self.landCoverObj[coverType].getPotET(meteo, currTimeStep)

        # interception module per land cover type (throughfall, interceptStor, snowfall, liquidPrecip,
        # potInterceptionFlux, interceptEvap, potBareSoilEvap, potTranspiration, actualET)
        for coverType in self.coverTypes:
            logger.info("Running the inteception module: " + str(coverType))
            self.landCoverObj[coverType].interceptionUpdate(meteo, currTimeStep)

        # snow module per land cover type (snowCoverSWE, snowMelt, snowFreeWater, netLqWaterToSoil,
        # actSnowFreeWaterEvap, potBareSoilEvap, actualET)
        for coverType in self.coverTypes:
            logger.info("Running the snow module: " + str(coverType))
            self.landCoverObj[coverType].snow_module_update(meteo, currTimeStep)

        # water demand (m), based on the states after the above processes (soil moisture and
        # topWaterLayer states should equal those of the previous day)
        self.water_demand.update(
            meteo=meteo,
            landSurface=self,
            groundwater=groundwater,
            routing=routing,
            currTimeStep=currTimeStep,
        )

        # gross sectoral water demands (m3)
        vol_gross_sectoral_water_demands = {}

        # non-irrigation demand (m3)
        vol_gross_sectoral_water_demands["domestic"] = (
            self.water_demand.water_demand_domestic.domesticGrossDemand
            * routing.cellArea
        )
        vol_gross_sectoral_water_demands["industry"] = (
            self.water_demand.water_demand_industry.industryGrossDemand
            * routing.cellArea
        )
        vol_gross_sectoral_water_demands["manufacture"] = (
            self.water_demand.water_demand_manufacture.manufactureGrossDemand
            * routing.cellArea
        )
        vol_gross_sectoral_water_demands["thermoelectric"] = (
            self.water_demand.water_demand_thermoelectric.thermoelectricGrossDemand
            * routing.cellArea
        )
        vol_gross_sectoral_water_demands["livestock"] = (
            self.water_demand.water_demand_livestock.livestockGrossDemand
            * routing.cellArea
        )

        # irrigation demand (m3)
        vol_gross_sectoral_water_demands["irrigation"] = pcr.scalar(0.0)
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                vol_gross_sectoral_water_demands["irrigation"] += (
                    self.water_demand.water_demand_irrigation[coverType].irrGrossDemand
                    * routing.cellArea
                    * self.landCoverObj[coverType].fracVegCover
                )

        # water allocation: pool the demands, allocate them to the available storages and pass the
        # withdrawals to surface water and groundwater; input: sectoral water demands and water
        # availability (surface water and groundwater from the previous time step, desalination from the
        # current one); output: abstraction per source and allocation, including irrigation supply for
        # the next time step; the water management calculation is done in volume (m3)

        if self.using_qualloc:
            # QUAlloc: update; water quality states (if specified)
            surfacewater_temperature = None
            surfacewater_organic = None
            surfacewater_salinity = None
            surfacewater_pathogen = None
            if self.using_dynqual:
                surfacewater_temperature = routing.waterTemp - 273.15
                surfacewater_organic = pcr.ifthen(
                    routing.organic < vos.MV, routing.organic
                )
                surfacewater_salinity = pcr.ifthen(
                    routing.salinity < vos.MV, routing.salinity
                )
                surfacewater_pathogen = pcr.ifthen(
                    routing.pathogen < vos.MV, routing.pathogen
                )

            # update QUAlloc for the current date
            self.qualloc_model_time.update(currTimeStep.timeStepPCR)
            self.qualloc_model.update(
                online_coupling_to_quantity=self.using_qualloc,
                irrigationGrossDemand=vol_gross_sectoral_water_demands["irrigation"]
                / routing.cellArea,
                domesticGrossDemand=self.water_demand.water_demand_domestic.domesticGrossDemand,
                domesticNettoDemand=self.water_demand.water_demand_domestic.domesticNettoDemand,
                industryGrossDemand=self.water_demand.water_demand_industry.industryGrossDemand,
                industryNettoDemand=self.water_demand.water_demand_industry.industryNettoDemand,
                livestockGrossDemand=self.water_demand.water_demand_livestock.livestockGrossDemand,
                livestockNettoDemand=self.water_demand.water_demand_livestock.livestockNettoDemand,
                manufactureGrossDemand=self.water_demand.water_demand_manufacture.manufactureGrossDemand,
                manufactureNettoDemand=self.water_demand.water_demand_manufacture.manufactureNettoDemand,
                thermoelectricGrossDemand=self.water_demand.water_demand_thermoelectric.thermoelectricGrossDemand,
                thermoelectricNettoDemand=self.water_demand.water_demand_thermoelectric.thermoelectricNettoDemand,
                environmentGrossDemand=None,
                surfacewater_storage=routing.channelStorage / routing.cellArea,
                surfacewater_discharge=routing.discharge,
                surfacewater_totalrunoff=routing.runoff,
                groundwater_recharge=groundwater.gwRecharge,
                groundwater_baseflow=groundwater.baseflow,
                groundwater_storage=groundwater.storGroundwater,
                online_coupling_to_quality=self.using_dynqual,
                surfacewater_temperature=surfacewater_temperature,
                surfacewater_organic=surfacewater_organic,
                surfacewater_salinity=surfacewater_salinity,
                surfacewater_pathogen=surfacewater_pathogen,
                groundwater_temperature=None,
                groundwater_organic=None,
                groundwater_salinity=None,
                groundwater_pathogen=None,
            )

            # QUAlloc: reporting
            self.qualloc_reporting.report(self.qualloc_model_time, self.qualloc_model)

            if self.qualloc_model_time.report_flags["yearly"]:
                # end of year: report the states so the run can be restarted
                self.qualloc_model.finalize_year()

            if self.qualloc_model_time.last_time_step:
                # close all input and output files
                self.qualloc_model.finalize_run()
                self.qualloc_reporting.close()

            # variables passed to other modules:
            # sectoral water allocation from all sources (despite the 'withdrawal' in the names)

            # domestic: total allocated water (m3)
            try:
                self.domesticWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["domestic"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["domestic"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["domestic"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "domestic"
                    ]
                )
            except:
                self.domesticWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # industry: total allocated water (m3)
            try:
                self.industryWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["industry"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["industry"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["industry"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "industry"
                    ]
                )
            except:
                self.industryWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # livestock: total allocated water (m3)
            try:
                self.livestockWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["livestock"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["livestock"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["livestock"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "livestock"
                    ]
                )
            except:
                self.livestockWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # manufacture: total allocated water (m3)
            try:
                self.manufactureWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["manufacture"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["manufacture"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["manufacture"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "manufacture"
                    ]
                )
            except:
                self.manufactureWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # thermoelectric: total allocated water (m3)
            try:
                self.thermoelectricWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["thermoelectric"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["thermoelectric"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["thermoelectric"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "thermoelectric"
                    ]
                )
            except:
                self.thermoelectricWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # irrigation: total allocated water (m3)
            try:
                self.irrigationWaterWithdrawal = (
                    self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_surfacewater"
                    ]["irrigation"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "renewable_groundwater"
                    ]["irrigation"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector[
                        "nonrenewable_groundwater"
                    ]["irrigation"]
                    + self.qualloc_model.water_management.allocated_demand_per_sector_desalwater[
                        "irrigation"
                    ]
                )
            except:
                self.irrigationWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))

            # desalinated water abstraction and allocation, total of all sectors (m)
            self.desalinationAbstraction = (
                self.qualloc_model.water_management.allocated_withdrawal_desalwater
                / self.cellArea
            )
            self.desalinationAllocation = (
                self.qualloc_model.water_management.allocated_demand_desalwater
                / self.cellArea
            )

            # surface water abstraction and allocation, total of all sectors (m/day)
            self.actSurfaceWaterAbstract = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_withdrawal_per_sector[
                            "renewable_surfacewater"
                        ].values()
                    )
                )
                / self.cellArea
            )
            self.allocSurfaceWaterAbstract = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_demand_per_sector[
                            "renewable_surfacewater"
                        ].values()
                    )
                )
                / self.cellArea
            )

            # renewable groundwater abstraction and allocation, total of all sectors (m/day)
            self.nonFossilGroundwaterAbs = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_withdrawal_per_sector[
                            "renewable_groundwater"
                        ].values()
                    )
                )
                / self.cellArea
            )
            self.allocNonFossilGroundwater = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_demand_per_sector[
                            "renewable_groundwater"
                        ].values()
                    )
                )
                / self.cellArea
            )

            # non-renewable groundwater abstraction and allocation, total of all sectors (m/day)
            self.fossilGroundwaterAbstr = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_withdrawal_per_sector[
                            "nonrenewable_groundwater"
                        ].values()
                    )
                )
                / self.cellArea
            )
            self.fossilGroundwaterAlloc = (
                sum(
                    list(
                        self.qualloc_model.water_management.allocated_demand_per_sector[
                            "nonrenewable_groundwater"
                        ].values()
                    )
                )
                / self.cellArea
            )

            # total groundwater abstraction and allocation (m/day)
            self.totalGroundwaterAbstraction = (
                self.nonFossilGroundwaterAbs + self.fossilGroundwaterAbstr
            )
            self.totalGroundwaterAllocation = (
                self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
            )

            # non-irrigation variables (m3/day)
            self.nonIrrReturnFlowVolumePerSector = {}
            self.nonIrrWaterConsumptionVolumePerSector = {}

            for sector_name in self.qualloc_model.water_management.sector_names:
                nonIrrReturnFlowVolume = pcr.scalar(0.0)
                nonIrrWaterConsumptionVolume = pcr.scalar(0.0)

                if sector_name != "irrigation":
                    # return flows from desalinated water
                    nonIrrReturnFlowVolume += self.qualloc_model.water_management.return_flow_demand_per_sector_desalwater[
                        sector_name
                    ]
                    # water consumption from desalinated water
                    nonIrrWaterConsumptionVolume += self.qualloc_model.water_management.consumed_demand_per_sector_desalwater[
                        sector_name
                    ]

                    for (
                        withdrawal_name
                    ) in self.qualloc_model.water_management.withdrawal_names:
                        for (
                            source_name
                        ) in self.qualloc_model.water_management.source_names:
                            key = "%s_%s" % (withdrawal_name, source_name)

                            # return flows from surface and groundwater
                            nonIrrReturnFlowVolume += self.qualloc_model.water_management.return_flow_demand_per_sector[
                                key
                            ][
                                sector_name
                            ]
                            # water consumption from surface and groundwater
                            nonIrrWaterConsumptionVolume += self.qualloc_model.water_management.consumed_demand_per_sector[
                                key
                            ][
                                sector_name
                            ]

                    self.nonIrrReturnFlowVolumePerSector[sector_name] = deepcopy(
                        nonIrrReturnFlowVolume
                    )
                    self.nonIrrWaterConsumptionVolumePerSector[sector_name] = deepcopy(
                        nonIrrWaterConsumptionVolume
                    )

            if "domestic" not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector["domestic"] = pcr.spatial(
                    pcr.scalar(0.0)
                )

            if "industry" not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector["industry"] = pcr.spatial(
                    pcr.scalar(0.0)
                )

            if "manufacture" not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector["manufacture"] = pcr.spatial(
                    pcr.scalar(0.0)
                )

            if "thermoelectric" not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector["thermoelectric"] = pcr.spatial(
                    pcr.scalar(0.0)
                )

            if "livestock" not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector["livestock"] = pcr.spatial(
                    pcr.scalar(0.0)
                )

            self.nonIrrReturnFlowVolume = sum(
                list(self.nonIrrReturnFlowVolumePerSector.values())
            )
            self.nonIrrWaterConsumptionVolume = sum(
                list(self.nonIrrWaterConsumptionVolumePerSector.values())
            )

            # water slice (m/day): return flows
            self.nonIrrReturnFlow = self.nonIrrReturnFlowVolume / self.cellArea
            # water consumption
            self.nonIrrWaterConsumption = (
                self.nonIrrWaterConsumptionVolume / self.cellArea
            )

            self.nonIrrReturnFlow = (
                pcr.rounddown(self.nonIrrReturnFlow * 10000.0) / 10000.0
            )
            self.nonIrrReturnFlowVolume = self.nonIrrReturnFlow * self.cellArea

            # reduce capillary rise so there is always enough water for non-fossil groundwater abstraction (m)
            self.reducedCapRise = self.nonFossilGroundwaterAbs

        # standard PCR-GLOBWB water management
        else:
            self.water_management.update(
                vol_gross_sectoral_water_demands=vol_gross_sectoral_water_demands,
                groundwater=groundwater,
                routing=routing,
                currTimeStep=currTimeStep,
            )

            # domestic: total allocated water (m3)
            self.domesticWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands["domestic"]
            )

            # industry: total allocated water (m3)
            self.industryWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands["industry"]
            )

            # livestock: total allocated water (m3)
            self.livestockWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "livestock"
                ]
            )

            # manufacture: total allocated water (m3)
            self.manufactureWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "manufacture"
                ]
            )

            # thermoelectric: total allocated water (m3)
            self.thermoelectricWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "thermoelectric"
                ]
            )

            # irrigation: total allocated water (m3)
            self.irrigationWaterWithdrawal = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "irrigation"
                ]
            )

            # variables passed to other modules:
            # desalinated water abstraction and allocation, total of all sectors (m)
            self.desalinationAbstraction = self.water_management.desalinationAbstraction
            self.desalinationAllocation = self.water_management.desalinationAllocation

            # surface water abstraction and allocation, total of all sectors (m)
            self.allocSurfaceWaterAbstract = (
                self.water_management.allocSurfaceWaterAbstract
            )
            self.actSurfaceWaterAbstract = self.water_management.actSurfaceWaterAbstract

            # renewable groundwater abstraction and allocation, total of all sectors (m)
            self.nonFossilGroundwaterAbs = self.water_management.nonFossilGroundwaterAbs
            self.allocNonFossilGroundwater = (
                self.water_management.allocNonFossilGroundwater
            )

            # non-renewable groundwater abstraction, total of all sectors (m)
            self.fossilGroundwaterAbstr = self.water_management.fossilGroundwaterAbstr
            self.fossilGroundwaterAlloc = self.water_management.fossilGroundwaterAlloc

            # total groundwater abstraction and allocation (m)
            self.totalGroundwaterAbstraction = (
                self.nonFossilGroundwaterAbs + self.fossilGroundwaterAbstr
            )
            self.totalGroundwaterAllocation = (
                self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
            )

            # non-irrigation return flow (m3)
            self.nonIrrReturnFlowVolumePerSector = {}
            self.nonIrrReturnFlowVolumePerSector["domestic"] = (
                self.water_demand.water_demand_domestic.domesticReturnFlowFraction
                * self.water_management.satisfied_gross_sectoral_water_demands[
                    "domestic"
                ]
            )
            self.nonIrrReturnFlowVolumePerSector["industry"] = (
                self.water_demand.water_demand_industry.industryReturnFlowFraction
                * self.water_management.satisfied_gross_sectoral_water_demands[
                    "industry"
                ]
            )
            self.nonIrrReturnFlowVolumePerSector["manufacture"] = (
                self.water_demand.water_demand_manufacture.manufactureReturnFlowFraction
                * self.water_management.satisfied_gross_sectoral_water_demands[
                    "manufacture"
                ]
            )
            self.nonIrrReturnFlowVolumePerSector["thermoelectric"] = (
                self.water_demand.water_demand_thermoelectric.thermoelectricReturnFlowFraction
                * self.water_management.satisfied_gross_sectoral_water_demands[
                    "thermoelectric"
                ]
            )
            self.nonIrrReturnFlowVolumePerSector["livestock"] = (
                self.water_demand.water_demand_livestock.livestockReturnFlowFraction
                * self.water_management.satisfied_gross_sectoral_water_demands[
                    "livestock"
                ]
            )

            self.nonIrrReturnFlowVolume = sum(
                list(self.nonIrrReturnFlowVolumePerSector.values())
            )

            # (m)
            self.nonIrrReturnFlow = self.nonIrrReturnFlowVolume / self.cellArea

            self.nonIrrReturnFlow = (
                pcr.rounddown(self.nonIrrReturnFlow * 10000.0) / 10000.0
            )
            self.nonIrrReturnFlowVolume = self.nonIrrReturnFlow * self.cellArea

            # non-irrigation consumption (m3)
            self.nonIrrWaterConsumptionVolumePerSector = {}
            self.nonIrrWaterConsumptionVolumePerSector["domestic"] = (
                self.water_management.satisfied_gross_sectoral_water_demands["domestic"]
                - self.nonIrrReturnFlowVolumePerSector["domestic"]
            )
            self.nonIrrWaterConsumptionVolumePerSector["industry"] = (
                self.water_management.satisfied_gross_sectoral_water_demands["industry"]
                - self.nonIrrReturnFlowVolumePerSector["industry"]
            )
            self.nonIrrWaterConsumptionVolumePerSector["manufacture"] = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "manufacture"
                ]
                - self.nonIrrReturnFlowVolumePerSector["manufacture"]
            )
            self.nonIrrWaterConsumptionVolumePerSector["thermoelectric"] = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "thermoelectric"
                ]
                - self.nonIrrReturnFlowVolumePerSector["thermoelectric"]
            )
            self.nonIrrWaterConsumptionVolumePerSector["livestock"] = (
                self.water_management.satisfied_gross_sectoral_water_demands[
                    "livestock"
                ]
                - self.nonIrrReturnFlowVolumePerSector["livestock"]
            )

            self.nonIrrWaterConsumptionVolume = sum(
                list(self.nonIrrWaterConsumptionVolumePerSector.values())
            )

            # (m)
            self.nonIrrWaterConsumption = (
                self.nonIrrWaterConsumptionVolume / self.cellArea
            )

            # reduce capillary rise so there is always enough water for non-fossil groundwater abstraction (m)
            self.reducedCapRise = self.water_management.reducedCapRise

        # water demand limited by the available/allocated water (m)
        self.totalPotentialGrossDemand = (
            self.fossilGroundwaterAlloc
            + self.allocNonFossilGroundwater
            + self.allocSurfaceWaterAbstract
            + self.desalinationAllocation
        )

        self.irrGrossDemand = self.irrigationWaterWithdrawal / self.cellArea
        self.nonIrrGrossDemand = pcr.max(
            0.0, self.totalPotentialGrossDemand - self.irrGrossDemand
        )

        # total fraction of irrigated areas within the cell
        total_cell_fraction_of_irrigated_areas = pcr.ifthen(
            self.landmask, pcr.scalar(0.0)
        )
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                total_cell_fraction_of_irrigated_areas = (
                    total_cell_fraction_of_irrigated_areas
                    + self.landCoverObj[coverType].fracVegCover
                )

        # distribute the allocated irrigation water
        self.satisfied_irrigation_water_volume = {}
        self.satisfied_irrigation_water_height = {}
        for coverType in self.coverTypes:

            # irrigation land cover types
            if coverType.startswith("irr"):

                # (m3)
                self.satisfied_irrigation_water_volume[coverType] = pcr.ifthenelse(
                    total_cell_fraction_of_irrigated_areas > 0.0,
                    self.irrigationWaterWithdrawal
                    * self.landCoverObj[coverType].fracVegCover
                    / total_cell_fraction_of_irrigated_areas,
                    pcr.scalar(0.0),
                )

                # (m)
                self.satisfied_irrigation_water_height[coverType] = pcr.ifthenelse(
                    self.landCoverObj[coverType].fracVegCover > 0.0,
                    self.satisfied_irrigation_water_volume[coverType]
                    / (routing.cellArea * self.landCoverObj[coverType].fracVegCover),
                    pcr.scalar(0.0),
                )

            # non-irrigation land cover types
            else:
                self.satisfied_irrigation_water_volume[coverType] = pcr.ifthen(
                    self.landmask, pcr.scalar(0.0)
                )
                self.satisfied_irrigation_water_height[coverType] = pcr.ifthen(
                    self.landmask, pcr.scalar(0.0)
                )

        # check the water balance
        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [
                    self.desalinationAllocation,
                    self.allocSurfaceWaterAbstract,
                    self.allocNonFossilGroundwater,
                    self.fossilGroundwaterAlloc,
                ],
                [self.totalPotentialGrossDemand],
                [pcr.scalar(0.0)],
                [pcr.scalar(0.0)],
                "satisfied demand allocation from different water sources: desalination, surface water, groundwater & unmetDemand. Error here may be due to rounding error.",
                True,
                currTimeStep.fulldate,
                threshold=1e-3,
            )

        # remaining land cover processes, including applying the allocated irrGrossDemand; every land cover
        # type also needs reducedCapRise (volRenewGroundwaterAbstraction / cellArea)
        self.land_surface_hydrology_update(meteo, groundwater, routing, currTimeStep)

        # old-style reporting (useful for debugging)
        self.old_style_land_surface_reporting(currTimeStep)

    def state_transfer_among_land_cover(self, currTimeStep):

        # transfer states due to dynamic irrigation areas (expansion/reduction); done at the start of each
        # year, including the first time step

        if (
            (self.dynamicIrrigationArea and self.includeIrrigation)
            or self.noAnnualChangesInLandCoverParameter == False
        ) and currTimeStep.doy == 1:
            for var in self.mainStates:
                logger.info("Transfering states for the variable " + str(var))

                # total land cover fraction to transfer
                moving_fraction = pcr.scalar(0.0)
                # total states to transfer
                moving_states = pcr.scalar(0.0)

                for coverType in self.coverTypes:

                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover

                    moving_fraction += pcr.max(0.0, old_fraction - new_fraction)
                    moving_states += (
                        pcr.max(0.0, old_fraction - new_fraction)
                        * vars(self.landCoverObj[coverType])[var]
                    )

                previous_state = pcr.scalar(0.0)
                rescaled_state = pcr.scalar(0.0)

                # correct the states
                for coverType in self.coverTypes:

                    old_states = vars(self.landCoverObj[coverType])[var]
                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover

                    correction = moving_states * vos.getValDivZero(
                        pcr.max(0.0, new_fraction - old_fraction),
                        moving_fraction,
                        vos.smallNumber,
                    )

                    new_states = pcr.ifthenelse(
                        new_fraction > old_fraction,
                        vos.getValDivZero(
                            old_states * old_fraction + correction,
                            new_fraction,
                            vos.smallNumber,
                        ),
                        old_states,
                    )

                    new_states = pcr.ifthenelse(
                        new_fraction > 0.0, new_states, pcr.scalar(0.0)
                    )

                    vars(self.landCoverObj[coverType])[var] = new_states

                    previous_state += old_fraction * old_states
                    rescaled_state += new_fraction * new_states

                # make sure that previous_state == rescaled_state
                check_map = previous_state - rescaled_state
                a, b, c = vos.getMinMaxMean(check_map)
                threshold = 1e-5
                if abs(a) > threshold or abs(b) > threshold:
                    logger.warning(
                        "Error in transfering states (due to dynamic in land cover fractions) ... Min %f Max %f Mean %f"
                        % (a, b, c)
                    )
                else:
                    logger.info(
                        "Successful in transfering states (after change in land cover fractions) ... Min %f Max %f Mean %f"
                        % (a, b, c)
                    )

        # on the last day of the year, save the land cover fractions (used in the next time step)
        if (
            self.dynamicIrrigationArea
            and self.includeIrrigation
            and currTimeStep.isLastDayOfYear
        ):
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[
                    coverType
                ].fracVegCover

    def land_surface_hydrology_update(self, meteo, groundwater, routing, currTimeStep):

        # cell fraction influenced by capillary rise
        self.capRiseFrac = self.calculateCapRiseFrac(groundwater, routing, currTimeStep)

        # update per land cover type (excluding potential evaporation, interception and snow)
        for coverType in self.coverTypes:

            logger.info("Updating land cover: " + str(coverType))

            # irrigation losses require the irrigation efficiency
            if coverType.startswith("irr") and self.includeIrrigation:
                self.landCoverObj[coverType].irrigationEfficiencyUsed = (
                    self.water_demand.water_demand_irrigation[
                        coverType
                    ].irrigationEfficiency
                )

            self.landCoverObj[coverType].land_surface_hydrology_update_for_every_lc(
                self.capRiseFrac,
                currTimeStep,
                groundwater,
                self.satisfied_irrigation_water_height[coverType],
                self.reducedCapRise,
            )

        # set all aggregated variables to zero
        for var in self.aggrVars:
            vars(self)[var] = pcr.scalar(0.0)
        for coverType in self.coverTypes:
            # aggregate the landSurface values
            for var in self.aggrVars:
                vars(self)[var] += (
                    self.landCoverObj[coverType].fracVegCover
                    * vars(self.landCoverObj[coverType])[var]
                )

        # total storage (m3) in the landSurface module
        if self.numberOfSoilLayers == 2:
            self.totalSto = (
                self.snowCoverSWE
                + self.snowFreeWater
                + self.interceptStor
                + self.topWaterLayer
                + self.storUpp
                + self.storLow
            )
        if self.numberOfSoilLayers == 3:
            self.totalSto = (
                self.snowCoverSWE
                + self.snowFreeWater
                + self.interceptStor
                + self.topWaterLayer
                + self.storUpp000005
                + self.storUpp005030
                + self.storLow030150
            )

        # old-style reporting (useful for debugging)
        self.old_style_land_surface_reporting(currTimeStep)

    def old_style_land_surface_reporting(self, currTimeStep):

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
                        pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
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
                            pcr.pcr2numpy(
                                self.__getattribute__(var + "MonthTot"), vos.MV
                            ),
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
                            pcr.pcr2numpy(
                                self.__getattribute__(var + "MonthAvg"), vos.MV
                            ),
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
                            pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
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
                            pcr.pcr2numpy(
                                self.__getattribute__(var + "AnnuaTot"), vos.MV
                            ),
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
                            pcr.pcr2numpy(
                                self.__getattribute__(var + "AnnuaAvg"), vos.MV
                            ),
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
                            pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                            timeStamp,
                            currTimeStep.annuaIdx - 1,
                        )
