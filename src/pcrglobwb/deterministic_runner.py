import logging
import os
import sys

from pcraster.framework import DynamicFramework, DynamicModel

from pcrglobwb.common import disclaimer
from pcrglobwb.common.currTimeStep import ModelTime
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

    def initial(self):
        pass

    def dynamic(self):

        # update the model time from the current PCRaster time step
        self.modelTime.update(self.currentTimeStep())

        # update the model (uses the current model time)

        self.model.read_forcings()
        self.model.update(report_water_balance=True)

        self.reporting.report()


def main():

    disclaimer.print_disclaimer()

    iniFileName = os.path.abspath(sys.argv[1])

    debug_mode = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "debug":
            debug_mode = True

    # use the ini file as given
    no_modification = True

    # use the output directory given as a command-line argument
    if len(sys.argv) > 3 and sys.argv[3] == "--output_dir":
        no_modification = False
        output_directory = sys.argv[4]

    configuration = Configuration(
        iniFileName=iniFileName, debug_mode=debug_mode, no_modification=no_modification
    )
    if not no_modification:
        configuration.globalOptions["outputDir"] = output_directory
        configuration.set_configuration()

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
    disclaimer.print_disclaimer(with_logger=True)
    sys.exit(main())
