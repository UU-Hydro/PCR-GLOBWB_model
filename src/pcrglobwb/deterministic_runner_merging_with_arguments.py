import datetime
import glob
import os
import shutil
import sys

import pcraster as pcr
from pcraster.framework import DynamicFramework, DynamicModel

from pcrglobwb.common.currTimeStep import ModelTime
from pcrglobwb.configuration_for_modflow import Configuration

try:
    from reporting_for_modflow import Reporting
except:
    pass

try:
    from modflow import ModflowCoupling
except:
    pass

import logging

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)

from pcrglobwb.common import disclaimer


class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime, system_argument=None):
        DynamicModel.__init__(self)

        self.number_of_clones = configuration.globalMergingAndModflowOptions[
            "number_of_clones"
        ]
        self.cellsize_in_arcsec = configuration.globalMergingAndModflowOptions[
            "cellsize_in_arcsec"
        ]
        self.xmin = configuration.globalMergingAndModflowOptions["xmin"]
        self.ymin = configuration.globalMergingAndModflowOptions["ymin"]
        self.xmax = configuration.globalMergingAndModflowOptions["xmax"]
        self.ymax = configuration.globalMergingAndModflowOptions["ymax"]

        self.modelTime = modelTime

        self.configuration = configuration

        # whether this run includes MODFLOW or merging
        self.include_merging_or_modflow = True
        # for the standard 5 arcmin runs, only the "Global" and "part_one" runs include MODFLOW or merging
        if (
            "cloneAreas" in list(self.configuration.globalOptions.keys())
            and self.configuration.globalOptions["cloneAreas"] == "part_two"
        ):
            self.include_merging_or_modflow = False

        if self.include_merging_or_modflow:

            self.netcdf_format = self.configuration.mergingOutputOptions["formatNetCDF"]
            self.zlib_option = self.configuration.mergingOutputOptions["zlib"]

            # output variables to merge
            nc_report_list = [
                "outDailyTotNC",
                "outMonthTotNC",
                "outMonthAvgNC",
                "outMonthEndNC",
                "outMonthMaxNC",
                "outAnnuaTotNC",
                "outAnnuaAvgNC",
                "outAnnuaEndNC",
                "outAnnuaMaxNC",
            ]
            for nc_report_type in nc_report_list:
                vars(self)[nc_report_type] = self.configuration.mergingOutputOptions[
                    nc_report_type
                ]

        # model and reporting objects, required for runs with MODFLOW
        if self.configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.model = ModflowCoupling(configuration, modelTime)
            self.reporting = Reporting(configuration, self.model, modelTime)

        # the dynamic framework needs a clone map (and self.model is not always created)
        pcr.setclone(self.configuration.cloneMap)

    def initial(self):

        # get or prepare the initial groundwater head
        if self.configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.model.get_initial_heads()

    def dynamic(self):

        # update the model time from the current PCRaster time step
        self.modelTime.update(self.currentTimeStep())

        # update the model and merge daily, but only report at the last day of the month
        if self.modelTime.isLastDayOfMonth():

            # wait until all PCR-GLOBWB runs are done
            pcrglobwb_is_ready = False
            self.count_check = 0
            while pcrglobwb_is_ready == False:
                if (
                    datetime.datetime.now().second == 14
                    or datetime.datetime.now().second == 29
                    or datetime.datetime.now().second == 34
                    or datetime.datetime.now().second == 49
                ):
                    pcrglobwb_is_ready = self.check_pcrglobwb_status()

            # merge daily netCDF files; TODO: support runs that do not start on 1 January
            start_date = "%04i-%02i-01" % (
                self.modelTime.year,
                self.modelTime.month,
            )
            end_date = self.modelTime.fulldate
            self.merging_netcdf_files("outDailyTotNC", start_date, end_date)

            if self.configuration.online_coupling_between_pcrglobwb_and_modflow:

                # merge the PCRaster maps needed for MODFLOW
                msg = "Merging pcraster map files that are needed for the MODFLOW calculation."
                logger.info(msg)
                cmd = (
                    "python3 "
                    + self.configuration.path_of_this_module
                    + "/merge_pcraster_maps.py "
                    + str(self.modelTime.fulldate)
                    + " "
                    + str(self.configuration.main_output_directory)
                    + "/ maps 8 "
                    + str("Global")
                )
                vos.cmd_line(cmd, using_subprocess=False)

                # clean up unmerged files (not tested yet)
                clean_up_pcraster_maps = False
                if (
                    self.configuration.mergingOutputOptions[
                        "delete_unmerged_pcraster_maps"
                    ]
                    == "True"
                ):
                    clean_up_pcraster_maps = (
                        # TODO: this is not working yet
                        True
                    )
                if clean_up_pcraster_maps:
                    files_to_be_removed = glob.glob(
                        str(self.configuration.main_output_directory)
                        + "/M*/maps/*"
                        + str(self.modelTime.fulldate)
                        + "*"
                    )
                    for f in files_to_be_removed:
                        print(f)
                        os.remove(f)

                # update MODFLOW (picks up the current model time from modelTime)
                self.model.update()
                # report only at the end of the month
                self.reporting.report()

        # merge the PCR-GLOBWB initial conditions (PCRaster maps)
        if self.modelTime.isLastDayOfYear():

            msg = "Merging pcraster map files belonging to initial conditions."
            logger.info(msg)

            # general extents (e.g. Africa, Europe)
            cmd = (
                "python3 "
                + self.configuration.path_of_this_module
                + "/merge_pcraster_maps_general.py "
                + str(self.modelTime.fulldate)
                + " "
                + str(self.configuration.main_output_directory)
                + "/ states 32 "
                + str(self.number_of_clones)
                + " "
                + str("defined")
                + " "
                + str(self.cellsize_in_arcsec)
                + " "
                + str(self.xmin)
                + " "
                + str(self.ymin)
                + " "
                + str(self.xmax)
                + " "
                + str(self.ymax)
                + " "
            )

            print(cmd)

            os.system(cmd)

            # clean up unmerged files (not tested yet)
            clean_up_pcraster_maps = False
            if (
                "delete_unmerged_pcraster_maps"
                in list(self.configuration.mergingOutputOptions.keys())
                and self.configuration.mergingOutputOptions[
                    "delete_unmerged_pcraster_maps"
                ]
                == "True"
            ):
                # TODO: this is not working yet
                clean_up_pcraster_maps = True
            if clean_up_pcraster_maps:
                files_to_be_removed = glob.glob(
                    str(self.configuration.main_output_directory)
                    + "/M*/states/*"
                    + str(self.modelTime.fulldate)
                    + "*"
                )
                for f in files_to_be_removed:
                    print(f)
                    os.remove(f)

        if self.modelTime.isLastDayOfYear():

            # merge monthly netCDF files; TODO: support runs that do not start on 1 January
            start_date = "%04i-01-31" % (self.modelTime.year)
            self.merging_netcdf_files("outMonthTotNC", start_date, end_date)
            self.merging_netcdf_files("outMonthAvgNC", start_date, end_date)
            self.merging_netcdf_files("outMonthEndNC", start_date, end_date)
            self.merging_netcdf_files("outMonthMaxNC", start_date, end_date)

            # merge annual netCDF files; TODO: support runs that do not start on 1 January
            start_date = "%04i-12-31" % (self.modelTime.year)
            end_date = self.modelTime.fulldate
            self.merging_netcdf_files("outAnnuaTotNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaAvgNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaEndNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaMaxNC", start_date, end_date)

        # create an empty file to indicate that merging is done
        if self.modelTime.isLastDayOfMonth() or self.modelTime.isLastDayOfYear():

            outputDirectory = (
                str(self.configuration.main_output_directory) + "/global/maps/"
            )
            if os.path.exists(outputDirectory) == False:
                os.makedirs(outputDirectory)
            filename = (
                outputDirectory
                + "/merged_files_for_"
                + str(self.modelTime.fulldate)
                + "_are_ready.txt"
            )
            if os.path.exists(filename):
                os.remove(filename)
            open(filename, "w").close()

    def merging_netcdf_files(
        self, nc_report_type, start_date, end_date, max_number_of_cores=20
    ):

        if str(vars(self)[nc_report_type]) != "None":

            netcdf_files_that_will_be_merged = vars(self)[nc_report_type]

            msg = (
                "Merging netcdf files for the files/variables: "
                + netcdf_files_that_will_be_merged
            )
            logger.info(msg)

            # general extents
            cmd = (
                "python3 "
                + self.configuration.path_of_this_module
                + "/merge_netcdf_general.py "
                + str(self.configuration.main_output_directory)
                + " "
                + str(self.configuration.main_output_directory)
                + "/global/netcdf/ "
                + str(nc_report_type)
                + " "
                + str(start_date)
                + " "
                + str(end_date)
                + " "
                + str(netcdf_files_that_will_be_merged)
                + " "
                + str(self.netcdf_format)
                + " "
                + str(self.zlib_option)
                + " "
                + str(max_number_of_cores)
                + " "
                + str(self.number_of_clones)
                + " "
                + str("defined")
                + " "
                + str(self.cellsize_in_arcsec)
                + " "
                + str(self.xmin)
                + " "
                + str(self.ymin)
                + " "
                + str(self.xmax)
                + " "
                + str(self.ymax)
                + " "
            )

            msg = "Using the following command line: " + cmd
            logger.info(msg)

            os.system(cmd)

    def check_pcrglobwb_status(self):

        clone_areas = ["M%07d" % i for i in range(1, int(self.number_of_clones) + 1, 1)]

        for clone_area in clone_areas:
            status_file = (
                str(self.configuration.main_output_directory)
                + "/"
                + str(clone_area)
                + "/maps/pcrglobwb_files_for_"
                + str(self.modelTime.fulldate)
                + "_are_ready.txt"
            )
            msg = "Waiting for the file: " + status_file
            if self.count_check == 1:
                logger.info(msg)
            if self.count_check < 7:
                self.count_check += 1
            status = os.path.exists(status_file)

            if status == False:
                return status
            if status:
                self.count_check = 0

        print(status)

        return status


def modify_ini_file(original_ini_file, system_argument):

    # created by Edwin H. Sutanudjaja in August 2020 for the Ulysses project

    file_ini = open(original_ini_file, "rt")
    file_ini_content = file_ini.read()
    file_ini.close()

    # output directory (-mod); always required
    main_output_dir = system_argument[system_argument.index("-mod") + 1]
    file_ini_content = file_ini_content.replace("MAIN_OUTPUT_DIR", main_output_dir)
    msg = (
        "The output folder 'outputDir' is set based on the system argument (-mod): "
        + main_output_dir
    )
    print(msg)

    # optional start (-sd) and end (-ed) dates
    if "-sd" in system_argument:
        starting_date = system_argument[system_argument.index("-sd") + 1]
        file_ini_content = file_ini_content.replace("STARTING_DATE", starting_date)
        msg = (
            "The starting date 'startTime' is set based on the system argument (-sd): "
            + starting_date
        )
        print(msg)
    if "-ed" in system_argument:
        end_date = system_argument[system_argument.index("-ed") + 1]
        file_ini_content = file_ini_content.replace("END_DATE", end_date)
        msg = (
            "The end date 'END_DATE' is set based on the system argument (-ed): "
            + end_date
        )
        print(msg)

    # optional initial conditions: main initial state folder (-misd)
    if "-misd" in system_argument:
        main_initial_state_folder = system_argument[system_argument.index("-misd") + 1]
        file_ini_content = file_ini_content.replace(
            "MAIN_INITIAL_STATE_FOLDER", main_initial_state_folder
        )
        msg = (
            "The main folder for all initial states is set based on the system argument (-misd): "
            + main_initial_state_folder
        )
        print(msg)
    # date for initial states (-dfis)
    if "-dfis" in system_argument:
        date_for_initial_states = system_argument[system_argument.index("-dfis") + 1]
        file_ini_content = file_ini_content.replace(
            "DATE_FOR_INITIAL_STATES", date_for_initial_states
        )
        msg = (
            "The date for all initial state files is set based on the system argument (-dfis): "
            + date_for_initial_states
        )
        print(msg)

    # optional forcing files
    if "-pff" in system_argument:
        precipitation_forcing_file = system_argument[system_argument.index("-pff") + 1]
        file_ini_content = file_ini_content.replace(
            "PRECIPITATION_FORCING_FILE", precipitation_forcing_file
        )
        msg = (
            "The precipitation forcing file 'precipitationNC' is set based on the system argument (-pff): "
            + precipitation_forcing_file
        )
        print(msg)
    if "-tff" in system_argument:
        temperature_forcing_file = system_argument[system_argument.index("-tff") + 1]
        file_ini_content = file_ini_content.replace(
            "TEMPERATURE_FORCING_FILE", temperature_forcing_file
        )
        msg = (
            "The temperature forcing file 'temperatureNC' is set based on the system argument (-tff): "
            + temperature_forcing_file
        )
        print(msg)
    if "-rpetff" in system_argument:
        ref_pot_et_forcing_file = system_argument[system_argument.index("-rpetff") + 1]
        file_ini_content = file_ini_content.replace(
            "REF_POT_ET_FORCING_FILE", ref_pot_et_forcing_file
        )
        msg = (
            "The reference potential ET forcing file 'refETPotFileNC' is set based on the system argument (-tff): "
            + ref_pot_et_forcing_file
        )
        print(msg)

    # number of spin-up years
    if "-num_of_sp_years" in system_argument:
        number_of_spinup_years = system_argument[
            system_argument.index("-num_of_sp_years") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "NUMBER_OF_SPINUP_YEARS", number_of_spinup_years
        )
        msg = (
            "The number_of_spinup_years is set based on the system argument (-num_of_sp_years): "
            + number_of_spinup_years
        )
        print(msg)

    # folder for the original and modified ini files
    folder_for_ini_files = os.path.join(main_output_dir, "ini_files")

    if os.path.exists(folder_for_ini_files):
        shutil.rmtree(folder_for_ini_files)
    os.makedirs(folder_for_ini_files)

    shutil.copy(
        original_ini_file,
        os.path.join(
            folder_for_ini_files, os.path.basename(original_ini_file) + ".original"
        ),
    )

    new_ini_file_name = os.path.join(
        folder_for_ini_files, os.path.basename(original_ini_file) + ".modified_and_used"
    )
    new_ini_file = open(new_ini_file_name, "w")
    new_ini_file.write(file_ini_content)
    new_ini_file.close()

    return new_ini_file_name


def main():

    disclaimer.print_disclaimer()

    iniFileName = os.path.abspath(sys.argv[1])

    # modify the ini file and save it to a new location
    if "-mod" in sys.argv:
        iniFileName = modify_ini_file(
            original_ini_file=iniFileName, system_argument=sys.argv
        )

    debug_mode = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "debug" or sys.argv[2] == "debug_parallel":
            debug_mode = True

    # option to perform a steady-state calculation (for MODFLOW)
    steady_state_only = False
    if len(sys.argv) > 3:
        if sys.argv[3] == "steady-state-only":
            steady_state_only = True

    configuration = Configuration(
        iniFileName=iniFileName,
        debug_mode=debug_mode,
        steady_state_only=steady_state_only,
    )

    # time step info: year, month, day, doy, etc.
    currTimeStep = ModelTime()

    currTimeStep.getStartEndTimeSteps(
        configuration.globalOptions["startTime"], configuration.globalOptions["endTime"]
    )
    logger.info("Model run starts.")
    deterministic_runner = DeterministicRunner(configuration, currTimeStep)

    dynamic_framework = DynamicFramework(
        deterministic_runner, currTimeStep.nrOfTimeSteps
    )
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()


if __name__ == "__main__":
    disclaimer.print_disclaimer(with_logger=True)
    sys.exit(main())
