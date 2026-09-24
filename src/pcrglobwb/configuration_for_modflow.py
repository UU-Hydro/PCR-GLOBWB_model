import datetime
import glob
import logging
import os
import shutil

from six.moves.configparser import RawConfigParser as ConfigParser

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)

from pcrglobwb.common import disclaimer

"""
Created on May 21, 2015

@author: Edwin H. Sutanudjaja

This file is to handle the configuration for modflow run. 


"""


class Configuration(object):

    def __init__(self, iniFileName, debug_mode=False, steady_state_only=False):
        object.__init__(self)

        # timestamp of this run, used in log file names etc.
        self._timestamp = datetime.datetime.now()

        self.iniFileName = os.path.abspath(iniFileName)

        self.debug_mode = debug_mode

        self.parse_configuration_file(self.iniFileName)

        # option for online coupling between PCR-GLOBWB and MODFLOW
        self.set_options_for_coupling_betweeen_pcrglobwb_and_modflow()

        self.steady_state_only = steady_state_only
        if self.steady_state_only:
            self.globalOptions["outputDir"] = (
                self.globalOptions["outputDir"] + "/steady-state_only/"
            )
        else:
            self.globalOptions["outputDir"] = (
                self.globalOptions["outputDir"] + "/transient/"
            )

        # set all paths, clean output when requested, initialize logging, copy the ini file, back up scripts
        self.set_configuration()

    def set_options_for_coupling_betweeen_pcrglobwb_and_modflow(self):

        # default: offline coupling
        self.online_coupling_between_pcrglobwb_and_modflow = False

        if "globalMergingAndModflowOptions" in self.allSections:

            if (
                "online_coupling_between_pcrglobwb_and_modflow"
                in self.globalMergingAndModflowOptions.keys()
                and self.globalMergingAndModflowOptions[
                    "online_coupling_between_pcrglobwb_and_modflow"
                ]
                == "True"
            ):
                self.online_coupling_between_pcrglobwb_and_modflow = True

            # use the cloneMap and landmask from globalMergingAndModflowOptions
            self.globalOptions["cloneMap"] = self.globalMergingAndModflowOptions[
                "cloneMap"
            ]
            self.globalOptions["landmask"] = self.globalMergingAndModflowOptions[
                "landmask"
            ]

            self.main_output_directory = self.globalOptions["outputDir"]

            # output directory for the MODFLOW calculation
            self.globalOptions["outputDir"] = self.main_output_directory + "/modflow/"

            # temporary MODFLOW output folder
            if "tmp_modflow_dir" in self.globalMergingAndModflowOptions.keys():
                self.globalOptions["tmp_modflow_dir"] = (
                    self.globalMergingAndModflowOptions["tmp_modflow_dir"]
                )

            if (
                "modflowParameterOptions" in self.allSections
                and "waterBodyInputNC" not in self.modflowParameterOptions.keys()
            ):
                self.modflowParameterOptions["waterBodyInputNC"] = self.routingOptions[
                    "waterBodyInputNC"
                ]

            # option to use only natural water bodies
            if (
                "modflowParameterOptions" in self.allSections
                and "onlyNaturalWaterBodies" not in self.modflowParameterOptions.keys()
            ):
                self.modflowParameterOptions["onlyNaturalWaterBodies"] = (
                    self.routingOptions["onlyNaturalWaterBodies"]
                )

            # reportingOptions are taken from reportingForModflowOptions
            if "reportingForModflowOptions" in self.allSections:
                self.reportingOptions = self.reportingForModflowOptions

    def set_configuration(self):

        self.set_input_files()
        self.create_output_directories()

        self.initialize_logging()

        self.backup_configuration()

    def initialize_logging(self, log_file_location="Default"):
        """
        Initialize logging. Prints to both the console and a log file, at configurable levels
        """

        logging.getLogger().setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

        log_level_console = "INFO"
        log_level_file = "INFO"
        # log levels in order: DEBUG, INFO, WARNING, ERROR, CRITICAL

        # log level from the ini file
        if "log_level_console" in self.globalOptions.keys():
            log_level_console = self.globalOptions["log_level_console"]
        if "log_level_file" in self.globalOptions.keys():
            log_level_file = self.globalOptions["log_level_file"]

        # log level for debug mode
        if self.debug_mode == True:
            log_level_console = "DEBUG"
            log_level_file = "DEBUG"

        console_level = getattr(logging, log_level_console.upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError("Invalid log level: %s", log_level_console)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logging.getLogger().addHandler(console_handler)

        if log_file_location != "Default":
            self.logFileDir = log_file_location
        log_filename = (
            self.logFileDir
            + os.path.basename(self.iniFileName)
            + "_"
            + str(self._timestamp.isoformat()).replace(":", ".")
            + ".log"
        )

        file_level = getattr(logging, log_level_file.upper(), logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError("Invalid log level: %s", log_level_file)

        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)

        # debug log file name
        dbg_filename = (
            self.logFileDir
            + os.path.basename(self.iniFileName)
            + "_"
            + str(self._timestamp.isoformat()).replace(":", ".")
            + ".dbg"
        )

        debug_handler = logging.FileHandler(dbg_filename)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(debug_handler)

        logger.info("Model run started at %s", self._timestamp)
        logger.info("Logging output to %s", log_filename)
        logger.info("Debugging output to %s", dbg_filename)

        disclaimer.print_disclaimer(with_logger=True)

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

    def set_input_files(self):

        self.cloneMap = vos.getFullPath(
            self.globalOptions["cloneMap"], self.globalOptions["inputDir"]
        )

    def create_output_directories(self):
        # root/parent of the output directory
        cleanOutputDir = False
        if cleanOutputDir:
            try:
                shutil.rmtree(self.globalOptions["outputDir"])
            except:
                # new outputDir (does not exist yet)
                pass

        try:
            os.makedirs(self.globalOptions["outputDir"])
        except:
            # new outputDir (does not exist yet)
            pass

        # temporary directory (needed for resampling)
        self.tmpDir = vos.getFullPath("tmp/", self.globalOptions["outputDir"])
        if os.path.exists(self.tmpDir):
            shutil.rmtree(self.tmpDir)
        os.makedirs(self.tmpDir)

        self.outNCDir = vos.getFullPath("netcdf/", self.globalOptions["outputDir"])
        if os.path.exists(self.outNCDir):
            shutil.rmtree(self.outNCDir)
        os.makedirs(self.outNCDir)

        # backup of the Python scripts used
        self.scriptDir = vos.getFullPath("scripts/", self.globalOptions["outputDir"])
        if os.path.exists(self.scriptDir):
            shutil.rmtree(self.scriptDir)
        os.makedirs(self.scriptDir)
        self.path_of_this_module = os.path.abspath(os.path.dirname(__file__))
        for filename in glob.glob(os.path.join(self.path_of_this_module, "*.py")):
            shutil.copy(filename, self.scriptDir)

        self.logFileDir = vos.getFullPath("log/", self.globalOptions["outputDir"])
        cleanLogDir = True
        if os.path.exists(self.logFileDir) and cleanLogDir:
            shutil.rmtree(self.logFileDir)
        os.makedirs(self.logFileDir)

        # end state directory; will contain the calculated groundwater heads
        self.endStateDir = vos.getFullPath("states/", self.globalOptions["outputDir"])
        if os.path.exists(self.endStateDir):
            shutil.rmtree(self.endStateDir)
        os.makedirs(self.endStateDir)

        # PCRaster maps directory; will contain all maps used in the PCRaster-MODFLOW coupling
        self.mapsDir = vos.getFullPath("maps/", self.globalOptions["outputDir"])
        cleanMapDir = True
        if os.path.exists(self.mapsDir) and cleanMapDir:
            shutil.rmtree(self.mapsDir)
        os.makedirs(self.mapsDir)

        # temporary directory for the MODFLOW calculation (must be empty)
        self.tmp_modflow_dir = "tmp_modflow/"
        if "tmp_modflow_dir" in self.globalOptions.keys():
            self.tmp_modflow_dir = self.globalOptions["tmp_modflow_dir"]
        self.tmp_modflow_dir = (
            vos.getFullPath(self.tmp_modflow_dir, self.globalOptions["outputDir"]) + "/"
        )
        if os.path.exists(self.tmp_modflow_dir):
            shutil.rmtree(self.tmp_modflow_dir)
        os.makedirs(self.tmp_modflow_dir)
        # go to the temporary MODFLOW directory so all output is saved there
        os.chdir(self.tmp_modflow_dir)
