import datetime
import logging

import pcraster as pcr

from pcrglobwb import variable_list as varDicts
from pcrglobwb.common import virtualOS as vos
from pcrglobwb.ncConverter import PCR2netCDF

logger = logging.getLogger(__name__)


class Reporting(object):

    def __init__(self, configuration, model, modelTime):

        # model (e.g. PCR-GLOBWB) and model time object
        self._model = model
        self._modelTime = modelTime

        self.configuration = configuration

        self.initiate_reporting()

        self.landmask_for_reporting = None
        if (
            "landmask_for_reporting" in list(configuration.reportingOptions.keys())
            and self.configuration.reportingOptions["landmask_for_reporting"] != "None"
        ):
            self.landmask_for_reporting = vos.readPCRmapClone(
                configuration.reportingOptions["landmask_for_reporting"],
                configuration.cloneMap,
                configuration.tmpDir,
                configuration.globalOptions["inputDir"],
            )

    def initiate_reporting(self):

        if (
            "is_sub_run" in list(self.configuration.reportingOptions.keys())
            and self.configuration.reportingOptions["is_sub_run"] == "True"
        ):
            # output directory for netCDF files
            self.outNCDir = str(self.configuration.outNCDir)

            # RvB (23 Feb 2017): specific attributes to allow for multiple netcdfAttributes
            if "netcdfAttributesOptions" in list(vars(self.configuration).keys()):
                logger.info(
                    "Passing specific netcdf attributes to the output files created"
                )
                specificAttributeDictionary = self.configuration.netcdfAttributesOptions
            else:
                specificAttributeDictionary = None
            self.netcdfObj = PCR2netCDF(self.configuration, specificAttributeDictionary)
            print("works")

            # netCDF output: daily
            self.outDailyTotNC = ["None"]
            try:
                self.outDailyTotNC = list(
                    set(self.configuration.reportingOptions["outDailyTotNC"].split(","))
                )
            except Exception:
                pass

            # monthly totals
            self.outMonthTotNC = ["None"]
            try:
                self.outMonthTotNC = list(
                    set(self.configuration.reportingOptions["outMonthTotNC"].split(","))
                )
            except Exception:
                pass

            # monthly averages
            self.outMonthAvgNC = ["None"]
            try:
                self.outMonthAvgNC = list(
                    set(self.configuration.reportingOptions["outMonthAvgNC"].split(","))
                )
            except Exception:
                pass

            # end of month
            self.outMonthEndNC = ["None"]
            try:
                self.outMonthEndNC = list(
                    set(self.configuration.reportingOptions["outMonthEndNC"].split(","))
                )
            except Exception:
                pass

            # monthly maximum
            self.outMonthMaxNC = ["None"]
            try:
                self.outMonthMaxNC = list(
                    set(self.configuration.reportingOptions["outMonthMaxNC"].split(","))
                )
            except Exception:
                pass

            # yearly totals
            self.outAnnuaTotNC = ["None"]
            try:
                self.outAnnuaTotNC = list(
                    set(self.configuration.reportingOptions["outAnnuaTotNC"].split(","))
                )
            except Exception:
                pass

            # yearly averages
            self.outAnnuaAvgNC = ["None"]
            try:
                self.outAnnuaAvgNC = list(
                    set(self.configuration.reportingOptions["outAnnuaAvgNC"].split(","))
                )
            except Exception:
                pass

            # end of year
            self.outAnnuaEndNC = ["None"]
            try:
                self.outAnnuaEndNC = list(
                    set(self.configuration.reportingOptions["outAnnuaEndNC"].split(","))
                )
            except Exception:
                pass

            # yearly maximum
            self.outAnnuaMaxNC = ["None"]
            try:
                self.outAnnuaMaxNC = list(
                    set(self.configuration.reportingOptions["outAnnuaMaxNC"].split(","))
                )
            except Exception:
                pass

            # daily upstream average (through the LDD)
            self.outDailyTotUpsAvgNC = ["None"]
            try:
                self.outDailyTotUpsAvgNC = list(
                    set(
                        self.configuration.reportingOptions[
                            "outDailyTotUpsAvgNC"
                        ].split(",")
                    )
                )
            except Exception:
                pass

            # variables to report
            self.variables_for_report = (
                self.outDailyTotNC
                + self.outMonthTotNC
                + self.outMonthAvgNC
                + self.outMonthEndNC
                + self.outMonthMaxNC
                + self.outAnnuaTotNC
                + self.outAnnuaAvgNC
                + self.outAnnuaEndNC
                + self.outMonthMaxNC
                + self.outDailyTotUpsAvgNC
            )

        else:
            # output directory for netCDF files
            self.outNCDir = str(self.configuration.outNCDir)

            # RvB (23 Feb 2017): specific attributes to allow for multiple netcdfAttributes
            if "netcdfAttributesOptions" in list(vars(self.configuration).keys()):
                logger.info(
                    "Passing specific netcdf attributes to the output files created"
                )
                specificAttributeDictionary = self.configuration.netcdfAttributesOptions
            else:
                specificAttributeDictionary = None
            self.netcdfObj = PCR2netCDF(self.configuration, specificAttributeDictionary)

            # netCDF output: daily
            self.outDailyTotNC = ["None"]
            try:
                self.outDailyTotNC = list(
                    set(self.configuration.reportingOptions["outDailyTotNC"].split(","))
                )
            except Exception:
                pass
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:

                    logger.info(
                        "Creating the netcdf file for daily reporting for variable %s.",
                        str(var),
                    )

                    short_name = varDicts.netcdf_short_name[var]
                    unit = varDicts.netcdf_unit[var]
                    long_name = varDicts.netcdf_long_name[var]
                    if long_name is None:
                        long_name = short_name
                    standard_name = short_name
                    if var in list(varDicts.netcdf_standard_name.keys()):
                        standard_name = varDicts.netcdf_standard_name[var]

                    self.netcdfObj.createNetCDF(
                        self.outNCDir + "/" + str(var) + "_dailyTot_output.nc",
                        short_name,
                        unit,
                        long_name,
                        standard_name,
                    )

        # weekly totals
        self.outWeekTotNC = ["None"]
        try:
            self.outWeekTotNC = self.configuration.reportingOptions["outWeekTotNC"].split(
                ","
            )
        except Exception:
            pass
        if self.outWeekTotNC[0] != "None":
            for var in self.outWeekTotNC:
                # accumulator
                vars(self)[var + "WeekTot"] = None

                logger.info(
                    "Creating the netcdf file for weekly accumulation reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_weekly_total_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_weekTot_output.nc",
                    short_name,
                    unit,
                    long_name,
                )

        self.outWeekAvgNC = ["None"]
        try:
            self.outWeekAvgNC = list(
                set(self.configuration.reportingOptions["outWeekAvgNC"].split(","))
            )
        except Exception:
            pass

        if self.outWeekAvgNC[0] != "None":
            for var in self.outWeekAvgNC:
                # accumulator
                vars(self)[var + "WeekTot"] = None

                vars(self)[var + "WeekAvg"] = None

                logger.info(
                    "Creating the netcdf file for weekly average reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_weekAvg_output.nc",
                    short_name,
                    unit,
                    long_name,
                )

        # monthly totals
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = list(
                set(self.configuration.reportingOptions["outMonthTotNC"].split(","))
            )
        except Exception:
            pass
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:
                # accumulator
                vars(self)[var + "MonthTot"] = None

                logger.info(
                    "Creating the netcdf file for monthly accumulation reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_monthly_total_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_monthTot_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # monthly averages
        self.outMonthAvgNC = ["None"]
        try:
            self.outMonthAvgNC = list(
                set(self.configuration.reportingOptions["outMonthAvgNC"].split(","))
            )
        except Exception:
            pass
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:
                # accumulator
                vars(self)[var + "MonthTot"] = None

                vars(self)[var + "MonthAvg"] = None

                logger.info(
                    "Creating the netcdf file for monthly average reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_monthAvg_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

            # end of month
        self.outMonthEndNC = ["None"]
        try:
            self.outMonthEndNC = list(
                set(self.configuration.reportingOptions["outMonthEndNC"].split(","))
            )
        except Exception:
            pass
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:
                logger.info(
                    "Creating the netcdf file for monthly end reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_monthEnd_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # monthly maximum
        self.outMonthMaxNC = ["None"]
        try:
            self.outMonthMaxNC = list(
                set(self.configuration.reportingOptions["outMonthMaxNC"].split(","))
            )
        except Exception:
            pass
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:
                logger.info(
                    "Creating the netcdf file for monthly maximum reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_monthMax_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

            # yearly totals
        self.outAnnuaTotNC = ["None"]
        try:
            self.outAnnuaTotNC = list(
                set(self.configuration.reportingOptions["outAnnuaTotNC"].split(","))
            )
        except Exception:
            pass
        if self.outAnnuaTotNC[0] != "None":
            for var in self.outAnnuaTotNC:
                # accumulator
                vars(self)[var + "AnnuaTot"] = None

                logger.info(
                    "Creating the netcdf file for annual accumulation reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_yearly_total_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_annuaTot_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # yearly averages
        self.outAnnuaAvgNC = ["None"]
        try:
            self.outAnnuaAvgNC = list(
                set(self.configuration.reportingOptions["outAnnuaAvgNC"].split(","))
            )
        except Exception:
            pass
        if self.outAnnuaAvgNC[0] != "None":
            for var in self.outAnnuaAvgNC:
                vars(self)[var + "AnnuaAvg"] = None

                # accumulator
                vars(self)[var + "AnnuaTot"] = None

                logger.info(
                    "Creating the netcdf file for annual average reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_annuaAvg_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # end of year
        self.outAnnuaEndNC = ["None"]
        try:
            self.outAnnuaEndNC = list(
                set(self.configuration.reportingOptions["outAnnuaEndNC"].split(","))
            )
        except Exception:
            pass
        if self.outAnnuaEndNC[0] != "None":
            for var in self.outAnnuaEndNC:
                logger.info(
                    "Creating the netcdf file for annual end reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_annuaEnd_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # yearly maximum
        self.outAnnuaMaxNC = ["None"]
        try:
            self.outAnnuaMaxNC = list(
                set(self.configuration.reportingOptions["outAnnuaMaxNC"].split(","))
            )
        except Exception:
            pass
        if self.outAnnuaMaxNC[0] != "None":
            for var in self.outAnnuaMaxNC:
                logger.info(
                    "Creating the netcdf file for annual maximum reporting for variable %s.",
                    str(var),
                )

                short_name = varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_annuaMax_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # daily upstream average (through the LDD)
        self.outDailyTotUpsAvgNC = ["None"]
        try:
            self.outDailyTotUpsAvgNC = list(
                set(
                    self.configuration.reportingOptions["outDailyTotUpsAvgNC"].split(
                        ","
                    )
                )
            )
        except Exception:
            pass
        if self.outDailyTotUpsAvgNC[0] != "None":
            for var in self.outDailyTotUpsAvgNC:
                logger.info(
                    "Creating the netcdf file for daily upstream average (through LDD) reporting for variable %s.",
                    str(var),
                )

                short_name = "upstream_average_" + varDicts.netcdf_short_name[var]
                unit = varDicts.netcdf_unit[var]
                long_name = varDicts.netcdf_long_name[var]
                if long_name is None:
                    long_name = short_name
                long_name = "upstream_average_" + long_name
                standard_name = short_name
                if var in list(varDicts.netcdf_standard_name.keys()):
                    standard_name = varDicts.netcdf_standard_name[var]

                self.netcdfObj.createNetCDF(
                    self.outNCDir + "/" + str(var) + "_dailyTotUpsAvg_output.nc",
                    short_name,
                    unit,
                    long_name,
                    standard_name,
                )

        # variables to report
        self.variables_for_report = (
            self.outDailyTotNC
            + self.outWeekTotNC
            + self.outWeekAvgNC
            + self.outMonthTotNC
            + self.outMonthAvgNC
            + self.outMonthEndNC
            + self.outMonthMaxNC
            + self.outAnnuaTotNC
            + self.outAnnuaAvgNC
            + self.outAnnuaEndNC
            + self.outMonthMaxNC
            + self.outDailyTotUpsAvgNC
        )

    def post_processing(self):

        self.basic_post_processing()
        self.additional_post_processing()
        # RvB (23 Feb 2017): post-processing for the eartH2Observe project
        self.e2o_post_processing()

        # post-processing for the Ulysses project
        self.ulysses_post_processing()

        # save model parameters that are constant over time
        if self._modelTime.timeStepPCR == 1:
            # recession coefficient (day-1)
            pcr.report(
                pcr.ifthen(
                    self._model.routing.landmask, self._model.groundwater.recessionCoeff
                ),
                self.configuration.mapsDir + "/globalalpha.map",
            )

    def basic_post_processing(self):
        # forcing
        self.precipitation = pcr.ifthen(
            self._model.routing.landmask, self._model.meteo.precipitation
        )
        self.temperature = pcr.ifthen(
            self._model.routing.landmask, self._model.meteo.temperature
        )
        self.referencePotET = pcr.ifthen(
            self._model.routing.landmask, self._model.meteo.referencePotET
        )

        # potential and actual evaporation from the land surface (m)
        self.totalLandSurfacePotET = self._model.landSurface.totalPotET
        self.totLandSurfaceActuaET = self._model.landSurface.actualET

        self.fractionLandSurfaceET = vos.getValDivZero(
            self.totLandSurfaceActuaET, self.totalLandSurfacePotET, vos.smallNumber
        )

        self.interceptStor = self._model.landSurface.interceptStor

        self.snowCoverSWE = self._model.landSurface.snowCoverSWE
        self.snowFreeWater = self._model.landSurface.snowFreeWater

        # added by Joren: snow transport
        self.incomingVolSnow = self._model.landSurface.incomingVolSnow
        self.transportVolSnow = self._model.landSurface.transportVolSnow

        self.incomingFreeWater = self._model.landSurface.incomingFreeWater
        self.transportFreeWater = self._model.landSurface.transportFreeWater

        self.topWaterLayer = self._model.landSurface.topWaterLayer
        self.storUppTotal = self._model.landSurface.storUppTotal
        self.storLowTotal = self._model.landSurface.storLowTotal

        self.interceptEvap = self._model.landSurface.interceptEvap
        self.actSnowFreeWaterEvap = self._model.landSurface.actSnowFreeWaterEvap
        self.topWaterLayerEvap = self._model.landSurface.openWaterEvap
        self.actBareSoilEvap = self._model.landSurface.actBareSoilEvap

        self.actTranspiTotal = self._model.landSurface.actTranspiTotal
        self.actTranspiUppTotal = self._model.landSurface.actTranspiUppTotal
        self.actTranspiLowTotal = self._model.landSurface.actTranspiLowTotal

        self.directRunoff = self._model.landSurface.directRunoff
        self.interflowTotal = self._model.landSurface.interflowTotal

        self.infiltration = self._model.landSurface.infiltration
        self.gwRecharge = self._model.landSurface.gwRecharge
        self.gwNetCapRise = pcr.ifthenelse(
            self._model.landSurface.gwRecharge < 0.0, self.gwRecharge * (-1.0), 0.0
        )

        # water demand (m)
        self.irrGrossDemand = self._model.landSurface.irrGrossDemand
        self.nonIrrGrossDemand = self._model.landSurface.nonIrrGrossDemand
        self.totalGrossDemand = self._model.landSurface.totalPotentialGrossDemand

        self.satDegUpp = self._model.landSurface.satDegUppTotal
        self.satDegLow = self._model.landSurface.satDegLowTotal

        self.satDegTotal = self._model.landSurface.satDegTotal

        self.storGroundwater = self._model.groundwater.storGroundwater

        self.baseflow = self._model.groundwater.baseflow

        # abstraction (m)
        self.desalinationAbstraction = self._model.landSurface.desalinationAbstraction
        self.surfaceWaterAbstraction = self._model.landSurface.actSurfaceWaterAbstract
        self.nonFossilGroundwaterAbstraction = (
            self._model.groundwater.nonFossilGroundwaterAbs
        )
        self.fossilGroundwaterAbstraction = (
            self._model.groundwater.fossilGroundwaterAbstr
        )
        self.totalAbstraction = (
            self.desalinationAbstraction
            + self.surfaceWaterAbstraction
            + self.nonFossilGroundwaterAbstraction
            + self.fossilGroundwaterAbstraction
        )

        # total evaporation from land and water fractions (m)
        self.totalEvaporation = (
            self._model.landSurface.actualET + self._model.routing.waterBodyEvaporation
        )

        self.fractionTotalEvaporation = vos.getValDivZero(
            self.totalEvaporation,
            self._model.landSurface.totalPotET + self._model.routing.waterBodyPotEvap,
            vos.smallNumber,
        )

        # total potential evaporation from land and water fractions (m)
        self.totalPotentialEvaporation = (
            self._model.landSurface.totalPotET + self._model.routing.waterBodyPotEvap
        )

        # runoff from the land surface, excluding local changes in water bodies (m)
        self.runoff = self._model.routing.runoff

        # discharge (m3/s)
        self.discharge = self._model.routing.disChanWaterBody

        # soil moisture of (approximately) the upper 5 cm of soil
        if self._model.landSurface.numberOfSoilLayers == 3:
            # (m)
            self.storUppSurface = self._model.landSurface.storUpp000005
            # (%)
            self.satDegUppSurface = self._model.landSurface.satDegUpp000005

        # fraction of surface water bodies
        self.dynamicFracWat = self._model.routing.dynamicFracWat

        if self._model.landSurface.numberOfSoilLayers == 3:
            self.storUpp000005 = self._model.landSurface.storUpp000005
            self.storUpp005030 = self._model.landSurface.storUpp005030
            self.storLow030150 = self._model.landSurface.storLow030150

    def additional_post_processing(self):
        # users can add their own post-processing here

        # water balance of the land surface (excluding surface water bodies)
        if "land_surface_water_balance" in self.variables_for_report:
            self.land_surface_water_balance = self._model.waterBalance

        # accumulated directRunoff along the drainage network (m3/s)
        if "accuDirectRunoff" in self.variables_for_report:
            self.accuDirectRunoff = (
                pcr.catchmenttotal(
                    self.directRunoff * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # accumulated interflowTotal along the drainage network (m3/s)
        if "accuInterflowTotal" in self.variables_for_report:
            self.accuInterflowTotal = (
                pcr.catchmenttotal(
                    self.interflowTotal * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # accumulated baseflow along the drainage network (m3/s)
        if "accuBaseflow" in self.variables_for_report:
            self.accuBaseflow = (
                pcr.catchmenttotal(
                    self.baseflow * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # accumulated runoff along the drainage network (m3/s)
        if "accuRunoff" in self.variables_for_report:
            self.accuRunoff = (
                pcr.catchmenttotal(
                    self.runoff * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # accumulated surface water abstraction along the drainage network (m3/s)
        if "accuSurfaceWaterAbstraction" in self.variables_for_report:
            self.accuSurfaceWaterAbstraction = (
                pcr.catchmenttotal(
                    self.surfaceWaterAbstraction * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # local changes in water bodies (abstraction, return flow, evaporation, bed exchange), excluding runoff
        self.local_water_body_flux = (
            self._model.routing.local_input_to_surface_water
            / self._model.routing.cellArea
            - self.runoff
        )

        # total runoff from local land surface runoff and local changes in water bodies (m); equals
        # routing.local_input_to_surface_water / routing.cellArea
        self.totalRunoff = self.runoff + self.local_water_body_flux

        # water body evaporation from surface water fractions only (m)
        self.waterBodyActEvaporation = self._model.routing.waterBodyEvaporation
        self.waterBodyPotEvaporation = self._model.routing.waterBodyPotEvap

        self.fractionWaterBodyEvaporation = vos.getValDivZero(
            self.waterBodyActEvaporation, self.waterBodyPotEvaporation, vos.smallNumber
        )

        # accumulated water body actual evaporation along the drainage network (m3/s)
        if "accuWaterBodyActEvaporation" in self.variables_for_report:
            self.accuWaterBodyActEvaporation = (
                pcr.catchmenttotal(
                    self.waterBodyActEvaporation * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # land surface evaporation (m)
        self.actualET = self._model.landSurface.actualET

        self.storGroundwaterFossil = self._model.groundwater.storGroundwaterFossil

        # total (non-fossil and fossil) groundwater storage
        self.storGroundwaterTotal = (
            self._model.groundwater.storGroundwater
            + self._model.groundwater.storGroundwaterFossil
        )

        # accumulated total groundwater storage along the drainage network (m3)
        if "accuStorGroundwaterTotalVolume" in self.variables_for_report:
            self.accuStorGroundwaterTotalVolume = pcr.catchmenttotal(
                self.storGroundwaterTotal * self._model.routing.cellArea,
                self._model.routing.lddMap,
            )

        # total active storage thickness of the water column (m): interception, snow, soil and non-fossil
        # groundwater (excluding fossil groundwater)
        self.totalActiveStorageThickness = pcr.ifthen(
            self._model.routing.landmask,
            self._model.routing.channelStorage / self._model.routing.cellArea
            + self._model.landSurface.totalSto
            + self._model.groundwater.storGroundwater,
        )

        # total water storage thickness of the water column (m): interception, snow, soil, and non-fossil
        # and fossil groundwater; usually used for GRACE comparison
        self.totalWaterStorageThickness = (
            self.totalActiveStorageThickness
            + self._model.groundwater.storGroundwaterFossil
        )

        # total water storage volume of the water column (m3)
        self.totalWaterStorageVolume = (
            self.totalWaterStorageThickness * self._model.routing.cellArea
        )

        # surface water storage (m); may be negative
        self.surfaceWaterStorage = (
            self._model.routing.channelStorage / self._model.routing.cellArea
        )

        # river/surface water level above the channel/surface water bottom
        self.surfaceWaterLevel = pcr.ifthenelse(
            self.dynamicFracWat > 0.0,
            self._model.routing.channelStorage
            / (self.dynamicFracWat * self._model.routing.cellArea),
            0.0,
        )
        self.surfaceWaterLevel = pcr.max(
            0.0, pcr.ifthen(self._model.routing.landmask, self.surfaceWaterLevel)
        )

        # Menno: fractions of the water sources allocated to satisfy the water demand per cell
        self.fracSurfaceWaterAllocation = pcr.ifthen(
            self._model.routing.landmask,
            vos.getValDivZero(
                self._model.landSurface.allocSurfaceWaterAbstract,
                self.totalGrossDemand,
                vos.smallNumber,
            ),
        )
        self.fracSurfaceWaterAllocation = pcr.ifthenelse(
            self.totalGrossDemand < vos.smallNumber,
            1.0,
            self.fracSurfaceWaterAllocation,
        )

        self.fracNonFossilGroundwaterAllocation = pcr.ifthen(
            self._model.routing.landmask,
            vos.getValDivZero(
                self._model.groundwater.allocNonFossilGroundwater,
                self.totalGrossDemand,
                vos.smallNumber,
            ),
        )

        self.fracOtherWaterSourceAllocation = pcr.ifthen(
            self._model.routing.landmask,
            vos.getValDivZero(
                self._model.groundwater.unmetDemand,
                self.totalGrossDemand,
                vos.smallNumber,
            ),
        )

        self.fracDesalinatedWaterAllocation = pcr.ifthen(
            self._model.routing.landmask,
            vos.getValDivZero(
                self._model.landSurface.desalinationAllocation,
                self.totalGrossDemand,
                vos.smallNumber,
            ),
        )

        self.totalFracWaterSourceAllocation = (
            self.fracSurfaceWaterAllocation
            + self.fracNonFossilGroundwaterAllocation
            + self.fracOtherWaterSourceAllocation
            + self.fracDesalinatedWaterAllocation
        )

        # Stefanie: lake and reservoir storage (m3), after lake/reservoir outflow
        self.waterBodyStorage = pcr.ifthen(
            self._model.routing.landmask,
            pcr.cover(
                pcr.ifthen(
                    pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.0,
                    self._model.routing.WaterBodies.waterBodyStorage,
                ),
                0.0,
            ),
        )
        # (m)
        self.snowMelt = self._model.landSurface.snowMelt

        # (m3)
        self.channelStorage = pcr.ifthen(
            self._model.routing.landmask,
            pcr.cover(self._model.routing.channelStorage, 0.0),
        )

        # DynQual
        if self._model.routing.quality:
            # water temperature (K)
            self.waterTemp = self._model.routing.waterTemp

            # water height (m)
            self.waterHeight = self._model.routing.water_height

            # ice thickness (m)
            self.iceThickness = self._model.routing.iceThickness

            # power plant flows: minimum demands of temperature-dependent technologies (m3/s)
            self.powerplants_fw_qmin = pcr.ifthen(
                self._model.routing.landmask,
                self._model.landSurface.water_demand.water_demand_thermoelectric.powerplants_fw_qmin,
            )
            # water temperature dependent demands of temperature-dependent technologies (m3/s)
            self.powerplants_fw_q = pcr.ifthen(
                self._model.routing.landmask,
                self._model.landSurface.water_demand.water_demand_thermoelectric.powerplants_fw_q,
            )
            # unrouted temperature loadings from power plants (W), temperature-dependent technologies
            self.PowTwload = pcr.ifthen(
                self._model.routing.landmask, self._model.routing.PowTwload
            )

            # salinity pollution (g)
            self.TDSload = self._model.routing.TDSload
            # (g)
            self.routedTDS = self._model.routing.routedTDS
            # (mg/L)
            self.salinity = self._model.routing.salinity
            # (g/s)
            self.TDSflux = pcr.ifthen(
                self._model.routing.salinity != vos.MV,
                self.salinity * self._model.routing.disChanWaterBody,
            )

            if self._model.routing.loadsPerSector:
                # TDS
                self.Dom_TDSload = self._model.routing.Dom_TDSload
                self.Man_TDSload = self._model.routing.Man_TDSload
                self.USR_TDSload = self._model.routing.USR_TDSload
                self.Irr_TDSload = self._model.routing.Irr_TDSload

                self.routedDomTDS = self._model.routing.routedDomTDS
                self.routedManTDS = self._model.routing.routedManTDS
                self.routedUSRTDS = self._model.routing.routedUSRTDS
                self.routedIrrTDS = self._model.routing.routedIrrTDS

            # organic pollution (g)
            self.BODload = self._model.routing.BODload
            # (g)
            self.routedBOD = self._model.routing.routedBOD
            # (mg/L)
            self.organic = self._model.routing.organic
            # (g/s)
            self.BODflux = pcr.ifthen(
                self._model.routing.organic != vos.MV,
                self.organic * self._model.routing.disChanWaterBody,
            )

            if self._model.routing.loadsPerSector:
                # BOD
                self.Dom_BODload = self._model.routing.Dom_BODload
                self.Man_BODload = self._model.routing.Man_BODload
                self.USR_BODload = self._model.routing.USR_BODload
                self.intLiv_BODload = self._model.routing.intLiv_BODload
                self.extLiv_BODload = self._model.routing.extLiv_BODload

                self.routedDomBOD = self._model.routing.routedDomBOD
                self.routedManBOD = self._model.routing.routedManBOD
                self.routedUSRBOD = self._model.routing.routedUSRBOD
                self.routedintLivBOD = self._model.routing.routedintLivBOD
                self.routedextLivBOD = self._model.routing.routedextLivBOD

            # dissolved oxygen (mg/L)
            self.dissolved_oxygen = self._model.routing.dissolved_oxygen

            # pathogen pollution (million cfu)
            self.FCload = self._model.routing.FCload
            # (million cfu)
            self.routedFC = self._model.routing.routedFC
            # (cfu/100mL)
            self.pathogen = self._model.routing.pathogen
            # (million cfu/s)
            self.FCflux = pcr.ifthen(
                self._model.routing.pathogen != vos.MV,
                self.pathogen * self._model.routing.disChanWaterBody * 0.01,
            )

            if self._model.routing.loadsPerSector:
                # FC
                self.Dom_FCload = self._model.routing.Dom_FCload
                self.Man_FCload = self._model.routing.Man_FCload
                self.USR_FCload = self._model.routing.USR_FCload
                self.intLiv_FCload = self._model.routing.intLiv_FCload
                self.extLiv_FCload = self._model.routing.extLiv_FCload

                self.routedDomFC = self._model.routing.routedDomFC
                self.routedManFC = self._model.routing.routedManFC
                self.routedUSRFC = self._model.routing.routedUSRFC
                self.routedintLivFC = self._model.routing.routedintLivFC
                self.routedextLivFC = self._model.routing.routedextLivFC

        # examples of reporting variables of certain land cover types (m/day, averaged over the cell area)
        self.precipitation_at_irrigation = pcr.ifthen(
            self._model.routing.landmask, pcr.spatial(pcr.scalar(0.0))
        )
        self.netLqWaterToSoil_at_irrigation = pcr.ifthen(
            self._model.routing.landmask, pcr.spatial(pcr.scalar(0.0))
        )
        self.evaporation_from_irrigation = pcr.ifthen(
            self._model.routing.landmask, pcr.spatial(pcr.scalar(0.0))
        )
        self.transpiration_from_irrigation = pcr.ifthen(
            self._model.routing.landmask, pcr.spatial(pcr.scalar(0.0))
        )
        if self._model.landSurface.includeIrrigation:
            self.precipitation_at_irrigation = (
                self._model.meteo.precipitation
                * self._model.landSurface.landCoverObj["irrPaddy"].fracVegCover
                + self._model.meteo.precipitation
                * self._model.landSurface.landCoverObj["irrNonPaddy"].fracVegCover
            )
            self.netLqWaterToSoil_at_irrigation = (
                self._model.landSurface.landCoverObj["irrPaddy"].netLqWaterToSoil
                * self._model.landSurface.landCoverObj["irrPaddy"].fracVegCover
                + self._model.landSurface.landCoverObj["irrNonPaddy"].netLqWaterToSoil
                * self._model.landSurface.landCoverObj["irrNonPaddy"].fracVegCover
            )
            self.evaporation_from_irrigation = (
                self._model.landSurface.landCoverObj["irrPaddy"].actualET
                * self._model.landSurface.landCoverObj["irrPaddy"].fracVegCover
                + self._model.landSurface.landCoverObj["irrNonPaddy"].actualET
                * self._model.landSurface.landCoverObj["irrNonPaddy"].fracVegCover
            )
            self.transpiration_from_irrigation = (
                self._model.landSurface.landCoverObj["irrPaddy"].actTranspiTotal
                * self._model.landSurface.landCoverObj["irrPaddy"].fracVegCover
                + self._model.landSurface.landCoverObj["irrNonPaddy"].actTranspiTotal
                * self._model.landSurface.landCoverObj["irrNonPaddy"].fracVegCover
            )

        # total groundwater abstraction (m), assuming otherWaterSourceAbstraction is fossil groundwater abstraction
        self.totalGroundwaterAbstraction = (
            self.nonFossilGroundwaterAbstraction + self.fossilGroundwaterAbstraction
        )

        # net liquid water passing to the soil
        self.net_liquid_water_to_soil = self._model.landSurface.netLqWaterToSoil

        # consumptive water use and return flow of the non-irrigation water demand (m/day)
        self.nonIrrWaterConsumption = self._model.landSurface.nonIrrWaterConsumption
        self.nonIrrReturnFlow = self._model.landSurface.nonIrrReturnFlow

        # accumulated non-irrigation return flow along the drainage network (m3/s)
        if "accuNonIrrReturnFlow" in self.variables_for_report:
            self.accuNonIrrReturnFlow = (
                pcr.catchmenttotal(
                    self.nonIrrReturnFlow * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # return flow due to groundwater abstraction (m/day)
        self.groundwaterAbsReturnFlow = (
            self._model.routing.riverbedExchange / self._model.routing.cellArea
        )
        # note: before 24 May 2015 this variable was not divided by routing.cellArea; it is zero if there
        # is no groundwater abstraction

        # surface water infiltration to groundwater (m/day); a better name than groundwaterAbsReturnFlow
        self.surfaceWaterInf = (
            self._model.routing.riverbedExchange / self._model.routing.cellArea
        )

        # accumulated surface water infiltration along the drainage network (m3/s)
        if "accuSurfaceWaterInf" in self.variables_for_report:
            self.accuSurfaceWaterInf = (
                pcr.catchmenttotal(
                    self.surfaceWaterInf * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # net groundwater discharge (m/day)
        self.netGroundwaterDischarge = self.baseflow - self.surfaceWaterInf

        # accumulated net groundwater discharge along the drainage network (m3/s)
        if "accuNetGroundwaterDischarge" in self.variables_for_report:
            self.accuNetGroundwaterDischarge = (
                pcr.catchmenttotal(
                    self.netGroundwaterDischarge * self._model.routing.cellArea,
                    self._model.routing.lddMap,
                )
                / vos.secondsPerDay()
            )

        # water withdrawal of the irrigation sector (m/day)
        self.irrigationWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.irrigationWaterWithdrawal
            / self._model.routing.cellArea,
        )

        # gross demands of the domestic, industry, livestock, manufacturing and thermoelectric sectors (m/day)
        self.domesticGrossDemand = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.water_demand.water_demand_domestic.domesticGrossDemand,
        )
        self.industryGrossDemand = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.water_demand.water_demand_industry.industryGrossDemand,
        )
        self.livestockGrossDemand = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.water_demand.water_demand_livestock.livestockGrossDemand,
        )
        self.manufactureGrossDemand = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.water_demand.water_demand_manufacture.manufactureGrossDemand,
        )
        self.thermoelectricGrossDemand = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.water_demand.water_demand_thermoelectric.thermoelectricGrossDemand,
        )

        # water withdrawal of the domestic, industry, livestock, manufacturing and thermoelectric sectors
        self.domesticWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.domesticWaterWithdrawal
            / self._model.routing.cellArea,
        )
        self.industryWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.industryWaterWithdrawal
            / self._model.routing.cellArea,
        )
        self.livestockWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.livestockWaterWithdrawal
            / self._model.routing.cellArea,
        )
        self.manufactureWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.manufactureWaterWithdrawal
            / self._model.routing.cellArea,
        )
        self.thermoelectricWaterWithdrawal = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.thermoelectricWaterWithdrawal
            / self._model.routing.cellArea,
        )

        # return flows of the domestic, industry, livestock, manufacturing and thermoelectric sectors
        self.domesticReturnFlow = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.nonIrrReturnFlowVolumePerSector["domestic"]
            / self._model.routing.cellArea,
        )
        self.industryReturnFlow = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.nonIrrReturnFlowVolumePerSector["industry"]
            / self._model.routing.cellArea,
        )
        self.livestockReturnFlow = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.nonIrrReturnFlowVolumePerSector["livestock"]
            / self._model.routing.cellArea,
        )
        self.manufactureReturnFlow = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.nonIrrReturnFlowVolumePerSector["manufacture"]
            / self._model.routing.cellArea,
        )
        self.thermoelectricReturnFlow = pcr.ifthen(
            self._model.routing.landmask,
            self._model.landSurface.nonIrrReturnFlowVolumePerSector["thermoelectric"]
            / self._model.routing.cellArea,
        )

        # all water withdrawal variables as volume (m3)
        waterWithdrawalVariables = [
            "totalGroundwaterAbstraction",
            "surfaceWaterAbstraction",
            "desalinationAbstraction",
            "domesticWaterWithdrawal",
            "industryWaterWithdrawal",
            "livestockWaterWithdrawal",
            "irrigationWaterWithdrawal",
            "irrGrossDemand",
            "nonIrrGrossDemand",
            "totalGrossDemand",
        ]
        for var in waterWithdrawalVariables:
            volVariable = var + "Volume"
            vars(self)[volVariable] = None
            vars(self)[volVariable] = self._model.routing.cellArea * vars(self)[var]

        # net consumptive water use of the irrigation sector, calculated from annual values
        irrigation_water_consumption_volume = (
            self.evaporation_from_irrigation
            * self._model.routing.cellArea
            * self.irrigationWaterWithdrawal
            / (self.precipitation_at_irrigation + self.irrigationWaterWithdrawal)
        )
        self.precipitation_at_irrigation_volume = (
            self.precipitation_at_irrigation * self._model.routing.cellArea
        )
        self.evaporation_from_irrigation_volume = (
            self.evaporation_from_irrigation * self._model.routing.cellArea
        )
        # additional values
        self.netLqWaterToSoil_at_irrigation_volume = (
            self.netLqWaterToSoil_at_irrigation * self._model.routing.cellArea
        )
        self.transpiration_from_irrigation_volume = (
            self.transpiration_from_irrigation * self._model.routing.cellArea
        )

        # fluxes from water bodies (lakes and reservoirs) (m3/s)
        self.lake_and_reservoir_inflow = (
            self._model.routing.WaterBodies.inflowInM3PerSec
        )

        # estimate of the total groundwater storage (m3) and thickness (m); may be negative
        if any(
            var in self.variables_for_report
            for var in (
                "groundwaterVolumeEstimate",
                "groundwaterThicknessEstimate",
                "accuGroundwaterVolumeEstimate",
            )
        ):
            self.groundwaterThicknessEstimate = (
                self.storGroundwater + self.storGroundwaterFossil
            )

            self.groundwaterVolumeEstimate = (
                self.groundwaterThicknessEstimate * self._model.routing.cellArea
            )

            self.accuGroundwaterVolumeEstimate = pcr.catchmenttotal(
                self.groundwaterVolumeEstimate, self._model.routing.lddMap
            )

    def report(self):
        self.post_processing()

        # time stamp for reporting
        timeStamp = datetime.datetime(
            self._modelTime.year, self._modelTime.month, self._modelTime.day, 0
        )

        logger.info("reporting for time %s", self._modelTime.currTime)

        # daily netCDF output
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                short_name = varDicts.netcdf_short_name[var]

                self.netcdfObj.data2NetCDF(
                    self.outNCDir + "/" + str(var) + "_dailyTot_output.nc",
                    short_name,
                    pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                    timeStamp,
                )

        # weekly totals
        if self.outWeekTotNC[0] != "None":
            for var in self.outWeekTotNC:
                # initialize at the start of the simulation or reset at the start of the year
                if self._modelTime.timeStepPCR == 1 or self._modelTime.doy == 1:
                    vars(self)[var + "WeekTot"] = pcr.scalar(0.0)

                valid = pcr.ifthen(
                    pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                )
                vars(self)[var + "WeekTot"] += pcr.ifthenelse(
                    valid, vars(self)[var], pcr.scalar(0.0)
                )
                vars(self)[var + "_ndays_week"] += pcr.ifthenelse(
                    valid, pcr.scalar(1.0), pcr.scalar(0.0)
                )

                # total and report (53 weeks per year)
                if self._modelTime.doy % 7 == 0 or self._modelTime.endYear:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_weekTot_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "WeekTot"), vos.MV),
                        timeStamp,
                    )
                    vars(self)[var + "WeekTot"] = pcr.scalar(0.0)

        # weekly averages
        if self.outWeekAvgNC[0] != "None":
            for var in self.outWeekAvgNC:

                # initialize at the start of the simulation or reset at the start of the year
                if self._modelTime.timeStepPCR == 1 or self._modelTime.doy == 1:
                    vars(self)[var + "WeekTot"] = pcr.scalar(0.0)
                    vars(self)[var + "_ndays_week"] = pcr.scalar(0.0)

                valid = pcr.ifthen(
                    pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                )
                vars(self)[var + "WeekTot"] += pcr.ifthenelse(
                    valid, vars(self)[var], pcr.scalar(0.0)
                )
                vars(self)[var + "_ndays_week"] += pcr.ifthenelse(
                    valid, pcr.scalar(1.0), pcr.scalar(0.0)
                )

                # average and report (53 weeks per year)
                if self._modelTime.doy % 7 == 0 or self._modelTime.endYear:

                    vars(self)[var + "WeekAvg"] = pcr.ifthenelse(
                        vars(self)[var + "_ndays_week"] > 0.0,
                        vars(self)[var + "WeekTot"] / vars(self)[var + "_ndays_week"],
                        pcr.scalar(vos.MV),
                    )

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_weekAvg_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "WeekAvg"), vos.MV),
                        timeStamp,
                    )

                    vars(self)[var + "WeekTot"] = pcr.scalar(0.0)
                    vars(self)[var + "_ndays_week"] = pcr.scalar(0.0)

        # monthly netCDF output: totals
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:

                # initialize at the start of the simulation or reset at the start of the month
                if self._modelTime.timeStepPCR == 1 or self._modelTime.day == 1:
                    vars(self)[var + "MonthTot"] = pcr.scalar(0.0)
                    vars(self)[var + "_ndays_month"] = pcr.scalar(0.0)

                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                valid = pcr.ifthen(
                    pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                )
                vars(self)[var + "MonthTot"] += pcr.ifthenelse(
                    valid, vars(self)[var], pcr.scalar(0.0)
                )
                vars(self)[var + "_ndays_month"] += pcr.ifthenelse(
                    valid, pcr.scalar(1.0), pcr.scalar(0.0)
                )

                if self._modelTime.endMonth:

                    short_name = varDicts.netcdf_short_name[var]

                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_monthTot_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "MonthTot"), vos.MV),
                        timeStamp,
                    )
        # averages
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:

                # only if no accumulator is defined
                if var not in self.outMonthTotNC:

                    # initialize at the start of the simulation or reset at the start of the month
                    if self._modelTime.timeStepPCR == 1 or self._modelTime.day == 1:
                        vars(self)[var + "MonthTot"] = pcr.scalar(0.0)
                        vars(self)[var + "_ndays_month"] = pcr.scalar(0.0)

                    # mask for reporting
                    if self.landmask_for_reporting is not None:
                        vars(self)[var] = pcr.ifthen(
                            self.landmask_for_reporting, vars(self)[var]
                        )

                    valid = pcr.ifthen(
                        pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                    )
                    vars(self)[var + "MonthTot"] += pcr.ifthenelse(
                        valid, vars(self)[var], pcr.scalar(0.0)
                    )
                    vars(self)[var + "_ndays_month"] += pcr.ifthenelse(
                        valid, pcr.scalar(1.0), pcr.scalar(0.0)
                    )

                if self._modelTime.endMonth:
                    vars(self)[var + "MonthAvg"] = pcr.ifthenelse(
                        vars(self)[var + "_ndays_month"] > 0.0,
                        vars(self)[var + "MonthTot"] / vars(self)[var + "_ndays_month"],
                        pcr.scalar(vos.MV),
                    )
                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_monthAvg_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "MonthAvg"), vos.MV),
                        timeStamp,
                    )

        # end of month
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:

                if self._modelTime.endMonth:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_monthEnd_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                        timeStamp,
                    )

        # maximum
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:

                # initialize at the start of the simulation or reset at the start of the month
                if self._modelTime.timeStepPCR == 1 or self._modelTime.day == 1:
                    vars(self)[var + "MonthMax"] = pcr.scalar(0.0)
                    vars(self)[var + "MonthMax"] = vars(self)[var]

                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                vars(self)[var + "MonthMax"] = pcr.max(
                    vars(self)[var], vars(self)[var + "MonthMax"]
                )

                if self._modelTime.endMonth:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_monthMax_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "MonthMax"), vos.MV),
                        timeStamp,
                    )

        # yearly netCDF output: totals
        if self.outAnnuaTotNC[0] != "None":
            for var in self.outAnnuaTotNC:

                # initialize at the start of the simulation or reset at the start of the year
                if self._modelTime.timeStepPCR == 1 or self._modelTime.doy == 1:
                    vars(self)[var + "AnnuaTot"] = pcr.scalar(0.0)
                    vars(self)[var + "_ndays_year"] = pcr.scalar(0.0)

                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                valid = pcr.ifthen(
                    pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                )
                vars(self)[var + "AnnuaTot"] += pcr.ifthenelse(
                    valid, vars(self)[var], pcr.scalar(0.0)
                )
                vars(self)[var + "_ndays_year"] += pcr.ifthenelse(
                    valid, pcr.scalar(1.0), pcr.scalar(0.0)
                )

                if self._modelTime.endYear:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_annuaTot_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "AnnuaTot"), vos.MV),
                        timeStamp,
                    )

        # averages
        if self.outAnnuaAvgNC[0] != "None":
            for var in self.outAnnuaAvgNC:

                # only if no accumulator is defined
                if var not in self.outAnnuaTotNC:

                    # initialize at the start of the simulation or reset at the start of the year
                    if self._modelTime.timeStepPCR == 1 or self._modelTime.doy == 1:
                        vars(self)[var + "AnnuaTot"] = pcr.scalar(0.0)
                        vars(self)[var + "_ndays_year"] = pcr.scalar(0.0)

                    # mask for reporting
                    if self.landmask_for_reporting is not None:
                        vars(self)[var] = pcr.ifthen(
                            self.landmask_for_reporting, vars(self)[var]
                        )

                    valid = pcr.ifthen(
                        pcr.defined(vars(self)[var]), vars(self)[var] != vos.MV
                    )
                    vars(self)[var + "AnnuaTot"] += pcr.ifthenelse(
                        valid, vars(self)[var], pcr.scalar(0.0)
                    )
                    vars(self)[var + "_ndays_year"] += pcr.ifthenelse(
                        valid, pcr.scalar(1.0), pcr.scalar(0.0)
                    )

                if self._modelTime.endYear:

                    vars(self)[var + "AnnuaAvg"] = pcr.ifthenelse(
                        vars(self)[var + "_ndays_year"] > 0.0,
                        vars(self)[var + "AnnuaTot"] / vars(self)[var + "_ndays_year"],
                        pcr.scalar(vos.MV),
                    )

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_annuaAvg_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "AnnuaAvg"), vos.MV),
                        timeStamp,
                    )

        # end of year
        if self.outAnnuaEndNC[0] != "None":
            for var in self.outAnnuaEndNC:

                if self._modelTime.endYear:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_annuaEnd_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var), vos.MV),
                        timeStamp,
                    )

        # maximum
        if self.outAnnuaMaxNC[0] != "None":
            for var in self.outAnnuaMaxNC:

                # initialize at the start of the simulation or reset at the start of the year
                if self._modelTime.timeStepPCR == 1 or self._modelTime.doy == 1:
                    vars(self)[var + "AnnuaMax"] = pcr.scalar(0.0)
                    vars(self)[var + "AnnuaMax"] = vars(self)[var]

                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                vars(self)[var + "AnnuaMax"] = pcr.max(
                    vars(self)[var], vars(self)[var + "AnnuaMax"]
                )

                if self._modelTime.endYear:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(
                        self.outNCDir + "/" + str(var) + "_annuaMax_output.nc",
                        short_name,
                        pcr.pcr2numpy(self.__getattribute__(var + "AnnuaMax"), vos.MV),
                        timeStamp,
                    )

        # daily upstream average (through the LDD)
        if self.outDailyTotUpsAvgNC[0] != "None":
            for var in self.outDailyTotUpsAvgNC:

                # upstream area
                if self._modelTime.timeStepPCR == 1:
                    self.upstream_area = pcr.catchmenttotal(
                        self._model.routing.cellArea, self._model.routing.lddMap
                    )

                # mask for reporting
                if self.landmask_for_reporting is not None:
                    vars(self)[var] = pcr.ifthen(
                        self.landmask_for_reporting, vars(self)[var]
                    )

                # upstream average
                vars(self)[var + "DailyTotUpsAvg"] = (
                    pcr.catchmenttotal(
                        vars(self)[var] * self._model.routing.cellArea,
                        self._model.routing.lddMap,
                    )
                    / self.upstream_area
                )

                short_name = "upstream_average_" + varDicts.netcdf_short_name[var]

                self.netcdfObj.data2NetCDF(
                    self.outNCDir + "/" + str(var) + "_dailyTotUpsAvg_output.nc",
                    short_name,
                    pcr.pcr2numpy(
                        self.__getattribute__(var + "DailyTotUpsAvg"), vos.MV
                    ),
                    timeStamp,
                )

    def e2o_post_processing(self):
        # RvB (23 Feb 2017): post-processing of the eartH2Observe variables;
        # fluxes in kg m-2 s-1 (/86.4 converts m/day to kg m-2 s-1)
        self.Precip = self._model.meteo.precipitation / 86.4
        self.Evap = (
            -(
                self._model.landSurface.actualET
                + self._model.routing.waterBodyEvaporation
            )
            / 86.4
        )
        self.Runoff = -self._model.routing.runoff / 86.4
        self.Qs = (
            -(
                self._model.landSurface.directRunoff
                + self._model.landSurface.interflowTotal
            )
            / 86.4
        )
        self.Qsb = -self._model.groundwater.baseflow / 86.4
        self.Qsm = self._model.landSurface.snowMelt / 86.4
        self.PotEvap = -self._model.meteo.referencePotET / 86.4
        self.ECanop = -self._model.landSurface.interceptEvap / 86.4
        self.TVeg = -self._model.landSurface.actTranspiTotal / 86.4
        self.ESoil = -self._model.landSurface.actBareSoilEvap / 86.4
        self.EWater = -self._model.routing.waterBodyEvaporation / 86.4
        # (m3/s)
        self.RivOut = self._model.routing.disChanWaterBody

        # state variables in kg m-2 (*1000 converts m to kg m-2)
        self.SWE = self._model.landSurface.snowCoverSWE * 1000
        self.CanopInt = self._model.landSurface.interceptStor * 1000
        self.SurfStor = (
            self._model.landSurface.topWaterLayer
            + (self._model.routing.channelStorage / self._model.routing.cellArea)
            + pcr.ifthen(
                self._model.routing.landmask,
                pcr.ifthen(
                    pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.0,
                    self._model.routing.WaterBodies.waterBodyStorage,
                ),
            )
        ) * 1000
        # water in SurfLayerThick
        self.SurfMoist = self._model.landSurface.storUppTotal * 1000
        # water in RootLayerThick
        self.RootMoist = (
            self._model.landSurface.storUppTotal + self._model.landSurface.storLowTotal
        ) * 1000
        # equals RootMoist
        self.TotMoist = self.RootMoist
        self.GroundMoist = self._model.groundwater.storGroundwater * 1000

    def ulysses_post_processing(self):
        # PCR-GLOBWB is assumed to write at least ET, SWE, Qsm, SM and Qr

        # surface temperature
        self.ulyssesTsurf = None

        # (kg m-2 s-1)
        self.ulyssesP = self._model.meteo.precipitation / 86.4

        # total evaporation and transpiration (kg m-2 s-1), land only
        self.ulyssesET = -(self._model.landSurface.actualET) / 86.4
        # including water bodies
        self.ulyssesETall = (
            -(
                self._model.landSurface.actualET
                + self._model.routing.waterBodyEvaporation
            )
            / 86.4
        )

        # reference potential evaporation
        self.ulyssessRefPET = -(self.referencePotET) / 86.4
        # with crop coefficient, land only (excluding water)
        self.ulyssessCropPET = -(self._model.landSurface.totalPotET) / 86.4
        # with crop coefficient, land and water
        self.ulyssessCropPETall = (
            -(self._model.landSurface.totalPotET + self._model.routing.waterBodyPotEvap)
            / 86.4
        )

        # snow water equivalent (kg m-2), including free water above the snow cover
        self.ulyssesSWE = (
            self._model.landSurface.snowCoverSWE + self._model.landSurface.snowFreeWater
        ) * 1000.0
        # excluding free water above the snow cover
        self.ulyssesSWE_excluding_free_water = (
            self._model.landSurface.snowCoverSWE
        ) * 1000.0

        # snowmelt (kg m-2 s-1)
        self.ulyssesQsm = self._model.landSurface.snowMelt / 86.4

        # total volumetric soil moisture (%); TODO: this is wrong, fix it
        self.ulyssesSM = self._model.landSurface.satDegTotal
        self.ulyssesSMUpp = self._model.landSurface.satDegUppTotal
        self.ulyssesSMLow = self._model.landSurface.satDegLowTotal

        # total runoff (kg m-2 s-1), land only, excluding local changes in water bodies
        self.ulyssesQrRunoff = -self._model.routing.runoff / 86.4

        # gridded river discharge
        self.ulyssesDischarge = self.discharge

        # terrestrial water storage (kg m-2)
        self.ulyssesTWS = self.totalWaterStorageThickness * 1000.0

        # extra variable for ILAMB evaluation
        self.ulyssesSnowFraction = pcr.ifthenelse(
            self.ulyssesSWE > 0.0, pcr.scalar(1.0), pcr.scalar(0.0)
        )
