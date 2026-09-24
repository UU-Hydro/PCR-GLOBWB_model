from __future__ import print_function

import datetime
import logging
import os
import shutil

import pcraster as pcr
from pcraster.framework import DynamicModel

from pcrglobwb import variable_list as varDicts
from pcrglobwb.common import virtualOS as vos
from pcrglobwb.ncConverter import *

logger = logging.getLogger(__name__)


class PCRGlobWBVersionOne(DynamicModel):

    def __init__(self, configuration, modelTime, landmask, cellArea):
        DynamicModel.__init__(self)

        self.configuration = configuration

        self.modelTime = modelTime

        self.cloneMapFileName = self.configuration.cloneMap
        pcr.setclone(self.cloneMapFileName)

        self.landmask = landmask
        self.cellArea = pcr.ifthen(self.landmask, cellArea)

        # output variables to compare (daily)
        self.debug_state_variables = [
            "temperature",
            "snowCoverSWE",
            "snowFreeWater",
            "interceptStor",
            "storUppTotal",
            "storLowTotal",
            "storGroundwater",
        ]
        self.debug_flux_variables = [
            "precipitation",
            "referencePotET",
            "interceptEvap",
            "actSnowFreeWaterEvap",
            "actBareSoilEvap",
            "actTranspiTotal",
            "actTranspiUppTotal",
            "actTranspiLowTotal",
            "infiltration",
            "gwRecharge",
            "runoff",
            "directRunoff",
            "interflowTotal",
            "baseflow",
            "actualET",
        ]
        self.debug_variables = self.debug_state_variables + self.debug_flux_variables

        # folder with the oldcalc input maps
        self.maps_folder = self.configuration.mapsDir

        # folder for the oldcalc results
        self.results_folder = (
            self.configuration.globalOptions["outputDir"] + "/oldcalc_results/"
        )
        if os.path.exists(self.results_folder):
            shutil.rmtree(self.results_folder)
        os.makedirs(self.results_folder)
        # folder for the netCDF files
        self.netcdf_folder = (
            self.configuration.globalOptions["outputDir"] + "/oldcalc_results/netcdf/"
        )
        os.makedirs(self.netcdf_folder)

        # go to the starting directory and back up the oldcalc script and parameter table
        os.chdir(self.configuration.starting_directory)

        # oldcalc scripts used
        self.oldcalc_script_file = vos.getFullPath(
            self.configuration.globalOptions["oldcalc_script_file"],
            self.configuration.starting_directory,
        )
        self.parameter_tabel_file = vos.getFullPath(
            self.configuration.globalOptions["parameter_tabel_file"],
            self.configuration.starting_directory,
        )

        shutil.copy(self.oldcalc_script_file, self.configuration.scriptDir)
        shutil.copy(self.parameter_tabel_file, self.configuration.scriptDir)

        # attributes for the netCDF files
        netcdfAttributeDictionary = {}
        netcdfAttributeDictionary["institution"] = self.configuration.globalOptions[
            "institution"
        ]
        netcdfAttributeDictionary["title"] = "PCR-GLOBWB 1 output"
        netcdfAttributeDictionary["description"] = (
            self.configuration.globalOptions["description"]
            + " (this is the output from the oldcalc PCR-GLOBWB version 1)"
        )

        self.netcdf_report = PCR2netCDF(configuration, netcdfAttributeDictionary)

        for var in self.debug_variables:

            short_name = varDicts.netcdf_short_name[var]
            unit = varDicts.netcdf_unit[var]
            long_name = varDicts.netcdf_long_name[var]
            if long_name == None:
                long_name = short_name

            netcdf_file_name = (
                self.netcdf_folder + "/" + str(var) + "_dailyTot_output_version_one.nc"
            )

            logger.info(
                "Creating the netcdf file for daily reporting for the variable %s to the file %s (output from PCR-GLOBWB version 1).",
                str(var),
                str(netcdf_file_name),
            )

            self.netcdf_report.createNetCDF(
                netcdf_file_name, short_name, unit, long_name
            )

    def initial(self):

        logger.info("Execute the oldcalc script.")

        # steps for monthly reporting
        if self.modelTime.nrOfTimeSteps == 365:
            monthly_end_times = "31 59 90 120 151 181 212 243 273 304 334 365"
        if self.modelTime.nrOfTimeSteps == 366:
            monthly_end_times = "31 60 91 121 152 182 213 244 274 305 335 366"

        # run the oldcalc script: copy the parameter table to mapsDir
        shutil.copy(self.parameter_tabel_file, self.configuration.mapsDir)
        # copy the script directory to outputDir and run it from there
        shutil.copy(
            self.oldcalc_script_file, self.configuration.globalOptions["outputDir"]
        )
        os.chdir(self.configuration.globalOptions["outputDir"])
        cmd = (
            "oldcalc -f "
            + str(os.path.basename(self.oldcalc_script_file))
            + " "
            + monthly_end_times
        )
        print(cmd)
        vos.cmd_line(cmd)

    def dynamic(self):

        # update the model time from the current PCRaster time step
        self.modelTime.update(self.currentTimeStep())

        # on the first day of the year or first time step, initialize the accumulated fluxes (yearly totals)
        if self.modelTime.timeStepPCR == 1 or self.modelTime.doy == 1:
            for var in self.debug_flux_variables:
                vars(self)[var + "AnnuaTot"] = pcr.ifthen(
                    self.landmask, pcr.scalar(0.0)
                )

        # read the PCRaster outputs, report them as netCDF and accumulate annual totals
        timeStamp = datetime.datetime(
            self.modelTime.year, self.modelTime.month, self.modelTime.day, 0
        )
        for var in self.debug_variables:

            pcraster_map_file_name = (
                self.results_folder
                + "/"
                + pcr.framework.frameworkBase.generateNameT(
                    varDicts.pcr_short_name[var], self.modelTime.timeStepPCR
                )
            )
            logger.debug(
                "Reading the variable %s from the file %s ", var, pcraster_map_file_name
            )
            pcr_map_values = pcr.readmap(str(pcraster_map_file_name))

            if var in self.debug_flux_variables:
                logger.debug("Accumulating variable %s ", var)
                vars(self)[var + "AnnuaTot"] += pcr_map_values

            netcdf_file_name = (
                self.netcdf_folder + "/" + str(var) + "_dailyTot_output_version_one.nc"
            )
            logger.debug("Saving to the file %s ", netcdf_file_name)
            short_name = varDicts.netcdf_short_name[var]
            self.netcdf_report.data2NetCDF(
                netcdf_file_name,
                short_name,
                pcr.pcr2numpy(pcr_map_values, vos.MV),
                timeStamp,
            )

        # on the last day of the year, log the yearly accumulated values
        if self.modelTime.isLastDayOfYear() or self.modelTime.isLastTimeStep():

            logger.info("")
            msg = "\n"
            msg += "=======================================================================================================================\n"
            msg += "=======================================================================================================================\n"
            msg += "Summary of yearly annual flux values of PCR-GLOBWB 1.0.\n"
            msg += "The following summary values do not include storages in surface water bodies (lake, reservoir and channel storages).\n"
            msg += "=======================================================================================================================\n"
            msg += "=======================================================================================================================\n"
            msg += "\n"
            msg += "\n"
            logger.info(msg)

            totalCellArea = vos.getMapTotal(pcr.ifthen(self.landmask, self.cellArea))
            msg = "Total area = %e km2" % (totalCellArea / 1e6)
            logger.info(msg)

            for var in self.debug_flux_variables:
                volume = vos.getMapVolume(
                    self.__getattribute__(var + "AnnuaTot"), self.cellArea
                )
                msg = (
                    "Accumulated %s from PCR-GLOBWB 1.0 days 1 to %i in %i = %e km3 = %e mm"
                    % (
                        var,
                        int(self.modelTime.doy),
                        int(self.modelTime.year),
                        volume / 1e9,
                        volume * 1000 / totalCellArea,
                    )
                )
                logger.info(msg)

            msg = "\n"
            msg += "\n"
            msg += "\n"
            msg += "=======================================================================================================================\n"
            msg += "\n"
            msg += "\n"
            logger.info(msg)

        # at the last time step, compare the outputs of versions 1 and 2
        if self.modelTime.isLastTimeStep():
            self.compare_output()

    def compare_output(self):

        logger.info(
            "Comparing the netcdf output files from versions one and two (using cdo)."
        )

        # prepare the debug directory and go there
        debug_directory = self.configuration.globalOptions["outputDir"] + "/debug/"
        if os.path.exists(debug_directory):
            shutil.rmtree(debug_directory)
        os.makedirs(debug_directory)
        os.chdir(debug_directory)

        for var in self.debug_variables:

            msg = "Comparing the netcdf output files from the variable " + str(var)
            logger.info(msg)

            short_name = varDicts.netcdf_short_name[var]

            filename_version_two = (
                self.configuration.outNCDir + "/" + str(var) + "_dailyTot_output.nc"
            )
            filename_version_one = (
                self.netcdf_folder + "/" + str(var) + "_dailyTot_output_version_one.nc"
            )

            cmd = (
                "cdo sub "
                + filename_version_two
                + " "
                + filename_version_one
                + " "
                + var
                + "_diff.nc"
            )
            vos.cmd_line(cmd)
