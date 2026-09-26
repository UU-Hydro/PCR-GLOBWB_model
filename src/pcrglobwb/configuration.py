from __future__ import print_function

import glob
import logging
import os
import shutil
from configparser import RawConfigParser as ConfigParser

from pcrglobwb.common import disclaimer
from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class Configuration(object):

    def __init__(
        self,
        iniFileName,
        relative_ini_meteo_paths=False,
        ini_text=None,
    ):
        object.__init__(self)

        if iniFileName is None:
            raise Exception("Error: No configuration file specified")

        self.iniFileName = os.path.abspath(iniFileName)
        self.ini_text = ini_text

        # save the cwd; it may be changed later by some utility functions
        self._cwd = os.getcwd()

        self.parse_configuration_file(self.iniFileName)

        # option to run in a sandbox with meteo files and initial conditions
        self.using_relative_path_for_output_directory = False
        if relative_ini_meteo_paths:
            self.using_relative_path_for_output_directory = True
            self.make_ini_meteo_paths_absolute()

    def set_configuration(self):

        self.set_input_files()
        self.create_output_directories()
        self.backup_configuration()

        disclaimer.print_disclaimer()

        self.repair_ini_key_names()

    def make_ini_meteo_paths_absolute(self):
        for section in self.allSections:
            sec = getattr(self, section)

            for key, value in list(sec.items()):
                if key.endswith("Ini") and value is not None and value != "None":
                    sec[key] = os.path.abspath(value)

                if key == "precipitationNC" or key == "temperatureNC":
                    sec[key] = os.path.abspath(value)

            for key, value in list(sec.items()):
                if key.endswith("Ini"):
                    if not os.path.exists(value):
                        logger.debug("%s does not exist: %s", key, value)

    # make paths absolute to the cwd at the time the configuration was created
    def make_absolute_path(self, path):
        return os.path.normpath(os.path.join(self._cwd, path))

    def backup_configuration(self):

        # written like QUAlloc's cfg backup, so the backup records the substituted
        # paths the run actually used
        backup = os.path.join(self.logFileDir, os.path.basename(self.iniFileName))
        if self.ini_text is None:
            shutil.copy(self.iniFileName, backup)
        else:
            with open(backup, "w") as backup_file:
                backup_file.write(self.ini_text)

    def parse_configuration_file(self, modelFileName):

        config = ConfigParser()
        config.optionxform = str
        if self.ini_text is not None:
            config.read_string(self.ini_text)
        elif not config.read(modelFileName):
            raise FileNotFoundError("cannot read the ini file %s" % modelFileName)

        self.allSections = config.sections()

        for sec in self.allSections:
            vars(self)[sec] = {}
            options = config.options(sec)
            for opt in options:
                val = config.get(sec, opt)
                self.__getattribute__(sec)[opt] = val

    def set_input_files(self):
        self.cloneMap = vos.getFullPath(
            self.globalOptions["cloneMap"], self.globalOptions["inputDir"]
        )

        # full paths of the input directories/files
        dirsAndFiles = ["precipitationNC", "temperatureNC", "refETPotFileNC"]
        for item in dirsAndFiles:
            if self.meteoOptions[item] != "None":
                self.meteoOptions[item] = vos.getFullPath(
                    self.meteoOptions[item], self.globalOptions["inputDir"]
                )

    def create_output_directories(self):

        if (
            "is_sub_run" in list(self.reportingOptions.keys())
            and self.reportingOptions["is_sub_run"] == "True"
        ):
            if self.using_relative_path_for_output_directory:
                self.globalOptions["outputDir"] = self.make_absolute_path(
                    self.globalOptions["outputDir"]
                )

            self.tmpDir = vos.getFullPath("tmp/", self.globalOptions["outputDir"])

            self.outNCDir = vos.getFullPath("netcdf/", self.globalOptions["outputDir"])

            # backup of the Python scripts used
            self.scriptDir = vos.getFullPath(
                "scripts/", self.globalOptions["outputDir"]
            )

            # starting directory where all scripts are stored
            path_of_this_module = os.path.abspath(os.path.dirname(__file__))
            self.starting_directory = path_of_this_module

            self.logFileDir = vos.getFullPath("log/", self.globalOptions["outputDir"])

            self.endStateDir = vos.getFullPath(
                "states/", self.globalOptions["outputDir"]
            )

            self.mapsDir = vos.getFullPath("maps/", self.globalOptions["outputDir"])

            # go to the PCRaster maps directory (so all pcr.report files are saved there)
            os.chdir(self.mapsDir)

        else:
            if self.using_relative_path_for_output_directory:
                self.globalOptions["outputDir"] = self.make_absolute_path(
                    self.globalOptions["outputDir"]
                )

            # root/parent of the output directory
            cleanOutputDir = False
            if cleanOutputDir:
                try:
                    shutil.rmtree(self.globalOptions["outputDir"])
                except Exception:
                    # new outputDir (does not exist yet)
                    pass
            try:
                os.makedirs(self.globalOptions["outputDir"])
            except Exception:
                # new outputDir (does not exist yet)
                pass

            self.tmpDir = vos.getFullPath("tmp/", self.globalOptions["outputDir"])

            if os.path.exists(self.tmpDir):
                shutil.rmtree(self.tmpDir)
            os.makedirs(self.tmpDir)

            self.outNCDir = vos.getFullPath("netcdf/", self.globalOptions["outputDir"])
            if os.path.exists(self.outNCDir):
                shutil.rmtree(self.outNCDir)
            os.makedirs(self.outNCDir)

            # backup of the Python scripts used
            self.scriptDir = vos.getFullPath(
                "scripts/", self.globalOptions["outputDir"]
            )

            if os.path.exists(self.scriptDir):
                shutil.rmtree(self.scriptDir)
            os.makedirs(self.scriptDir)

            # starting directory where all scripts are stored
            path_of_this_module = os.path.abspath(os.path.dirname(__file__))
            self.starting_directory = path_of_this_module

            for filename in glob.glob(os.path.join(path_of_this_module, "*.py")):
                shutil.copy(filename, self.scriptDir)
            # TODO: fix this copying (it does not include subfolders)

            # absolute, as the runner opens run.log here after the chdir below
            self.logFileDir = os.path.abspath(
                vos.getFullPath("log/", self.globalOptions["outputDir"])
            )
            if os.path.exists(self.logFileDir):
                shutil.rmtree(self.logFileDir)
            os.makedirs(self.logFileDir)

            self.endStateDir = vos.getFullPath(
                "states/", self.globalOptions["outputDir"]
            )
            if os.path.exists(self.endStateDir):
                shutil.rmtree(self.endStateDir)
            os.makedirs(self.endStateDir)

            self.mapsDir = vos.getFullPath("maps/", self.globalOptions["outputDir"])
            cleanMapDir = True
            if os.path.exists(self.mapsDir) and cleanMapDir:
                shutil.rmtree(self.mapsDir)
            os.makedirs(self.mapsDir)

            # go to the PCRaster maps directory (so all pcr.report files are saved there)
            os.chdir(self.mapsDir)

    def repair_ini_key_names(self):
        """
        If needed, change/modify some key names for initial condition fields.
        This is introduced because Edwin was very stupid as once he changed some key names of initial conditions! Yet, it is also useful particularly for runs without complete ini files.
        """

        # model time step (days)
        self.timeStep = 1.0
        self.timeStepUnit = "day"
        if "timeStep" in list(self.globalOptions.keys()) and "timeStepUnit" in list(
            self.globalOptions.keys()
        ):

            if (
                float(self.globalOptions["timeStep"]) != 1.0
                or self.globalOptions["timeStepUnit"] != "day"
            ):
                logger.error(
                    "The model runs only on daily time step. Please check your ini/configuration file"
                )
                self.timeStep = None
                self.timeStepUnit = None

        # defaults for missing options
        if "routingMethod" not in list(self.routingOptions.keys()):
            logger.warning(
                'The "routingMethod" is not defined in the "routingOptions" of the configuration file. "accuTravelTime" is used in this run.'
            )
            self.routingOptions["routingMethod"] = "accuTravelTime"

        if "dynamicFloodPlain" not in list(self.routingOptions.keys()):
            msg = 'The option "dynamicFloodPlain" is not defined in the "routingOptions" of the configuration file. '
            msg += 'We assume "False" for this option. Hence, the flood plain extent is constant for the entire simulation.'
            logger.warning(msg)
            self.routingOptions["dynamicFloodPlain"] = "False"

        if "historicalIrrigationArea" not in list(self.landSurfaceOptions.keys()):
            msg = 'The option "historicalIrrigationArea" is not defined in the "landSurfaceOptions" of the configuration file. '
            msg += 'This run assumes "None" for this option.'
            logger.warning(msg)
            self.landSurfaceOptions["historicalIrrigationArea"] = "None"

        # options to read a different forcing file for each year
        if "precipitation_set_per_year" not in list(self.meteoOptions.keys()):
            self.meteoOptions["precipitation_set_per_year"] = "False"
        if "temperature_set_per_year" not in list(self.meteoOptions.keys()):
            self.meteoOptions["temperature_set_per_year"] = "False"
        if "refETPotFileNC_set_per_year" not in list(self.meteoOptions.keys()):
            self.meteoOptions["refETPotFileNC_set_per_year"] = "False"

        # TODO: repair key names when running a 3-layer model with 2-layer initial conditions (and vice versa)

        # TODO: set a specific set of configuration options for a debugging run
