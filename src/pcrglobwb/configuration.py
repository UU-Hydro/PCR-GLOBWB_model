import datetime
import logging
import os
from configparser import ConfigParser, ExtendedInterpolation

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self, iniFileName, overrides=()):

        if iniFileName is None:
            raise Exception("Error: No configuration file specified")

        # timestamp of this run, used in log file names etc.
        self._timestamp = datetime.datetime.now()

        self.iniFileName = iniFileName

        self.parse_configuration_file(self.iniFileName, overrides)

        self.set_output_paths()

        self.repair_ini_key_names()

    def parse_configuration_file(self, modelFileName, overrides):

        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        with open(modelFileName) as f:
            config.read_file(f)
        apply_overrides(config, overrides, modelFileName)

        self.allSections = config.sections()

        for sec in self.allSections:
            vars(self)[sec] = {}
            options = config.options(sec)
            for opt in options:
                val = config.get(sec, opt)
                self.__getattribute__(sec)[opt] = val

    def set_output_paths(self):
        outputDir = self.globalOptions["outputDir"]
        self.tmpDir = vos.getFullPath("tmp/", outputDir)
        self.outNCDir = vos.getFullPath("netcdf/", outputDir)
        self.scriptDir = vos.getFullPath("scripts/", outputDir)
        self.logFileDir = vos.getFullPath("log/", outputDir)
        self.endStateDir = vos.getFullPath("states/", outputDir)
        self.mapsDir = vos.getFullPath("maps/", outputDir)
        self.starting_directory = os.path.abspath(os.path.dirname(__file__))

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

        if "is_sub_run" not in self.reportingOptions:
            self.reportingOptions["is_sub_run"] = "False"

        # TODO: repair key names when running a 3-layer model with 2-layer initial conditions (and vice versa)

        # TODO: set a specific set of configuration options for a debugging run


def apply_overrides(parser, overrides, iniFileName):
    for section, key, value in overrides:
        if not parser.has_option(section, key):
            raise ValueError(f"--set {section}.{key}: no such option in the ini file")
        parser.set(section, key, value)
        logger.info(f"{section}.{key} set from the command line: {value}")

    missing = [
        f"{section}.{key}"
        for section in parser.sections()
        for key, value in parser.items(section, raw=True)
        if value.strip() == "???"
    ]
    if missing:
        raise ValueError(
            f"{iniFileName} has no value for {missing}; "
            "set them in the file or with --set SECTION.KEY=VALUE"
        )
