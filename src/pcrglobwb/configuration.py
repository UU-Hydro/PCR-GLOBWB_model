import datetime
import glob
import logging
import os
import shutil
from configparser import RawConfigParser as ConfigParser

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self, iniFileName):

        if iniFileName is None:
            raise Exception("Error: No configuration file specified")

        # timestamp of this run, used in log file names etc.
        self._timestamp = datetime.datetime.now()

        self.iniFileName = os.path.abspath(iniFileName)

        self.parse_configuration_file(self.iniFileName)

        self.set_configuration()

    def set_configuration(self):

        self.create_output_directories()

        self.backup_configuration()

        self.repair_ini_key_names()

    def backup_configuration(self):

        shutil.copy(
            self.iniFileName,
            self.logFileDir
            + os.path.basename(self.iniFileName)
            + "_"
            + str(self._timestamp.isoformat()).replace(":", ".")
            + ".ini",
        )

    def parse_configuration_file(self, modelFileName):

        config = ConfigParser()
        config.optionxform = str
        config.read(modelFileName)

        self.allSections = config.sections()

        for sec in self.allSections:
            vars(self)[sec] = {}
            options = config.options(sec)
            for opt in options:
                val = config.get(sec, opt)
                self.__getattribute__(sec)[opt] = val

    def create_output_directories(self):

        if (
            "is_sub_run" in self.reportingOptions
            and self.reportingOptions["is_sub_run"] == "True"
        ):
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
            # root/parent of the output directory
            os.makedirs(self.globalOptions["outputDir"], exist_ok=True)

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

            self.logFileDir = vos.getFullPath("log/", self.globalOptions["outputDir"])
            cleanLogDir = True
            if os.path.exists(self.logFileDir) and cleanLogDir:
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
        if "timeStep" in self.globalOptions and "timeStepUnit" in self.globalOptions:

            if (
                float(self.globalOptions["timeStep"]) != 1.0
                or self.globalOptions["timeStepUnit"] != "day"
            ):
                raise ValueError(
                    "Only a daily time step is supported; check the ini file"
                )

        # defaults for missing options
        if "routingMethod" not in self.routingOptions:
            logger.warning('No routingMethod in routingOptions; using "accuTravelTime"')
            self.routingOptions["routingMethod"] = "accuTravelTime"

        if "dynamicFloodPlain" not in self.routingOptions:
            logger.warning(
                'No dynamicFloodPlain; using "False": flood plain extent is constant'
            )
            self.routingOptions["dynamicFloodPlain"] = "False"

        if "historicalIrrigationArea" not in self.landSurfaceOptions:
            logger.warning(
                'No historicalIrrigationArea in landSurfaceOptions; using "None"'
            )
            self.landSurfaceOptions["historicalIrrigationArea"] = "None"

        # options to read a different forcing file for each year
        if "precipitation_set_per_year" not in self.meteoOptions:
            self.meteoOptions["precipitation_set_per_year"] = "False"
        if "temperature_set_per_year" not in self.meteoOptions:
            self.meteoOptions["temperature_set_per_year"] = "False"
        if "refETPotFileNC_set_per_year" not in self.meteoOptions:
            self.meteoOptions["refETPotFileNC_set_per_year"] = "False"

        # TODO: repair key names when running a 3-layer model with 2-layer initial conditions (and vice versa)

        # TODO: set a specific set of configuration options for a debugging run
