"""
configuration:
"""

import datetime
import logging
import os
import re
import shutil
import stat
import sys

if sys.version[0] == "2":
    from ConfigParser import RawConfigParser as ConfigParser
else:
    from six.moves.configparser import RawConfigParser as ConfigParser

from qualloc.basic_functions import convert_string_to_list, get_decision

logger = logging.getLogger(__name__)


critical_improvements = str.join("\n", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "make a general function to process list",
        "",
    ),
)

print("\nDevelopmens for model config class:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()


NoneType = type(None)

# placeholders that the calling program replaces in the configuration file; they
# match the tokens PCR-GLOBWB's run-with-arguments substitutes in its ini files,
# so a cfg and an ini can be driven by the same arguments
substitutable_tokens = [
    "MAIN_INPUT_DIR",
    "MAIN_OUTPUT_DIR",
    "PCRGLOBWB_OUTPUT_DIR",
    "CLONEMAP",
]

token_pattern = re.compile(r"\b(%s)\b" % str.join("|", substitutable_tokens))


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
        debug_mode=False,
        subst_args=[],
        replacements={},
        **optional_arguments,
    ):

        object.__init__(self)

        message_str = "\n%s\nInitializing the QUAlloc model run\n%s\n" % (
            "=" * 80,
            "=" * 80,
        )
        print(message_str)

        # configuration file, groups and sections
        self.cfgfilename = cfgfilename
        self.sections = sections
        self.groups = groups

        # timestamp of this run, used in log file names etc.
        self._timestamp = datetime.datetime.now()
        self._timestamp_str = str(self._timestamp.isoformat())
        self._timestamp_str = self._timestamp_str[: self._timestamp_str.find(".")]
        self._timestamp_str = self._timestamp_str.replace(":", ".")

        self.debug_mode = debug_mode

        # save the initial root for later use
        self.start_root_path = os.path.abspath(os.path.dirname(__file__))

        # substitute tokens before parsing so every value is covered, including those
        # in the optional sections and groups
        self.cfg_content = self.substitute_tokens(self.cfgfilename, replacements)

        self.parse_configuration_file(
            self.cfgfilename, self.groups, self.sections, subst_args
        )

        # create all necessary directories
        self.create_output_directories()

        # copy the configuration file
        logfileroot = self.backup_configuration_file(
            self.cfgfilename, self.logpath, self._timestamp_str
        )

        logfileroot = os.path.splitext(logfileroot)[0]
        self.initialize_logger(logfileroot)

        logger.info("Model run started at %s" % self._timestamp)
        logger.info("Logging output to %s" % self.logfilename)
        logger.info("Debugging output to %s" % self.dbgfilename)

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

    def substitute_tokens(self, cfgfilename, replacements):
        """

substitute_tokens: function that returns the contents of the configuration file \
with each of the substitutable tokens replaced by the value the calling program \
passed for it. Halts the run if the file uses a token that was not passed, as \
the unreplaced token would otherwise surface much later as a missing file.

"""

        with open(cfgfilename) as cfgfile:
            cfg_content = cfgfile.read()

        missing_tokens = sorted(
            set(token_pattern.findall(cfg_content)) - set(replacements.keys())
        )

        if len(missing_tokens) > 0:
            message_str = (
                "configuration file %s uses the placeholder(s) %s, for which no value was passed"
                % (cfgfilename, str.join(", ", missing_tokens))
            )
            sys.exit(message_str)

        return token_pattern.sub(
            lambda match: replacements[match.group(1)], cfg_content
        )

    def parse_configuration_file(self, cfgfilename, groups, sections, subst_args):

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
                    for key, value in section_info.items():
                        if "$" in value:
                            argposcnt = value.find("$")
                            argpos = int(value[argposcnt + 1 :]) - 1
                            value = str.join(
                                "", (value[:argposcnt], subst_args[argpos])
                            )
                            section_info[key] = value
                    setattr(self, section, section_info)
                except:
                    message_str = (
                        "processing information on the compulsory section [%s] raised an error"
                        % (section)
                    )
                    sys.exit(message_str)
            else:
                message_str = (
                    "configuration file does not contain information for the compulsory section [%s] "
                    % (section)
                )
                sys.exit(message_str)
        # process groups and miscellaneous sections
        for group in groups:
            try:
                setattr(self, group, {})
            except:
                message_str = (
                    "processing information on the group [%s] raised an error" % (group)
                )
                sys.exit(message_str)
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
                for key, value in section_info.items():
                    if "$" in value:
                        try:
                            value = subst_args[int(value.lstrip("$")) - 1]
                        except:
                            message_str = (
                                "argument substitution failed on %s in optional section %s"
                                % (key, section)
                            )
                        section_info[key] = value
                setattr(self, section, section_info)

            except:
                message_str = (
                    "processing information on the section [%s] raised an error"
                    % (section)
                )
                sys.exit(message_str)

        # check that the required entries of every group are present
        for group in groups:
            if len(getattr(self, group).keys()) == 0:
                message_str = (
                    "configuration file does not contain the necessary information on %s "
                    % (group)
                )
                sys.exit(message_str)

        return None

    def initialize_logger(self, logfileroot):
        """

initialize_logger: function that initializes the logger that prints messages \
to a log file and to the screen at configurable levels.

    """

        logging.getLogger().setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%m-%d %H:%M"
        )

        log_level_console = "INFO"
        log_level_file = "INFO"
        # log levels in order: DEBUG, INFO, WARNING, ERROR, CRITICAL

        # log level from the configuration file
        if "log_level_console" in list(self.general.keys()):
            log_level_console = self.general["log_level_console"]
        if "log_level_file" in list(self.general.keys()):
            log_level_file = self.general["log_level_file"]

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

        self.logfilename = str.join("", (logfileroot, ".log"))

        file_level = getattr(logging, log_level_file.upper(), logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError("Invalid log level: %s", log_level_file)

        file_handler = logging.FileHandler(self.logfilename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)

        # debug log file name
        self.dbgfilename = str.join("", (logfileroot, ".dbg"))

        debug_handler = logging.FileHandler(self.dbgfilename)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(debug_handler)

        self.log_file_handlers = [debug_handler, file_handler]

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
            sys.exit(message_str)

        if not os.path.isabs(self.general["outputpath"]):
            self.general["outputpath"] = os.path.abspath(self.general["outputpath"])

        if not os.path.isdir(self.general["outputpath"]):
            os.makedirs(self.general["outputpath"])
            message_str = "output path %s does not exist and is created" % (
                self.general["outputpath"]
            )
            print(message_str)

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
                    sys.exit("run halted!")
                else:
                    print("run continues, existing data are overwritten")
            else:
                sys.exit("run halted!")

        # create the subdirectories and add them to the object
        for subdirectory in subdirectories:
            subdirname = "%spath" % os.path.split(subdirectory)[1]
            # create or empty
            if os.path.isdir(subdirectory):
                shutil.rmtree(subdirectory, onerror=remove_readonly)
            os.makedirs(subdirectory)
            setattr(self, subdirname, subdirectory)

        return None

    def backup_configuration_file(self, cfgfilename, outputpath, replacement_str=""):

        fn = os.path.split(cfgfilename)[1]
        fn, ext = os.path.splitext(fn)

        fn = str.join("", (fn, "_", replacement_str, ext))
        fn = os.path.join(outputpath, fn)

        # written out rather than copied, so the backup records the substituted paths
        # the run actually used
        with open(fn, "w") as backup_file:
            backup_file.write(self.cfg_content)

        return fn

    def convert_string_to_input(self, val_str, ftype, **kwargs):

        separators = [","]

        if not isinstance(ftype, type):
            logger.error("data type %s is not a data type" % ftype)
            sys.exit()

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
                except:
                    logger.error("%s cannot be converted to %s" % (val_str, ftype))
        return value
