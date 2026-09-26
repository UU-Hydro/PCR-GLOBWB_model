import datetime
import logging
import os
import shutil
import stat
from configparser import RawConfigParser as ConfigParser

from pcrglobwb.common.arguments import fill_placeholders
from qualloc.basic_functions import convert_string_to_list, get_decision

logger = logging.getLogger(__name__)


NoneType = type(None)

# command-line flags whose placeholders the calling program replaces in the configuration file
substitutable_flags = [
    "--input-dir",
    "--output-dir",
    "--pcrglobwb-output-dir",
    "--clone-map",
]


def remove_readonly(func, path, _):
    """

    clears the readonly bit and reattempt the removal"

    """

    stat_method = stat.FILE_ATTRIBUTE_NORMAL

    os.chmod(path, stat_method)
    func(path)


class configuration_parser(object):
    """

configuration_parser:
object to parse the configuration file and  hold all information to run \
the CALEROS model.

"""

    def __init__(
        self,
        cfgfilename,
        sections=[],
        groups=[],
        replacements={},
        **optional_arguments,
    ):

        object.__init__(self)

        logger.info("Initializing the QUAlloc model run")

        # configuration file, groups and sections
        self.cfgfilename = cfgfilename
        self.sections = sections
        self.groups = groups

        # timestamp of this run, used in log file names etc.
        self._timestamp = datetime.datetime.now()
        self._timestamp_str = str(self._timestamp.isoformat())
        self._timestamp_str = self._timestamp_str[: self._timestamp_str.find(".")]
        self._timestamp_str = self._timestamp_str.replace(":", ".")

        # save the initial root for later use
        self.start_root_path = os.path.abspath(os.path.dirname(__file__))

        # substitute tokens before parsing so every value is covered, including those
        # in the optional sections and groups
        with open(self.cfgfilename) as cfgfile:
            self.cfg_content = fill_placeholders(
                cfgfile.read(), replacements, substitutable_flags, self.cfgfilename
            )

        self.parse_configuration_file(self.cfgfilename, self.groups, self.sections)

        # create all necessary directories
        self.create_output_directories()

        # copy the configuration file
        self.backup_configuration_file(self.cfgfilename, self.logpath)

    def __repr__(self):
        return "this is an instance of the model configuration class object"

    def __str__(self):
        return "this object contains information on the model configuration"

    def get_items(self, config, section):
        # dictionary of all key-value pairs in the current section
        options = {}
        for key, value in config.items(section):
            options[key] = value
        return options

    def parse_configuration_file(self, cfgfilename, groups, sections):

        config = ConfigParser()
        config.optionxform = str
        config.read_string(self.cfg_content)
        sections_present = config.sections()
        # process the single, preset sections first
        for section in sections:
            # check whether the section exists (compulsory for the model parameterization)
            if config.has_section(section):
                sections_present.remove(section)
                try:
                    section_info = self.get_items(config, section)
                    setattr(self, section, section_info)
                except Exception as exc:
                    message_str = (
                        "processing information on the compulsory section [%s] raised an error"
                        % (section)
                    )
                    raise ValueError(message_str) from exc
            else:
                message_str = (
                    "configuration file does not contain information for the compulsory section [%s]"
                    % (section)
                )
                raise ValueError(message_str)
        # process groups and miscellaneous sections
        for group in groups:
            try:
                setattr(self, group, {})
            except Exception as exc:
                message_str = (
                    "processing information on the group [%s] raised an error" % (group)
                )
                raise ValueError(message_str) from exc
        for section in sections_present:
            try:
                # name and group name (if present)
                namelist = section.split(None, 1)
                for icnt in range(len(namelist)):
                    namelist[icnt] = namelist[icnt].strip()
                group = namelist[0]
                if group in groups:
                    entryname = namelist[1]
                    section_info = getattr(self, group)[entryname] = {}
                else:
                    section = section.replace(" ", "")
                    # miscellaneous section
                    section_info = self.get_items(config, section)
                setattr(self, section, section_info)

            except Exception as exc:
                message_str = (
                    "processing information on the section [%s] raised an error"
                    % (section)
                )
                raise ValueError(message_str) from exc

        # check that the required entries of every group are present
        for group in groups:
            if len(getattr(self, group).keys()) == 0:
                message_str = (
                    "configuration file does not contain the necessary information on %s"
                    % (group)
                )
                raise ValueError(message_str)

        return None

    def create_output_directories(self):
        """
create_output_directories: function to create all the necessary output \
directories using information from the model configuration.

"""
        # check the input and output paths
        if not os.path.isabs(self.general["inputpath"]):
            self.general["inputpath"] = os.path.abspath(self.general["inputpath"])
        if not os.path.isdir(self.general["inputpath"]):
            message_str = "input path %s does not exist" % (self.general["inputpath"])
            raise FileNotFoundError(message_str)

        if not os.path.isabs(self.general["outputpath"]):
            self.general["outputpath"] = os.path.abspath(self.general["outputpath"])

        if not os.path.isdir(self.general["outputpath"]):
            os.makedirs(self.general["outputpath"])
            logger.info(
                "output path %s does not exist and is created",
                self.general["outputpath"],
            )

        # short names for the input and output directories
        self.inputpath = self.general["inputpath"]
        self.outputpath = self.general["outputpath"]

        # the temporary (working) directory and the log, script, netCDF, states and
        # table directories
        subdirectories = [
            os.path.join(self.outputpath, subdirectory)
            for subdirectory in [
                "temp",
                "netcdf",
                "scripts",
                "log",
                "states",
                "summary",
                "maps",
            ]
        ]

        # check for existing directories and files
        files_exist = False
        for subdirectory in subdirectories:
            if os.path.isdir(subdirectory) and not files_exist:
                files_exist = files_exist or (len(os.listdir(subdirectory)) > 0)

        # ask whether to continue if files exist

        possible_outcomes = {"yes": True, "no": False}
        if files_exist and self.general["overwrite_output"] == "False":
            question_str = str.join(
                " ",
                (
                    "WARNING: Output directory already exists.",
                    "Continuing will overwrite existing data:",
                    "do you want to continue?",
                ),
            )
            result = get_decision(question_str, possible_outcomes)

            if result:
                question_str = str.join(
                    " ",
                    (
                        "WARNING: All existing data will be overwritten.",
                        "Are you sure?",
                    ),
                )
                result = get_decision(question_str, possible_outcomes)

                # halt unless the answer is yes
                if not result:
                    raise RuntimeError(
                        "run halted: existing output not overwritten "
                        "(set overwrite_output = True to skip this question)"
                    )
                else:
                    logger.warning("run continues, existing data are overwritten")
            else:
                raise RuntimeError(
                    "run halted: existing output not overwritten "
                    "(set overwrite_output = True to skip this question)"
                )

        # create the subdirectories and add them to the object
        for subdirectory in subdirectories:
            subdirname = "%spath" % os.path.split(subdirectory)[1]
            # create or empty
            if os.path.isdir(subdirectory):
                shutil.rmtree(subdirectory, onerror=remove_readonly)
            os.makedirs(subdirectory)
            setattr(self, subdirname, subdirectory)

        return None

    def backup_configuration_file(self, cfgfilename, outputpath):

        fn = os.path.join(outputpath, os.path.basename(cfgfilename))

        # written out rather than copied, so the backup records the substituted paths
        # the run actually used
        with open(fn, "w") as backup_file:
            backup_file.write(self.cfg_content)

        return fn

    def convert_string_to_input(self, val_str, ftype, **kwargs):

        separators = [","]

        if not isinstance(ftype, type):
            raise TypeError("data type %s is not a data type" % ftype)

        value = None

        if isinstance(val_str, NoneType) or val_str.lower() == "none":
            value = None

        elif ftype == bool:

            if val_str.lower() == "true":
                value = True
            else:
                value = False

        else:
            # test whether the value is a list
            possible_list = False

            for separator in separators:

                possible_list = possible_list or separator in val_str

            if possible_list:

                value = convert_string_to_list(val_str, separators)

                # convert every entry to the right data type
                for ix in range(len(value)):
                    value[ix] = ftype(value[ix])

                logger.warning(
                    "include additional separators and data type conversion!"
                )

            else:

                # single entry
                try:
                    value = ftype(val_str)
                except Exception:
                    logger.error("%s cannot be converted to %s" % (val_str, ftype))
        return value
