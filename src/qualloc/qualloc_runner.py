# TODO: move spin-up to a separate class to reduce the size of this runner
# TODO: include general spin-up settings as global variables for easy adaptation

import argparse
import os

from pcraster.framework import DynamicFramework, DynamicModel
from pcraster.multicore import set_nr_worker_threads

from pcrglobwb.common.arguments import add_placeholder_arguments, placeholder_values
from pcrglobwb.common.logging_config import (
    TimeStepProgress,
    add_log_level_arguments,
    log_run_status,
    set_log_dir,
    start_logging,
)
from qualloc.model_configuration import configuration_parser, substitutable_flags
from qualloc.model_time import model_time
from qualloc.qualloc_main import qualloc_model
from qualloc.qualloc_reporting import qualloc_reporting

# number of multicore workers
set_nr_worker_threads(4)

NoneType = type(None)

# allowed time increments
allowed_time_increments = ["monthly", "daily"]


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
        self.progress = TimeStepProgress(model_time.number_time_steps)

        return None

    def initial(self):

        self.model.initialize()

        self.reporting.initialize()

        return None

    def dynamic(self):

        self.model_time.update(self.currentTimeStep())
        self.progress.start_step(self.currentTimeStep(), self.model_time.date)

        self.model.update()

        self.reporting.report(self.model_time, self.model)

        if self.model_time.report_flags["yearly"]:
            # end of year: report the states so the run can be restarted
            self.model.finalize_year()

        self.progress.end_step(self.model_time.report_flags["yearly"])

        if self.model_time.last_time_step:

            # close all input and output files
            self.model.finalize_run()
            self.reporting.close()

            return self.model.initial_conditions


@log_run_status
def main():
    # parse the command-line options and arguments (including the configuration file) and run the model

    parser = argparse.ArgumentParser(
        description="Run QUAlloc from a cfg file.", allow_abbrev=False
    )
    parser.add_argument("cfgfilename", help="QUAlloc cfg file")
    add_placeholder_arguments(parser, substitutable_flags)
    add_log_level_arguments(parser)
    args = parser.parse_args()

    replacements = placeholder_values(args, substitutable_flags)
    cfgfilename = os.path.abspath(args.cfgfilename)

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
    start_logging(args.log_level, args.file_level)
    model_configuration = configuration_parser(
        cfgfilename=cfgfilename,
        sections=sections,
        groups=groups,
        replacements=replacements,
    )

    set_log_dir(model_configuration.logpath)

    os.chdir(model_configuration.temppath)

    # time object; called pcr_time here and recast to model_time in the dynamic
    # model and dependent modules
    startyear = int(model_configuration.time["startyear"])
    endyear = int(model_configuration.time["endyear"])
    time_increment = model_configuration.time["time_increment"]

    if time_increment not in allowed_time_increments:
        message_str = str.join(
            " ",
            (
                "time increment %s is invalid," % time_increment,
                "any of the following allowed:",
                str.join(", ", allowed_time_increments),
            ),
        )
        raise ValueError(message_str)

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

    os.chdir(model_configuration.start_root_path)


if __name__ == "__main__":
    main()
