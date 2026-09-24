import calendar
import logging
import math

import pcraster as pcr
from pcraster.framework import *

from pcrglobwb.common import virtualOS as vos
from pcrglobwb.evaporation import hamonETPFunctions as hamon_et0
from pcrglobwb.evaporation import ref_pot_et_penman_monteith as penman_monteith
from pcrglobwb.evaporation import shortwave_radiation as sw_rad
from pcrglobwb.ncConverter import *

logger = logging.getLogger(__name__)


class Meteo(object):

    def getState(self):

        result = {}

        # annual average precipitation over the last 365 days (m/day)
        result["avgAnnualPrecipitation"] = self.avgAnnualPrecipitation

        # annual average temperature and diurnal temperature difference over the last 365 days (degC)
        result["avgAnnualTemperature"] = self.avgAnnualTemperature
        result["avgAnnualDiurnalDeltaTemp"] = self.avgAnnualDiurnalDeltaTemp

        return result

    def getPseudoState(self):
        result = {}

        return result

    def getICs(self, iniItems, iniConditions=None):

        self.initialize_states(iniItems, iniConditions)

    def initialize_states(self, iniItems, iniConditions):

        # initial conditions (m) at the start of the model (read from file)
        if iniConditions is None:

            if "avgAnnualPrecipitationIni" in list(iniItems.meteoOptions.keys()):
                self.avgAnnualPrecipitation = vos.readPCRmapClone(
                    iniItems.meteoOptions["avgAnnualPrecipitationIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                msg = "The initial condition avgAnnualPrecipitationIni is not defined and set to zero. This is needed only for the Bristow-Campbell method."
                self.avgAnnualPrecipitation = pcr.scalar(0.0)

            if "avgAnnualTemperatureIni" in list(iniItems.meteoOptions.keys()):
                self.avgAnnualTemperature = vos.readPCRmapClone(
                    iniItems.meteoOptions["avgAnnualTemperatureIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                msg = "The initial condition avgAnnualTemperatureIni is not defined and set to zero. This is needed only for the Bristow-Campbell method."
                self.avgAnnualTemperature = pcr.scalar(0.0)

            if "avgAnnualDiurnalDeltaTempIni" in list(iniItems.meteoOptions.keys()):
                self.avgAnnualDiurnalDeltaTemp = vos.readPCRmapClone(
                    iniItems.meteoOptions["avgAnnualDiurnalDeltaTempIni"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
            else:
                msg = "The initial condition avgAnnualDiurnalDeltaTempIni is not defined and set to zero. This is needed only for the Bristow-Campbell method."
                self.avgAnnualDiurnalDeltaTemp = pcr.scalar(0.0)

        # during/after spin-up
        else:

            self.avgAnnualPrecipitation = iniConditions["meteo"][
                "avgAnnualPrecipitation"
            ]
            self.avgAnnualTemperature = iniConditions["meteo"]["avgAnnualTemperature"]
            self.avgAnnualDiurnalDeltaTemp = iniConditions["meteo"][
                "avgAnnualDiurnalDeltaTemp"
            ]

        # these values cannot be negative
        self.avgAnnualPrecipitation = pcr.ifthen(
            self.landmask, pcr.max(0.0, pcr.cover(self.avgAnnualPrecipitation, 0.0))
        )
        self.avgAnnualDiurnalDeltaTemp = pcr.ifthen(
            self.landmask, pcr.max(0.0, pcr.cover(self.avgAnnualDiurnalDeltaTemp, 0.0))
        )

        # these values can be negative
        self.avgAnnualTemperature = pcr.ifthen(self.landmask, self.avgAnnualTemperature)

    def __init__(self, iniItems, landmask, spinUp):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]

        self.landmask = landmask
        if iniItems.globalOptions["landmask"] != "None":
            self.landmask = vos.readPCRmapClone(
                iniItems.globalOptions["landmask"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
        # note: to keep the water balance consistent during downscaling, perhaps we should not mask during the calculation (only for reporting and reading initial conditions)

        # option to ignore snow (temperature is set to 25 degC)
        self.ignore_snow = False
        if (
            "ignoreSnow" in list(iniItems.meteoOptions.keys())
            and iniItems.meteoOptions["ignoreSnow"] == "True"
        ):
            self.ignore_snow = True

        # only netCDF input files are supported (since 19 Feb 2014)
        self.preFileNC = iniItems.meteoOptions["precipitationNC"]
        self.tmpFileNC = iniItems.meteoOptions["temperatureNC"]

        self.refETPotMethod = iniItems.meteoOptions["referenceETPotMethod"]
        msg = "Method for the reference potential evaporation: " + str(
            self.refETPotMethod
        )
        logger.info(msg)

        # Penman-Monteith class
        if self.refETPotMethod == "Penman-Monteith":
            self.penman_monteith = penman_monteith.penmanMonteithET(windHeight=10.00)
            msg = "The Penman Monteith is instantiated for wind input data at 10 m height."
            logger.info(msg)
            # TODO: make windHeight flexible

        if self.refETPotMethod == "Input":
            self.etpFileNC = iniItems.meteoOptions["refETPotFileNC"]

        # extra meteo variables needed for the Penman-Monteith method
        self.extra_meteo_var_names = [
            "wind_speed_10m",
            "wind_speed_10m_u_comp",
            "wind_speed_10m_v_comp",
            "atmospheric_pressure",
            "extraterestrial_radiation",
            "shortwave_radiation",
            "longwave_radiation",
            "relative_humidity",
            "surface_net_solar_radiation",
            "albedo",
            "air_temperature_max",
            "air_temperature_min",
            "dewpoint_temperature_avg",
        ]

        # RvB (13 Jul 2016): conversion constants and factors and variable names for easier use of netCDF
        # climate input files; modified by EHS (20 Aug 2016)
        self.preConst = 0.0
        self.preFactor = 1.0
        self.tmpConst = 0.0
        self.tmpFactor = 1.0
        self.refETPotConst = 0.0
        self.refETPotFactor = 1.0
        self.read_meteo_conversion_factors(iniItems.meteoOptions)
        self.preVarName = "precipitation"
        self.tmpVarName = "temperature"
        self.refETPotVarName = "evapotranspiration"
        self.read_meteo_variable_names(iniItems.meteoOptions)

        # latitudes, required to calculate referenceETPot with the Hamon and Penman-Monteith methods
        self.latitudes = pcr.ycoordinate(pcr.defined(self.cloneMap))
        self.latitudes_in_radian = vos.deg2rad(self.latitudes)

        self.lon = pcr.pcr2numpy(pcr.xcoordinate(pcr.defined(self.cloneMap)), np.nan)[
            0, :
        ]
        self.lat = pcr.pcr2numpy(pcr.ycoordinate(pcr.defined(self.cloneMap)), np.nan)[
            0, :
        ]

        # shortwave radiation class, required for the Bristow-Campbell method
        self.sw_rad_based_on_bristow_campbell = False
        if ("shortwave_radiation" in iniItems.meteoOptions) and (
            iniItems.meteoOptions["shortwave_radiation"] == "Bristow-Campbell"
        ):

            self.sw_rad_based_on_bristow_campbell = True

            msg = "The shortwave (solar) radiation will be estimated based on actual shortwave radiation is estimated based on an adaptation of the Bristow-Campbell model by Winslow et al (2001)"
            logger.info(msg)

            self.elevation_meteo = pcr.cover(
                vos.readPCRmapClone(
                    iniItems.meteoOptions["dem_for_input_meteo"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                0.0,
            )

        # daily time step
        self.usingDailyTimeStepForcingData = False
        if iniItems.timeStep == 1.0 and iniItems.timeStepUnit == "day":
            self.usingDailyTimeStepForcingData = True

        # option to remove drizzle: precipitation below 0.00001 m/day (0.01 kg.m-2.day-1) is ignored
        self.rounddownPrecipitation = False

        self.forcingDownscalingOptions(iniItems)

        # option to use one netCDF file per year
        self.precipitation_set_per_year = (
            iniItems.meteoOptions["precipitation_set_per_year"] == "True"
        )
        self.temperature_set_per_year = (
            iniItems.meteoOptions["temperature_set_per_year"] == "True"
        )
        self.refETPotFileNC_set_per_year = (
            iniItems.meteoOptions["refETPotFileNC_set_per_year"] == "True"
        )

        # option to downscale meteo with a daily climatological factor
        self.using_daily_factor_for_downscaling = False
        if (
            "using_daily_factor_for_downscaling"
            in list(iniItems.meteoDownscalingOptions.keys())
            and iniItems.meteoDownscalingOptions["using_daily_factor_for_downscaling"]
            == "True"
        ):
            self.using_daily_factor_for_downscaling = True
            self.precip_downscaling_factor_file = vos.getFullPath(
                iniItems.meteoDownscalingOptions["precip_downscaling_factor_file"],
                self.inputDir,
            )
            self.precip_drydays_file = vos.getFullPath(
                iniItems.meteoDownscalingOptions["precip_drydays_file"], self.inputDir
            )
            self.temp_downscaling_factor_file = vos.getFullPath(
                iniItems.meteoDownscalingOptions["temp_downscaling_factor_file"],
                self.inputDir,
            )
            self.evap_downscaling_factor_file = vos.getFullPath(
                iniItems.meteoDownscalingOptions["evap_downscaling_factor_file"],
                self.inputDir,
            )

            # TODO: expand this for T and ET0
        self.iniItems = iniItems

        self.getICs(iniItems, spinUp)

        self.report = True
        try:
            self.outDailyTotNC = iniItems.meteoOptions["outDailyTotNC"].split(",")
            self.outMonthTotNC = iniItems.meteoOptions["outMonthTotNC"].split(",")
            self.outMonthAvgNC = iniItems.meteoOptions["outMonthAvgNC"].split(",")
            self.outMonthEndNC = iniItems.meteoOptions["outMonthEndNC"].split(",")
            self.outAnnuaTotNC = iniItems.meteoOptions["outAnnuaTotNC"].split(",")
            self.outAnnuaAvgNC = iniItems.meteoOptions["outAnnuaAvgNC"].split(",")
            self.outAnnuaEndNC = iniItems.meteoOptions["outAnnuaEndNC"].split(",")
        except Exception:
            self.report = False
        if self.report:
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

    def read_meteo_conversion_factors(self, meteoOptions):

        # conversion constants and factors for precipitation, temperature and reference potential evaporation
        if "precipitationConstant" in meteoOptions:
            self.preConst = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["precipitationConstant"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                0.0,
            )
        if "precipitationFactor" in meteoOptions:
            self.preFactor = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["precipitationFactor"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                1.0,
            )
        if "temperatureConstant" in meteoOptions:
            self.tmpConst = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["temperatureConstant"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                0.0,
            )
        if "temperatureFactor" in meteoOptions:
            self.tmpFactor = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["temperatureFactor"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                1.0,
            )
        if "referenceEPotConstant" in meteoOptions:
            self.refETPotConst = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["referenceEPotConstant"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                0.0,
            )
        if "referenceEPotFactor" in meteoOptions:
            self.refETPotFactor = pcr.cover(
                vos.readPCRmapClone(
                    meteoOptions["referenceEPotFactor"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                ),
                1.0,
            )

        # conversion constants and factors for the extra meteo variables
        for meteo_var_name in self.extra_meteo_var_names:
            consta_var_name = "consta_for_" + meteo_var_name
            vars(self)[consta_var_name] = pcr.spatial(pcr.scalar(0.0))
            if consta_var_name in meteoOptions:
                vars(self)[consta_var_name] = pcr.cover(
                    vos.readPCRmapClone(
                        meteoOptions[consta_var_name],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    0.0,
                )
            factor_var_name = "factor_for_" + meteo_var_name
            vars(self)[factor_var_name] = pcr.spatial(pcr.scalar(1.0))
            if factor_var_name in meteoOptions:
                vars(self)[factor_var_name] = pcr.cover(
                    vos.readPCRmapClone(
                        meteoOptions[factor_var_name],
                        self.cloneMap,
                        self.tmpDir,
                        self.inputDir,
                    ),
                    1.0,
                )

    def read_meteo_variable_names(self, meteoOptions):

        if "precipitationVariableName" in meteoOptions:
            self.preVarName = meteoOptions["precipitationVariableName"]
        if "temperatureVariableName" in meteoOptions:
            self.tmpVarName = meteoOptions["temperatureVariableName"]
        if "referenceEPotVariableName" in meteoOptions:
            self.refETPotVarName = meteoOptions["referenceEPotVariableName"]

    def forcingDownscalingOptions(self, iniItems):

        self.downscalePrecipitationOption = False
        self.downscaleTemperatureOption = False
        self.downscaleReferenceETPotOption = False

        if "meteoDownscalingOptions" in iniItems.allSections:

            if iniItems.meteoDownscalingOptions["downscalePrecipitation"] == "True":
                self.downscalePrecipitationOption = True
                logger.info(
                    "Precipitation forcing will be downscaled to the cloneMap resolution."
                )

            if iniItems.meteoDownscalingOptions["downscaleTemperature"] == "True":
                self.downscaleTemperatureOption = True
                logger.info(
                    "Temperature forcing will be downscaled to the cloneMap resolution."
                )

            if iniItems.meteoDownscalingOptions["downscaleReferenceETPot"] == "True":
                self.downscaleReferenceETPotOption = True
                logger.info(
                    "Reference potential evaporation will be downscaled to the cloneMap resolution."
                )

                # with the Hamon method, referencePotET is calculated from temperature, so it may not need downscaling
                # (particularly if temperature is already given at high resolution)

        if (
            self.downscalePrecipitationOption
            or self.downscaleTemperatureOption
            or self.downscaleReferenceETPotOption
        ):

            # cell area (m2), needed to downscale P and ET0
            if "cellAreaMap" not in list(iniItems.meteoOptions.keys()):
                iniItems.meteoOptions["cellAreaMap"] = iniItems.routingOptions[
                    "cellAreaMap"
                ]
            cellArea = vos.readPCRmapClone(
                iniItems.meteoOptions["cellAreaMap"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )

            # anomaly DEM
            highResolutionDEM = vos.readPCRmapClone(
                iniItems.meteoDownscalingOptions["highResolutionDEM"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            highResolutionDEM = pcr.cover(highResolutionDEM, 0.0)
            highResolutionDEM = pcr.max(highResolutionDEM, 0.0)
            self.meteoDownscaleIds = vos.readPCRmapClone(
                iniItems.meteoDownscalingOptions["meteoDownscaleIds"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
                isLddMap=False,
                cover=None,
                isNomMap=True,
            )
            self.cellArea = vos.readPCRmapClone(
                iniItems.routingOptions["cellAreaMap"],
                self.cloneMap,
                self.tmpDir,
                self.inputDir,
            )
            loweResolutionDEM = pcr.areatotal(
                pcr.cover(highResolutionDEM * self.cellArea, 0.0),
                self.meteoDownscaleIds,
            ) / pcr.areatotal(pcr.cover(self.cellArea, 0.0), self.meteoDownscaleIds)
            # (m)
            self.anomalyDEM = highResolutionDEM - loweResolutionDEM

            # temperature lapse rate (netCDF) file
            self.temperLapseRateNC = vos.getFullPath(
                iniItems.meteoDownscalingOptions["temperLapseRateNC"], self.inputDir
            )
            # TODO: remove this criterion
            self.temperatCorrelNC = vos.getFullPath(
                iniItems.meteoDownscalingOptions["temperatCorrelNC"], self.inputDir
            )

            # precipitation lapse rate (netCDF) file
            self.precipLapseRateNC = vos.getFullPath(
                iniItems.meteoDownscalingOptions["precipLapseRateNC"], self.inputDir
            )
            # TODO: remove this criterion
            self.precipitCorrelNC = vos.getFullPath(
                iniItems.meteoDownscalingOptions["precipitCorrelNC"], self.inputDir
            )

        else:
            logger.info("No forcing downscaling is implemented.")

        # forcing smoothing options (experimental; must be tested)
        self.forcingSmoothing = False
        if (
            "meteoDownscalingOptions" in iniItems.allSections
            and "smoothingWindowsLength"
            in list(iniItems.meteoDownscalingOptions.keys())
        ):

            if float(iniItems.meteoDownscalingOptions["smoothingWindowsLength"]) > 0.0:
                self.forcingSmoothing = True
                self.smoothingWindowsLength = vos.readPCRmapClone(
                    iniItems.meteoDownscalingOptions["smoothingWindowsLength"],
                    self.cloneMap,
                    self.tmpDir,
                    self.inputDir,
                )
                msg = (
                    "Forcing data will be smoothed with 'windowaverage' using the window length:"
                    + str(iniItems.meteoDownscalingOptions["smoothingWindowsLength"])
                )
                logger.info(msg)

    def update(self, routing, currTimeStep):

        self.precipitation_before_downscaling = pcr.ifthen(
            self.landmask, self.precipitation
        )
        if self.downscalePrecipitationOption:
            self.downscalePrecipitation(
                currTimeStep,
                read_factor_from_file=self.using_daily_factor_for_downscaling,
            )

        # downscale the average temperature
        self.temperature_before_downscaling = pcr.ifthen(
            self.landmask, self.temperature
        )
        if self.downscaleTemperatureOption:
            self.downscaleTemperature(
                currTimeStep,
                read_factor_from_file=self.using_daily_factor_for_downscaling,
            )

        # downscale the minimum temperature
        if self.air_temperature_min is not None and self.downscaleTemperatureOption:
            self.air_temperature_min = self.downscaleTemperatureFunction(
                currTimeStep, self.air_temperature_min
            )
            self.air_temperature_min = pcr.min(
                self.temperature, self.air_temperature_min
            )

        # downscale the maximum temperature
        if self.air_temperature_max is not None and self.downscaleTemperatureOption:
            self.air_temperature_max = self.downscaleTemperatureFunction(
                currTimeStep, self.air_temperature_max
            )
            self.air_temperature_max = pcr.max(
                self.temperature, self.air_temperature_max
            )

        # calculate or read referencePotET
        if self.refETPotMethod == "Hamon":

            msg = (
                "Calculating reference potential evaporation based on the Hamon method"
            )
            logger.info(msg)

            self.referencePotET = hamon_et0.HamonPotET(
                self.temperature, pcr.scalar(currTimeStep.doy), self.latitudes
            )

        if self.refETPotMethod == "Penman-Monteith":

            msg = "Calculating reference potential evaporation based on the Penman-Monteith"
            logger.info(msg)

            # actual vapour pressure (Pa) from relative humidity (rh = e / e_sat)
            vapourPressure = None
            if self.relative_humidity is not None:
                msg = "Estimating actual vapour pressure based on relative humidity and temperature"
                logger.info(msg)
                saturatedVapourPressure = penman_monteith.getSaturatedVapourPressure(
                    self.temperature
                )
                vapourPressure = self.relative_humidity * saturatedVapourPressure

            # actual vapour pressure (Pa) from the dew point temperature
            if vapourPressure is None and self.dewpoint_temperature_avg is not None:
                msg = (
                    "Estimating actual vapour pressure based on dew point temperature."
                )
                logger.info(msg)
                vapourPressure = penman_monteith.getSaturatedVapourPressure(
                    self.dewpoint_temperature_avg
                )

                # TODO: if dewpoint_temperature_avg is unavailable, should we use air_temperature_min?

            # wind speed (m.s-1)
            if ("wind_speed_10m" not in list(self.iniItems.meteoOptions.keys())) or (
                self.iniItems.meteoOptions["wind_speed_10m"] == "None"
            ):
                msg = "Calculating wind speed based on their u and v components"
                logger.info(msg)
                self.wind_speed_10m = (
                    self.wind_speed_10m_u_comp**2.0 + self.wind_speed_10m_v_comp**2.0
                ) ** (0.5)

            # extraterrestrial radiation

            if (
                "extraterestrial_radiation"
                not in list(self.iniItems.meteoOptions.keys())
            ) or (self.iniItems.meteoOptions["extraterestrial_radiation"] == "None"):

                msg = "Estimating extraterestrial radiation based on Dingman's Physical Geography (2015)"
                logger.info(msg)

                # day angle (rad) from the julian day
                julian_day = currTimeStep.doy
                number_days = 365
                if calendar.isleap(currTimeStep.year):
                    number_days = 366
                day_angle = float(julian_day - 1) / number_days * 2 * math.pi

                solar_declination = sw_rad.compute_solar_declination(day_angle)

                eccentricity = sw_rad.compute_eccentricity(day_angle)

                # day length (hours)
                day_length = sw_rad.compute_day_length(
                    latitude=self.latitudes_in_radian,
                    solar_declination=solar_declination,
                )

                # extraterrestrial radiation (MJ.m-2.day-1)
                extraterestrial_radiation = sw_rad.compute_radsw_ext(
                    latitude=self.latitudes_in_radian,
                    solar_declination=solar_declination,
                    eccentricity=eccentricity,
                    day_length=day_length,
                    solar_constant=118.1,
                )
                # TODO: double check the deg and rad values

                # TODO: set solar_constant in the configuration file

                # the default unit of extraterestrial_radiation is J.m-2.day-1
                self.extraterestrial_radiation = extraterestrial_radiation * 1e6

            else:

                msg = "Extraterestrial radiation is obtained from the input file."
                logger.info(msg)

            # TODO: extraterrestrial shortwave radiation is not always needed (e.g. if shortwave and longwave radiation are given)

            # convert the extraterrestrial radiation to W.m-2
            if "extraterestrial_radiation_input_in_w_per_m2" in list(
                self.iniItems.meteoOptions.keys()
            ) and (
                self.iniItems.meteoOptions[
                    "extraterestrial_radiation_input_in_w_per_m2"
                ]
                == "True"
            ):
                self.extraterestrial_radiation = pcr.max(
                    0.0, self.extraterestrial_radiation
                )
            else:
                self.extraterestrial_radiation = (
                    pcr.max(0.0, self.extraterestrial_radiation / 1e6) / 0.0864
                )

            if self.iniItems.meteoOptions["shortwave_radiation"].endswith(
                (".nc", ".nc4", ".nc3")
            ):

                msg = "Shortwave (solar) radiation is obtained from the input file."
                logger.info(msg)

            if self.iniItems.meteoOptions["shortwave_radiation"] == "None":

                msg = "Estimating shortwave (solar) radiation based on the input of net radiation and albedo."
                logger.info(msg)

                self.shortwave_radiation = self.surface_net_solar_radiation / (
                    pcr.spatial(pcr.scalar(1.0)) - self.albedo
                )

            if self.sw_rad_based_on_bristow_campbell:

                msg = "Estimating shortwave (solar) radiation based on an adaptation of the Bristow-Campbell model by Winslow et al (2001)."
                logger.info(msg)

                # TODO: the shortwave radiation module must still be initialized every time step, as temp_annual and delta_temp_mean are defined in init

                # shortwave radiation class with solar constant = 118.1 MJ.m-2.day-1
                self.sw_rad_model = sw_rad.ShortwaveRadiation(
                    latitude=self.latitudes,
                    elevation=self.elevation_meteo,
                    temp_annual=self.avgAnnualTemperature,
                    delta_temp_mean=self.avgAnnualDiurnalDeltaTemp,
                    solar_constant=118.1,
                )

                # TODO: set solar_constant in the configuration file

                # sw_rad_model needs the radiation input in MJ.m-2.day-1 (given the solar constant = 118.1 MJ.m-2.day-1)
                extraterrestrial_rad_in_watt_per_m2 = self.extraterestrial_radiation
                extraterrestrial_rad = extraterrestrial_rad_in_watt_per_m2 * 0.0864

                self.sw_rad_model.update(
                    date=currTimeStep._currTimeFull,
                    prec_daily=self.precipitation,
                    temp_min_daily=self.air_temperature_min,
                    temp_max_daily=self.air_temperature_max,
                    temp_avg_daily=self.temperature,
                    dew_temperature=self.dewpoint_temperature_avg,
                    extraterrestrial_rad=extraterrestrial_rad,
                    relative_humidity=self.relative_humidity,
                )

                # values from the shortwave radiation model (J.m-2.day-1)
                self.shortwave_radiation = self.sw_rad_model.radsw_act * 1e6

            # convert the shortwave radiation to W.m-2
            if "shortwave_radiation_input_in_w_per_m2" in list(
                self.iniItems.meteoOptions.keys()
            ) and (
                self.iniItems.meteoOptions["shortwave_radiation_input_in_w_per_m2"]
                == "True"
            ):
                self.shortwave_radiation = pcr.max(0.0, self.shortwave_radiation)
            else:
                self.shortwave_radiation = (
                    pcr.max(0.0, self.shortwave_radiation / 1e6) / 0.0864
                )

            if "longwave_radiation" in list(
                self.iniItems.meteoOptions.keys()
            ) and self.iniItems.meteoOptions["longwave_radiation"].endswith(
                (".nc", ".nc4", ".nc3")
            ):

                msg = "Longwave radiation is obtained from the input file."
                logger.info(msg)

                # convert the longwave radiation to W.m-2 (the default input unit is J.m-2.day-1)
                if "longwave_radiation_input_in_w_per_m2" in list(
                    self.iniItems.meteoOptions.keys()
                ) and (
                    self.iniItems.meteoOptions["longwave_radiation_input_in_w_per_m2"]
                    == "True"
                ):
                    self.longwave_radiation = pcr.max(0.0, self.longwave_radiation)
                else:
                    self.longwave_radiation = (
                        pcr.max(0.0, self.longwave_radiation / 1e6) / 0.0864
                    )

            else:

                msg = "Longwave radiation is estimated from shortwave radiation, extraterestrial radiation, and actual vapour pressue"
                logger.info(msg)

                # fraction of shortwave radiation (-)
                fractionShortWaveRadiation = pcr.cover(
                    pcr.min(
                        1.0, self.shortwave_radiation / self.extraterestrial_radiation
                    ),
                    0.0,
                )

                # longwave radiation (already in W.m-2)
                self.longwave_radiation = penman_monteith.getLongWaveRadiation(
                    self.temperature,
                    vapourPressure,
                    fractionShortWaveRadiation,
                    self.relative_humidity,
                )

            # net radiation (W.m-2)
            self.net_radiation = pcr.max(
                0.0, self.shortwave_radiation - self.longwave_radiation
            )

            # referencePotET (m.day-1)
            self.referencePotET = self.penman_monteith.updatePotentialEvaporation(
                netRadiation=self.net_radiation,
                airTemperature=self.temperature,
                windSpeed=self.wind_speed_10m,
                atmosphericPressure=self.atmospheric_pressure,
                unsatVapPressure=vapourPressure,
                relativeHumidity=self.relative_humidity,
                timeStepLength=86400,
            )

        # downscale referenceETPot (based on temperature)
        self.referencePotET_before_downscaling = self.referencePotET
        if self.downscaleReferenceETPotOption:
            self.downscaleReferenceETPot(
                currTimeStep,
                read_factor_from_file=self.using_daily_factor_for_downscaling,
            )

        # smoothing
        if self.forcingSmoothing:
            logger.debug("Forcing data are smoothed.")
            self.precipitation = pcr.windowaverage(
                self.precipitation, self.smoothingWindowsLength
            )
            self.temperature = pcr.windowaverage(
                self.temperature, self.smoothingWindowsLength
            )
            self.referencePotET = pcr.windowaverage(
                self.referencePotET, self.smoothingWindowsLength
            )

        # round temperature values to minimize numerical errors
        self.temperature = pcr.roundoff(self.temperature * 1000.0) / 1000.0

        # ignore snow by setting the temperature to 25 degC
        if self.ignore_snow:
            self.temperature = pcr.spatial(pcr.scalar(25.0))

        # precipitation and referencePotET must be positive
        self.precipitation = pcr.max(0.0, self.precipitation)
        self.referencePotET = pcr.max(0.0, self.referencePotET)

        # only define precipitation, temperature and referencePotET within the landmask (for reporting)
        self.precipitation = pcr.ifthen(self.landmask, self.precipitation)
        self.temperature = pcr.ifthen(self.landmask, self.temperature)
        self.referencePotET = pcr.ifthen(self.landmask, self.referencePotET)

        # update the long-term averages

        deltaAnnualPrecipitation = self.precipitation - self.avgAnnualPrecipitation
        self.avgAnnualPrecipitation = (
            self.avgAnnualPrecipitation
            + deltaAnnualPrecipitation
            / pcr.min(365.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgAnnualPrecipitation = pcr.max(0.0, self.avgAnnualPrecipitation)

        deltaAnnualTemperature = self.temperature - self.avgAnnualTemperature
        self.avgAnnualTemperature = (
            self.avgAnnualTemperature
            + deltaAnnualTemperature
            / pcr.min(365.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )

        if self.air_temperature_max is not None or self.air_temperature_min is not None:
            diurnalDeltaTemp = pcr.max(
                0.0, self.air_temperature_max - self.air_temperature_min
            )
        else:
            diurnalDeltaTemp = pcr.ifthen(pcr.pcrnot(self.landmask), pcr.scalar(0.0))
        deltaAnnualDiurnalDeltaTemp = diurnalDeltaTemp - self.avgAnnualDiurnalDeltaTemp
        self.avgAnnualDiurnalDeltaTemp = (
            self.avgAnnualDiurnalDeltaTemp
            + deltaAnnualDiurnalDeltaTemp
            / pcr.min(365.0, pcr.max(1.0, routing.timestepsToAvgDischarge))
        )
        self.avgAnnualDiurnalDeltaTemp = pcr.max(0.0, self.avgAnnualDiurnalDeltaTemp)

        if self.report:
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

                    if currTimeStep.endMonth:
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

                    if currTimeStep.endMonth:
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
                    if currTimeStep.endMonth:
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

                    if currTimeStep.endYear:
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
                    if currTimeStep.endYear:
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
                    if currTimeStep.endYear:
                        self.netcdfObj.data2NetCDF(
                            str(self.outNCDir) + "/" + str(var) + "_annuaEnd.nc",
                            var,
                            pcr2numpy(self.__getattribute__(var), vos.MV),
                            timeStamp,
                            currTimeStep.annuaIdx - 1,
                        )

    def downscalePrecipitation(
        self,
        currTimeStep,
        read_factor_from_file=False,
        useFactor=True,
        minCorrelationCriteria=0.85,
        drizzle_limit=0.001,
        considerCellArea=True,
    ):

        # TODO: add CorrelationCriteria to the config file
        if read_factor_from_file:

            doyStep = currTimeStep.doy
            if calendar.isleap(currTimeStep.year) and doyStep > 59:
                doyStep = doyStep - 1
            factor = vos.readDownscalingZarr(
                self.precip_downscaling_factor_file,
                doyStep,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
            )
            drizzle_limit = vos.readDownscalingZarr(
                self.precip_drydays_file,
                currTimeStep.month,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
            )

            self.precipitation = pcr.ifthenelse(
                self.precipitation > drizzle_limit, self.precipitation, 0.00
            )
            # TODO: use this one too?
            self.precipitation = self.precipitation * factor
            self.precipitation = pcr.max(0.0, self.precipitation)

        else:
            preSlope = 0.001 * vos.netcdf2PCRobjClone(
                self.precipLapseRateNC,
                dateInput=currTimeStep.month,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )
            preSlope = pcr.cover(preSlope, 0.0)
            preSlope = pcr.max(0.0, preSlope)

            preCriteria = vos.netcdf2PCRobjClone(
                self.precipitCorrelNC,
                dateInput=currTimeStep.month,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )
            preSlope = pcr.ifthenelse(
                preCriteria > minCorrelationCriteria, preSlope, 0.0
            )
            preSlope = pcr.cover(preSlope, 0.0)

            if useFactor:
                factor = pcr.max(0.0, self.precipitation + preSlope * self.anomalyDEM)

                # avoid zero factor
                min_limit = drizzle_limit
                factor = pcr.max(min_limit, factor)

                if considerCellArea:
                    factor = factor * self.cellArea

                factor = factor / pcr.areaaverage(factor, self.meteoDownscaleIds)

                # do not downscale drizzle
                factor = pcr.ifthenelse(
                    self.precipitation > drizzle_limit, factor, 1.00
                )

                factor = pcr.cover(factor, 1.0)

                self.precipitation = factor * self.precipitation
            else:
                self.precipitation = self.precipitation + preSlope * self.anomalyDEM

        self.precipitation = pcr.max(0.0, self.precipitation)

    def downscaleTemperature(
        self,
        currTimeStep,
        read_factor_from_file=False,
        useFactor=False,
        maxCorrelationCriteria=-0.75,
        zeroCelciusInKelvin=273.15,
        considerCellArea=True,
    ):

        # TODO: add CorrelationCriteria to the config file
        if read_factor_from_file:
            doyStep = currTimeStep.doy
            if calendar.isleap(currTimeStep.year) and doyStep > 59:
                doyStep = doyStep - 1
            factor = vos.readDownscalingZarr(
                self.temp_downscaling_factor_file,
                doyStep,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
            )
            self.temperature = self.temperature + factor

        else:
            tmpSlope = 1.000 * vos.netcdf2PCRobjClone(
                self.temperLapseRateNC,
                dateInput=currTimeStep.month,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )
            # must be negative
            tmpSlope = pcr.min(0.0, tmpSlope)
            tmpCriteria = vos.netcdf2PCRobjClone(
                self.temperatCorrelNC,
                dateInput=currTimeStep.month,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )
            tmpSlope = pcr.ifthenelse(
                tmpCriteria < maxCorrelationCriteria, tmpSlope, 0.0
            )
            tmpSlope = pcr.cover(tmpSlope, 0.0)

            if useFactor:

                temperatureInKelvin = self.temperature + zeroCelciusInKelvin
                factor = pcr.max(0.0, temperatureInKelvin + tmpSlope * self.anomalyDEM)
                if considerCellArea:
                    factor = factor * self.cellArea
                factor = factor / pcr.areaaverage(factor, self.meteoDownscaleIds)
                factor = pcr.cover(factor, 1.0)
                self.temperature = factor * temperatureInKelvin - zeroCelciusInKelvin
            else:
                self.temperature = self.temperature + tmpSlope * self.anomalyDEM

    def downscaleTemperatureFunction(
        self,
        currTimeStep,
        input_temperature,
        useFactor=False,
        maxCorrelationCriteria=-0.75,
        zeroCelciusInKelvin=273.15,
        considerCellArea=True,
    ):

        # TODO: add CorrelationCriteria to the config file

        tmpSlope = 1.000 * vos.netcdf2PCRobjClone(
            self.temperLapseRateNC,
            dateInput=currTimeStep.month,
            useDoy="Yes",
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
        )
        # must be negative
        tmpSlope = pcr.min(0.0, tmpSlope)
        tmpCriteria = vos.netcdf2PCRobjClone(
            self.temperatCorrelNC,
            dateInput=currTimeStep.month,
            useDoy="Yes",
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude=True,
        )
        tmpSlope = pcr.ifthenelse(tmpCriteria < maxCorrelationCriteria, tmpSlope, 0.0)
        tmpSlope = pcr.cover(tmpSlope, 0.0)

        if useFactor:
            temperatureInKelvin = input_temperature + zeroCelciusInKelvin
            factor = pcr.max(0.0, temperatureInKelvin + tmpSlope * self.anomalyDEM)
            if considerCellArea:
                factor = factor * self.cellArea
            factor = factor / pcr.areaaverage(factor, self.meteoDownscaleIds)
            factor = pcr.cover(factor, 1.0)
            output_temperature = factor * temperatureInKelvin - zeroCelciusInKelvin
        else:
            output_temperature = input_temperature + tmpSlope * self.anomalyDEM

        return output_temperature

    def downscaleReferenceETPot(
        self,
        currTimeStep,
        read_factor_from_file=False,
        zeroCelciusInKelvin=273.15,
        usingHamon=True,
        considerCellArea=True,
        min_limit=0.001,
    ):
        if read_factor_from_file:
            doyStep = currTimeStep.doy
            if calendar.isleap(currTimeStep.year) and doyStep > 59:
                doyStep = doyStep - 1
            factor = vos.readDownscalingZarr(
                self.evap_downscaling_factor_file,
                doyStep,
                useDoy="Yes",
                cloneMapFileName=self.cloneMap,
            )
            self.referencePotET = self.referencePotET * factor

        else:
            if usingHamon:
                # factor based on the Hamon reference potential evaporation using the high-resolution temperature
                factor = hamon_et0.HamonPotET(
                    self.temperature, pcr.scalar(currTimeStep.doy), self.latitudes
                )
            else:
                # factor based on the high-resolution temperature (K)
                factor = self.temperature + zeroCelciusInKelvin

            factor = pcr.max(0.0, factor)

            # avoid zero factor
            factor = pcr.max(min_limit, factor)

            if considerCellArea:
                factor = factor * self.cellArea

            factor = factor / pcr.areaaverage(factor, self.meteoDownscaleIds)

            # do not downscale small values
            factor = pcr.ifthenelse(self.referencePotET > min_limit, factor, 1.00)

            factor = pcr.cover(factor, 1.0)

            self.referencePotET = pcr.max(0.0, factor * self.referencePotET)

    def read_forcings(self, currTimeStep):

        # RvB (13 Jul 2016): the hard-coded variable names of precipitation, temperature and
        # evapotranspiration are replaced by the netCDF variable names from the ini file

        # method to find the time indices in the precipitation netCDF file (default: None, or from the ini file)
        method_for_time_index = None
        method_for_time_index = "daily"
        if (
            "time_index_method_for_precipitation_netcdf"
            in list(self.iniItems.meteoOptions.keys())
            and self.iniItems.meteoOptions["time_index_method_for_precipitation_netcdf"]
            != "None"
        ):
            method_for_time_index = self.iniItems.meteoOptions[
                "time_index_method_for_precipitation_netcdf"
            ]

        netcdf_file_name = self.preFileNC

        if (
            "precipitation_file_per_month" in list(self.iniItems.meteoOptions.keys())
        ) and (self.iniItems.meteoOptions["precipitation_file_per_month"] == "True"):
            try:
                netcdf_file_name = self.preFileNC % (
                    int(currTimeStep.year),
                    int(currTimeStep.month),
                )
            except Exception:
                netcdf_file_name = self.preFileNC % (
                    int(currTimeStep.month),
                    int(currTimeStep.year),
                )
            method_for_time_index = "daily_per_monthly_file"

        if self.precipitation_set_per_year:
            netcdf_file_name = self.preFileNC % (
                int(currTimeStep.year),
                int(currTimeStep.year),
            )

        if (
            self.using_daily_factor_for_downscaling
            and self.downscalePrecipitationOption
        ):
            self.precipitation = vos.readDownscalingMeteo(
                netcdf_file_name,
                "automatic",
                str(currTimeStep.fulldate),
                useDoy=method_for_time_index,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )

        else:
            self.precipitation = vos.netcdf2PCRobjClone(
                netcdf_file_name,
                "automatic",
                str(currTimeStep.fulldate),
                useDoy=method_for_time_index,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )

        # RvB (13 Jul 2016): apply the conversion constant and factor
        self.precipitation = self.preConst + self.preFactor * self.precipitation

        self.precipitation = pcr.max(0.0, self.precipitation)
        self.precipitation = pcr.cover(self.precipitation, 0.0)

        # ignore very small precipitation (below 0.00001 m/day or 0.01 kg.m-2.day-1)
        if self.usingDailyTimeStepForcingData and self.rounddownPrecipitation:
            self.precipitation = pcr.rounddown(self.precipitation * 100000.0) / 100000.0

        # method to find the time indices in the temperature netCDF file (default: None, or from the ini file)
        method_for_time_index = None
        method_for_time_index = "daily"
        if (
            "time_index_method_for_temperature_netcdf"
            in list(self.iniItems.meteoOptions.keys())
            and self.iniItems.meteoOptions["time_index_method_for_temperature_netcdf"]
            != "None"
        ):
            method_for_time_index = self.iniItems.meteoOptions[
                "time_index_method_for_temperature_netcdf"
            ]

        netcdf_file_name = self.tmpFileNC

        if (
            "temperature_file_per_month" in list(self.iniItems.meteoOptions.keys())
        ) and (self.iniItems.meteoOptions["temperature_file_per_month"] == "True"):
            try:
                netcdf_file_name = self.tmpFileNC % (
                    int(currTimeStep.year),
                    int(currTimeStep.month),
                    int(currTimeStep.month),
                    int(currTimeStep.year),
                )
            except Exception:
                netcdf_file_name = self.tmpFileNC % (
                    int(currTimeStep.month),
                    int(currTimeStep.year),
                )
            method_for_time_index = "daily_per_monthly_file"

        if self.temperature_set_per_year:
            netcdf_file_name = self.tmpFileNC % (
                int(currTimeStep.year),
                int(currTimeStep.year),
            )

        if self.using_daily_factor_for_downscaling and self.downscaleTemperatureOption:
            self.temperature = vos.readDownscalingMeteo(
                netcdf_file_name,
                "automatic",
                str(currTimeStep.fulldate),
                useDoy=method_for_time_index,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )

        else:
            self.temperature = vos.netcdf2PCRobjClone(
                netcdf_file_name,
                "automatic",
                str(currTimeStep.fulldate),
                useDoy=method_for_time_index,
                cloneMapFileName=self.cloneMap,
                LatitudeLongitude=True,
            )

        # RvB (13 Jul 2016): apply the conversion constant and factor
        self.temperature = self.tmpConst + self.tmpFactor * self.temperature

        if self.refETPotMethod == "Input":

            # method to find the time indices in the reference potential ET netCDF file (default: None, or from the ini file)
            method_for_time_index = None
            method_for_time_index = "daily"
            if (
                "time_index_method_for_ref_pot_et_netcdf"
                in list(self.iniItems.meteoOptions.keys())
                and self.iniItems.meteoOptions[
                    "time_index_method_for_ref_pot_et_netcdf"
                ]
                != "None"
            ):
                method_for_time_index = self.iniItems.meteoOptions[
                    "time_index_method_for_ref_pot_et_netcdf"
                ]

            netcdf_file_name = self.etpFileNC

            if (
                "refETPotFileNC_file_per_month"
                in list(self.iniItems.meteoOptions.keys())
            ) and (
                self.iniItems.meteoOptions["refETPotFileNC_file_per_month"] == "True"
            ):
                try:
                    netcdf_file_name = self.etpFileNC % (
                        int(currTimeStep.year),
                        int(currTimeStep.month),
                        int(currTimeStep.month),
                        int(currTimeStep.year),
                    )
                except Exception:
                    netcdf_file_name = self.etpFileNC % (
                        int(currTimeStep.month),
                        int(currTimeStep.year),
                    )
                method_for_time_index = "daily_per_monthly_file"

            if self.temperature_set_per_year:
                netcdf_file_name = self.etpFileNC % (
                    int(currTimeStep.year),
                    int(currTimeStep.year),
                )

            if (
                self.using_daily_factor_for_downscaling
                and self.downscaleReferenceETPotOption
            ):
                self.referencePotET = vos.readDownscalingMeteo(
                    netcdf_file_name,
                    "automatic",
                    str(currTimeStep.fulldate),
                    useDoy=method_for_time_index,
                    cloneMapFileName=self.cloneMap,
                    LatitudeLongitude=True,
                )

            else:
                self.referencePotET = vos.netcdf2PCRobjClone(
                    netcdf_file_name,
                    "automatic",
                    str(currTimeStep.fulldate),
                    useDoy=method_for_time_index,
                    cloneMapFileName=self.cloneMap,
                    LatitudeLongitude=True,
                )

            # RvB (13 Jul 2016): apply the conversion constant and factor
            self.referencePotET = (
                self.refETPotConst + self.refETPotFactor * self.referencePotET
            )

        # extra meteo variables (needed for the Penman-Monteith method)
        for meteo_var_name in self.extra_meteo_var_names:
            vars(self)[meteo_var_name] = None
            if meteo_var_name in list(
                self.iniItems.meteoOptions.keys()
            ) and self.iniItems.meteoOptions[meteo_var_name].endswith(
                (".nc", ".nc4", ".nc3")
            ):

                method_for_time_index = None
                method_for_time_index = "daily"
                netcdf_file_name = vos.getFullPath(
                    self.iniItems.meteoOptions[meteo_var_name], self.inputDir
                )
                vars(self)[meteo_var_name] = vos.netcdf2PCRobjClone(
                    ncFile=netcdf_file_name,
                    varName="automatic",
                    dateInput=str(currTimeStep.fulldate),
                    useDoy=method_for_time_index,
                    cloneMapFileName=self.cloneMap,
                )

                # apply the conversion factor and constant
                vars(self)[meteo_var_name] = (
                    vars(self)["consta_for_" + meteo_var_name]
                    + vars(self)["factor_for_" + meteo_var_name]
                    * vars(self)[meteo_var_name]
                )
