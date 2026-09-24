import logging
import os

import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class IrrigationWaterDemand(object):

    def __init__(
        self,
        iniItems,
        nameOfSectionInIniFileThatIsRellevantForThisIrrLC,
        landmask,
        landCoverObject,
    ):
        object.__init__(self)

        self.iniItems = iniItems

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        self.iniItemsIrrLC = iniItems.__getattribute__(
            nameOfSectionInIniFileThatIsRellevantForThisIrrLC
        )

        self.name = self.iniItemsIrrLC["name"]

        # 'static' parameters (mainly soil and topography)
        self.parameters = landCoverObject.parameters

        # inundation height allowed within this land cover
        self.minTopWaterLayer = landCoverObject.minTopWaterLayer

        self.cropDeplFactor = vos.readPCRmapClone(
            self.iniItemsIrrLC["cropDeplFactor"],
            self.cloneMap,
            self.tmpDir,
            self.inputDir,
        )

        self.numberOfLayers = landCoverObject.numberOfLayers

        self.maxRootDepth = landCoverObject.maxRootDepth

        # water capacity within the root zone (sets self.totAvlWater)
        self.calculateTotAvlWaterCapacityInRootZone()

        # irrigation efficiency input (value or file name)
        self.ini_items_for_irrigation_efficiency = None
        # by default, use the one in waterDemandOptions
        if "irrigationEfficiency" in self.iniItems.waterDemandOptions.keys():
            self.ini_items_for_irrigation_efficiency = self.iniItems.waterDemandOptions[
                "irrigationEfficiency"
            ]
        # a specific one in the landCoverOptions takes precedence
        if "irrigationEfficiency" in self.iniItemsIrrLC.keys():
            self.ini_items_for_irrigation_efficiency = self.iniItemsIrrLCOptions[
                "irrigationEfficiency"
            ]
        # otherwise, use 1.0
        if self.ini_items_for_irrigation_efficiency is None:
            logger.info("'irrigationEfficiency' is not defined, we set this to 1.0")
            self.ini_items_for_irrigation_efficiency = "1.0"

        # needed in updateLC
        self.includeIrrigation = True

    def get_irrigation_efficiency(self, currTimeStep):
        # irrigation efficiency map (%); TODO: use a time series of efficiency (historical technological development)
        # PCRaster map
        if self.ini_items_for_irrigation_efficiency.endswith(".map"):
            self.irrigationEfficiency = vos.readPCRmapClone(
                self.ini_items_for_irrigation_efficiency,
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        # netCDF file
        elif "nc" in os.path.splitext(self.ini_items_for_irrigation_efficiency)[1]:
            try:
                # netCDF file with a time dimension
                ncFileIn = vos.getFullPath(
                    self.ini_items_for_irrigation_efficiency, self.inputDir
                )
                self.irrigationEfficiency = vos.netcdf2PCRobjClone(
                    ncFileIn,
                    "automatic",
                    currTimeStep,
                    useDoy="yearly",
                    cloneMapFileName=self.cloneMap,
                )

            except Exception:
                # netCDF file without a time dimension
                msg = (
                    "The file "
                    + (ncFileIn)
                    + " has no time dimension. Constant values will be used."
                )
                logger.warning(msg)
                self.irrigationEfficiency = vos.readPCRmapClone(
                    self.ini_items_for_irrigation_efficiency,
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            # TODO: remove try/except
        else:
            # constant value
            self.irrigationEfficiency = float(self.ini_items_for_irrigation_efficiency)

        extrapolate = True
        if (
            "noParameterExtrapolation" in self.iniItems.landSurfaceOptions.keys()
            and self.iniItems.landSurfaceOptions["noParameterExtrapolation"] == "True"
        ):
            extrapolate = False

        if extrapolate:
            # extrapolate the efficiency map; TODO: better extrapolation (considering cell size etc.)
            window_size = 1.25 * pcr.clone().cellSize()
            window_size = min(
                window_size,
                min(pcr.clone().nrRows(), pcr.clone().nrCols())
                * pcr.clone().cellSize(),
            )
            try:
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, window_size),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, window_size),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, window_size),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, window_size),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, window_size),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, 0.75),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, 1.00),
                )
                self.irrigationEfficiency = pcr.cover(
                    self.irrigationEfficiency,
                    pcr.windowaverage(self.irrigationEfficiency, 1.50),
                )
            except Exception:
                pass

        self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, 1.0)
        self.irrigationEfficiency = pcr.max(0.1, self.irrigationEfficiency)
        self.irrigationEfficiency = pcr.ifthen(self.landmask, self.irrigationEfficiency)

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
            max_percolation_loss = vos.readPCRmapClone(
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

    def calculateTotAvlWaterCapacityInRootZone(self):
        # total water capacity in the root zone (upper soil layers); depends on the land cover type

        if self.numberOfLayers == 2:
            # Edwin uses the soil thicknesses thickUpp and thickLow instead of storCapUpp and storCapLow
            self.totAvlWater = (
                pcr.max(
                    0.0,
                    self.parameters.effSatAtFieldCapUpp
                    - self.parameters.effSatAtWiltPointUpp,
                )
            ) * (
                self.parameters.satVolMoistContUpp - self.parameters.resVolMoistContUpp
            ) * pcr.min(
                self.parameters.thickUpp, self.maxRootDepth
            ) + (
                pcr.max(
                    0.0,
                    self.parameters.effSatAtFieldCapLow
                    - self.parameters.effSatAtWiltPointLow,
                )
            ) * (
                self.parameters.satVolMoistContLow - self.parameters.resVolMoistContLow
            ) * pcr.min(
                self.parameters.thickLow,
                pcr.max(self.maxRootDepth - self.parameters.thickUpp, 0.0),
            )
            # (supported by Rens)
            self.totAvlWater = pcr.min(
                self.totAvlWater,
                self.parameters.storCapUpp + self.parameters.storCapLow,
            )

        if self.numberOfLayers == 3:
            self.totAvlWater = (
                (
                    pcr.max(
                        0.0,
                        self.parameters.effSatAtFieldCapUpp000005
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
                        self.parameters.effSatAtFieldCapUpp005030
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
                        self.parameters.effSatAtFieldCapLow030150
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
            self.totAvlWater = pcr.min(
                self.totAvlWater,
                self.parameters.storCapUpp000005
                + self.parameters.storCapUpp005030
                + self.parameters.storCapLow030150,
            )

    def get_readily_available_water_within_the_root_zone(self):

        if self.numberOfLayers == 2:
            effSatUpp = vos.getValDivZero(self.storUpp, self.parameters.storCapUpp)
            effSatLow = vos.getValDivZero(self.storLow, self.parameters.storCapLow)
            effSatUpp = pcr.min(1.0, effSatUpp)
            effSatLow = pcr.min(1.0, effSatLow)

            # readily available water in the root zone (upper soil layers)
            readAvlWater = (
                pcr.max(0.0, effSatUpp - self.parameters.effSatAtWiltPointUpp)
            ) * (
                self.parameters.satVolMoistContUpp - self.parameters.resVolMoistContUpp
            ) * pcr.min(
                self.parameters.thickUpp, self.maxRootDepth
            ) + (
                pcr.max(0.0, effSatLow - self.parameters.effSatAtWiltPointLow)
            ) * (
                self.parameters.satVolMoistContLow - self.parameters.resVolMoistContLow
            ) * pcr.min(
                self.parameters.thickLow,
                pcr.max(self.maxRootDepth - self.parameters.thickUpp, 0.0),
            )

        if self.numberOfLayers == 3:
            # effective degree of saturation (-)
            effSatUpp000005 = vos.getValDivZero(
                self.storUpp000005, self.parameters.storCapUpp000005
            )
            effSatUpp005030 = vos.getValDivZero(
                self.storUpp005030, self.parameters.storCapUpp005030
            )
            effSatLow030150 = vos.getValDivZero(
                self.storLow030150, self.parameters.storCapLow030150
            )
            effSatUpp000005 = pcr.min(1.0, effSatUpp000005)
            effSatUpp005030 = pcr.min(1.0, effSatUpp005030)
            effSatLow030150 = pcr.min(1.0, effSatLow030150)

            # readily available water in the root zone (upper soil layers)
            readAvlWater = (
                (
                    pcr.max(
                        0.0,
                        effSatUpp000005 - self.parameters.effSatAtWiltPointUpp000005,
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
                        effSatUpp005030 - self.parameters.effSatAtWiltPointUpp005030,
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
                        effSatLow030150 - self.parameters.effSatAtWiltPointLow030150,
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

        return readAvlWater

    def update(self, meteo, landSurface, groundwater, routing, currTimeStep):

        # variables from landSurface.landCoverObj
        self.cropKC = landSurface.landCoverObj[self.name].cropKC
        self.topWaterLayer = landSurface.landCoverObj[self.name].topWaterLayer

        if self.numberOfLayers == 2:
            self.adjRootFrUpp = landSurface.landCoverObj[self.name].adjRootFrUpp
            self.adjRootFrLow = landSurface.landCoverObj[self.name].adjRootFrLow

        if self.numberOfLayers == 3:
            self.adjRootFrUpp000005 = landSurface.landCoverObj[
                self.name
            ].adjRootFrUpp000005
            self.adjRootFrUpp005030 = landSurface.landCoverObj[
                self.name
            ].adjRootFrUpp005030
            self.adjRootFrLow030150 = landSurface.landCoverObj[
                self.name
            ].adjRootFrLow030150

        # soil states from landSurface.landCoverObj
        if self.numberOfLayers == 2:
            self.storUpp = landSurface.landCoverObj[self.name].storUpp
            self.storLow = landSurface.landCoverObj[self.name].storLow
            self.soilWaterStorage = self.storUpp + self.storLow

        if self.numberOfLayers == 3:
            self.storUpp000005 = landSurface.landCoverObj[self.name].storUpp000005
            self.storUpp005030 = landSurface.landCoverObj[self.name].storUpp005030
            self.storLow030150 = landSurface.landCoverObj[self.name].storLow030150
            self.soilWaterStorage = (
                self.storUpp000005 + self.storUpp005030 + self.storLow030150
            )

        self.readAvlWater = self.get_readily_available_water_within_the_root_zone()

        # more variables from landSurface.landCoverObj
        self.netLqWaterToSoil = landSurface.landCoverObj[self.name].netLqWaterToSoil
        self.fracVegCover = landSurface.landCoverObj[self.name].fracVegCover
        self.totalPotET = landSurface.landCoverObj[self.name].totalPotET
        self.potBareSoilEvap = landSurface.landCoverObj[self.name].potBareSoilEvap
        self.potTranspiration = landSurface.landCoverObj[self.name].potTranspiration

        # irrigation efficiency (yearly; sets self.irrigationEfficiency)
        if currTimeStep.doy == 1 or currTimeStep.timeStepPCR == 1:
            self.get_irrigation_efficiency(currTimeStep)

        # irrigation water demand (m/day) for paddy and non-paddy fields;
        # TODO: split between paddy and non-paddy fields
        self.irrGrossDemand = pcr.scalar(0.0)
        if self.name == "irrPaddy" or self.name == "irr_paddy":
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
            # original formula from Allen et al. (1998); see http://www.fao.org/docrep/x0490e/x0490e0e.html
            adjDeplFactor = pcr.max(
                0.1,
                pcr.min(
                    0.8, (self.cropDeplFactor + 0.04 * (5.0 - self.totalPotET * 1000.0))
                ),
            )

            # irrigation demand to fill totAvlWater (maintaining field capacity), corrected
            # for rooting depth with the crop coefficient as a proxy
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

            # limit the demand by the potential evaporation of the coming days, to avoid
            # unrealistically high demands
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

    def estimateTranspirationAndBareSoilEvap(
        self, returnTotalEstimation=False, returnTotalTranspirationOnly=False
    ):

        # transpiration: fractions based on root fractions and actual layer storages
        # Rens: WF1 = if((S1_L[TYPE]+S2_L[TYPE])>0,RFW1[TYPE]*S1_L[TYPE]/max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW1[TYPE])
        # Rens: WF2 = if((S1_L[TYPE]+S2_L[TYPE])>0,RFW2[TYPE]*S2_L[TYPE]/max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW2[TYPE])
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

        # note: for the irrigation demand returnTotalEstimation is always True, so this is not used
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
