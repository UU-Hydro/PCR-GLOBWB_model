import logging
import os
from copy import deepcopy

import pcraster as pcr
from pcraster.framework import *
from six.moves import map

logger = logging.getLogger(__name__)

from pcrglobwb import waterBodies
from pcrglobwb.common import virtualOS as vos
from pcrglobwb.ncConverter import *


class Routing(object):

    def getPseudoState(self):
        result = {}
        return result

    def getState(self):
        result = {}

        # hydrology states
        # (day)
        result["timestepsToAvgDischarge"] = self.timestepsToAvgDischarge
        # channel storage, including lake and reservoir storage (m3)
        result["channelStorage"] = self.channelStorage
        # readily available channel storage that can be abstracted to satisfy water demand (m3)
        result["readAvlChannelStorage"] = self.readAvlChannelStorage
        # long-term average discharge (m3/s)
        result["avgDischargeLong"] = self.avgDischarge
        # ((m3/s)^2)
        result["m2tDischargeLong"] = self.m2tDischarge
        # long-term average baseflow (m3/s)
        result["avgBaseflowLong"] = self.avgBaseflow
        # river bed infiltration from surface water bodies to groundwater (m3/day)
        result["riverbedExchange"] = self.riverbedExchange
        # lake and reservoir storage (m3), per water body id (not per cell)
        result["waterBodyStorage"] = self.waterBodyStorage
        # long-term average lake and reservoir outflow (m3/s), per water body id (not per cell)
        result["avgLakeReservoirOutflowLong"] = self.avgOutflow
        # short-term average lake and reservoir inflow (m3/s), per water body id (not per cell)
        result["avgLakeReservoirInflowShort"] = self.avgInflow
        # short-term average discharge (m3/s)
        result["avgDischargeShort"] = self.avgDischargeShort
        # sub-time step discharge (m3/s), needed for the kinematic wave methods
        result["subDischarge"] = self.subDischarge

        # QUAlloc: long-term water availability
        if self.using_qualloc:
            # discharge (m3/s)
            result["discharge"] = self.discharge
            # total runoff (m/day)
            result["runoff"] = self.runoff

            if self.quality:
                # TDS concentration (mg/L)
                result["salinity"] = self.salinity
                # BOD concentration (mg/L)
                result["organic"] = self.organic
                # FC concentration (cfu/100mL)
                result["pathogen"] = self.pathogen

        # DynQual: irrigation return flows
        if self.quality:
            # average irrigation gross demand (m/day)
            result["avg_irrGrossDemand"] = self.avg_irrGrossDemand
            # average net liquid water transferred to the soil (m/day)
            result["avg_netLqWaterToSoil"] = self.avg_netLqWaterToSoil
        else:
            logger.info("Irrigation return flows not estimated")

        # water quality states
        if self.quality:
            # water temperature (K)
            result["waterTemperature"] = self.waterTemp
            # ice thickness (m)
            result["iceThickness"] = self.iceThickness
            # routed TDS load (g), converted to salinity pollution (mg/L)
            result["routedTDS"] = self.routedTDS
            # routed BOD load (g), converted to organic pollution (mg/L)
            result["routedBOD"] = self.routedBOD
            # routed FC load (cfu), converted to pathogen pollution (cfu/100mL)
            result["routedFC"] = self.routedFC

            if self.offlineRun == False and self.calculateLoads and self.loadsPerSector:
                # pollutants routed per sector (for the analysis of sectoral contributions): domestic
                # (g TDS)
                result["routedDomTDS"] = self.routedDomTDS
                # (g BOD)
                result["routedDomBOD"] = self.routedDomBOD
                # (10^6 cfu)
                result["routedDomFC"] = self.routedDomFC
                # manufacturing
                # (g TDS)
                result["routedManTDS"] = self.routedManTDS
                # (g BOD)
                result["routedManBOD"] = self.routedManBOD
                # (10^6 cfu)
                result["routedManFC"] = self.routedManFC
                # urban surface runoff
                # (g TDS)
                result["routedUSRTDS"] = self.routedUSRTDS
                # (g BOD)
                result["routedUSRBOD"] = self.routedUSRBOD
                # (10^6 cfu)
                result["routedUSRFC"] = self.routedUSRFC
                # intensive livestock
                # (g BOD)
                result["routedintLivBOD"] = self.routedintLivBOD
                # (10^6 cfu)
                result["routedintLivFC"] = self.routedintLivFC
                # extensive livestock
                # (g BOD)
                result["routedextLivBOD"] = self.routedextLivBOD
                # (10^6 cfu)
                result["routedextLivFC"] = self.routedextLivFC
                # irrigation
                # (g TDS)
                result["routedIrrTDS"] = self.routedIrrTDS
            else:
                logger.info("Water quality per sector not tracked")
        else:
            logger.info("Water quality elements not simulated")
        return result

    def __init__(self, iniItems, initialConditions, lddMap):
        object.__init__(self)

        self.lddMap = lddMap

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]

        # option to activate the water balance check
        self.debugWaterBalance = True
        if iniItems.routingOptions["debugWaterBalance"] == "False":
            self.debugWaterBalance = False

        self.method = iniItems.routingOptions["routingMethod"]

        # option to include lakes and reservoirs
        self.includeWaterBodies = True
        if "includeWaterBodies" in list(iniItems.routingOptions.keys()):
            if (
                iniItems.routingOptions["includeWaterBodies"] == "False"
                or iniItems.routingOptions["includeWaterBodies"] == "None"
            ):
                self.includeWaterBodies = False

        # sectors evaluated
        self.includeSectors = {}
        self.includeSectors["industry"] = False
        self.includeSectors["manufacture"] = False
        if iniItems.waterDemandOptions["includeIndustryWaterDemand"] == "True":
            self.includeSectors["industry"] = True
        elif iniItems.waterDemandOptions["includeManufactureWaterDemand"] == "True":
            self.includeSectors["manufacture"] = True

        self.lddMap = vos.readPCRmapClone(
            iniItems.routingOptions["lddMap"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
            True,
        )
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        self.lddMap = pcr.lddrepair(self.lddMap)

        # complete ldd before clipping to the landmask (see below); needed to route upstream discharge
        # (from other sub-runs) into this basin, as the cells supplying it lie just outside the landmask
        self.ldd_complete = self.lddMap

        if iniItems.globalOptions["landmask"] != "None":
            self.landmask = vos.readPCRmapClone(
                iniItems.globalOptions["landmask"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        else:
            self.landmask = pcr.defined(self.lddMap)
        self.landmask = pcr.ifthen(pcr.defined(self.lddMap), self.landmask)
        self.landmask = pcr.cover(self.landmask, pcr.boolean(0))

        self.lddMap = pcr.lddmask(self.lddMap, self.landmask)

        # cell area (m2)
        self.cellArea = vos.readPCRmapClone(
            iniItems.routingOptions["cellAreaMap"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        # model resolution (arc-degree)
        self.cellSizeInArcDeg = vos.getMapAttributes(self.cloneMap, "cellsize")

        # maximum number of time steps for long-term average flows (default: 5 years = 1825 days)
        self.maxTimestepsToAvgDischargeLong = 1825.0

        # maximum number of time steps for short-term average values (default: 1 month = 30 days)
        self.maxTimestepsToAvgDischargeShort = 30.0

        routingParameters = ["gradient", "manningsN"]
        for var in routingParameters:
            input = iniItems.routingOptions[str(var)]
            vars(self)[var] = vos.readPCRmapClone(
                input, self.cloneMap, self.tmpDir, self.inputDir
            )

        # parameters to estimate the channel dimensions (used in getRoutingParamAvgDischarge)
        self.eta = 0.25
        self.nu = 0.40
        self.tau = 8.00
        self.phi = 0.58

        # option to use a minimum channel width (m)
        self.minChannelWidth = pcr.scalar(0.0)
        if "minimumChannelWidth" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions["minimumChannelWidth"] != "None":
                self.minChannelWidth = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.routingOptions["minimumChannelWidth"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )

        # option to use a predefined channel width (m)
        self.predefinedChannelWidth = None
        if "constantChannelWidth" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions["constantChannelWidth"] != "None":
                self.predefinedChannelWidth = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.routingOptions["constantChannelWidth"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )

        # option to use a predefined channel depth (m)
        self.predefinedChannelDepth = None
        if "constantChannelDepth" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions["constantChannelDepth"] != "None":
                self.predefinedChannelDepth = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.routingOptions["constantChannelDepth"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )

        # assumption for broad sheet flow in the kinematic wave methods
        self.beta = 0.6

        # channel length (m), approximated by the cell diagonal
        cellSizeInArcMin = self.cellSizeInArcDeg * 60.0
        verticalSizeInMeter = cellSizeInArcMin * 1852.0
        self.cellLengthFD = (
            (self.cellArea / verticalSizeInMeter) ** (2) + (verticalSizeInMeter) ** (2)
        ) ** (0.5)
        self.channelLength = self.cellLengthFD
        # channel length (m)
        if "channelLength" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions["channelLength"] != "None":
                self.channelLength = pcr.cover(
                    vos.readPCRmapClone(
                        iniItems.routingOptions["channelLength"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    self.channelLength,
                )

        # dist2celllength (m/arcDegree), needed in the accuTravelTime function
        nrCellsDownstream = pcr.ldddist(self.lddMap, pcr.nominal(self.lddMap) == 5, 1.0)
        distanceDownstream = pcr.ldddist(
            self.lddMap, pcr.nominal(self.lddMap) == 5, self.channelLength
        )
        # (m)
        channelLengthDownstream = (self.channelLength + distanceDownstream) / (
            nrCellsDownstream + 1
        )
        # (m/arcDegree)
        self.dist2celllength = channelLengthDownstream / self.cellSizeInArcDeg

        self.distance_to_pit = 0.5 * self.channelLength + distanceDownstream

        # the channel gradient must be >= minGradient
        minGradient = 0.00005
        self.gradient = pcr.max(minGradient, pcr.cover(self.gradient, minGradient))

        self.WaterBodies = waterBodies.WaterBodies(iniItems, self.landmask)

        # crop evaporation coefficient of surface water bodies
        self.no_zero_crop_water_coefficient = True
        if iniItems.routingOptions["cropCoefficientWaterNC"] == "None":
            self.no_zero_crop_water_coefficient = False
        else:
            self.fileCropKC = vos.getFullPath(
                iniItems.routingOptions["cropCoefficientWaterNC"], self.inputDir
            )

        # Courant number criterion for numerical stability in the kinematic wave methods
        self.courantNumber = 0.50

        # empirical values for the minimum number of sub-time steps (m/s)
        design_flood_speed = 5.00
        design_length_of_sub_time_step = pcr.cellvalue(
            pcr.mapminimum(
                self.courantNumber * self.channelLength / design_flood_speed
            ),
            1,
        )[0]
        self.limit_num_of_sub_time_steps = np.ceil(
            vos.secondsPerDay() / design_length_of_sub_time_step
        )
        # at least 24 sub-time steps (hourly, as in Van Beek et al., 2011)
        self.limit_num_of_sub_time_steps = max(24.0, self.limit_num_of_sub_time_steps)

        # minimum number of sub-time steps from the ini file
        if "maxiumLengthOfSubTimeStep" in list(iniItems.routingOptions.keys()):
            maxiumLengthOfSubTimeStep = float(
                iniItems.routingOptions["maxiumLengthOfSubTimeStep"]
            )
            minimum_number_of_sub_time_step = np.ceil(
                vos.secondsPerDay() / maxiumLengthOfSubTimeStep
            )
            self.limit_num_of_sub_time_steps = max(
                minimum_number_of_sub_time_step, self.limit_num_of_sub_time_steps
            )
        self.limit_num_of_sub_time_steps = int(self.limit_num_of_sub_time_steps)

        # critical water height (m) to select a stable sub-time step length in the kinematic wave methods,
        self.critical_water_height = 0.25
        # as in Van Beek et al. (2011)

        # minimum fracWat used to calculate the water height (-)
        self.min_fracwat_for_water_height = 0.001
        self.max_water_height = 50000000

        # minimum crop coefficient of surface water bodies
        self.minCropWaterKC = 0.00
        if "minCropWaterKC" in list(iniItems.routingOptions.keys()):
            self.minCropWaterKC = float(iniItems.routingOptions["minCropWaterKC"])

        # floodplain options
        self.floodPlain = iniItems.routingOptions["dynamicFloodPlain"] == "True"
        if self.floodPlain:

            logger.info("Flood plain extents can vary during the simulation.")

            # Manning's n of the floodplain areas
            input = iniItems.routingOptions["floodplainManningsN"]
            self.floodplainManN = vos.readPCRmapClone(
                input, self.cloneMap, self.tmpDir, self.inputDir
            )

            # reduction parameter of the smoothing interval and error threshold
            self.reductionKK = 0.5
            if "reductionKK" in list(iniItems.routingOptions.keys()):
                self.reductionKK = float(iniItems.routingOptions["reductionKK"])
            self.criterionKK = 40.0
            if "criterionKK" in list(iniItems.routingOptions.keys()):
                self.criterionKK = float(iniItems.routingOptions["criterionKK"])

            # profile of relative elevation above the floodplain per cell (including smoothing parameters)
            (
                self.nrZLevels,
                self.areaFractions,
                self.relZ,
                self.floodVolume,
                self.kSlope,
                self.mInterval,
            ) = self.getElevationProfile(iniItems)

            # bankfull capacity (m3)
            self.predefinedBankfullCapacity = None
            self.usingFixedBankfullCapacity = False
            if iniItems.routingOptions["bankfullCapacity"] != "None":

                self.usingFixedBankfullCapacity = True
                self.predefinedBankfullCapacity = vos.readPCRmapClone(
                    iniItems.routingOptions["bankfullCapacity"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                self.predefinedBankfullCapacity = pcr.cover(
                    self.predefinedBankfullCapacity, pcr.spatial(pcr.scalar(0.0))
                )

            else:
                msg = "The bankfull channel storage capacity is NOT defined in the configuration file. "

                if (
                    self.predefinedChannelWidth is None
                    or self.predefinedChannelDepth is None
                ):
                    msg += "The bankfull capacity is estimated from average discharge (5 year long term average)."
                else:
                    msg += "The bankfull capacity is estimated from the given channel depth and channel width."
                    self.usingFixedBankfullCapacity = True
                    self.predefinedBankfullCapacity = self.estimateBankfullCapacity(
                        self.predefinedChannelWidth, self.predefinedChannelDepth
                    )

                logger.info(msg)

        # option to limit the flood depth (to avoid unrealistic flood depths)
        self.maxFloodDepth = None
        if "maxFloodDepth" in list(iniItems.routingOptions.keys()):
            self.maxFloodDepth = vos.readPCRmapClone(
                iniItems.routingOptions["maxFloodDepth"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

        # input file for upstream discharge (from upstream basins)
        self.upstream_discharge_input_files = None
        if (
            "upstream_discharge_input_files" in list(iniItems.routingOptions.keys())
            and iniItems.routingOptions["upstream_discharge_input_files"] != "None"
        ):
            self.upstream_discharge_input_files = iniItems.routingOptions[
                "upstream_discharge_input_files"
            ].split(",")

        # DynQual
        self.quality = False
        if (
            "quality" in iniItems.routingOptions.keys()
            and iniItems.routingOptions["quality"] == "True"
        ):
            self.quality = True
            logger.info("Water quality modelling initiated.")
        else:
            logger.info("Water quality modelling not initiated.")

        print("waterTemperature =", self.quality)
        print("Salinity = ", self.quality)
        print("Organic = ", self.quality)
        print("Dissolved oxygen = ", self.quality)
        print("Pathogen = ", self.quality)

        self.WWtPlants = False
        if "WWtPlantsNC" in list(iniItems.routingOptions.keys()):
            self.WWtPlants = True
            # wastewater pathways and removal efficiencies (treatment: tertiary, secondary, primary; collected but untreated; basic sanitation; open defecation; direct)
            self.WWtPlantsNC = vos.getFullPath(
                iniItems.routingOptions["WWtPlantsNC"], self.inputDir
            )

        if self.quality:

            # discharge threshold for estimating concentrations (default: 0.1 m3/s)
            self.WQ_discharge_threshold = 0.1
            if "WQ_discharge_threshold" in iniItems.routingOptions.keys():
                self.WQ_discharge_threshold = float(
                    iniItems.routingOptions["WQ_discharge_threshold"]
                )

            # water temperature parameters: temperature threshold for snowmelt (K)
            self.iceThresTemp = pcr.scalar(273.15)
            # density of water (kg/m3)
            self.densityWater = pcr.scalar(1000.0)
            # latent heat of vaporization (J/kg)
            self.latentHeatVapor = pcr.scalar(2.5e6)
            # latent heat of fusion (J/kg)
            self.latentHeatFusion = pcr.scalar(3.34e5)
            # specific heat of water (J/kg/degC)
            self.specificHeatWater = pcr.scalar(4190.0)
            # heat transfer coefficient of water (W/m2/degC)
            self.heatTransferWater = pcr.scalar(20.0)
            # heat transfer coefficient of ice (W/m2/degC)
            self.heatTransferIce = pcr.scalar(8.0)
            # albedo of water (-)
            self.albedoWater = pcr.scalar(0.15)
            # albedo of snow and ice (-)
            self.albedoSnow = pcr.scalar(0.50)
            # energy balance proxy for the groundwater temperature: mean annual temperature and the temperature reduction for falling rain
            self.deltaTPrec = pcr.scalar(1.5)

            self.radCon = 0.25
            self.radSlope = 0.50
            # Stefan-Boltzmann constant (W/m2/K4)
            self.stefanBoltzman = 5.67e-8
            # maximum river temperature: 322.15 K (50 degC)
            self.maxThresTemp = pcr.scalar(322.15)

            self.maxIceThickness = 3.0
            self.deltaIceThickness = 0.0

            if iniItems.meteoOptions["sunhoursTable"] != "Default":
                # convert cloud cover to sunshine hours (Doornkamp & Pruitt)
                self.sunFracTBL = vos.getFullPath(
                    iniItems.meteoOptions["sunhoursTable"], self.inputDir
                )
            else:
                self.sunFracTBL = vos.getFullPath(
                    "sunhoursfrac.tbl", os.path.abspath(os.path.dirname(__file__))
                )
                msg = "Using the default sunhoursfrac.tbl stored on " + self.sunFracTBL
                # sunshine fraction table
                logger.info(msg)

            # paths to additional meteorological variables
            self.cloudFileNC = vos.getFullPath(
                iniItems.meteoOptions["cloudcoverNC"], self.inputDir
            )
            self.radFileNC = vos.getFullPath(
                iniItems.meteoOptions["radiationNC"], self.inputDir
            )
            self.vapFileNC = vos.getFullPath(
                iniItems.meteoOptions["vaporNC"], self.inputDir
            )
            self.annualTFileNC = vos.getFullPath(
                iniItems.meteoOptions["annualAvgTNC"], self.inputDir
            )

            # paths to power plant data
            self.TlmaxNC = vos.getFullPath(
                iniItems.routingOptions["TlmaxNC"], self.inputDir
            )
            self.powerplants_fwNC = vos.getFullPath(
                iniItems.routingOptions["powerplants_fwNC"], self.inputDir
            )
            self.powerplants_fwfixedNC = vos.getFullPath(
                iniItems.routingOptions["powerplants_fwfixedNC"], self.inputDir
            )
            self.powerplants_swNC = vos.getFullPath(
                iniItems.routingOptions["powerplants_swNC"], self.inputDir
            )

            # salinity: background TDS concentration (mg/L)
            self.backgroundSalinityNC = vos.getFullPath(
                iniItems.routingOptions["backgroundSalinity"], self.inputDir
            )
            # (mg/L)
            self.backgroundSalinity = vos.netcdf2PCRobjCloneWithoutTime(
                self.backgroundSalinityNC, "bgTDS", self.cloneMap
            )

            # organic pollution: first-order degradation coefficient at 20 degC (van Vliet et al., 2021)
            self.k_BOD = pcr.scalar(0.35)
            # temperature correction (van Vliet et al., 2021; Wen et al., 2017)
            self.watertempcorrection_BOD = pcr.scalar(1.047)

            # dissolved oxygen: elevation data
            self.elevation_path = vos.getFullPath(
                iniItems.landSurfaceOptions["topographyNC"], self.inputDir
            )
            self.elevation = vos.netcdf2PCRobjCloneWithoutTime(
                self.elevation_path,
                "dem_average",
                self.cloneMap,
                True,
                None,
                self.inputDir,
            )

            # fecal coliforms: temperature-dependent decay (day-1; Reder et al., 2015)

            self.darkinactivation_FC = pcr.scalar(0.82)
            # Reder et al. (2015)
            self.watertempcorrection_FC = pcr.scalar(1.07)

            # solar radiation dependent decay: total suspended solids (Beusen et al., 2005)
            self.tss = vos.readPCRmapClone(
                iniItems.routingOptions["TSSmap"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            # (m2/W; Reder et al., 2015)
            self.sunlightinactivation_FC = pcr.scalar(0.0068)
            # (m-1; Reder et al., 2015)
            self.attenuation_FC = 0.0931 * self.tss + 0.881

            # sedimentation: the stream depth must exceed 0.5 m for sedimentation to occur (m)
            self.threshold_FC_settlingdepth = pcr.scalar(0.5)
            # (m/day; Reder et al., 2015)
            self.settlingvelocity_FC = pcr.scalar(1.656)

            # options for offline runs
            if iniItems.routingOptions["offlineRun"] == "True":
                self.offlineRun = True
                logger.info("DynQual running in offline configuration")

                # baseflow, interflow and direct runoff, required for offline DynQual runs
                self.baseflowNC = vos.getFullPath(
                    iniItems.routingOptions["baseflowNC"], self.inputDir
                )
                self.interflowNC = vos.getFullPath(
                    iniItems.routingOptions["interflowNC"], self.inputDir
                )
                self.directRunoffNC = vos.getFullPath(
                    iniItems.routingOptions["directRunoffNC"], self.inputDir
                )

                if iniItems.routingOptions["calculateLoads"] == "True":
                    logger.info(
                        "WARNING: Cannot calculate pollutant loadings in offline configuration."
                    )
                    logger.info(
                        "Switch to online configuration or prescribe loadings directly."
                    )

            else:
                self.offlineRun = False
                logger.info("DynQual running online")

            # calculate the loadings within the model run
            if (
                iniItems.routingOptions["calculateLoads"] == "True"
                and self.offlineRun == False
            ):
                self.calculateLoads = True
                logger.info("Loadings calculated within model run.")

                if iniItems.routingOptions["loadsPerSector"] == "True":
                    self.loadsPerSector = True
                    logger.info("Option to report loads per sector enabled")
                else:
                    self.loadsPerSector = False

            else:
                self.calculateLoads = False
                self.loadsPerSector = False
                logger.info(
                    "Loadings are prescribed (i.e. akin to a forcing) to the model"
                )

            if self.calculateLoads:

                # pollutant loading input data: domestic, gridded annual population at 5 arcmin (Lange & Geiger, 2020)

                self.PopulationNC = vos.getFullPath(
                    iniItems.routingOptions["PopulationNC"], self.inputDir
                )
                # average (regional) excretion rates
                self.Dom_ExcrLoadNC = vos.getFullPath(
                    iniItems.routingOptions["Dom_ExcrLoadNC"], self.inputDir
                )
                # (g/capita/day)
                self.DomTDS_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Dom_ExcrLoadNC, "Dom_Fixed_TDSload", self.cloneMap
                )
                # (g/capita/day)
                self.DomBOD_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Dom_ExcrLoadNC, "Dom_Fixed_BODload", self.cloneMap
                )
                # (cfu/capita/day)
                self.DomFC_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Dom_ExcrLoadNC, "Dom_Fixed_FCload", self.cloneMap
                )

                # manufacturing: average (regional) effluent concentrations
                self.Man_EfflConcNC = vos.getFullPath(
                    iniItems.routingOptions["Man_EfflConcNC"], self.inputDir
                )
                # (mg/L, i.e. g/m3)
                self.ManTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Man_EfflConcNC, "Man_Fixed_TDSload", self.cloneMap
                )
                # (mg/L, i.e. g/m3)
                self.ManBOD_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Man_EfflConcNC, "Man_Fixed_BODload", self.cloneMap
                )
                # (cfu/100mL)
                self.ManFC_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Man_EfflConcNC, "Man_Fixed_FCload", self.cloneMap
                )

                # urban surface runoff: urban fraction, from 0 (no urban) to 1 (all urban)
                self.UrbanFractionNC = vos.getFullPath(
                    iniItems.routingOptions["UrbanFractionNC"], self.inputDir
                )
                # average (regional) effluent concentrations
                self.USR_EfflConcNC = vos.getFullPath(
                    iniItems.routingOptions["USR_EfflConcNC"], self.inputDir
                )
                # (mg/L, i.e. g/m3)
                self.USRTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.USR_EfflConcNC, "USR_Fixed_TDSload", self.cloneMap
                )
                # (mg/L, i.e. g/m3)
                self.USRBOD_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.USR_EfflConcNC, "USR_Fixed_BODload", self.cloneMap
                )
                # (cfu/100mL)
                self.USRFC_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.USR_EfflConcNC, "USR_Fixed_FCload", self.cloneMap
                )

                # livestock: gridded populations, 2010, 5 arcmin (Gilbert et al., 2018)
                self.LivPopulationNC = vos.getFullPath(
                    iniItems.routingOptions["LivPopulationNC"], self.inputDir
                )
                # average (regional) excretion rates
                self.Liv_ExcrLoadNC = vos.getFullPath(
                    iniItems.routingOptions["Liv_ExcrLoadNC"], self.inputDir
                )
                # (g/stock/day)
                self.Bufallo_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "bufallo_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Chicken_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "chicken_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Cow_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "cow_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Duck_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "duck_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Goat_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "goat_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Horse_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "horse_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Pig_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "pig_BODload", self.cloneMap
                )
                # (g/stock/day)
                self.Sheep_BODload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "sheep_BODload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Bufallo_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "bufallo_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Chicken_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "chicken_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Cow_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "cow_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Duck_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "duck_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Goat_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "goat_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Horse_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "horse_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Pig_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "pig_FCload", self.cloneMap
                )
                # (cfu/stock/day)
                self.Sheep_FCload = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Liv_ExcrLoadNC, "sheep_FCload", self.cloneMap
                )

                # irrigation: soil concentration averaged over the topsoil and subsoil
                self.Irr_EfflConcNC = vos.getFullPath(
                    iniItems.routingOptions["Irr_EfflConcNC"], self.inputDir
                )
                # (mg/L)
                self.IrrTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(
                    self.Irr_EfflConcNC, "soil_TDS", self.cloneMap
                )

            else:
                # paths to (non-natural) TDS, BOD and FC loading inputs
                self.TDSloadNC = vos.getFullPath(
                    iniItems.routingOptions["TDSloadNC"], self.inputDir
                )
                self.BODloadNC = vos.getFullPath(
                    iniItems.routingOptions["BODloadNC"], self.inputDir
                )
                self.FCloadNC = vos.getFullPath(
                    iniItems.routingOptions["FCloadNC"], self.inputDir
                )

        else:
            self.calculateLoads = False
            self.loadsPerSector = False

        self.using_qualloc = False
        if (
            "using_qualloc" in iniItems.waterManagementOptions
            and iniItems.waterManagementOptions["using_qualloc"] == "True"
        ):
            self.using_qualloc = True

        self.getICs(iniItems, initialConditions)

        # old-style reporting (useful for debugging)
        self.initiate_old_style_routing_reporting(iniItems)

    def getICs(self, iniItems, iniConditions=None):

        if iniConditions == None:
            logger.info(
                "Reading initial conditions from pcraster maps listed in the .ini file"
            )
            # read the initial conditions from the PCRaster maps in the ini file (at the start of the model)
            self.timestepsToAvgDischarge = vos.readPCRmapClone(
                iniItems.routingOptions["timestepsToAvgDischargeIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            self.channelStorage = vos.readPCRmapClone(
                iniItems.routingOptions["channelStorageIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.readAvlChannelStorage = vos.readPCRmapClone(
                iniItems.routingOptions["readAvlChannelStorageIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgDischarge = vos.readPCRmapClone(
                iniItems.routingOptions["avgDischargeLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.m2tDischarge = vos.readPCRmapClone(
                iniItems.routingOptions["m2tDischargeLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgBaseflow = vos.readPCRmapClone(
                iniItems.routingOptions["avgBaseflowLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.riverbedExchange = vos.readPCRmapClone(
                iniItems.routingOptions["riverbedExchangeIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # initial condition introduced in version 2.0.2: avgDischargeShort
            self.avgDischargeShort = vos.readPCRmapClone(
                iniItems.routingOptions["avgDischargeShortIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # initial conditions needed for the kinematic wave methods
            self.subDischarge = vos.readPCRmapClone(
                iniItems.routingOptions["subDischargeIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # initial conditions needed for coupling with QUAlloc
            if self.using_qualloc:
                self.discharge = vos.readPCRmapClone(
                    iniItems.routingOptions["dischargeIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                self.runoff = vos.readPCRmapClone(
                    iniItems.routingOptions["runoffIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

                if self.quality:
                    # salinity pollution
                    self.salinity = vos.readPCRmapClone(
                        iniItems.routingOptions["salinityIni"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )
                    # organic pollution
                    self.organic = vos.readPCRmapClone(
                        iniItems.routingOptions["organicIni"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )
                    # pathogen pollution
                    self.pathogen = vos.readPCRmapClone(
                        iniItems.routingOptions["pathogenIni"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )

            # initial conditions needed for the water quality module
            if self.quality:
                self.waterTemp = vos.readPCRmapClone(
                    iniItems.routingOptions["waterTemperatureIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                self.iceThickness = vos.readPCRmapClone(
                    iniItems.routingOptions["iceThicknessIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                # salinity pollution
                self.routedTDS = vos.readPCRmapClone(
                    iniItems.routingOptions["routedTDSIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                # organic pollution
                self.routedBOD = vos.readPCRmapClone(
                    iniItems.routingOptions["routedBODIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                # pathogen pollution
                self.routedFC = vos.readPCRmapClone(
                    iniItems.routingOptions["routedFCIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )

                # initial average irrigation demand and net liquid water to the soil, for the irrigation return flows
                if self.calculateLoads and self.offlineRun == False:
                    self.avg_irrGrossDemand = vos.readPCRmapClone(
                        iniItems.routingOptions["avg_irrGrossDemandIni"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )
                    self.avg_netLqWaterToSoil = vos.readPCRmapClone(
                        iniItems.routingOptions["avg_netLqWaterToSoilIni"],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    )

                    # per water quality sector
                    if self.loadsPerSector:
                        self.routedDomTDS = vos.readPCRmapClone(
                            iniItems.routingOptions["routedDomTDSIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedDomBOD = vos.readPCRmapClone(
                            iniItems.routingOptions["routedDomBODIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedDomFC = vos.readPCRmapClone(
                            iniItems.routingOptions["routedDomFCIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedManTDS = vos.readPCRmapClone(
                            iniItems.routingOptions["routedManTDSIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedManBOD = vos.readPCRmapClone(
                            iniItems.routingOptions["routedManBODIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedManFC = vos.readPCRmapClone(
                            iniItems.routingOptions["routedManFCIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedUSRTDS = vos.readPCRmapClone(
                            iniItems.routingOptions["routedUSRTDSIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedUSRBOD = vos.readPCRmapClone(
                            iniItems.routingOptions["routedUSRBODIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedUSRFC = vos.readPCRmapClone(
                            iniItems.routingOptions["routedUSRFCIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedintLivBOD = vos.readPCRmapClone(
                            iniItems.routingOptions["routedintLivBODIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedintLivFC = vos.readPCRmapClone(
                            iniItems.routingOptions["routedintLivFCIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedextLivBOD = vos.readPCRmapClone(
                            iniItems.routingOptions["routedextLivBODIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedextLivFC = vos.readPCRmapClone(
                            iniItems.routingOptions["routedextLivFCIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )
                        self.routedIrrTDS = vos.readPCRmapClone(
                            iniItems.routingOptions["routedIrrTDSIni"],
                            self.cloneMap,
                            self.tmpDir,
                            self.inputDir,
                        )

        else:
            logger.info("Reading initial conditions from memory.")
            # read the initial conditions from memory
            self.timestepsToAvgDischarge = iniConditions["routing"][
                "timestepsToAvgDischarge"
            ]

            self.channelStorage = iniConditions["routing"]["channelStorage"]
            self.readAvlChannelStorage = iniConditions["routing"][
                "readAvlChannelStorage"
            ]
            self.avgDischarge = iniConditions["routing"]["avgDischargeLong"]
            self.m2tDischarge = iniConditions["routing"]["m2tDischargeLong"]
            self.avgBaseflow = iniConditions["routing"]["avgBaseflowLong"]
            self.riverbedExchange = iniConditions["routing"]["riverbedExchange"]
            self.avgDischargeShort = iniConditions["routing"]["avgDischargeShort"]

            self.subDischarge = iniConditions["routing"]["subDischarge"]

            # initial conditions needed for coupling with QUAlloc
            if self.using_qualloc:
                self.discharge = iniConditions["routing"]["discharge"]
                self.runoff = iniConditions["routing"]["runoff"]

                if self.quality:
                    self.salinity = iniConditions["routing"]["salinity"]
                    self.organic = iniConditions["routing"]["organic"]
                    self.pathogen = iniConditions["routing"]["pathogen"]

            # initial conditions needed for the water quality module (DynQual)
            if self.quality:
                self.waterTemp = iniConditions["routing"]["waterTemperature"]
                self.iceThickness = iniConditions["routing"]["iceThickness"]
                self.routedTDS = iniConditions["routing"]["routedTDS"]
                self.routedBOD = iniConditions["routing"]["routedBOD"]
                self.routedFC = iniConditions["routing"]["routedFC"]

                # initial average irrigation demand and net liquid water to the soil, for the irrigation return flows
                if self.calculateLoads and self.offlineRun == False:
                    self.avg_irrGrossDemand = iniConditions["routing"][
                        "avg_irrGrossDemand"
                    ]
                    self.avg_netLqWaterToSoil = iniConditions["routing"][
                        "avg_netLqWaterToSoil"
                    ]

                    # per water quality sector
                    if self.loadsPerSector:
                        self.routedDomTDS = iniConditions["routing"]["routedDomTDS"]
                        self.routedDomBOD = iniConditions["routing"]["routedDomBOD"]
                        self.routedDomFC = iniConditions["routing"]["routedDomFC"]
                        self.routedManTDS = iniConditions["routing"]["routedManTDS"]
                        self.routedManBOD = iniConditions["routing"]["routedManBOD"]
                        self.routedManFC = iniConditions["routing"]["routedManFC"]
                        self.routedUSRTDS = iniConditions["routing"]["routedUSRTDS"]
                        self.routedUSRBOD = iniConditions["routing"]["routedUSRBOD"]
                        self.routedUSRFC = iniConditions["routing"]["routedUSRFC"]
                        self.routedintLivBOD = iniConditions["routing"][
                            "routedintLivBOD"
                        ]
                        self.routedintLivFC = iniConditions["routing"]["routedintLivFC"]
                        self.routedextLivBOD = iniConditions["routing"][
                            "routedextLivBOD"
                        ]
                        self.routedextLivFC = iniConditions["routing"]["routedextLivFC"]
                        self.routedIrrTDS = iniConditions["routing"]["routedIrrTDS"]

        # values within the landmask
        self.channelStorage = pcr.ifthen(
            self.landmask, pcr.cover(self.channelStorage, 0.0)
        )
        self.readAvlChannelStorage = pcr.ifthen(
            self.landmask, pcr.cover(self.readAvlChannelStorage, 0.0)
        )
        self.avgDischarge = pcr.ifthen(self.landmask, pcr.cover(self.avgDischarge, 0.0))
        self.m2tDischarge = pcr.ifthen(self.landmask, pcr.cover(self.m2tDischarge, 0.0))
        self.avgDischargeShort = pcr.ifthen(
            self.landmask, pcr.cover(self.avgDischargeShort, 0.0)
        )
        self.avgBaseflow = pcr.ifthen(self.landmask, pcr.cover(self.avgBaseflow, 0.0))
        self.riverbedExchange = pcr.ifthen(
            self.landmask, pcr.cover(self.riverbedExchange, 0.0)
        )
        self.subDischarge = pcr.ifthen(self.landmask, pcr.cover(self.subDischarge, 0.0))

        self.readAvlChannelStorage = pcr.min(
            self.readAvlChannelStorage, self.channelStorage
        )
        self.readAvlChannelStorage = pcr.max(self.readAvlChannelStorage, 0.0)

        # QUAlloc
        if self.using_qualloc:
            self.discharge = pcr.ifthen(self.landmask, pcr.cover(self.discharge, 0.0))
            self.runoff = pcr.ifthen(self.landmask, pcr.cover(self.runoff, 0.0))

            if self.quality:
                self.salinity = pcr.ifthen(self.landmask, pcr.cover(self.salinity, 0.0))
                self.organic = pcr.ifthen(self.landmask, pcr.cover(self.organic, 0.0))
                self.pathogen = pcr.ifthen(self.landmask, pcr.cover(self.pathogen, 0.0))

        # DynQual
        if self.quality:
            self.waterTemp = pcr.ifthen(self.landmask, pcr.cover(self.waterTemp, 0.0))
            self.iceThickness = pcr.ifthen(
                self.landmask, pcr.cover(self.iceThickness, 0.0)
            )
            self.dissolved_oxygen = (1 - 0.0001148 * self.elevation) * exp(
                -139.34411
                + (157570.1) / (self.waterTemp)
                - (66423080.0) / (self.waterTemp**2)
                + (12438000000.0) / (self.waterTemp**3)
                - (862194900000.0) / (self.waterTemp**4)
            )
            self.channelStorageTimeBefore = self.channelStorage
            self.totEW = (
                self.channelStorage
                * self.waterTemp
                * self.specificHeatWater
                * self.densityWater
            )
            self.temp_water_height = yMean = self.eta * pow(self.avgDischarge, self.nu)
            self.routedTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedTDS, 0.0))
            self.routedBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedBOD, 0.0))
            self.routedFC = pcr.ifthen(self.landmask, pcr.cover(self.routedFC, 0.0))

            # per water quality sector
            if self.calculateLoads and self.offlineRun == False:
                self.avg_irrGrossDemand = pcr.ifthen(
                    self.landmask, pcr.cover(self.avg_irrGrossDemand, 0.0)
                )
                self.avg_netLqWaterToSoil = pcr.ifthen(
                    self.landmask, pcr.cover(self.avg_netLqWaterToSoil, 0.0)
                )

                if self.loadsPerSector:
                    self.routedDomTDS = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedDomTDS, 0.0)
                    )
                    self.routedDomBOD = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedDomBOD, 0.0)
                    )
                    self.routedDomFC = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedDomFC, 0.0)
                    )
                    self.routedManTDS = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedManTDS, 0.0)
                    )
                    self.routedManBOD = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedManBOD, 0.0)
                    )
                    self.routedManFC = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedManFC, 0.0)
                    )
                    self.routedUSRTDS = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedUSRTDS, 0.0)
                    )
                    self.routedUSRBOD = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedUSRBOD, 0.0)
                    )
                    self.routedUSRFC = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedUSRFC, 0.0)
                    )
                    self.routedintLivBOD = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedintLivBOD, 0.0)
                    )
                    self.routedintLivFC = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedintLivFC, 0.0)
                    )
                    self.routedextLivBOD = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedextLivBOD, 0.0)
                    )
                    self.routedextLivFC = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedextLivFC, 0.0)
                    )
                    self.routedIrrTDS = pcr.ifthen(
                        self.landmask, pcr.cover(self.routedIrrTDS, 0.0)
                    )

        # make sure timestepsToAvgDischarge is the same for the entire map
        try:
            self.timestepsToAvgDischarge = pcr.mapmaximum(self.timestepsToAvgDischarge)
        except:
            # try/except because pcr.mapmaximum cannot handle scalar values
            pass

        # for netCDF reporting, timestepsToAvgDischarge must be spatial and scalar (e.g. for pcr2numpy)
        self.timestepsToAvgDischarge = pcr.spatial(
            pcr.scalar(self.timestepsToAvgDischarge)
        )
        self.timestepsToAvgDischarge = pcr.ifthen(
            self.landmask, self.timestepsToAvgDischarge
        )

        # initial conditions of water bodies: short-term average inflow (m3/s) and long-term average outflow (m3/s)
        if iniConditions == None:
            # read the initial conditions from the PCRaster maps in the ini file (at the start of the model)
            self.avgInflow = vos.readPCRmapClone(
                iniItems.routingOptions["avgLakeReservoirInflowShortIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            self.avgOutflow = vos.readPCRmapClone(
                iniItems.routingOptions["avgLakeReservoirOutflowLongIni"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            if iniItems.routingOptions["waterBodyStorageIni"] is not None:
                self.waterBodyStorage = vos.readPCRmapClone(
                    iniItems.routingOptions["waterBodyStorageIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                self.waterBodyStorage = pcr.ifthen(
                    self.landmask, pcr.cover(self.waterBodyStorage, 0.0)
                )
            else:
                self.waterBodyStorage = None
        else:
            # read the initial conditions from memory
            self.avgInflow = iniConditions["routing"]["avgLakeReservoirInflowShort"]
            self.avgOutflow = iniConditions["routing"]["avgLakeReservoirOutflowLong"]
            self.waterBodyStorage = iniConditions["routing"]["waterBodyStorage"]

        self.avgInflow = pcr.ifthen(self.landmask, pcr.cover(self.avgInflow, 0.0))
        self.avgOutflow = pcr.ifthen(self.landmask, pcr.cover(self.avgOutflow, 0.0))
        if self.waterBodyStorage is not None:
            self.waterBodyStorage = pcr.ifthen(
                self.landmask, pcr.cover(self.waterBodyStorage, 0.0)
            )

    def estimateBankfullCapacity(self, width, depth, minWidth=5.0, minDepth=1.0):

        # bankfull capacity (m3)
        bankfullCapacity = (
            pcr.max(minWidth, width) * pcr.max(minDepth, depth) * self.channelLength
        )

        return bankfullCapacity

    def getElevationProfile(self, iniItems):

        # profile of relative elevation above the floodplain (per cell); output: dictionaries kSlope,

        # mInterval, relZ and floodVolume with keys iCnt (index):
        # nrZLevels: number of levels; areaFractions (-): fraction of flooded area; relZ (m): relative
        # elevation above the floodplain; floodVolume (m3): flood volume above the bankfull capacity;
        # kSlope (-): slope used in the interpolation; mInterval (m3): smoothing interval of the interpolation

        msg = "Get the profile of relative elevation (relZ, unit: m) !!!"
        logger.info(msg)

        relativeElevationFileNC = (
            # TODO: define the relative elevation files in a netCDF file
            None
        )
        if relativeElevationFileNC != None:
            # TODO: use a netCDF file
            pass

        if relativeElevationFileNC == None:

            relZFileName = vos.getFullPath(
                iniItems.routingOptions["relativeElevationFiles"],
                iniItems.globalOptions["inputDir"],
            )

            # fractions of flooded areas (-)
            areaFractions = list(
                map(
                    float,
                    str(iniItems.routingOptions["relativeElevationLevels"]).split(","),
                )
            )
            print(areaFractions)
            # number of levels
            nrZLevels = len(areaFractions)
            # TODO: read areaFractions and nrZLevels automatically

        # patch the elevations of sills using the floodplain gradient, with local distances deltaX per
        # increment up to z[N] and the sum over sills; fill all lists (including smoothing interval and slopes)

        relZ = [0.0] * nrZLevels
        for iCnt in range(0, nrZLevels):

            if relativeElevationFileNC == None:
                inputName = relZFileName % (areaFractions[iCnt] * 100)
                relZ[iCnt] = vos.readPCRmapClone(
                    inputName, self.cloneMap, self.tmpDir, self.inputDir
                )
            if relativeElevationFileNC != None:
                # TODO: use a netCDF file
                pass

            # cover the elevation values
            relZ[iCnt] = pcr.ifthen(self.landmask, pcr.cover(relZ[iCnt], 0.0))

            # make sure that relZ[iCnt] >= relZ[iCnt-1] (added by Edwin)
            if iCnt > 0:
                relZ[iCnt] = pcr.max(relZ[iCnt], relZ[iCnt - 1])

        # minimum floodplain slope, defined by the longest sill (first used to retrieve the longest
        # cumulative distance)
        deltaX = [self.cellArea**0.5] * nrZLevels
        deltaX[0] = 0.0
        sumX = deltaX[:]
        minSlope = 0.0
        for iCnt in range(nrZLevels):
            if iCnt < nrZLevels - 1:
                deltaX[iCnt] = (
                    areaFractions[iCnt + 1] ** 0.5 - areaFractions[iCnt] ** 0.5
                ) * deltaX[iCnt]
            else:
                deltaX[iCnt] = (1.0 - areaFractions[iCnt - 1] ** 0.5) * deltaX[iCnt]
            if iCnt > 0:
                sumX[iCnt] = pcr.ifthenelse(
                    relZ[iCnt] == relZ[iCnt - 1], sumX[iCnt - 1] + deltaX[iCnt], 0.0
                )
                minSlope = pcr.ifthenelse(
                    relZ[iCnt] == relZ[iCnt - 1],
                    pcr.max(sumX[iCnt], minSlope),
                    minSlope,
                )
        # the floodplain slope is at most the channel gradient (flow is slower on the floodplain)
        minSlope = pcr.min(self.gradient, 0.5 * pcr.max(deltaX[1], minSlope) ** -1.0)

        # add a small increment to the elevation of each sill (except for lakes; TODO: verify this)
        for iCnt in range(nrZLevels):
            relZ[iCnt] = relZ[iCnt] + sumX[iCnt] * pcr.ifthenelse(
                relZ[nrZLevels - 1] > 0.0, minSlope, 0.0
            )
            # make sure that relZ[iCnt] >= relZ[iCnt-1] (added by Edwin)
            if iCnt > 0:
                relZ[iCnt] = pcr.max(relZ[iCnt], relZ[iCnt - 1])

        # slope and smoothing interval between dy = y(i+1)-y(i) and dx = x(i+1)-x(i), based on volume;
        # volume (m3)
        floodVolume = [0.0] * (nrZLevels)
        # smoothing interval (m3)
        mInterval = [0.0] * (nrZLevels)
        # slope (-)
        kSlope = [0.0] * (nrZLevels)
        for iCnt in range(1, nrZLevels):
            floodVolume[iCnt] = (
                floodVolume[iCnt - 1]
                + 0.5
                * (areaFractions[iCnt] + areaFractions[iCnt - 1])
                * (relZ[iCnt] - relZ[iCnt - 1])
                * self.cellArea
            )
            kSlope[iCnt - 1] = (
                areaFractions[iCnt] - areaFractions[iCnt - 1]
            ) / pcr.max(0.001, floodVolume[iCnt] - floodVolume[iCnt - 1])
        for iCnt in range(1, nrZLevels):
            if iCnt < (nrZLevels - 1):
                mInterval[iCnt] = (
                    0.5
                    * self.reductionKK
                    * pcr.min(
                        floodVolume[iCnt + 1] - floodVolume[iCnt],
                        floodVolume[iCnt] - floodVolume[iCnt - 1],
                    )
                )
            else:
                mInterval[iCnt] = (
                    0.5 * self.reductionKK * (floodVolume[iCnt] - floodVolume[iCnt - 1])
                )

        return nrZLevels, areaFractions, relZ, floodVolume, kSlope, mInterval

    def getRoutingParamAvgDischarge(self, avgDischarge, dist2celllength):
        # routing parameters from the long-term average discharge (m3/s); output: channel dimensions and
        # characteristicDistance (input of accuTravelTime)

        yMean = self.eta * pow(avgDischarge, self.nu)
        wMean = self.tau * pow(avgDischarge, self.phi)

        # option to use a predefined channel width (m)
        if self.predefinedChannelWidth is not None:
            wMean = pcr.cover(self.predefinedChannelWidth, wMean)
        wMean = pcr.max(self.minChannelWidth, wMean)

        # average flow width (m); may be used as channel width estimate (assuming rectangular channels)
        wMean = pcr.max(wMean, 0.01)
        wMean = pcr.cover(wMean, 0.01)
        # average flow depth (m); should not be used as channel depth estimate
        yMean = pcr.max(yMean, 0.01)
        yMean = pcr.cover(yMean, 0.01)

        # characteristicDistance (-), used for accutraveltimeflux (discharge: the total material flowing
        # through the cell, m3/s) and accutraveltimestate (storage: the material deposited in the cell, m3);
        # (m/day)
        characteristicDistance = (
            ((yMean * wMean) / (wMean + 2 * yMean)) ** (2.0 / 3.0)
            * ((self.gradient) ** (0.5))
            / self.manningsN
            * vos.secondsPerDay()
        )

        # (arcDeg/day)
        characteristicDistance = pcr.max(
            (self.cellSizeInArcDeg) * 0.000000001,
            characteristicDistance / dist2celllength,
        )

        # characteristicDistance of each lake/reservoir
        lakeReservoirCharacteristicDistance = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.areaaverage(characteristicDistance, self.WaterBodies.waterBodyIds),
        )

        # make sure all outflow is released outside lakes and reservoirs
        outlets = pcr.cover(
            pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyOut) > 0, pcr.boolean(1)),
            pcr.boolean(0),
        )
        distance_to_outlets = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.ldddist(self.lddMap, outlets, pcr.scalar(1.0)),
        )
        lakeReservoirCharacteristicDistance = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.max(
                distance_to_outlets + pcr.downstreamdist(self.lddMap) * 1.50,
                lakeReservoirCharacteristicDistance,
            ),
        )
        characteristicDistance = pcr.cover(
            lakeReservoirCharacteristicDistance, characteristicDistance
        )
        # (arcDeg/day)
        characteristicDistance = pcr.roundup(characteristicDistance * 100.0) / 100.0

        # minimum characteristicDistance
        characteristicDistance = pcr.cover(
            characteristicDistance, 0.1 * self.cellSizeInArcDeg
        )
        characteristicDistance = pcr.max(
            0.100 * self.cellSizeInArcDeg, characteristicDistance
        )

        return (yMean, wMean, characteristicDistance)

    def getCharacteristicDistance(self, yMean, wMean):

        # Manning's coefficient
        usedManningsN = self.manningsN

        # corrected Manning's coefficient
        if self.floodPlain:

            # wetted perimeter
            flood_only_wetted_perimeter = self.floodDepth * (2.0) + pcr.max(
                0.0,
                self.innundatedFraction * self.cellArea / self.channelLength
                - self.channelWidth,
            )
            channel_only_wetted_perimeter = (
                pcr.min(
                    self.channelDepth,
                    vos.getValDivZero(
                        self.channelStorage, self.channelLength * self.channelWidth, 0.0
                    ),
                )
                * 2.0
                + self.channelWidth
            )
            # total channel wetted perimeter (m)
            channel_wetted_perimeter = (
                channel_only_wetted_perimeter + flood_only_wetted_perimeter
            )
            # minimum channel wetted perimeter: 10 cm
            channel_wetted_perimeter = pcr.max(0.1, channel_wetted_perimeter)

            usedManningsN = (
                (channel_only_wetted_perimeter / channel_wetted_perimeter)
                * self.manningsN ** (1.5)
                + (flood_only_wetted_perimeter / channel_wetted_perimeter)
                * self.floodplainManN ** (1.5)
            ) ** (2.0 / 3.0)

        # characteristicDistance (-), used for accutraveltimeflux (discharge: the total material flowing
        # through the cell, m3/s) and accutraveltimestate (storage: the material deposited in the cell, m3);
        # (m/day)
        characteristicDistance = (
            ((yMean * wMean) / (wMean + 2 * yMean)) ** (2.0 / 3.0)
            * ((self.gradient) ** (0.5))
            / usedManningsN
            * vos.secondsPerDay()
        )

        # (arcDeg/day)
        characteristicDistance = pcr.max(
            (self.cellSizeInArcDeg) * 0.000000001,
            characteristicDistance / self.dist2celllength,
        )

        # characteristicDistance of each lake/reservoir
        lakeReservoirCharacteristicDistance = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.areaaverage(characteristicDistance, self.WaterBodies.waterBodyIds),
        )
        # make sure all outflow is released outside lakes and reservoirs
        outlets = pcr.cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyOut) > 0,
                pcr.spatial(pcr.boolean(1)),
            ),
            pcr.spatial(pcr.boolean(0)),
        )
        distance_to_outlets = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.ldddist(self.lddMap, outlets, pcr.scalar(1.0)),
        )

        lakeReservoirCharacteristicDistance = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.max(
                distance_to_outlets + pcr.downstreamdist(self.lddMap) * 2.50,
                lakeReservoirCharacteristicDistance,
            ),
        )
        lakeReservoirCharacteristicDistance = pcr.areamaximum(
            lakeReservoirCharacteristicDistance, self.WaterBodies.waterBodyIds
        )
        # TODO: calculate lakeReservoirCharacteristicDistance while obtaining the lake and reservoir parameters

        characteristicDistance = pcr.cover(
            lakeReservoirCharacteristicDistance, characteristicDistance
        )

        # note: in accutraveltime, a characteristicDistance (velocity) of 0 gives zero accutraveltimestate
        # and a very high accutraveltimeflux

        # TODO: consider using the downstreamdist function

        # current solution: roundup to ignore zero and very small values (arcDeg/day)
        characteristicDistance = pcr.roundup(characteristicDistance * 100.0) / 100.0

        # minimum characteristicDistance
        characteristicDistance = pcr.cover(
            characteristicDistance, 0.1 * self.cellSizeInArcDeg
        )
        # TODO: check the minimum distance for the accutraveltime function
        characteristicDistance = pcr.max(
            0.100 * self.cellSizeInArcDeg, characteristicDistance
        )

        return characteristicDistance

    def accuTravelTime(self):

        # accuTravelTime routing

        # only route non-negative channelStorage (otherwise it stays)
        channelStorageThatWillNotMove = pcr.ifthenelse(
            self.channelStorage < 0.0, self.channelStorage, 0.0
        )
        self.channelStorage = pcr.max(0.0, self.channelStorage)

        # at least 1 m3 of water stays, to minimize numerical errors of the float32 PCRaster implementation
        channelStorageThatWillNotMove += self.channelStorage - pcr.rounddown(
            self.channelStorage
        )
        self.channelStorage = pcr.rounddown(self.channelStorage)

        # channelStorage passed to the routing
        channelStorageForAccuTravelTime = pcr.max(0.0, self.channelStorage)
        # TODO: check why the cover operation is needed
        channelStorageForAccuTravelTime = pcr.cover(
            channelStorageForAccuTravelTime, 0.0
        )

        characteristicDistance = self.getCharacteristicDistance(self.yMean, self.wMean)

        # channel discharge (m3/day)
        self.Q = pcr.accutraveltimeflux(
            self.lddMap,
            channelStorageForAccuTravelTime,
            pcr.max(0.0, characteristicDistance),
        )
        self.Q = pcr.cover(self.Q, 0.0)
        # for very small velocities (characteristicDistanceForAccuTravelTime), discharge can be missing, see
        # http://sourceforge.net/p/pcraster/bugs-and-feature-requests/543/ and
        # http://karssenberg.geo.uu.nl/tt/TravelTimeSpecification.htm; also avoid negative discharge (m3/day)
        self.Q = pcr.max(0.0, self.Q)

        # update channelStorage after routing (m3)
        self.channelStorage = pcr.accutraveltimestate(
            self.lddMap,
            channelStorageForAccuTravelTime,
            pcr.max(0.0, characteristicDistance),
        )

        # return channelStorageThatWillNotMove to channelStorage (m3)
        self.channelStorage += channelStorageThatWillNotMove

        # for non-kinematic wave approaches, subDischarge is Q in m3/s
        self.subDischarge = self.Q / vos.secondsPerDay()
        self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)

    def estimate_length_of_sub_time_step(self):

        # sub-time step length (s), the shorter the better, estimated from the initial or latest
        # sub-time step discharge (m3/s)
        length_of_sub_time_step = pcr.ifthenelse(
            self.subDischarge > 0.0,
            self.water_height * self.dynamicFracWat * self.cellArea / self.subDischarge,
            vos.secondsPerDay(),
        )

        # number of sub-time steps (Rens van Beek's method)
        critical_condition = (
            (length_of_sub_time_step < vos.secondsPerDay())
            & (self.water_height > self.critical_water_height)
            & (self.lddMap != pcr.ldd(5))
        )
        number_of_sub_time_steps = vos.secondsPerDay() / pcr.cover(
            pcr.areaminimum(
                pcr.ifthen(critical_condition, length_of_sub_time_step), self.landmask
            ),
            vos.secondsPerDay() / self.limit_num_of_sub_time_steps,
        )
        number_of_sub_time_steps = 1.25 * number_of_sub_time_steps + 1
        number_of_sub_time_steps = pcr.roundup(number_of_sub_time_steps)
        # at least one sub-time step
        number_of_loops = max(
            1.0, pcr.cellvalue(pcr.mapmaximum(number_of_sub_time_steps), 1)[1]
        )
        number_of_loops = int(max(self.limit_num_of_sub_time_steps, number_of_loops))

        # actual sub-time step length (s)
        length_of_sub_time_step = vos.secondsPerDay() / number_of_loops

        return (length_of_sub_time_step, number_of_loops)

    def simplifiedKinematicWave(self, meteo, landSurface, groundwater):
        """
        The 'simplifiedKinematicWave':
        1. First, assume that all local fluxes has been added to 'channelStorage'. This is done outside of this function/method.
        2. Then, the 'channelStorage' is routed by using 'pcr.kinematic function' with 'lateral_inflow' = 0.0.
        """

        logger.info("Using the simplifiedKinematicWave method!")

        # only route non-negative channelStorage (otherwise it stays)
        channelStorageThatWillNotMove = pcr.ifthenelse(
            self.channelStorage < 0.0, self.channelStorage, 0.0
        )

        # channelStorage passed to the routing (m3)
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)

        # water height (m), needed to estimate the sub-time step length and the channel wetted area (for
        # alpha and dischargeInitial)
        self.water_height = pcr.min(
            self.max_water_height,
            channelStorageForRouting
            / (
                pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat)
                * self.cellArea
            ),
        )

        # sub-time step length (s)
        length_of_sub_time_step, number_of_loops = (
            self.estimate_length_of_sub_time_step()
        )

        for i_loop in range(number_of_loops):

            # alpha parameter and initial discharge for the kinematic wave
            if self.floodPlain:
                self.dynamicFracWat, self.water_height, alpha, dischargeInitial = (
                    self.kinAlpha(channelStorageForRouting)
                )
                self.dynamicFracWat = pcr.min(
                    pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0
                )
            else:
                # alpha parameter and initial discharge for the kinematic wave
                alpha, dischargeInitial = (
                    self.calculate_alpha_and_initial_discharge_for_kinematic_wave(
                        channelStorageForRouting,
                        self.water_height,
                        self.innundatedFraction,
                        self.floodDepth,
                    )
                )

            # at the lake/reservoir outlets, use the water body outflow
            waterBodyOutflowInM3PerSec = (
                pcr.cover(
                    pcr.ifthen(
                        self.WaterBodies.waterBodyOut, self.WaterBodies.waterBodyOutflow
                    ),
                    0.0,
                )
                / vos.secondsPerDay()
            )
            waterBodyOutflowInM3PerSec = pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                waterBodyOutflowInM3PerSec,
            )
            dischargeInitial = pcr.cover(waterBodyOutflowInM3PerSec, dischargeInitial)

            # discharge (m3/s) from the kinematic wave approximation
            self.subDischarge = pcr.kinematic(
                self.lddMap,
                dischargeInitial,
                0.0,
                alpha,
                self.beta,
                1,
                length_of_sub_time_step,
                self.channelLength,
            )
            self.subDischarge = pcr.cover(self.subDischarge, 0.0)
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))

            # avoid negative channel storage
            self.subDischarge = (
                pcr.min(
                    self.subDischarge * length_of_sub_time_step,
                    pcr.max(
                        0.0,
                        channelStorageForRouting
                        + pcr.upstream(
                            self.lddMap, self.subDischarge * length_of_sub_time_step
                        ),
                    ),
                )
                / length_of_sub_time_step
            )

            # update channelStorage (m3)
            storage_change_in_volume = (
                pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)
                - self.subDischarge * length_of_sub_time_step
            )
            channelStorageForRouting += storage_change_in_volume
            # only route non-negative channelStorage (otherwise it stays)
            channelStorageThatWillNotMove += pcr.ifthenelse(
                channelStorageForRouting < 0.0, channelStorageForRouting, 0.0
            )
            channelStorageForRouting = pcr.max(0.000, channelStorageForRouting)

            # update the flood fraction and flood depth (without floodplain)
            if not self.floodPlain:
                self.inundatedFraction, self.floodDepth = (
                    self.returnInundationFractionAndFloodDepth(channelStorageForRouting)
                )

                # dynamicFracWat: fraction of surface water bodies (-), including lakes and reservoirs; lake and
                # reservoir surface water fraction
                self.dynamicFracWat = pcr.cover(
                    pcr.min(1.0, self.WaterBodies.fracWat), 0.0
                )
                # fraction of channel (including its excess above bankfull capacity)
                self.dynamicFracWat += pcr.max(
                    0.0, 1.0 - self.dynamicFracWat
                ) * pcr.max(self.channelFraction, self.innundatedFraction)

                # dynamicFracWat is at most 1
                self.dynamicFracWat = pcr.ifthen(
                    self.landmask,
                    pcr.min(
                        pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0
                    ),
                )
                self.dynamicFracWat = pcr.ifthen(
                    self.landmask, pcr.min(1.0, self.dynamicFracWat)
                )
                self.dynamicFracWat = pcr.ifthen(
                    self.landmask, pcr.max(1e-6, self.dynamicFracWat)
                )

                # water height for the next loop, needed to estimate the channel wetted area (for alpha and dischargeInitial)
                self.water_height = channelStorageForRouting / (
                    pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat)
                    * self.cellArea
                )

            # total discharge volume (m3) until this loop
            if i_loop == 0:
                discharge_volume = pcr.scalar(0.0)
            discharge_volume += self.subDischarge * length_of_sub_time_step

            # quality routing
            if self.quality:
                self.channelStorageNow = pcr.max(0.0, channelStorageForRouting)
                self.qualityRouting(length_of_sub_time_step)
                self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorageNow)

        # channel discharge (m3/day)
        self.Q = discharge_volume

        # update channelStorage after routing
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage
        self.channelStorage += channelStorageThatWillNotMove

        # channel storage cannot be negative
        self.channelStorage = pcr.max(0.0, self.channelStorage)

    def update(self, landSurface, groundwater, currTimeStep, meteo):

        logger.info("routing in progress")

        # water bodies: get the parameters at the start of each year or simulation; this must be called first
        # to define the initial conditions at the start of the simulation
        if currTimeStep.timeStepPCR == 1:
            initial_conditions_for_water_bodies = self.getState()
            # the last argument is for the initial conditions of lakes/reservoirs
            self.WaterBodies.getParameterFiles(
                currTimeStep,
                self.cellArea,
                self.lddMap,
                initial_conditions_for_water_bodies,
            )

        if (currTimeStep.doy == 1) and (currTimeStep.timeStepPCR > 1):
            self.WaterBodies.getParameterFiles(currTimeStep, self.cellArea, self.lddMap)
        if self.includeWaterBodies == False:
            # ignore all lakes and reservoirs
            self.WaterBodies.waterBodyIds = pcr.ifthen(self.landmask, pcr.nominal(-1))

        # downstream demand (m3/s) for reservoirs, estimated from the environmental flow discharge; must be
        # called before updating timestepsToAvgDischarge
        self.downstreamDemand = self.estimate_discharge_for_environmental_flow(
            self.channelStorage
        )

        # routing/channel parameters (based on avgDischarge) and water body fraction, needed for the
        # evaporation from water bodies
        self.yMean, self.wMean, self.characteristicDistance = (
            self.getRoutingParamAvgDischarge(self.avgDischarge, self.dist2celllength)
        )

        # channel width (m), depth (m) and fraction
        self.channelWidth = self.wMean
        self.channelDepth = pcr.max(0.0, self.yMean)
        self.channelFraction = pcr.max(
            0.0, pcr.min(1.0, self.channelWidth * self.channelLength / (self.cellArea))
        )

        # water height for the first time step
        if currTimeStep.timeStepPCR == 1:
            if self.floodPlain:
                self.dynamicFracWat, self.water_height = self.returnFloodedFraction(
                    self.channelStorage
                )
                self.dynamicFracWat = pcr.min(
                    pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0
                )
            else:
                self.dynamicFracWat = pcr.max(
                    self.channelFraction, self.WaterBodies.fracWat
                )
            self.dynamicFracWat = pcr.ifthen(self.landmask, self.dynamicFracWat)

        # channel bankfull capacity (m3)
        if self.floodPlain:
            if self.usingFixedBankfullCapacity:
                self.channelStorageCapacity = self.predefinedBankfullCapacity
            else:
                self.channelStorageCapacity = self.estimateBankfullCapacity(
                    self.channelWidth, self.channelDepth
                )

        # flood inundation fraction (-) and depth (m)
        self.innundatedFraction, self.floodDepth = (
            self.returnInundationFractionAndFloodDepth(self.channelStorage)
        )
        # dynamicFracWat: fraction of surface water bodies (-), including lakes and reservoirs; lake and
        # reservoir surface water fraction
        self.dynamicFracWat = pcr.cover(pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
        # fraction of channel (including its excess above bankfull capacity)
        self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(
            self.channelFraction, self.innundatedFraction
        )
        # dynamicFracWat is at most 1
        self.dynamicFracWat = pcr.ifthen(
            self.landmask,
            pcr.min(pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0),
        )
        self.dynamicFracWat = pcr.ifthen(
            self.landmask, pcr.min(1.0, self.dynamicFracWat)
        )
        self.dynamicFracWat = pcr.ifthen(
            self.landmask, pcr.max(1e-6, self.dynamicFracWat)
        )

        # routing methods
        if self.method == "accuTravelTime" or self.method == "simplifiedKinematicWave":
            self.simple_update(landSurface, groundwater, currTimeStep, meteo)
        if self.method == "kinematicWave":
            self.kinematic_wave_update(landSurface, groundwater, currTimeStep, meteo)
        # note: this method requires abstraction from fossil groundwater

        # infiltration from surface water bodies (channels, lakes and reservoirs) to groundwater, passed on in
        # the next time step
        self.calculate_exchange_to_groundwater(groundwater, currTimeStep)

        # volume released in pits (losses to the ocean/endorheic basins)
        self.outgoing_volume_at_pits = pcr.ifthen(
            self.landmask, pcr.cover(pcr.ifthen(self.lddMap == pcr.ldd(5), self.Q), 0.0)
        )

        # volume that can be abstracted in the next time step
        self.readAvlChannelStorage = pcr.max(
            0.0, self.estimate_available_volume_for_abstraction(self.channelStorage)
        )

        # water body balance check
        self.waterBodyBalance = self.WaterBodies.waterBodyBalance

        # total runoff from local land surface runoff and local changes in water bodies (m)
        self.totalRunoff = self.local_input_to_surface_water / self.cellArea

        # statistics of long- and short-term flow values
        self.calculate_statistics(groundwater, landSurface)

        # old-style reporting; TODO: remove
        self.old_style_routing_reporting(currTimeStep)

    def calculate_potential_evaporation(
        self, landSurface, currTimeStep, meteo, definedDynamicFracWat=None
    ):

        if self.no_zero_crop_water_coefficient == False:
            self.waterKC = 0.0

        # potential evaporation from water bodies; if landSurface.actualET < waterKC *
        # meteo.referencePotET * fracWat, more evaporation is added
        if (
            (currTimeStep.day == 1) or (currTimeStep.timeStepPCR == 1)
        ) and self.no_zero_crop_water_coefficient:
            waterKC = vos.netcdf2PCRobjClone(
                self.fileCropKC,
                "kc",
                currTimeStep.fulldate,
                useDoy="month",
                cloneMapFileName=self.cloneMap,
            )
            self.waterKC = pcr.ifthen(self.landmask, pcr.cover(waterKC, 0.0))
            self.waterKC = pcr.max(self.minCropWaterKC, self.waterKC)

        # potential evaporation from water bodies (m/day), reduced by the evaporation calculated in the
        # landSurface module; not over the entire cell area
        waterBodyPotEvapOvesSurfaceWaterArea = pcr.ifthen(
            self.landmask,
            pcr.max(0.0, self.waterKC * meteo.referencePotET - landSurface.actualET),
        )

        # potential evaporation from water bodies over the entire cell area (m/day)
        if definedDynamicFracWat == None:
            dynamicFracWat = self.dynamicFracWat
        waterBodyPotEvap = pcr.max(
            0.0, waterBodyPotEvapOvesSurfaceWaterArea * dynamicFracWat
        )
        return waterBodyPotEvap

    def calculate_evaporation(self, landSurface, groundwater, currTimeStep, meteo):

        # potential evaporation from water bodies over the entire cell area, not only the water bodies (m/day)
        self.waterBodyPotEvap = self.calculate_potential_evaporation(
            landSurface, currTimeStep, meteo
        )

        # evaporation volume from water bodies (m3), not limited to the available channelStorage
        volLocEvapWaterBody = self.waterBodyPotEvap * self.cellArea
        # limited to the available channelStorage
        volLocEvapWaterBody = pcr.min(
            pcr.max(0.0, self.channelStorage), volLocEvapWaterBody
        )

        # update channelStorage (m3) after evaporation from water bodies
        self.channelStorage = self.channelStorage - volLocEvapWaterBody
        self.local_input_to_surface_water -= volLocEvapWaterBody

        # evaporation from water bodies (m)
        self.waterBodyEvaporation = volLocEvapWaterBody / self.cellArea
        self.waterBodyEvaporation = pcr.ifthen(self.landmask, self.waterBodyEvaporation)

        # remaining potential evaporation from water bodies (m)
        self.remainWaterBodyPotEvap = pcr.max(
            0.0, self.waterBodyPotEvap - self.waterBodyEvaporation
        )

    def calculate_exchange_to_groundwater(self, groundwater, currTimeStep):

        if self.debugWaterBalance:
            # (m3)
            preStorage = self.channelStorage

        # riverbed infiltration (m3/day), following Inge's principle: only if 0 < baseflow < total groundwater abstraction
        # (fossil and non-fossil); the rate is based on the aquifer saturated conductivity, limited to fracWat
        # and the available channelStorage, and passed to groundwater in the next time step (de Graaf et al.,
        # 2014; Wada et al., 2012; Wada et al., 2010); TODO: improve this concept
        # (m/day)
        riverbedConductivity = groundwater.riverBedConductivity
        # maximum conductivity of 0.1 m/day (Marc Bierkens: resistance of 1 day for a 0.1 m river bed)
        riverbedConductivity = pcr.min(0.1, riverbedConductivity)
        # (m)
        total_groundwater_abstraction = pcr.max(
            0.0,
            groundwater.nonFossilGroundwaterAbs + groundwater.fossilGroundwaterAbstr,
        )
        self.riverbedExchange = pcr.max(
            0.0,
            pcr.min(
                pcr.max(0.0, self.channelStorage),
                pcr.ifthenelse(
                    groundwater.baseflow > 0.0,
                    pcr.ifthenelse(
                        total_groundwater_abstraction > groundwater.baseflow,
                        riverbedConductivity * self.dynamicFracWat * self.cellArea,
                        0.0,
                    ),
                    0.0,
                ),
            ),
        )
        self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)
        # avoid flip-flopping
        factor = 0.25
        self.riverbedExchange = pcr.min(
            self.riverbedExchange,
            (1.0 - factor) * pcr.max(0.0, self.channelStorage),
        )
        self.riverbedExchange = pcr.ifthenelse(
            self.channelStorage < 0.0, 0.0, self.riverbedExchange
        )
        self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)
        self.riverbedExchange = pcr.ifthen(self.landmask, self.riverbedExchange)

        # update channelStorage (m3) after riverbedExchange (m3)
        self.channelStorage -= self.riverbedExchange
        self.local_input_to_surface_water -= self.riverbedExchange

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [pcr.scalar(0.0)],
                [self.riverbedExchange / self.cellArea],
                [preStorage / self.cellArea],
                [self.channelStorage / self.cellArea],
                "channelStorage after surface water infiltration",
                True,
                currTimeStep.fulldate,
                threshold=1e-4,
            )

    def return_flows_to_wastewater_treatment_plants(self, currTimeStep, landSurface):

        # wastewater treatment plants: ids
        if currTimeStep.doy == 1:
            # wastewater treatment plant (point) locations
            self.WWt_plantID = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "plant_id",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.WWt_plantID = pcr.nominal(self.WWt_plantID)

            # wastewater treatment plant service zones
            self.WWt_zoneID = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "zone_id",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.WWt_zoneID = pcr.nominal(self.WWt_zoneID)

        # return flow: the sum of the domestic and manufacturing return flows only
        self.nonIrrReturnFlow = (
            landSurface.nonIrrReturnFlowVolumePerSector["domestic"]
            + landSurface.nonIrrReturnFlowVolumePerSector["manufacture"]
        )

        # redirect the return flow to the wastewater treatment plant locations, with removal at the plant (m3/day)
        self.nonIrrReturnFlow = pcr.ifthenelse(
            # cells not in a wastewater treatment zone
            self.WWt_zoneID == 0,
            self.nonIrrReturnFlow,
            pcr.ifthenelse(
                self.WWt_zoneID
                # accumulate water over the treatment zone to the plant location
                == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, self.nonIrrReturnFlow, 0),
                    self.WWt_zoneID,
                ),
                # after accumulation, set locations without a treatment plant to 0
                0.0,
            ),
        )

        # return flow of the non-irrigation water demand, calculated in landSurface.py (m3)
        self.nonIrrReturnFlow = (
            self.nonIrrReturnFlow
            + landSurface.nonIrrReturnFlowVolumePerSector["livestock"]
            + landSurface.nonIrrReturnFlowVolumePerSector["thermoelectric"]
            + landSurface.nonIrrReturnFlowVolumePerSector["industry"]
        )

    def simple_update(self, landSurface, groundwater, currTimeStep, meteo):

        # update the time steps for the long- and short-term statistics (avgDischarge, avgInflow, avgOutflow, etc.)
        self.timestepsToAvgDischarge += 1.0

        if self.debugWaterBalance:
            # (m3)
            preStorage = self.channelStorage

        # total local change (input) to surface water storage (m3); only local processes, no routing;
        # initialized at zero
        self.local_input_to_surface_water = pcr.scalar(0.0)

        # runoff from land surface cells (m/day)
        self.runoff = landSurface.landSurfaceRunoff + groundwater.baseflow

        # update channelStorage (m3) after runoff
        self.channelStorage += self.runoff * self.cellArea
        self.local_input_to_surface_water += self.runoff * self.cellArea

        # upstream discharge (m3/s)
        total_upstream_discharge = pcr.spatial(pcr.scalar(0.0))
        if self.upstream_discharge_input_files is not None:
            for i_ups_file in range(0, len(self.upstream_discharge_input_files)):
                upstream_discharge_input_file = self.upstream_discharge_input_files[
                    i_ups_file
                ]
                self.upstream_discharge = vos.readUpstreamDischarge(
                    upstream_discharge_input_file,
                    "automatic",
                    str(currTimeStep.fulldate),
                    cloneMapFileName=self.cloneMap,
                    useDoy=None,
                )
                total_upstream_discharge = total_upstream_discharge + pcr.cover(
                    self.upstream_discharge, 0.0
                )
            # add the upstream discharge to the current basin
            total_upstream_discharge = pcr.upstream(
                self.ldd_complete, total_upstream_discharge
            )
        # only values within the landmask
        self.total_upstream_discharge = pcr.ifthen(
            self.landmask, total_upstream_discharge
        )
        # add the upstream discharge to channelStorage (m3)
        self.channelStorage = (
            pcr.cover(self.total_upstream_discharge, 0.0) * 3600.0 * 24.0
            + self.channelStorage
        )

        # update channelStorage (m3) after actSurfaceWaterAbstraction
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea
        self.local_input_to_surface_water -= (
            landSurface.actSurfaceWaterAbstract * self.cellArea
        )

        # channelStorage after surface water abstraction, for reporting (m3)
        self.channelStorageAfterAbstraction = pcr.ifthen(
            self.landmask, self.channelStorage
        )

        # redirect the return flow to the wastewater treatment plant locations (m3)
        if self.WWtPlants:
            self.return_flows_to_wastewater_treatment_plants(currTimeStep, landSurface)
        else:
            self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowVolume

        # add the return flows to channelStorage (m3)
        self.channelStorage += self.nonIrrReturnFlow
        self.local_input_to_surface_water += self.nonIrrReturnFlow

        # evaporation from water bodies (sets self.waterBodyEvaporation, in m)
        self.calculate_evaporation(landSurface, groundwater, currTimeStep, meteo)

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.runoff, self.nonIrrReturnFlow / self.cellArea],
                [landSurface.actSurfaceWaterAbstract, self.waterBodyEvaporation],
                [preStorage / self.cellArea],
                [self.channelStorage / self.cellArea],
                "channelStorage (unit: m) before lake/reservoir outflow",
                True,
                currTimeStep.fulldate,
                threshold=5e-3,
            )

        # lake and reservoir operations
        if self.debugWaterBalance:
            # (m3)
            preStorage = self.channelStorage

        # move channelStorage to waterBodyStorage at lake and reservoir cells
        storageAtLakeAndReservoirs = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, self.channelStorage
        )
        storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs, 0.0)

        # only non-negative, rounded-down values
        storageAtLakeAndReservoirs = pcr.max(
            0.00, pcr.rounddown(storageAtLakeAndReservoirs)
        )
        # (m3)
        self.channelStorage -= storageAtLakeAndReservoirs

        # update waterBodyStorage (inflow, storage and outflow)
        self.WaterBodies.update(
            storageAtLakeAndReservoirs,
            self.timestepsToAvgDischarge,
            self.maxTimestepsToAvgDischargeShort,
            self.maxTimestepsToAvgDischargeLong,
            currTimeStep,
            self.avgDischarge,
            vos.secondsPerDay(),
            self.downstreamDemand,
        )

        # waterBodyStorage (m3) after outflow, per water body id (not per cell)
        self.waterBodyStorage = pcr.ifthen(
            self.landmask, self.WaterBodies.waterBodyStorage
        )

        if self.quality:
            self.waterBodyStorageTimeBefore = (
                self.waterBodyStorage + self.WaterBodies.waterBodyOutflow
            )

        # transfer the outflow from lakes and reservoirs to channelStorage (m3/day)
        waterBodyOutflow = pcr.cover(
            pcr.ifthen(
                self.WaterBodies.waterBodyOut, self.WaterBodies.waterBodyOutflow
            ),
            0.0,
        )

        if self.method == "accuTravelTime":
            # distribute the outflow over the lake/reservoir cells, to avoid waterBodyOutflow skipping cells
            waterBodyOutflow = pcr.areaaverage(
                waterBodyOutflow, self.WaterBodies.waterBodyIds
            )
            waterBodyOutflow = pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, waterBodyOutflow
            )
        # (m3/day)
        self.waterBodyOutflow = pcr.cover(waterBodyOutflow, 0.0)

        # update channelStorage (m3) after waterBodyOutflow (m3)
        self.channelStorage += self.waterBodyOutflow
        # note: local_input_to_surface_water does not include waterBodyOutflow

        if self.debugWaterBalance:
            vos.waterBalanceCheck(
                [self.waterBodyOutflow / self.cellArea],
                [storageAtLakeAndReservoirs / self.cellArea],
                [preStorage / self.cellArea],
                [self.channelStorage / self.cellArea],
                "channelStorage (unit: m) after lake reservoir/outflow fluxes (errors here are most likely due to pcraster implementation in float_32)",
                True,
                currTimeStep.fulldate,
                threshold=1e-3,
            )

        if self.quality:
            # daily input data, unless adjusted in the function
            self.readExtensiveMeteo(currTimeStep)

            # pollutant loadings
            if self.calculateLoads:
                # daily input data for estimating the pollutant loadings, unless adjusted in the function
                self.readPollutantLoadingsInputData(currTimeStep)
                # pollutant loadings calculated (or read) daily, unless adjusted in the function
                self.calculatePollutantLoadings(currTimeStep, landSurface, groundwater)
            else:
                self.readPollutantLoadings(currTimeStep)

            # heat dumps from water temperature dependent power plants (J/day)
            self.PowTwload = pcr.cover(
                landSurface.nonIrrReturnFlowVolumePerSector["thermoelectric"]
                * self.specificHeatWater
                * self.densityWater
                * landSurface.water_demand.water_demand_thermoelectric.min_Tlmax_dTlmax,
                0.0,
            )

            self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorage)
            self.qualityLocal(meteo, landSurface, groundwater, currTimeStep)
            self.qualityWaterBody()

        # routing: returns the new channelStorage (still without waterBodyStorage) and self.Q, the channel
        # discharge (m3/day)
        if self.method == "accuTravelTime":
            self.accuTravelTime()
        if self.method == "simplifiedKinematicWave":
            self.simplifiedKinematicWave(meteo, landSurface, groundwater)
        # channel discharge of the current time step (m3/s)
        self.discharge = self.Q / vos.secondsPerDay()
        # reported channel discharge cannot be negative
        self.discharge = pcr.max(0.0, self.discharge)
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        self.disChanWaterBody = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.areamaximum(self.discharge, self.WaterBodies.waterBodyIds),
        )
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        # reported channel discharge cannot be negative
        self.disChanWaterBody = pcr.max(0.0, self.disChanWaterBody)

        if self.quality:
            self.qualityWaterBodyAverage(currTimeStep)

        # return waterBodyStorage to channelStorage
        self.channelStorage = self.return_water_body_storage_to_channel(
            self.channelStorage
        )

        # reported channel storage cannot be negative
        self.channelStorage = pcr.max(0.0, self.channelStorage)

        if self.quality:
            self.estimate_concentrations()

    def calculate_alpha_and_initial_discharge_for_kinematic_wave(
        self, channelStorage, water_height, innundatedFraction, floodDepth
    ):
        # alpha (-), the roughness coefficient of the kinematic wave (see
        # http://pcraster.geo.uu.nl/pcraster/4.0.0/doc/manual/op_kinematic.html), from the wetted area (m2),
        # wetted perimeter (m) and beta (-), assuming a rectangular channel

        # channel wetted area (m2): at least water height x channel width (Edwin), mainly based on
        # channelStorage and channelLength (Rens's approach)
        channel_wetted_area = water_height * self.channelWidth
        channel_wetted_area = pcr.max(
            channel_wetted_area, channelStorage / self.channelLength
        )

        # wetted perimeter
        flood_only_wetted_perimeter = floodDepth * (2.0) + pcr.max(
            0.0,
            innundatedFraction * self.cellArea / self.channelLength - self.channelWidth,
        )
        channel_only_wetted_perimeter = (
            pcr.min(
                self.channelDepth,
                vos.getValDivZero(
                    channelStorage, self.channelLength * self.channelWidth, 0.0
                ),
            )
            * 2.0
            + self.channelWidth
        )
        # total channel wetted perimeter (m)
        channel_wetted_perimeter = (
            channel_only_wetted_perimeter + flood_only_wetted_perimeter
        )
        # minimum channel wetted perimeter: 10 cm
        channel_wetted_perimeter = pcr.max(0.1, channel_wetted_perimeter)

        # corrected Manning's coefficient
        if self.floodPlain:
            usedManningsN = (
                (channel_only_wetted_perimeter / channel_wetted_perimeter)
                * self.manningsN ** (1.5)
                + (flood_only_wetted_perimeter / channel_wetted_perimeter)
                * self.floodplainManN ** (1.5)
            ) ** (2.0 / 3.0)
        else:
            usedManningsN = self.manningsN

        # alpha (-) and initial estimate of the channel discharge (m3/s)
        alpha = (
            usedManningsN
            * channel_wetted_perimeter ** (2.0 / 3.0)
            * self.gradient ** (-0.5)
        ) ** self.beta
        # (m3)
        dischargeInitial = pcr.ifthenelse(
            alpha > 0.0, (channel_wetted_area / alpha) ** (1.0 / self.beta), 0.0
        )

        return (alpha, dischargeInitial)

    def returnInundationFractionAndFloodDepth(self, channelStorage):

        # flood inundation depth above the floodplain (m)
        floodDepth = 0.0

        # channel and flood inundated fraction (-), at least channelFraction
        inundatedFraction = self.channelFraction

        if self.floodPlain:

            # flooded fraction and associated water height for the given channel volume, using a logistic
            # smoother near intersections (K&K, 2007)

            # flood/excess volume above the bankfull capacity (m3)
            excessVolume = pcr.max(0.0, channelStorage - self.channelStorageCapacity)

            # find the match based on the shortest distance to the available intersections or steps
            deltaXMin = self.floodVolume[self.nrZLevels - 1]
            y_i = pcr.scalar(1.0)
            k = [pcr.scalar(0.0)] * 2
            mInt = pcr.scalar(0.0)
            for iCnt in range(self.nrZLevels - 1, 0, -1):
                # find x_i for the current volume and update the match, slope and intercept if applicable
                deltaX = excessVolume - self.floodVolume[iCnt]
                mask = pcr.abs(deltaX) < pcr.abs(deltaXMin)
                deltaXMin = pcr.ifthenelse(mask, deltaX, deltaXMin)
                y_i = pcr.ifthenelse(mask, self.areaFractions[iCnt], y_i)
                k[0] = pcr.ifthenelse(mask, self.kSlope[iCnt - 1], k[0])
                k[1] = pcr.ifthenelse(mask, self.kSlope[iCnt], k[1])
                mInt = pcr.ifthenelse(mask, self.mInterval[iCnt], mInt)

            # scaled deltaX and smoothed function, based on the integrated logistic functions PHI(x) and 1-PHI(x)
            deltaX = deltaXMin
            deltaXScaled = pcr.ifthenelse(
                deltaX < 0.0, pcr.scalar(-1.0), 1.0
            ) * pcr.min(self.criterionKK, pcr.abs(deltaX / pcr.max(1.0, mInt)))
            logInt = self.integralLogisticFunction(deltaXScaled)

            # fractional inundated area
            inundatedFraction = pcr.ifthenelse(
                excessVolume > 0.0,
                pcr.ifthenelse(
                    pcr.abs(deltaXScaled) < self.criterionKK,
                    y_i - k[0] * mInt * logInt[0] + k[1] * mInt * logInt[1],
                    y_i + pcr.ifthenelse(deltaX < 0.0, k[0], k[1]) * deltaX,
                ),
                0.0,
            )
            # at least channelFraction
            inundatedFraction = pcr.max(self.channelFraction, inundatedFraction)
            # at most 1 (-)
            inundatedFraction = pcr.max(0.0, pcr.min(1.0, inundatedFraction))

            # inundation depth above the floodplain (m), zero if excessVolume == 0
            floodDepth = pcr.ifthenelse(
                inundatedFraction > 0.0,
                excessVolume
                / (
                    pcr.max(self.min_fracwat_for_water_height, inundatedFraction)
                    * self.cellArea
                ),
                0.0,
            )

            # maximum flood depth
            if self.maxFloodDepth is not None:
                floodDepth = pcr.max(0.0, pcr.min(self.maxFloodDepth, floodDepth))

        return inundatedFraction, floodDepth

    def return_water_body_storage_to_channel(self, channelStorage):

        # return waterBodyStorage to channelStorage
        waterBodyStorageTotal = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.areaaverage(
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyStorage),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            )
            + pcr.areatotal(
                pcr.cover(pcr.ifthen(self.landmask, channelStorage), 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            ),
        )
        waterBodyStoragePerCell = (
            waterBodyStorageTotal
            * self.cellArea
            / pcr.areatotal(
                pcr.cover(self.cellArea, 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            )
        )
        # (m3)
        waterBodyStoragePerCell = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, waterBodyStoragePerCell
        )
        # (m3)
        channelStorage = pcr.ifthen(
            self.landmask, pcr.cover(waterBodyStoragePerCell, channelStorage)
        )
        return channelStorage

    def kinematic_wave_update(self, landSurface, groundwater, currTimeStep, meteo):

        logger.info("Using the fully kinematic wave method! ")

        # update the time steps for the long- and short-term statistics (avgDischarge, avgInflow, avgOutflow, etc.)
        self.timestepsToAvgDischarge += 1.0

        # total local change (input) to surface water storage (m3); only local processes, no routing;
        # initialized at zero
        self.local_input_to_surface_water = pcr.scalar(0.0)

        # for simplicity, surface water abstraction is done outside the sub-daily time steps;
        # update channelStorage (m3) after actSurfaceWaterAbstraction
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea
        self.local_input_to_surface_water -= (
            landSurface.actSurfaceWaterAbstract * self.cellArea
        )
        # channelStorage after surface water abstraction, for reporting (m3)
        self.channelStorageAfterAbstraction = pcr.ifthen(
            self.landmask, self.channelStorage
        )

        # runoff from land surface cells, over the entire cell area (m/day)
        self.runoff = landSurface.landSurfaceRunoff + groundwater.baseflow

        # only route non-negative channelStorage (otherwise it stays)
        channelStorageThatWillNotMove = pcr.ifthenelse(
            self.channelStorage < 0.0, self.channelStorage, 0.0
        )

        # channelStorage passed to the routing (m3)
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)

        # water height (m), needed to estimate the sub-time step length
        self.water_height = channelStorageForRouting / (
            pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat)
            * self.cellArea
        )

        # sub-time step length (s)
        length_of_sub_time_step, number_of_loops = (
            self.estimate_length_of_sub_time_step()
        )

        for i_loop in range(number_of_loops):

            msg = (
                "sub-daily time step "
                + str(i_loop + 1)
                + " from "
                + str(number_of_loops)
            )
            logger.info(msg)

            if self.debugWaterBalance:
                preStorage = pcr.ifthen(self.landmask, channelStorageForRouting)

            # initialize the accumulated values
            if i_loop == 0:
                # (m3)
                acc_local_input_to_surface_water = pcr.scalar(0.0)
                # (m3)
                acc_water_body_evaporation_volume = pcr.scalar(0.0)
                # (m3)
                acc_discharge_volume = pcr.scalar(0.0)

            # update channelStorageForRouting after runoff and non-irrigation return flow (m3)
            channelStorageForRouting += (
                (self.runoff + landSurface.nonIrrReturnFlow)
                * self.cellArea
                * length_of_sub_time_step
                / vos.secondsPerDay()
            )
            # (m3)
            acc_local_input_to_surface_water += (
                (self.runoff + landSurface.nonIrrReturnFlow)
                * self.cellArea
                * length_of_sub_time_step
                / vos.secondsPerDay()
            )

            # potential evaporation within the sub-time step, over the entire cell area (m)
            water_body_potential_evaporation = (
                self.calculate_potential_evaporation(landSurface, currTimeStep, meteo)
                * length_of_sub_time_step
                / vos.secondsPerDay()
            )

            # accumulate the potential evaporation
            if i_loop == 0:
                self.waterBodyPotEvap = pcr.scalar(0.0)
            self.waterBodyPotEvap += water_body_potential_evaporation

            # update channelStorageForRouting after evaporation
            water_body_evaporation_volume = pcr.min(
                pcr.max(channelStorageForRouting, 0.0),
                water_body_potential_evaporation
                * self.cellArea
                * length_of_sub_time_step
                / vos.secondsPerDay(),
            )
            channelStorageForRouting -= water_body_evaporation_volume
            acc_local_input_to_surface_water -= water_body_evaporation_volume
            acc_water_body_evaporation_volume += water_body_evaporation_volume

            if self.debugWaterBalance:
                vos.waterBalanceCheck(
                    [
                        self.runoff * length_of_sub_time_step / vos.secondsPerDay(),
                        landSurface.nonIrrReturnFlow
                        * length_of_sub_time_step
                        / vos.secondsPerDay(),
                    ],
                    [water_body_evaporation_volume / self.cellArea],
                    [preStorage / self.cellArea],
                    [channelStorageForRouting / self.cellArea],
                    "channelStorageForRouting (local fluxes)",
                    True,
                    currTimeStep.fulldate,
                    threshold=5e-5,
                )

            # move channelStorageForRouting (m3) to waterBodyStorage at lake and reservoir cells
            storageAtLakeAndReservoirs = pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                channelStorageForRouting,
            )
            storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs, 0.0)

            # only non-negative, rounded-down values
            storageAtLakeAndReservoirs = pcr.max(
                0.00, pcr.rounddown(storageAtLakeAndReservoirs)
            )
            channelStorageForRouting = pcr.max(
                0.0, channelStorageForRouting - storageAtLakeAndReservoirs
            )

            # update waterBodyStorage (inflow, storage and outflow)
            self.WaterBodies.update(
                storageAtLakeAndReservoirs,
                self.timestepsToAvgDischarge,
                self.maxTimestepsToAvgDischargeShort,
                self.maxTimestepsToAvgDischargeLong,
                currTimeStep,
                self.avgDischarge,
                length_of_sub_time_step,
                self.downstreamDemand,
            )

            # waterBodyOutflow (m3 per sub-time step) at lake/reservoir outlet cells
            waterBodyOutflow = pcr.cover(
                pcr.ifthen(
                    self.WaterBodies.waterBodyOut, self.WaterBodies.waterBodyOutflow
                ),
                0.0,
            )
            waterBodyOutflow = pcr.ifthen(self.landmask, waterBodyOutflow)

            # (m3/s)
            waterBodyOutflowInM3PerSec = waterBodyOutflow / length_of_sub_time_step

            # waterBodyStorage (m3) after outflow, per water body id (not per cell)
            self.waterBodyStorage = pcr.ifthen(
                self.landmask, self.WaterBodies.waterBodyStorage
            )

            # update channelStorage (m3) after waterBodyOutflow (m3); local_input_to_surface_water does not
            # include waterBodyOutflow
            storage_change_in_volume = pcr.upstream(self.lddMap, waterBodyOutflow)
            channelStorageForRouting += storage_change_in_volume

            # water height (m) in channels (excluding lakes and reservoirs), needed to estimate the channel
            # wetted area (for alpha and dischargeInitial)
            self.water_height = channelStorageForRouting / (
                pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat)
                * self.cellArea
            )
            # deactivating this line gives negative channelStorage (probably due to too high water heights in lakes and reservoirs)

            # alpha parameter and initial discharge estimate for the kinematic wave
            alpha, dischargeInitial = (
                self.calculate_alpha_and_initial_discharge_for_kinematic_wave(
                    channelStorageForRouting,
                    self.water_height,
                    self.innundatedFraction,
                    self.floodDepth,
                )
            )

            # at lake and reservoir outlet cells, the initial discharge is waterBodyOutflowInM3PerSec
            dischargeInitial = pcr.cover(
                pcr.ifthen(self.WaterBodies.waterBodyOut, waterBodyOutflowInM3PerSec),
                dischargeInitial,
            )

            # also for cells with zero channelStorageForRouting
            dischargeInitial = pcr.ifthenelse(
                channelStorageForRouting > 0.0, dischargeInitial, 0.0
            )

            # (m3/s)
            dischargeInitial = pcr.cover(dischargeInitial, 0.0)
            dischargeInitial = pcr.ifthen(self.landmask, dischargeInitial)

            # discharge (m3/s) from the kinematic wave approximation
            self.subDischarge = pcr.kinematic(
                self.lddMap,
                dischargeInitial,
                0.0,
                alpha,
                self.beta,
                1,
                length_of_sub_time_step,
                self.channelLength,
            )
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))

            # zero discharge at lake and reservoir cells
            self.subDischarge = pcr.cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, pcr.scalar(0.0)
                ),
                self.subDischarge,
            )

            # avoid negative channel storage
            self.subDischarge = (
                pcr.min(
                    self.subDischarge * length_of_sub_time_step,
                    pcr.max(
                        0.0,
                        channelStorageForRouting
                        + pcr.upstream(
                            self.lddMap, self.subDischarge * length_of_sub_time_step
                        ),
                    ),
                )
                / length_of_sub_time_step
            )

            # update channelStorage (m3) after lateral flows in channels
            storage_change_in_volume = (
                pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)
                - self.subDischarge * length_of_sub_time_step
            )
            channelStorageForRouting += storage_change_in_volume

            # return waterBodyStorage to channelStorage
            channelStorageForRouting = self.return_water_body_storage_to_channel(
                channelStorageForRouting
            )

            # add waterBodyOutflowInM3PerSec to subDischarge
            self.subDischarge += waterBodyOutflowInM3PerSec
            self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)

            # total discharge volume (m3) until this loop
            acc_discharge_volume += self.subDischarge * length_of_sub_time_step

            # update the flood fraction and flood depth
            self.inundatedFraction, self.floodDepth = (
                self.returnInundationFractionAndFloodDepth(channelStorageForRouting)
            )

            # dynamicFracWat: fraction of surface water bodies (-), including lakes and reservoirs; lake and
            # reservoir surface water fraction
            self.dynamicFracWat = pcr.cover(pcr.min(1.0, self.WaterBodies.fracWat), 0.0)

            # fraction of channel (including its excess above bankfull capacity)
            self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(
                self.channelFraction, self.innundatedFraction
            )

            # dynamicFracWat is at most 1
            self.dynamicFracWat = pcr.ifthen(
                self.landmask,
                pcr.min(pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0),
            )
            self.dynamicFracWat = pcr.ifthen(
                self.landmask, pcr.min(1.0, self.dynamicFracWat)
            )

            # for the next loop, only route non-negative channelStorage
            channelStorageThatWillNotMove += pcr.ifthenelse(
                channelStorageForRouting < 0.0, channelStorageForRouting, 0.0
            )
            channelStorageForRouting = pcr.max(0.000, channelStorageForRouting)

            # water height, including lakes and reservoirs
            self.water_height = pcr.max(0.0, channelStorageForRouting) / (
                pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat)
                * self.cellArea
            )

        # evaporation (m/day)
        self.waterBodyEvaporation = acc_water_body_evaporation_volume / self.cellArea

        # local input to surface water (m3)
        self.local_input_to_surface_water += acc_local_input_to_surface_water

        # channel discharge (m3/day)
        self.Q = acc_discharge_volume

        # update channelStorage after routing
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage
        self.channelStorage += channelStorageThatWillNotMove

        # reported channel storage cannot be negative
        self.channelStorage = pcr.max(0.0, self.channelStorage)

        # channel discharge of the current time step (m3/s)
        self.discharge = self.Q / vos.secondsPerDay()
        # reported channel discharge cannot be negative
        self.discharge = pcr.max(0.0, self.discharge)
        self.discharge = pcr.ifthen(self.landmask, self.discharge)

        self.disChanWaterBody = pcr.ifthen(
            pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
            pcr.areamaximum(self.discharge, self.WaterBodies.waterBodyIds),
        )
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)

        # reported channel discharge cannot be negative
        self.disChanWaterBody = pcr.max(0.0, self.disChanWaterBody)

    def calculate_statistics(self, groundwater, landSurface):

        # short-term average inflow (m3/s) and long-term average outflow (m3/s) of lakes and reservoirs
        self.avgInflow = pcr.ifthen(
            self.landmask, pcr.cover(self.WaterBodies.avgInflow, 0.0)
        )
        self.avgOutflow = pcr.ifthen(
            self.landmask, pcr.cover(self.WaterBodies.avgOutflow, 0.0)
        )

        # short- and long-term average discharge (m3/s), using the online algorithm of
        # http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

        # long-term average discharge
        dishargeUsed = pcr.max(0.0, self.discharge)
        dishargeUsed = pcr.max(dishargeUsed, self.disChanWaterBody)

        deltaAnoDischarge = dishargeUsed - self.avgDischarge
        self.avgDischarge = self.avgDischarge + deltaAnoDischarge / pcr.min(
            self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge
        )
        self.avgDischarge = pcr.max(0.0, self.avgDischarge)
        self.m2tDischarge = self.m2tDischarge + pcr.abs(
            deltaAnoDischarge * (dishargeUsed - self.avgDischarge)
        )

        # short-term average discharge
        deltaAnoDischargeShort = dishargeUsed - self.avgDischargeShort
        self.avgDischargeShort = (
            self.avgDischargeShort
            + deltaAnoDischargeShort
            / pcr.min(
                self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge
            )
        )
        self.avgDischargeShort = pcr.max(0.0, self.avgDischargeShort)

        # long-term average baseflow (m3/s), used as proxy to partition groundwater and surface water abstractions
        baseflowM3PerSec = groundwater.baseflow * self.cellArea / vos.secondsPerDay()

        deltaAnoBaseflow = baseflowM3PerSec - self.avgBaseflow
        self.avgBaseflow = self.avgBaseflow + deltaAnoBaseflow / pcr.min(
            self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge
        )
        self.avgBaseflow = pcr.max(0.0, self.avgBaseflow)

        # DynQual: average irrigation water allocated over the last 30 days (needed for online runs where
        # loadings are calculated in the loop)
        if self.quality:
            if self.calculateLoads and self.offlineRun == False:
                # average irrigation gross demand over the last 30 days
                irrGrossDemand = deepcopy(landSurface.irrGrossDemand)
                deltaAno_irrGrossDemand = (
                    pcr.max(0.0, irrGrossDemand) - self.avg_irrGrossDemand
                )
                self.avg_irrGrossDemand = (
                    self.avg_irrGrossDemand
                    + deltaAno_irrGrossDemand
                    / pcr.min(30.0, self.timestepsToAvgDischarge)
                )
                self.avg_irrGrossDemand = pcr.max(0.0, self.avg_irrGrossDemand)

                # average netLqWaterToSoil over the last 30 days
                deltaAno_netLqWaterToSoil = (
                    pcr.max(0.0, landSurface.netLqWaterToSoil)
                    - self.avg_netLqWaterToSoil
                )
                self.avg_netLqWaterToSoil = (
                    self.avg_netLqWaterToSoil
                    + deltaAno_netLqWaterToSoil
                    / pcr.min(30.0, self.timestepsToAvgDischarge)
                )
                self.avg_netLqWaterToSoil = pcr.max(0.0, self.avg_netLqWaterToSoil)

    def estimate_discharge_for_environmental_flow(self, channelStorage):

        # statistical assumption: z-score of the 90th percentile
        z_score = 1.2816

        # long-term variance and standard deviation of discharge, using the online algorithm of
        # http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        varDischarge = self.m2tDischarge / pcr.max(
            1.0,
            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)
            - 1.0,
        )
        stdDischarge = pcr.max(varDischarge**0.5, 0.0)

        # minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = pcr.max(
            0.0, self.avgDischarge - z_score * stdDischarge
        )
        # avoid flip-flopping
        factor = 0.10
        # (m3/s)
        minDischargeForEnvironmentalFlow = pcr.max(
            factor * self.avgDischarge, minDischargeForEnvironmentalFlow
        )
        minDischargeForEnvironmentalFlow = pcr.max(
            0.0, minDischargeForEnvironmentalFlow
        )

        return minDischargeForEnvironmentalFlow

    def estimate_available_volume_for_abstraction(
        self, channelStorage, length_of_time_step=vos.secondsPerDay()
    ):
        # input: channelStorage (m3)

        # minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = (
            self.estimate_discharge_for_environmental_flow(channelStorage)
        )

        # channelStorage available for surface water abstraction
        readAvlChannelStorage = pcr.max(0.0, channelStorage)

        # reduce readAvlChannelStorage if the average discharge < minDischargeForEnvironmentalFlow
        readAvlChannelStorage *= pcr.min(
            1.0,
            vos.getValDivZero(
                pcr.max(0.0, pcr.min(self.avgDischargeShort, self.avgDischarge)),
                minDischargeForEnvironmentalFlow,
                vos.smallNumber,
            ),
        )

        # maintain the environmental flow if the average discharge > minDischargeForEnvironmentalFlow; TODO: check why this is needed
        readAvlChannelStorage = pcr.ifthenelse(
            self.avgDischargeShort < minDischargeForEnvironmentalFlow,
            readAvlChannelStorage,
            pcr.max(
                readAvlChannelStorage,
                pcr.max(0.0, self.avgDischargeShort - minDischargeForEnvironmentalFlow)
                * length_of_time_step,
            ),
        )

        # maximum fraction of water that can be abstracted from the channel (to avoid flip-flopping)
        maximum_percentage = 0.90
        readAvlChannelStorage = pcr.min(
            readAvlChannelStorage, maximum_percentage * channelStorage
        )
        readAvlChannelStorage = pcr.max(0.0, readAvlChannelStorage)

        # ignore small volumes (less than 0.1 m3)
        readAvlChannelStorage = pcr.rounddown(readAvlChannelStorage * 10.0) / 10.0
        readAvlChannelStorage = pcr.ifthen(self.landmask, readAvlChannelStorage)

        # (m3)
        return readAvlChannelStorage

    def initiate_old_style_routing_reporting(self, iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.routingOptions["outDailyTotNC"].split(",")
            self.outMonthTotNC = iniItems.routingOptions["outMonthTotNC"].split(",")
            self.outMonthAvgNC = iniItems.routingOptions["outMonthAvgNC"].split(",")
            self.outMonthEndNC = iniItems.routingOptions["outMonthEndNC"].split(",")
            self.outAnnuaTotNC = iniItems.routingOptions["outAnnuaTotNC"].split(",")
            self.outAnnuaAvgNC = iniItems.routingOptions["outAnnuaAvgNC"].split(",")
            self.outAnnuaEndNC = iniItems.routingOptions["outAnnuaEndNC"].split(",")
        except:
            self.report = False
        if self.report == True:
            # daily netCDF output
            self.outNCDir = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
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

    def old_style_routing_reporting(self, currTimeStep):

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

    def returnFloodedFraction(self, channelStorage):
        # flooded fraction and associated water height for the given flood volume, using a logistic smoother
        # near intersections (K&K, 2007); find the match based on the shortest distance to the available
        # intersections or steps
        deltaXMin = self.floodVolume[self.nrZLevels - 1]
        y_i = pcr.scalar(1.0)
        k = [pcr.scalar(0.0)] * 2
        mInt = pcr.scalar(0.0)
        for iCnt in range(self.nrZLevels - 1, 0, -1):
            # find x_i for the current volume and update the match, slope and intercept if applicable
            deltaX = channelStorage - self.floodVolume[iCnt]
            mask = pcr.abs(deltaX) < pcr.abs(deltaXMin)
            deltaXMin = pcr.ifthenelse(mask, deltaX, deltaXMin)
            y_i = pcr.ifthenelse(mask, self.areaFractions[iCnt], y_i)
            k[0] = pcr.ifthenelse(mask, self.kSlope[iCnt - 1], k[0])
            k[1] = pcr.ifthenelse(mask, self.kSlope[iCnt], k[1])
            mInt = pcr.ifthenelse(mask, self.mInterval[iCnt], mInt)

        # scaled deltaX and smoothed function, based on the integrated logistic functions PHI(x) and 1-PHI(x)
        deltaX = deltaXMin
        deltaXScaled = pcr.ifthenelse(deltaX < 0.0, pcr.scalar(-1.0), 1.0) * pcr.min(
            self.criterionKK, pcr.abs(deltaX / pcr.max(1.0, mInt))
        )
        logInt = self.integralLogisticFunction(deltaXScaled)

        # fractional flooded area and flood depth
        floodedFraction = pcr.ifthenelse(
            channelStorage > 0.0,
            pcr.ifthenelse(
                pcr.abs(deltaXScaled) < self.criterionKK,
                y_i - k[0] * mInt * logInt[0] + k[1] * mInt * logInt[1],
                y_i + pcr.ifthenelse(deltaX < 0.0, k[0], k[1]) * deltaX,
            ),
            0.0,
        )
        floodedFraction = pcr.max(0.0, pcr.min(1.0, floodedFraction))
        floodDepth = pcr.ifthenelse(
            floodedFraction > 0.0,
            channelStorage / (floodedFraction * self.cellArea),
            0.0,
        )
        floodDepth = pcr.min(self.max_water_height, floodDepth)

        return floodedFraction, floodDepth

    def integralLogisticFunction(self, x):
        # tuple with the integrals of the logistic functions of x and -x
        logInt = pcr.ln(pcr.exp(-x) + 1)
        return logInt, x + logInt

    def kinAlpha(self, channelStorage):
        mask = pcr.boolean(1)

        # kinAlphaDynamic logic
        floodVol = pcr.max(0, channelStorage - self.channelStorageCapacity)
        floodedFraction, floodDepth = self.returnFloodedFraction(floodVol)

        self.channelFraction = pcr.max(
            0.0, pcr.min(1.0, self.wMean * self.cellLengthFD / self.cellArea)
        )
        floodFrac_dyn = floodedFraction + self.channelFraction

        wetA_dyn = channelStorage / self.channelLength
        wetPFld = (
            pcr.max(
                0.0, floodFrac_dyn * self.cellArea / self.channelLength - self.wMean
            )
            + 2.0 * floodDepth
        )
        wetPCh = self.wMean + 2.0 * pcr.min(
            self.channelDepth, channelStorage / (self.channelLength * self.wMean)
        )
        wetP_dyn = wetPFld + wetPCh
        manQ = (
            wetPCh / wetP_dyn * self.manningsN**1.5
            + wetPFld / wetP_dyn * self.floodplainManN**1.5
        ) ** (2.0 / 3.0)
        dynamicAlphaQ = (
            manQ * wetP_dyn ** (2.0 / 3.0) * self.gradient**-0.5
        ) ** self.beta
        dynamicDischargeInitial = pcr.ifthenelse(
            dynamicAlphaQ > 0.0, (wetA_dyn / dynamicAlphaQ) ** (1 / self.beta), 0.0
        )

        # kinAlphaStatic logic
        if self.quality:
            manIce = pcr.max(
                self.manningsN,
                0.0493
                * pcr.max(
                    0.01, self.channelStorage / (self.dynamicFracWat * self.cellArea)
                )
                ** (-0.23)
                * self.iceThickness**0.57,
            )
            manningsWithIce = (0.5 * (self.manningsN**1.5 + manIce**1.5)) ** (2.0 / 3.0)
            wetA_sta = self.channelStorage / self.channelLength
            wetP_sta = 2.0 * wetA_sta / self.wMean + self.wMean
            staticAlphaQ = (
                manningsWithIce * wetP_sta ** (2.0 / 3.0) * self.gradient**-0.5
            ) ** self.beta
        else:
            wetA_sta = channelStorage / self.channelLength
            wetP_sta = 2.0 * wetA_sta / self.wMean + self.wMean
            staticAlphaQ = (
                self.manningsN * wetP_sta ** (2.0 / 3.0) * self.gradient**-0.5
            ) ** self.beta

        staticDischargeInitial = pcr.ifthenelse(
            staticAlphaQ > 0.0, (wetA_sta / staticAlphaQ) ** (1 / self.beta), 0.0
        )

        # combine using the mask
        floodedFraction = pcr.ifthenelse(mask, floodFrac_dyn, 0.0)
        floodDepth = pcr.ifthenelse(mask, floodDepth, 0.0)
        alphaQ = pcr.ifthenelse(mask, dynamicAlphaQ, staticAlphaQ)
        dischargeInitial = pcr.ifthenelse(
            mask, dynamicDischargeInitial, staticDischargeInitial
        )

        return floodedFraction, floodDepth, alphaQ, dischargeInitial

    def readExtensiveMeteo(self, currTimeStep):
        # read the meteorological input directly from netCDF files
        if currTimeStep.day == 1:
            self.cloudCover = vos.netcdf2PCRobjClone(
                self.cloudFileNC,
                "cld",
                str(currTimeStep.fulldate),
                useDoy="monthly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=-999.0,
            ) / pcr.scalar(100)

            self.vaporPressure = vos.netcdf2PCRobjClone(
                self.vapFileNC,
                "vap",
                str(currTimeStep.fulldate),
                useDoy="monthly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=-999.0,
            )

            self.annualT = vos.netcdf2PCRobjClone(
                self.annualTFileNC,
                "tas",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=-999.0,
            ) + pcr.scalar(273.15)

        self.radiation = vos.netcdf2PCRobjClone(
            self.radFileNC,
            "rsds",
            str(currTimeStep.fulldate),
            useDoy="daily",
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
            specificFillValue=-999.0,
        )

        # atmospheric emissivity (-) from vapour pressure:
        # min(1, (0.53 + 0.0065 * vaporPressure**0.5) * (1 + 0.4 * cloudCover))
        self.atmosEmis = pcr.scalar(1.0)
        cld1 = pcr.roundoff(10 * self.cloudCover + 0.5)
        cld0 = cld1 - 1
        sun0 = pcr.lookupscalar(self.sunFracTBL, cld0)
        deltaSun = (pcr.lookupscalar(self.sunFracTBL, cld1) - sun0) / (cld1 - cld0)
        sunFrac = sun0 + (10 * self.cloudCover - cld0) * deltaSun
        radFrac = self.radCon + self.radSlope * sunFrac
        self.rsw = radFrac * self.radiation

    def readPollutantLoadingsInputData(self, currTimeStep):

        if currTimeStep.doy == 1:
            # domestic: gridded population (5 arcmin)
            self.Population = vos.netcdf2PCRobjClone(
                self.PopulationNC,
                "Population",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # urban surface runoff: urban fraction (0-1)
            self.urban_area_fraction = vos.netcdf2PCRobjClone(
                self.UrbanFractionNC,
                "urban_fraction",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            # zero urban fraction if missing (e.g. for lakes)
            self.urban_area_fraction = pcr.cover(self.urban_area_fraction, 0)

            # livestock populations (5 arcmin): buffalo
            self.BufalloPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "BufalloPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.BufalloPopulation = pcr.cover(self.BufalloPopulation, 0.0)

            # chicken
            self.ChickenPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "ChickenPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.ChickenPopulation = pcr.cover(self.ChickenPopulation, 0.0)

            # cow
            self.CowPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "CowPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.CowPopulation = pcr.cover(self.CowPopulation, 0.0)

            # duck
            self.DuckPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "DuckPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.DuckPopulation = pcr.cover(self.DuckPopulation, 0.0)

            # goat
            self.GoatPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "GoatPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.GoatPopulation = pcr.cover(self.GoatPopulation, 0.0)

            # horse
            self.HorsePopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "HorsePop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.HorsePopulation = pcr.cover(self.HorsePopulation, 0.0)

            # pig
            self.PigPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "PigPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.PigPopulation = pcr.cover(self.PigPopulation, 0.0)

            # sheep
            self.SheepPopulation = vos.netcdf2PCRobjClone(
                self.LivPopulationNC,
                "SheepPop",
                str(currTimeStep.fulldate),
                useDoy=None,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )
            self.SheepPopulation = pcr.cover(self.SheepPopulation, 0.0)

            # livestock densities accounting for livestock units (Wen et al., 2018); convert m2 to km2
            self.cellArea_km2 = self.cellArea / 1000000.0
            self.LivDensityThres = pcr.scalar(25.0)

            self.BufalloDensity = self.BufalloPopulation / self.cellArea_km2
            self.ChickenDensity = (self.ChickenPopulation * 0.01) / self.cellArea_km2
            self.CowDensity = self.CowPopulation / self.cellArea_km2
            self.DuckDensity = (self.DuckPopulation * 0.01) / self.cellArea_km2
            self.GoatDensity = (self.GoatPopulation * 0.1) / self.cellArea_km2
            self.HorseDensity = self.HorsePopulation / self.cellArea_km2
            self.PigDensity = (self.PigPopulation * 0.3) / self.cellArea_km2
            self.SheepDensity = (self.SheepPopulation * 0.1) / self.cellArea_km2

            # wastewater treatment: fraction of wastewater that is collected and treated
            self.WWt_ct = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "WW_ct",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # country-level fraction of uncollected wastewater with basic sanitation
            self.WWt_bs = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "WW_bs",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # country-level fraction of uncollected wastewater that is open defecation
            self.WWt_od = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "WW_od",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # fraction of TDS removed at each wastewater treatment plant
            self.WWt_TDS_removal = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "TDS_removal",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # fraction of BOD removed at each wastewater treatment plant
            self.WWt_BOD_removal = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "BOD_removal",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

            # fraction of FC removed at each wastewater treatment plant
            self.WWt_FC_removal = vos.netcdf2PCRobjClone(
                self.WWtPlantsNC,
                "FC_removal",
                str(currTimeStep.fulldate),
                useDoy="yearly",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
                specificFillValue=None,
            )

    def calculatePollutantLoadings(self, currTimeStep, landSurface, groundwater):
        # calculate the pollutant loadings
        logger.info("Calculating pollutant loadings")

        # fraction of direct runoff (direct runoff / total runoff), used to transport pollution from open
        # defecation and extensive livestock
        self.frac_surfaceRunoff = vos.getValDivZero(
            landSurface.directRunoff,
            (landSurface.landSurfaceRunoff + groundwater.baseflow),
        )

        # pollution from municipal wastewater (domestic, manufacturing and urban surface runoff)

        # gross domestic loadings: population (capita) * excretion rate per capita (g/capita/day; cfu/capita/day),
        # with removal at the wastewater treatment plant (g/day)
        self.Dom_TDSload = pcr.ifthenelse(
            # cells not in a wastewater treatment zone
            self.WWt_zoneID == 0,
            (self.Population * self.DomTDS_ExcrLoad * self.WWt_bs)
            + (
                self.Population
                * self.DomTDS_ExcrLoad
                * self.WWt_od
                * self.frac_surfaceRunoff
            ),
            pcr.ifthenelse(
                self.WWt_zoneID
                # accumulate the loadings over the treatment zone to the plant location
                == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.Population * self.DomTDS_ExcrLoad, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_TDS_removal * self.WWt_ct)),
                # after accumulation, set locations without a treatment plant to 0
                0.0,
            ),
        )

        # (g/day)
        self.Dom_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            (self.Population * self.DomBOD_ExcrLoad * self.WWt_bs)
            + (
                self.Population
                * self.DomBOD_ExcrLoad
                * self.WWt_od
                * self.frac_surfaceRunoff
            ),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.Population * self.DomBOD_ExcrLoad, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_BOD_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # (million cfu/day)
        self.Dom_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            (self.Population * (self.DomFC_ExcrLoad / 1000000.0) * self.WWt_bs)
            + (
                self.Population
                * (self.DomFC_ExcrLoad / 1000000.0)
                * self.WWt_od
                * self.frac_surfaceRunoff
            ),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0,
                        self.Population * (self.DomFC_ExcrLoad / 1000000.0),
                        0,
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_FC_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # gross manufacturing loadings: manufacturing wastewater (m3/day) * average effluent concentration (mg/L; cfu/100mL)
        if self.includeSectors["industry"]:
            self.ManWWp = landSurface.nonIrrReturnFlowVolumePerSector["industry"]
        elif self.includeSectors["manufacture"]:
            self.ManWWp = landSurface.nonIrrReturnFlowVolumePerSector["manufacture"]

        # (g/day)
        self.Man_TDSload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.ManWWp * self.ManTDS_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.ManWWp * self.ManTDS_EfflConc, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_TDS_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # (g/day)
        self.Man_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.ManWWp * self.ManBOD_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.ManWWp * self.ManBOD_EfflConc, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_BOD_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # (million cfu/day)
        self.Man_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.ManWWp * (self.ManFC_EfflConc / 100.0),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0,
                        self.ManWWp * (self.ManFC_EfflConc / 100.0),
                        0,
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_FC_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # gross urban surface runoff loadings: USR return flow (m3/day) * average effluent concentration (mg/L; cfu/100mL)
        # (m3/day)
        self.USR_RF = (
            landSurface.directRunoff * self.urban_area_fraction * self.cellArea
        )

        # (g/day)
        self.USR_TDSload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.USR_RF * self.USRTDS_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.USR_RF * self.USRTDS_EfflConc, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_TDS_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # (g/day)
        self.USR_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.USR_RF * self.USRBOD_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0, self.USR_RF * self.USRBOD_EfflConc, 0
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_BOD_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # (million cfu/day)
        self.USR_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.USR_RF * (self.USRFC_EfflConc / 100.0),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(
                        self.WWt_zoneID != 0,
                        self.USR_RF * (self.USRFC_EfflConc / 100.0),
                        0,
                    ),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_FC_removal * self.WWt_ct)),
                0.0,
            ),
        )

        # pollution from livestock (intensive and extensive): BOD
        self.intLiv_Bufallo_BODload = pcr.ifthenelse(
            self.BufalloDensity > self.LivDensityThres,
            self.BufalloPopulation * self.Bufallo_BODload,
            0.0,
        )
        self.intLiv_Chicken_BODload = pcr.ifthenelse(
            self.ChickenDensity > self.LivDensityThres,
            self.ChickenPopulation * self.Chicken_BODload,
            0.0,
        )
        self.intLiv_Cow_BODload = pcr.ifthenelse(
            self.CowDensity > self.LivDensityThres,
            self.CowPopulation * self.Cow_BODload,
            0.0,
        )
        self.intLiv_Duck_BODload = pcr.ifthenelse(
            self.DuckDensity > self.LivDensityThres,
            self.DuckPopulation * self.Duck_BODload,
            0.0,
        )
        self.intLiv_Goat_BODload = pcr.ifthenelse(
            self.GoatDensity > self.LivDensityThres,
            self.GoatPopulation * self.Goat_BODload,
            0.0,
        )
        self.intLiv_Horse_BODload = pcr.ifthenelse(
            self.HorseDensity > self.LivDensityThres,
            self.HorsePopulation * self.Horse_BODload,
            0.0,
        )
        self.intLiv_Pig_BODload = pcr.ifthenelse(
            self.PigDensity > self.LivDensityThres,
            self.PigPopulation * self.Pig_BODload,
            0.0,
        )
        self.intLiv_Sheep_BODload = pcr.ifthenelse(
            self.SheepDensity > self.LivDensityThres,
            self.SheepPopulation * self.Sheep_BODload,
            0.0,
        )

        # (g/day)
        self.intLiv_BODload = (
            self.intLiv_Bufallo_BODload
            + self.intLiv_Chicken_BODload
            + self.intLiv_Cow_BODload
            + self.intLiv_Duck_BODload
            + self.intLiv_Goat_BODload
            + self.intLiv_Horse_BODload
            + self.intLiv_Pig_BODload
            + self.intLiv_Sheep_BODload
        )

        # (g/day)
        self.intLiv_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.intLiv_BODload * self.frac_surfaceRunoff,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, self.intLiv_BODload, 0),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_BOD_removal * self.WWt_ct))
                * self.frac_surfaceRunoff,
                0.0,
            ),
        )

        self.extLiv_Bufallo_BODload = pcr.ifthenelse(
            self.BufalloDensity <= self.LivDensityThres,
            self.BufalloPopulation * self.Bufallo_BODload,
            0.0,
        )
        self.extLiv_Chicken_BODload = pcr.ifthenelse(
            self.ChickenDensity <= self.LivDensityThres,
            self.ChickenPopulation * self.Chicken_BODload,
            0.0,
        )
        self.extLiv_Cow_BODload = pcr.ifthenelse(
            self.CowDensity <= self.LivDensityThres,
            self.CowPopulation * self.Cow_BODload,
            0.0,
        )
        self.extLiv_Duck_BODload = pcr.ifthenelse(
            self.DuckDensity <= self.LivDensityThres,
            self.DuckPopulation * self.Duck_BODload,
            0.0,
        )
        self.extLiv_Goat_BODload = pcr.ifthenelse(
            self.GoatDensity <= self.LivDensityThres,
            self.GoatPopulation * self.Goat_BODload,
            0.0,
        )
        self.extLiv_Horse_BODload = pcr.ifthenelse(
            self.HorseDensity <= self.LivDensityThres,
            self.HorsePopulation * self.Horse_BODload,
            0.0,
        )
        self.extLiv_Pig_BODload = pcr.ifthenelse(
            self.PigDensity <= self.LivDensityThres,
            self.PigPopulation * self.Pig_BODload,
            0.0,
        )
        self.extLiv_Sheep_BODload = pcr.ifthenelse(
            self.SheepDensity <= self.LivDensityThres,
            self.SheepPopulation * self.Sheep_BODload,
            0.0,
        )

        # (g/day)
        self.extLiv_BODload = (
            self.extLiv_Bufallo_BODload
            + self.extLiv_Chicken_BODload
            + self.extLiv_Cow_BODload
            + self.extLiv_Duck_BODload
            + self.extLiv_Goat_BODload
            + self.extLiv_Horse_BODload
            + self.extLiv_Pig_BODload
            + self.extLiv_Sheep_BODload
        ) * self.frac_surfaceRunoff

        # FC
        self.intLiv_Bufallo_FCload = pcr.ifthenelse(
            self.BufalloDensity > self.LivDensityThres,
            self.BufalloPopulation * self.Bufallo_FCload,
            0.0,
        )
        self.intLiv_Chicken_FCload = pcr.ifthenelse(
            self.ChickenDensity > self.LivDensityThres,
            self.ChickenPopulation * self.Chicken_FCload,
            0.0,
        )
        self.intLiv_Cow_FCload = pcr.ifthenelse(
            self.CowDensity > self.LivDensityThres,
            self.CowPopulation * self.Cow_FCload,
            0.0,
        )
        self.intLiv_Duck_FCload = pcr.ifthenelse(
            self.DuckDensity > self.LivDensityThres,
            self.DuckPopulation * self.Duck_FCload,
            0.0,
        )
        self.intLiv_Goat_FCload = pcr.ifthenelse(
            self.GoatDensity > self.LivDensityThres,
            self.GoatPopulation * self.Goat_FCload,
            0.0,
        )
        self.intLiv_Horse_FCload = pcr.ifthenelse(
            self.HorseDensity > self.LivDensityThres,
            self.HorsePopulation * self.Horse_FCload,
            0.0,
        )
        self.intLiv_Pig_FCload = pcr.ifthenelse(
            self.PigDensity > self.LivDensityThres,
            self.PigPopulation * self.Pig_FCload,
            0.0,
        )
        self.intLiv_Sheep_FCload = pcr.ifthenelse(
            self.SheepDensity > self.LivDensityThres,
            self.SheepPopulation * self.Sheep_FCload,
            0.0,
        )

        self.intLiv_FCload = (
            self.intLiv_Bufallo_FCload
            + self.intLiv_Chicken_FCload
            + self.intLiv_Cow_FCload
            + self.intLiv_Duck_FCload
            + self.intLiv_Goat_FCload
            + self.intLiv_Horse_FCload
            + self.intLiv_Pig_FCload
            + self.intLiv_Sheep_FCload
        ) / 1000000.0

        # (million cfu/day)
        self.intLiv_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,
            self.intLiv_FCload * self.frac_surfaceRunoff,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, self.intLiv_FCload, 0),
                    self.WWt_zoneID,
                )
                * (1 - (self.WWt_FC_removal * self.WWt_ct))
                * self.frac_surfaceRunoff,
                0.0,
            ),
        )

        self.extLiv_Bufallo_FCload = pcr.ifthenelse(
            self.BufalloDensity <= self.LivDensityThres,
            self.BufalloPopulation * self.Bufallo_FCload,
            0.0,
        )
        self.extLiv_Chicken_FCload = pcr.ifthenelse(
            self.ChickenDensity <= self.LivDensityThres,
            self.ChickenPopulation * self.Chicken_FCload,
            0.0,
        )
        self.extLiv_Cow_FCload = pcr.ifthenelse(
            self.CowDensity <= self.LivDensityThres,
            self.CowPopulation * self.Cow_FCload,
            0.0,
        )
        self.extLiv_Duck_FCload = pcr.ifthenelse(
            self.DuckDensity <= self.LivDensityThres,
            self.DuckPopulation * self.Duck_FCload,
            0.0,
        )
        self.extLiv_Goat_FCload = pcr.ifthenelse(
            self.GoatDensity <= self.LivDensityThres,
            self.GoatPopulation * self.Goat_FCload,
            0.0,
        )
        self.extLiv_Horse_FCload = pcr.ifthenelse(
            self.HorseDensity <= self.LivDensityThres,
            self.HorsePopulation * self.Horse_FCload,
            0.0,
        )
        self.extLiv_Pig_FCload = pcr.ifthenelse(
            self.PigDensity <= self.LivDensityThres,
            self.PigPopulation * self.Pig_FCload,
            0.0,
        )
        self.extLiv_Sheep_FCload = pcr.ifthenelse(
            self.SheepDensity <= self.LivDensityThres,
            self.SheepPopulation * self.Sheep_FCload,
            0.0,
        )

        # (million cfu/day)
        self.extLiv_FCload = (
            (
                self.extLiv_Bufallo_FCload
                + self.extLiv_Chicken_FCload
                + self.extLiv_Cow_FCload
                + self.extLiv_Duck_FCload
                + self.extLiv_Goat_FCload
                + self.extLiv_Horse_FCload
                + self.extLiv_Pig_FCload
                + self.extLiv_Sheep_FCload
            )
            / 1000000.0
        ) * self.frac_surfaceRunoff

        # pollution from irrigation: irrigation return flow (m3/day) * soil TDS (mg/L); the return flows
        # follow from direct runoff, interflow and baseflow
        self.irr_rf_from_direct_runoff = landSurface.directRunoff * vos.getValDivZero(
            self.avg_irrGrossDemand,
            (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil),
        )
        self.irr_rf_from_interflow = landSurface.interflowTotal * vos.getValDivZero(
            self.avg_irrGrossDemand,
            (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil),
        )
        self.irr_rf_from_baseflow = groundwater.baseflow * vos.getValDivZero(
            self.avg_irrGrossDemand,
            (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil),
        )

        # total irrigation return flow (m3/day)
        self.Irr_RF = (
            self.irr_rf_from_direct_runoff
            + self.irr_rf_from_interflow
            + self.irr_rf_from_baseflow
        ) * self.cellArea
        # (g/day)
        self.Irr_TDSload = self.Irr_RF * self.IrrTDS_EfflConc

        # pollution from all human activities combined (g/day)
        self.TDSload = (
            self.Dom_TDSload + self.Man_TDSload + self.USR_TDSload + self.Irr_TDSload
        )
        # (g/day)
        self.BODload = (
            self.Dom_BODload
            + self.Man_BODload
            + self.USR_BODload
            + self.intLiv_BODload
            + self.extLiv_BODload
        )
        # (million cfu/day)
        self.FCload = (
            self.Dom_FCload
            + self.Man_FCload
            + self.USR_FCload
            + self.intLiv_FCload
            + self.extLiv_FCload
        )

    def readPollutantLoadings(self, currTimeStep):
        # use precalculated pollutant loadings
        logger.info("Reading loadings directly")

        # TDS loadings (all sectors combined)
        self.TDSload = vos.netcdf2PCRobjClone(
            self.TDSloadNC,
            "TDSload",
            str(currTimeStep.fulldate),
            useDoy=None,
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
        )
        self.TDSload = pcr.ifthen(self.landmask, self.TDSload)

        # BOD loadings (all sectors combined)
        self.BODload = vos.netcdf2PCRobjClone(
            self.BODloadNC,
            "BODload",
            str(currTimeStep.fulldate),
            useDoy=None,
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
        )
        self.BODload = pcr.ifthen(self.landmask, self.BODload)

        # FC loadings (all sectors combined)
        self.FCload = vos.netcdf2PCRobjClone(
            self.FCloadNC,
            "FCload",
            str(currTimeStep.fulldate),
            useDoy=None,
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
        )
        self.FCload = pcr.ifthen(self.landmask, self.FCload)

    def qualityLocal(
        self, meteo, landSurface, groundwater, currTimeStep, timeSec=vos.secondsPerDay()
    ):

        # water temperature: surface water energy fluxes (W/m2) within the current time step; ice formation
        # is evaluated before routing to account for the loss in water height, the vertical energy change is
        # evaluated and warming is capped at the air temperature

        # constants and variables
        self.temperatureKelvin = meteo.temperature + pcr.scalar(273.15)
        landRunoff = self.runoff
        self.correctPrecip = pcr.scalar(0.0)
        self.dynamicFracWatBeforeRouting = self.dynamicFracWat

        # land temperature considering the runoff fractions
        landT = pcr.cover(
            landSurface.directRunoff
            / landRunoff
            * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin - self.deltaTPrec)
            + landSurface.interflowTotal
            / landRunoff
            * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin)
            + groundwater.baseflow
            / landRunoff
            * pcr.max(self.iceThresTemp + 5.0, self.annualT),
            self.temperatureKelvin,
        )

        # heat transfer (ice and water)
        iceHeatTransfer = self.heatTransferWater * (
            self.temperatureKelvin - self.iceThresTemp
        )
        waterHeatTransfer = self.heatTransferIce * (self.iceThresTemp - self.waterTemp)

        # check for ice
        noIce = pcr.ifthenelse(
            self.iceThickness > 0,
            pcr.boolean(0),
            pcr.ifthenelse(
                ((iceHeatTransfer - waterHeatTransfer) < 0)
                & (self.temperatureKelvin < self.iceThresTemp),
                pcr.boolean(0),
                pcr.boolean(1),
            ),
        )

        # update the water heat transfer based on the presence of ice
        waterHeatTransfer = pcr.ifthenelse(
            noIce,
            self.heatTransferWater * (self.temperatureKelvin - self.waterTemp),
            waterHeatTransfer,
        )

        # radiative heat transfer
        radiativHeatTransfer = (
            1 - pcr.ifthenelse(noIce, self.albedoWater, self.albedoSnow)
        ) * self.rsw
        radiativHeatTransfer -= self.stefanBoltzman * (
            pcr.ifthenelse(noIce, self.waterTemp, self.iceThresTemp) ** 4
            - self.atmosEmis * self.temperatureKelvin**4
        )

        # advected energy due to precipitation and inflow
        advectedEnergyPrecip = (
            pcr.max(0, self.correctPrecip)
            * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin - self.deltaTPrec)
            * self.specificHeatWater
            * self.densityWater
            / timeSec
        )
        advectedEnergyInflow = (
            (1 - self.dynamicFracWat)
            / self.dynamicFracWat
            * landRunoff
            * landT
            * self.specificHeatWater
            * self.densityWater
            / timeSec
        )
        advectedEnergyInflow -= (
            landSurface.actSurfaceWaterAbstract
            / self.dynamicFracWat
            * self.waterTemp
            * self.specificHeatWater
            * self.densityWater
            / timeSec
        )

        # ice formation and thickness
        diceHeatTransfer = pcr.ifthenelse(
            noIce, 0, iceHeatTransfer - waterHeatTransfer + radiativHeatTransfer
        )
        self.deltaIceThickness = (
            -diceHeatTransfer * timeSec / (self.densityWater * self.latentHeatFusion)
        )
        self.deltaIceThickness = pcr.max(-self.iceThickness, self.deltaIceThickness)
        self.deltaIceThickness = pcr.min(
            self.deltaIceThickness, pcr.max(0, self.maxIceThickness - self.iceThickness)
        )

        # direct gain over the water surface
        watQ = pcr.ifthenelse(
            self.temperatureKelvin >= self.iceThresTemp,
            pcr.max(0, self.correctPrecip)
            - self.waterBodyEvaporation / self.dynamicFracWat,
            0,
        )
        # TODO: move
        self.waterBodyEvaporation = pcr.ifthenelse(
            self.temperatureKelvin >= self.iceThresTemp, self.waterBodyEvaporation, 0
        )

        # vertical gains/losses
        deltaIceThickness_melt = pcr.max(0, -self.deltaIceThickness)
        verticalGain = (
            watQ
            + (landRunoff - landSurface.actSurfaceWaterAbstract) / (self.dynamicFracWat)
            + deltaIceThickness_melt
        )

        # water storage change
        dtotStorLoc = verticalGain
        totStorLoc = (
            self.channelStorageTimeBefore / (self.dynamicFracWat * self.cellArea)
            - dtotStorLoc
        )
        totStorLoc = (
            self.return_water_body_storage_to_channel(self.channelStorageTimeBefore)
            / (self.dynamicFracWat * self.cellArea)
            - dtotStorLoc
        )

        # energy in the channel
        self.totEW = (
            totStorLoc * self.waterTemp * self.specificHeatWater * self.densityWater
        )
        dtotStorLoc = pcr.max(-totStorLoc, dtotStorLoc)

        # latent heat flux and advected energy of water evaporation
        latentHeat = (
            -self.waterBodyEvaporation
            / self.dynamicFracWat
            * self.densityWater
            * self.latentHeatVapor
            / timeSec
        )
        advectedEnergyPrecip += (
            deltaIceThickness_melt
            * self.iceThresTemp
            * self.specificHeatWater
            * self.densityWater
            / timeSec
        )

        # total energy change
        totEWC = totStorLoc * self.specificHeatWater * self.densityWater
        dtotEWC = dtotStorLoc * self.specificHeatWater * self.densityWater
        dtotEWLoc = (
            waterHeatTransfer + pcr.scalar(noIce) * (radiativHeatTransfer + latentHeat)
        ) * timeSec
        dtotEWAdv = (advectedEnergyInflow + advectedEnergyPrecip) * timeSec

        dtotEWLoc = pcr.min(
            dtotEWLoc,
            pcr.max(0, totEWC * self.temperatureKelvin - self.totEW)
            + pcr.ifthenelse(
                dtotStorLoc > 0,
                pcr.max(0, dtotEWC * self.temperatureKelvin - dtotEWAdv),
                0,
            ),
        )
        dtotEWLoc = pcr.ifthenelse(
            self.waterTemp > self.temperatureKelvin, pcr.min(0, dtotEWLoc), dtotEWLoc
        )
        dtotEWLoc = pcr.max(
            dtotEWLoc,
            pcr.min(
                0,
                (totEWC + dtotEWC)
                * pcr.max(self.temperatureKelvin, self.iceThresTemp + 0.1)
                - (self.totEW + dtotEWAdv),
            ),
        )

        # update the water height, energy and water temperature
        self.temp_water_height = pcr.max(1e-16, totStorLoc + dtotStorLoc)
        self.totEW = pcr.max(0, self.totEW + dtotEWLoc + dtotEWAdv)

        # temporary fix for an error in the water temperature in the first time step
        if currTimeStep.timeStepPCR != 1:
            self.waterTemp = pcr.ifthenelse(
                self.temp_water_height > self.critical_water_height,
                self.totEW
                / self.temp_water_height
                / (self.specificHeatWater * self.densityWater),
                self.temperatureKelvin,
            )
        self.waterTemp = min(
            pcr.ifthenelse(
                self.waterTemp < self.iceThresTemp + 0.1,
                self.iceThresTemp + 0.1,
                self.waterTemp,
            ),
            self.maxThresTemp,
        )
        # water temperature (degC)
        self.waterTemp_C = self.waterTemp - pcr.scalar(273.15)

        # BOD (non-conservative; depends on water temperature only): temperature-dependent decay
        self.BODdecay_temperature = cover(
            self.k_BOD * (self.watertempcorrection_BOD ** (self.waterTemp_C - 20)), 0.0
        )

        # FC (non-conservative; depends on temperature, solar radiation and sedimentation): temperature-dependent decay
        self.FCdecay_temperature = cover(
            self.darkinactivation_FC
            * (self.watertempcorrection_FC ** (self.waterTemp_C - 20)),
            0.0,
        )

        # solar radiation dependent decay, with a minimum water depth of 0.1 m for the decay coefficients
        self.water_height_pathogen = pcr.max(self.water_height, 0.1)
        self.FCdecay_solarradiation = cover(
            self.sunlightinactivation_FC
            * (self.rsw / (self.attenuation_FC * self.water_height_pathogen))
            * (1 - (exp(-(self.attenuation_FC * self.water_height_pathogen)))),
            0.0,
        )

        # sedimentation (day-1)
        self.FCdecay_sedimentation = pcr.ifthenelse(
            self.water_height_pathogen > self.threshold_FC_settlingdepth,
            cover(self.settlingvelocity_FC / self.water_height, 0.0),
            0,
        )

    def qualityRouting(self, timeSec):

        channelTransFrac = cover(
            pcr.max(
                pcr.min(
                    (self.subDischarge * timeSec) / self.channelStorageTimeBefore, 1.0
                ),
                0.0,
            ),
            0.0,
        )

        # energy (water temperature) routing, adding heat effluents from power plants (J per timeSec)
        self.volumeEW = self.volumeEW + (
            self.PowTwload * (timeSec / vos.secondsPerDay())
        )
        dtotEWLat = channelTransFrac * self.volumeEW
        self.volumeEW = self.volumeEW + pcr.upstream(self.lddMap, dtotEWLat) - dtotEWLat

        # salinity (TDS) routing
        self.routedTDS = self.routedTDS + (
            self.TDSload * (timeSec / vos.secondsPerDay())
        )
        dTDSLat = channelTransFrac * self.routedTDS
        self.routedTDS = self.routedTDS + pcr.upstream(self.lddMap, dTDSLat) - dTDSLat

        if self.loadsPerSector:
            self.routedDomTDS = self.routedDomTDS + (
                self.Dom_TDSload * (timeSec / vos.secondsPerDay())
            )
            dDomTDSLat = channelTransFrac * self.routedDomTDS
            self.routedDomTDS = (
                self.routedDomTDS + pcr.upstream(self.lddMap, dDomTDSLat) - dDomTDSLat
            )

            self.routedManTDS = self.routedManTDS + (
                self.Man_TDSload * (timeSec / vos.secondsPerDay())
            )
            dManTDSLat = channelTransFrac * self.routedManTDS
            self.routedManTDS = (
                self.routedManTDS + pcr.upstream(self.lddMap, dManTDSLat) - dManTDSLat
            )

            self.routedUSRTDS = self.routedUSRTDS + (
                self.USR_TDSload * (timeSec / vos.secondsPerDay())
            )
            dUSRTDSLat = channelTransFrac * self.routedUSRTDS
            self.routedUSRTDS = (
                self.routedUSRTDS + pcr.upstream(self.lddMap, dUSRTDSLat) - dUSRTDSLat
            )

            self.routedIrrTDS = self.routedIrrTDS + (
                self.Irr_TDSload * (timeSec / vos.secondsPerDay())
            )
            dIrrTDSLat = channelTransFrac * self.routedIrrTDS
            self.routedIrrTDS = (
                self.routedIrrTDS + pcr.upstream(self.lddMap, dIrrTDSLat) - dIrrTDSLat
            )

        # organic (BOD) routing
        self.routedBOD = self.routedBOD + (
            self.BODload * (timeSec / vos.secondsPerDay())
        )
        dBODLat = channelTransFrac * self.routedBOD
        self.BODdecay = exp(
            -(self.BODdecay_temperature) * (timeSec / vos.secondsPerDay())
        )
        self.routedBOD = (
            self.routedBOD + pcr.upstream(self.lddMap, dBODLat) - dBODLat
        ) * self.BODdecay

        if self.loadsPerSector:
            self.routedDomBOD = self.routedDomBOD + (
                self.Dom_BODload * (timeSec / vos.secondsPerDay())
            )
            dDomBODLat = channelTransFrac * self.routedDomBOD
            self.routedDomBOD = (
                self.routedDomBOD + pcr.upstream(self.lddMap, dDomBODLat) - dDomBODLat
            ) * self.BODdecay

            self.routedManBOD = self.routedManBOD + (
                self.Man_BODload * (timeSec / vos.secondsPerDay())
            )
            dManBODLat = channelTransFrac * self.routedManBOD
            self.routedManBOD = (
                self.routedManBOD + pcr.upstream(self.lddMap, dManBODLat) - dManBODLat
            ) * self.BODdecay

            self.routedUSRBOD = self.routedUSRBOD + (
                self.USR_BODload * (timeSec / vos.secondsPerDay())
            )
            dUSRBODLat = channelTransFrac * self.routedUSRBOD
            self.routedUSRBOD = (
                self.routedUSRBOD + pcr.upstream(self.lddMap, dUSRBODLat) - dUSRBODLat
            ) * self.BODdecay

            self.routedintLivBOD = self.routedintLivBOD + (
                self.intLiv_BODload * (timeSec / vos.secondsPerDay())
            )
            dintLivBODLat = channelTransFrac * self.routedintLivBOD
            self.routedintLivBOD = (
                self.routedintLivBOD
                + pcr.upstream(self.lddMap, dintLivBODLat)
                - dintLivBODLat
            ) * self.BODdecay

            self.routedextLivBOD = self.routedextLivBOD + (
                self.extLiv_BODload * (timeSec / vos.secondsPerDay())
            )
            dextLivBODLat = channelTransFrac * self.routedextLivBOD
            self.routedextLivBOD = (
                self.routedextLivBOD
                + pcr.upstream(self.lddMap, dextLivBODLat)
                - dextLivBODLat
            ) * self.BODdecay

        # pathogen (FC) routing
        self.routedFC = self.routedFC + (self.FCload * (timeSec / vos.secondsPerDay()))
        dFCLat = channelTransFrac * self.routedFC
        self.FCdecay = exp(
            -(
                self.FCdecay_temperature
                + self.FCdecay_solarradiation
                + self.FCdecay_sedimentation
            )
            * (timeSec / vos.secondsPerDay())
        )
        self.routedFC = (
            self.routedFC + pcr.upstream(self.lddMap, dFCLat) - dFCLat
        ) * self.FCdecay

        if self.loadsPerSector:
            self.routedDomFC = self.routedDomFC + (
                self.Dom_FCload * (timeSec / vos.secondsPerDay())
            )
            dDomFCLat = channelTransFrac * self.routedDomFC
            self.routedDomFC = (
                self.routedDomFC + pcr.upstream(self.lddMap, dDomFCLat) - dDomFCLat
            ) * self.FCdecay

            self.routedManFC = self.routedManFC + (
                self.Man_FCload * (timeSec / vos.secondsPerDay())
            )
            dManFCLat = channelTransFrac * self.routedManFC
            self.routedManFC = (
                self.routedManFC + pcr.upstream(self.lddMap, dManFCLat) - dManFCLat
            ) * self.FCdecay

            self.routedUSRFC = self.routedUSRFC + (
                self.USR_FCload * (timeSec / vos.secondsPerDay())
            )
            dUSRFCLat = channelTransFrac * self.routedUSRFC
            self.routedUSRFC = (
                self.routedUSRFC + pcr.upstream(self.lddMap, dUSRFCLat) - dUSRFCLat
            ) * self.FCdecay

            self.routedintLivFC = self.routedintLivFC + (
                self.intLiv_FCload * (timeSec / vos.secondsPerDay())
            )
            dintLivFCLat = channelTransFrac * self.routedintLivFC
            self.routedintLivFC = (
                self.routedintLivFC
                + pcr.upstream(self.lddMap, dintLivFCLat)
                - dintLivFCLat
            ) * self.FCdecay

            self.routedextLivFC = self.routedextLivFC + (
                self.extLiv_FCload * (timeSec / vos.secondsPerDay())
            )
            dextLivFCLat = channelTransFrac * self.routedextLivFC
            self.routedextLivFC = (
                self.routedextLivFC
                + pcr.upstream(self.lddMap, dextLivFCLat)
                - dextLivFCLat
            ) * self.FCdecay

    def qualityWaterBody(self):

        lakeTransFrac = pcr.max(
            pcr.min(
                (self.WaterBodies.waterBodyOutflow) / (self.waterBodyStorageTimeBefore),
                1.0,
            ),
            0.0,
        )
        lakeTransFrac = cover(ifthen(self.WaterBodies.waterBodyOut, lakeTransFrac), 0.0)

        # water temperature (energy in the water body)
        energyTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(
                        self.landmask, self.totEW * self.dynamicFracWat * self.cellArea
                    ),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.totEW * self.dynamicFracWat * self.cellArea,
        )
        self.volumeEW = cover(
            ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                energyTotal * lakeTransFrac,
            ),
            energyTotal,
        )
        self.remainingVolumeEW = cover(
            ifthen(self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * energyTotal),
            0.0,
        )

        # salinity (TDS in the water body)
        wbTDSTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedTDS),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedTDS,
        )
        self.routedTDS = cover(
            ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                wbTDSTotal * lakeTransFrac,
            ),
            wbTDSTotal,
        )
        self.wbRemainingTDS = cover(
            ifthen(self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbTDSTotal), 0.0
        )

        if self.loadsPerSector:
            wbDomTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedDomTDS),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomTDS,
            )
            self.routedDomTDS = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbDomTDSTotal * lakeTransFrac,
                ),
                wbDomTDSTotal,
            )
            self.wbRemainingDomTDS = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbDomTDSTotal
                ),
                0.0,
            )

            wbManTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedManTDS),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManTDS,
            )
            self.routedManTDS = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbManTDSTotal * lakeTransFrac,
                ),
                wbManTDSTotal,
            )
            self.wbRemainingManTDS = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbManTDSTotal
                ),
                0.0,
            )

            wbUSRTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedUSRTDS),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRTDS,
            )
            self.routedUSRTDS = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbUSRTDSTotal * lakeTransFrac,
                ),
                wbUSRTDSTotal,
            )
            self.wbRemainingUSRTDS = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbUSRTDSTotal
                ),
                0.0,
            )

            wbIrrTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedIrrTDS),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedIrrTDS,
            )
            self.routedIrrTDS = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbIrrTDSTotal * lakeTransFrac,
                ),
                wbIrrTDSTotal,
            )
            self.wbRemainingIrrTDS = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbIrrTDSTotal
                ),
                0.0,
            )

        # organic (BOD in the water body)
        wbBODTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedBOD),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedBOD,
        )
        self.routedBOD = cover(
            ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                wbBODTotal * lakeTransFrac,
            ),
            wbBODTotal,
        )
        self.wbRemainingBOD = cover(
            ifthen(self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbBODTotal), 0.0
        )

        if self.loadsPerSector:
            wbDomBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedDomBOD),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomBOD,
            )
            self.routedDomBOD = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbDomBODTotal * lakeTransFrac,
                ),
                wbDomBODTotal,
            )
            self.wbRemainingDomBOD = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbDomBODTotal
                ),
                0.0,
            )

            wbManBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedManBOD),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManBOD,
            )
            self.routedManBOD = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbManBODTotal * lakeTransFrac,
                ),
                wbManBODTotal,
            )
            self.wbRemainingManBOD = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbManBODTotal
                ),
                0.0,
            )

            wbUSRBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedUSRBOD),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRBOD,
            )
            self.routedUSRBOD = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbUSRBODTotal * lakeTransFrac,
                ),
                wbUSRBODTotal,
            )
            self.wbRemainingUSRBOD = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbUSRBODTotal
                ),
                0.0,
            )

            wbintLivBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedintLivBOD),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedintLivBOD,
            )
            self.routedintLivBOD = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbintLivBODTotal * lakeTransFrac,
                ),
                wbintLivBODTotal,
            )
            self.wbRemainingintLivBOD = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut,
                    (1 - lakeTransFrac) * wbintLivBODTotal,
                ),
                0.0,
            )

            wbextLivBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedextLivBOD),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedextLivBOD,
            )
            self.routedextLivBOD = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbextLivBODTotal * lakeTransFrac,
                ),
                wbextLivBODTotal,
            )
            self.wbRemainingextLivBOD = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut,
                    (1 - lakeTransFrac) * wbextLivBODTotal,
                ),
                0.0,
            )

        # pathogen (FC in the water body)
        wbFCTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedFC),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedFC,
        )
        self.routedFC = cover(
            ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                wbFCTotal * lakeTransFrac,
            ),
            wbFCTotal,
        )
        self.wbRemainingFC = cover(
            ifthen(self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbFCTotal), 0.0
        )

        if self.loadsPerSector:
            wbDomFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedDomFC),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomFC,
            )
            self.routedDomFC = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbDomFCTotal * lakeTransFrac,
                ),
                wbDomFCTotal,
            )
            self.wbRemainingDomFC = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbDomFCTotal
                ),
                0.0,
            )

            wbManFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedManFC),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManFC,
            )
            self.routedManFC = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbManFCTotal * lakeTransFrac,
                ),
                wbManFCTotal,
            )
            self.wbRemainingManFC = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbManFCTotal
                ),
                0.0,
            )

            wbUSRFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedUSRFC),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRFC,
            )
            self.routedUSRFC = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbUSRFCTotal * lakeTransFrac,
                ),
                wbUSRFCTotal,
            )
            self.wbRemainingUSRFC = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbUSRFCTotal
                ),
                0.0,
            )

            wbintLivFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedintLivFC),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedintLivFC,
            )
            self.routedintLivFC = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbintLivFCTotal * lakeTransFrac,
                ),
                wbintLivFCTotal,
            )
            self.wbRemainingintLivFC = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbintLivFCTotal
                ),
                0.0,
            )

            wbextLivFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(self.landmask, self.routedextLivFC),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedextLivFC,
            )
            self.routedextLivFC = cover(
                ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    wbextLivFCTotal * lakeTransFrac,
                ),
                wbextLivFCTotal,
            )
            self.wbRemainingextLivFC = cover(
                ifthen(
                    self.WaterBodies.waterBodyOut, (1 - lakeTransFrac) * wbextLivFCTotal
                ),
                0.0,
            )

    def qualityWaterBodyAverage(self, currTimeStep):

        # water temperature (energy averaged over the water body)
        self.totalVolumeEW = self.volumeEW + self.remainingVolumeEW

        energyTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.totalVolumeEW),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.totalVolumeEW,
        )
        energyAverageLakeCell = cover(
            energyTotal
            * self.cellArea
            / pcr.areatotal(
                pcr.cover(self.cellArea, 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            ),
            energyTotal,
        )
        self.totEW = cover(
            energyAverageLakeCell / (self.dynamicFracWat * self.cellArea), 1e-16
        )

        self.temp_water_height = self.return_water_body_storage_to_channel(
            self.channelStorageNow
        ) / (self.dynamicFracWat * self.cellArea)

        iceReductionFactor = ifthen(
            self.landmask,
            cover(self.dynamicFracWatBeforeRouting / self.dynamicFracWat, 1.0),
        )

        self.deltaIceThickness = iceReductionFactor * self.deltaIceThickness
        self.deltaIceThickness = pcr.min(self.deltaIceThickness, self.temp_water_height)

        self.iceThickness = iceReductionFactor * self.iceThickness
        self.iceThickness = pcr.max(
            0,
            self.iceThickness
            + (
                self.deltaIceThickness
                + pcr.ifthenelse(
                    self.temperatureKelvin >= self.iceThresTemp, 0, self.correctPrecip
                )
            ),
        )
        self.iceThickness = pcr.ifthenelse(
            (self.iceThickness <= 0.001) & (self.deltaIceThickness < 0),
            0,
            self.iceThickness,
        )
        self.iceThickness = pcr.min(self.iceThickness, self.maxIceThickness)

        self.channelStorageNow = (
            self.channelStorageNow
            - self.deltaIceThickness * self.dynamicFracWat * self.cellArea
        )

        if currTimeStep.timeStepPCR == 1:
            logger.info(
                "Issue with estimating water temperature in first timestep: retrieving water temperature from initial condition"
            )
        else:
            self.waterTemp = pcr.ifthenelse(
                self.temp_water_height > self.critical_water_height,
                self.totEW
                / self.temp_water_height
                / (self.specificHeatWater * self.densityWater),
                self.temperatureKelvin,
            )

        self.waterTemp = min(
            pcr.ifthenelse(
                self.waterTemp < self.iceThresTemp + 0.1,
                self.iceThresTemp + 0.1,
                self.waterTemp,
            ),
            self.maxThresTemp,
        )
        # water temperature (degC)
        self.waterTemp_C = self.waterTemp - pcr.scalar(273.15)

        # salinity (TDS averaged over the water body)
        wbTDSTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedTDS + self.wbRemainingTDS),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedTDS,
        )
        self.routedTDS = cover(
            wbTDSTotal
            * self.cellArea
            / pcr.areatotal(
                pcr.cover(self.cellArea, 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            ),
            wbTDSTotal,
        )

        if self.loadsPerSector:
            wbDomTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedDomTDS + self.wbRemainingDomTDS
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomTDS,
            )
            self.routedDomTDS = cover(
                wbDomTDSTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbDomTDSTotal,
            )

            wbManTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedManTDS + self.wbRemainingManTDS
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManTDS,
            )
            self.routedManTDS = cover(
                wbManTDSTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbManTDSTotal,
            )

            wbUSRTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedUSRTDS + self.wbRemainingUSRTDS
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRTDS,
            )
            self.routedUSRTDS = cover(
                wbUSRTDSTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbUSRTDSTotal,
            )

            wbIrrTDSTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedIrrTDS + self.wbRemainingIrrTDS
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedIrrTDS,
            )
            self.routedIrrTDS = cover(
                wbIrrTDSTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbIrrTDSTotal,
            )

        # organic (BOD averaged over the water body)
        wbBODTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedBOD + self.wbRemainingBOD),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedBOD,
        )
        self.routedBOD = cover(
            wbBODTotal
            * self.cellArea
            / pcr.areatotal(
                pcr.cover(self.cellArea, 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            ),
            wbBODTotal,
        )

        if self.loadsPerSector:
            wbDomBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedDomBOD + self.wbRemainingDomBOD
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomBOD,
            )
            self.routedDomBOD = cover(
                wbDomBODTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbDomBODTotal,
            )

            wbManBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedManBOD + self.wbRemainingManBOD
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManBOD,
            )
            self.routedManBOD = cover(
                wbManBODTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbManBODTotal,
            )

            wbUSRBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedUSRBOD + self.wbRemainingUSRBOD
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRBOD,
            )
            self.routedUSRBOD = cover(
                wbUSRBODTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbUSRBODTotal,
            )

            wbintLivBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask,
                            self.routedintLivBOD + self.wbRemainingintLivBOD,
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedintLivBOD,
            )
            self.routedintLivBOD = cover(
                wbintLivBODTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbintLivBODTotal,
            )

            wbextLivBODTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask,
                            self.routedextLivBOD + self.wbRemainingextLivBOD,
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedextLivBOD,
            )
            self.routedextLivBOD = cover(
                wbextLivBODTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbextLivBODTotal,
            )

        # pathogen (FC averaged over the water body)
        wbFCTotal = cover(
            pcr.ifthen(
                pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                pcr.areatotal(
                    pcr.ifthen(self.landmask, self.routedFC + self.wbRemainingFC),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
            ),
            self.routedFC,
        )
        self.routedFC = cover(
            wbFCTotal
            * self.cellArea
            / pcr.areatotal(
                pcr.cover(self.cellArea, 0.0),
                pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
            ),
            wbFCTotal,
        )

        if self.loadsPerSector:
            wbDomFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedDomFC + self.wbRemainingDomFC
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedDomFC,
            )
            self.routedDomFC = cover(
                wbDomFCTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbDomFCTotal,
            )

            wbManFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedManFC + self.wbRemainingManFC
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedManFC,
            )
            self.routedManFC = cover(
                wbManFCTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbManFCTotal,
            )

            wbUSRFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask, self.routedUSRFC + self.wbRemainingUSRFC
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedUSRFC,
            )
            self.routedUSRFC = cover(
                wbUSRFCTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbUSRFCTotal,
            )

            wbintLivFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask,
                            self.routedintLivFC + self.wbRemainingintLivFC,
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedintLivFC,
            )
            self.routedintLivFC = cover(
                wbintLivFCTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbintLivFCTotal,
            )

            wbextLivFCTotal = cover(
                pcr.ifthen(
                    pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                    pcr.areatotal(
                        pcr.ifthen(
                            self.landmask,
                            self.routedextLivFC + self.wbRemainingextLivFC,
                        ),
                        pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                    ),
                ),
                self.routedextLivFC,
            )
            self.routedextLivFC = cover(
                wbextLivFCTotal
                * self.cellArea
                / pcr.areatotal(
                    pcr.cover(self.cellArea, 0.0),
                    pcr.ifthen(self.landmask, self.WaterBodies.waterBodyIds),
                ),
                wbextLivFCTotal,
            )

    def estimate_concentrations(self):

        # channel storage with discharge threshold, to estimate in-stream concentrations
        self.channelStorage_Qthres = pcr.ifthenelse(
            pcr.cover(self.disChanWaterBody, vos.MV) > self.WQ_discharge_threshold,
            self.channelStorage,
            vos.MV,
        )

        # total dissolved solids concentration, salinity indicator (mg/L)
        self.salinity = pcr.ifthenelse(
            self.channelStorage_Qthres != vos.MV,
            (self.routedTDS / self.channelStorage_Qthres) + self.backgroundSalinity,
            vos.MV,
        )

        # biochemical oxygen demand concentration, organic indicator (mg/L)
        self.organic = pcr.ifthenelse(
            self.channelStorage_Qthres != vos.MV,
            self.routedBOD / self.channelStorage_Qthres,
            vos.MV,
        )

        # dissolved oxygen concentration (Streeter-Phelps equation)
        self.k1 = self.BODdecay_temperature * self.organic
        # oxygen saturation (mg/L)
        self.DOsat = (1 - 0.0001148 * self.elevation) * exp(
            -139.34411
            + (157570.1) / (self.waterTemp)
            - (66423080.0) / (self.waterTemp**2)
            + (12438000000.0) / (self.waterTemp**3)
            - (862194900000.0) / (self.waterTemp**4)
        )
        # velocity assuming a rectangular channel (m/s)
        self.velocity = self.avgDischarge / (self.yMean * self.wMean)
        # reaeration rate (day-1; O'Connor and Dobbins, 1958)
        self.k2 = 3.93 * (self.velocity**0.5) / (self.yMean**1.5)
        self.k2 = pcr.ifthenelse(
            self.k2 > 1.5, 1.5, pcr.ifthenelse(self.k2 < 0.4, 0.4, self.k2)
        )
        self.dissolved_oxygen = pcr.ifthenelse(
            self.dissolved_oxygen
            - self.k1
            + self.k2 * (self.DOsat - self.dissolved_oxygen)
            < 0.0,
            0.0,
            self.dissolved_oxygen
            - self.k1
            + self.k2 * (self.DOsat - self.dissolved_oxygen),
        )
        # dissolved oxygen concentration (mg/L)
        self.dissolved_oxygen = pcr.ifthenelse(
            self.channelStorage_Qthres != vos.MV, self.dissolved_oxygen, vos.MV
        )

        # fecal coliform concentration, pathogen indicator (cfu/100mL)
        self.pathogen = pcr.ifthenelse(
            self.channelStorage_Qthres != vos.MV,
            self.routedFC * 100.0 / self.channelStorage_Qthres,
            vos.MV,
        )
