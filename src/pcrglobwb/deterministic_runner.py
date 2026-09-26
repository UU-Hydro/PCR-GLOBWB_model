import argparse
import logging
import os
import sys

from pcraster.framework import DynamicFramework, DynamicModel

from pcrglobwb.common.currTimeStep import ModelTime
from pcrglobwb.common.logging_config import (
    TimeStepProgress,
    add_log_level_arguments,
    log_run_status,
    set_log_dir,
    start_logging,
)
from pcrglobwb.configuration import Configuration
from pcrglobwb.pcrglobwb import PCRGlobWB
from pcrglobwb.reporting import Reporting
from pcrglobwb.spinUp import SpinUp

logger = logging.getLogger(__name__)


class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime, initialState=None):
        DynamicModel.__init__(self)

        self.modelTime = modelTime
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        self.reporting = Reporting(configuration, self.model, modelTime)
        self.progress = TimeStepProgress(modelTime.nrOfTimeSteps)

    def initial(self):
        pass

    def dynamic(self):

        # update the model time from the current PCRaster time step
        self.modelTime.update(self.currentTimeStep())
        self.progress.start_step(self.currentTimeStep(), self.modelTime.currTime)

        # update the model (uses the current model time)

        self.model.read_forcings()
        self.model.update(report_water_balance=True)

        self.reporting.report()

        self.progress.end_step(self.modelTime.isLastDayOfYear())


@log_run_status
def main():

    parser = argparse.ArgumentParser(
        description="Run PCR-GLOBWB from an ini file.", allow_abbrev=False
    )
    parser.add_argument("ini_file", help="PCR-GLOBWB ini file")
    add_log_level_arguments(parser)
    args = parser.parse_args()

    iniFileName = os.path.abspath(args.ini_file)

    start_logging(args.log_level, args.file_level)

    configuration = Configuration(iniFileName=iniFileName)
    configuration.set_configuration()
    set_log_dir(configuration.logFileDir)

    # time step info: year, month, day, doy, etc.
    currTimeStep = ModelTime()

    spin_up = SpinUp(configuration)

    # spin-up
    noSpinUps = int(configuration.globalOptions["maxSpinUpsInYears"])
    initial_state = None
    if noSpinUps > 0:

        logger.info("Spin-Up #Total Years: " + str(noSpinUps))

        spinUpRun = 0
        has_converged = False
        while spinUpRun < noSpinUps and not has_converged:
            spinUpRun += 1
            currTimeStep.getStartEndTimeStepsForSpinUp(
                configuration.globalOptions["startTime"], spinUpRun, noSpinUps
            )
            logger.info("Spin-Up Run No. " + str(spinUpRun))
            deterministic_runner = DeterministicRunner(
                configuration, currTimeStep, initial_state
            )

            all_state_begin = deterministic_runner.model.getAllState()

            dynamic_framework = DynamicFramework(
                deterministic_runner, currTimeStep.nrOfTimeSteps
            )
            dynamic_framework.setQuiet(True)
            dynamic_framework.run()

            all_state_end = deterministic_runner.model.getAllState()

            has_converged = spin_up.checkConvergence(
                all_state_begin,
                all_state_end,
                spinUpRun,
                deterministic_runner.model.routing.cellArea,
            )

            initial_state = deterministic_runner.model.getState()

    # run the model (excluding the DA scheme)
    currTimeStep.getStartEndTimeSteps(
        configuration.globalOptions["startTime"], configuration.globalOptions["endTime"]
    )
    logger.info("Transient simulation run started.")
    deterministic_runner = DeterministicRunner(
        configuration, currTimeStep, initial_state
    )
    dynamic_framework = DynamicFramework(
        deterministic_runner, currTimeStep.nrOfTimeSteps
    )
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()


if __name__ == "__main__":
    sys.exit(main())
