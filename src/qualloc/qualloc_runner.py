# TODO: move spin-up to a separate class to reduce the size of this runner
# TODO: include general spin-up settings as global variables for easy adaptation

import logging
import os
import sys

from pcraster.framework import DynamicFramework, DynamicModel
from pcraster.multicore import set_nr_worker_threads

from qualloc.model_configuration import configuration_parser
from qualloc.model_time import model_time
from qualloc.qualloc_main import qualloc_model
from qualloc.qualloc_reporting import qualloc_reporting

# number of multicore workers
set_nr_worker_threads(4)

NoneType = type(None)

logger = logging.getLogger(__name__)

# allowed time increments
allowed_time_increments = ["monthly", "daily"]

# command-line flags and the configuration placeholders they fill; the names
# match those of PCR-GLOBWB's run-with-arguments so a coupled run can pass the
# same values to both models
argument_tokens = {
    "-mid": "MAIN_INPUT_DIR",
    "-mod": "MAIN_OUTPUT_DIR",
    "-clonemap": "CLONEMAP",
    "-pcrglobwb_mod": "PCRGLOBWB_OUTPUT_DIR",
}


class qualloc_runner(DynamicModel):

    def __init__(
        self, model_configuration, model_time, model_flags={}, initial_conditions=None
    ):
        DynamicModel.__init__(self)

        self.model_configuration = model_configuration
        self.model_time = model_time
        self.model = qualloc_model(
            self.model_configuration, self.model_time, model_flags, initial_conditions
        )
        self.reporting = qualloc_reporting(self.model_configuration)

        return None

    def initial(self):

        self.model.initialize()

        self.reporting.initialize()

        return None

    def dynamic(self):

        self.model_time.update(self.currentTimeStep())

        self.model.update()

        self.reporting.report(self.model_time, self.model)

        if self.model_time.report_flags["yearly"]:
            # end of year: report the states so the run can be restarted
            self.model.finalize_year()

        if self.model_time.last_time_step:

            # close all input and output files
            self.model.finalize_run()
            self.reporting.close()

            return self.model.initial_conditions


def main():
    # parse the command-line options and arguments (including the configuration file) and run the model

    # split the command line into the flags of argument_tokens and the remaining
    # arguments: the configuration file, followed by the positional substitution
    # arguments
    replacements = {}
    arguments = []

    system_argument = sys.argv[1:]
    argument_cnt = 0

    while argument_cnt < len(system_argument):

        argument = system_argument[argument_cnt]

        if argument in argument_tokens:

            if argument_cnt + 1 == len(system_argument):
                sys.exit("%s is not followed by a value" % argument)

            replacements[argument_tokens[argument]] = system_argument[argument_cnt + 1]
            argument_cnt += 2

        else:
            arguments.append(argument)
            argument_cnt += 1

    # substitution arguments that make the input file more generic
    subst_args = []

    # note: the error is currently disabled
    if len(arguments) < 1:
        cfgfilename = "qualloc_basic_setup.cfg"

    else:
        cfgfilename = arguments[0]
        subst_args = arguments[1:]
    cfgfilename = os.path.abspath(cfgfilename)

    # configuration object
    sections = [
        "general",
        "time",
        "forcing",
        "groundwater",
        "surfacewater",
        "water_management",
        "water_quality",
    ]
    groups = []
    model_configuration = configuration_parser(
        cfgfilename=cfgfilename,
        sections=sections,
        groups=groups,
        subst_args=subst_args,
        replacements=replacements,
    )
    os.chdir(model_configuration.temppath)

    # time object; called pcr_time here and recast to model_time in the dynamic
    # model and dependent modules
    startyear = int(model_configuration.time["startyear"])
    endyear = int(model_configuration.time["endyear"])
    time_increment = model_configuration.time["time_increment"]

    if time_increment not in allowed_time_increments:
        message_str = ""
        message_str = str.join(
            " ",
            (
                "time increment %s is invalid," % time_increment,
                "any of the following allowed:",
                str.join(", ", allowed_time_increments),
            ),
        )
        logger.error(message_str)
        sys.exit()

    pcr_time = model_time(startyear, endyear, time_increment)

    # dummy model flags and initial conditions; initial conditions are read from
    # the configuration file if None, otherwise the existing warm states are used
    model_flags = {}
    initial_conditions = None

    qualloc_instance = qualloc_runner(
        model_configuration, pcr_time, model_flags, initial_conditions
    )

    qualloc_model = DynamicFramework(
        qualloc_instance, lastTimeStep=pcr_time.number_time_steps, firstTimestep=1
    )
    qualloc_model.setQuiet(True)
    initial_conditions = qualloc_model.run()

    # close the log files and change directory
    logging.shutdown()
    os.chdir(model_configuration.start_root_path)


if __name__ == "__main__":
    main()
    logging.shutdown()
    print("all done")
