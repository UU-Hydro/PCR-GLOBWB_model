#!/usr/bin/env python
import os
import sys

import tqdm

import lue.framework as lfr

from configuration import Configuration
from currTimeStep import ModelTime
from reporting import Reporting

from pcrglobwb import PCRGlobWB


class Progressor(lfr.Progressor):
    """
    Class for progressor object that shows progress during model run
    """

    def __init__(self, nr_time_steps):
        lfr.Progressor.__init__(self)
        self.progressbar = tqdm.tqdm(
            total=nr_time_steps,
            colour="#5e81ac",
            # leave=False,
        )

    def initialize(self):
        self.progressbar.reset()

    def simulate(self, _):
        self.progressbar.update()

    def finalize(self):
        self.progressbar.refresh()


class DeterministicRunner(lfr.Model):

    def __init__(self, configuration, modelTime, initialState=None):
        super().__init__()

        self.modelTime = modelTime
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        # TODO LUE self.reporting = Reporting(configuration, self.model, modelTime)

    def initialize(self):
        pass

    def simulate(self, time_step):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(time_step)

        # update model (will pick up current model time from model time object)

        self.model.read_forcings()
        self.model.update(report_water_balance=True)

        # do any needed reporting for this time step
        # TODO self.reporting.report()


@lfr.runtime_scope
def main():

    iniFileName = os.path.abspath(sys.argv[1])

    debug_mode = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "debug":
            debug_mode = True

    # no modification in the given ini file, use it as it is
    no_modification = True

    # use the output directory as given in the system argument
    if len(sys.argv) > 3 and sys.argv[3] == "--output_dir":
        no_modification = False
        output_directory = sys.argv[4]

    # object to handle configuration/ini file
    configuration = Configuration(
        iniFileName=iniFileName, debug_mode=debug_mode, no_modification=no_modification
    )
    if no_modification == False:
        configuration.main_output_directory = output_directory
        configuration.globalOptions["outputDir"] = output_directory
        configuration.set_configuration()

    # timeStep info: year, month, day, doy, hour, etc
    currTimeStep = ModelTime()
    initial_state = None

    currTimeStep.getStartEndTimeSteps(
        configuration.globalOptions["startTime"], configuration.globalOptions["endTime"]
    )

    model = DeterministicRunner(
        configuration, currTimeStep, initial_state
    )

    progressor = Progressor(currTimeStep.nrOfTimeSteps)

    lfr.run_deterministic(model, progressor, currTimeStep.nrOfTimeSteps)


if __name__ == "__main__":
    sys.exit(main())
