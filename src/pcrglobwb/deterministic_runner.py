import argparse
import glob
import logging
import logging.handlers
import os
import platform
import shutil
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

        # update the model
        self.model.update(report_water_balance=True)

        self.reporting.report()


def parse_args(argv=None):
    def parse_override(text):
        target, sep, value = text.partition("=")
        section, dot, key = target.partition(".")
        if not (sep and dot and section and key):
            raise argparse.ArgumentTypeError(
                f"expected SECTION.KEY=VALUE, got {text!r}"
            )
        return section, key, value

    parser = argparse.ArgumentParser(prog="deterministic_runner", allow_abbrev=False)
    parser.add_argument("ini")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        type=parse_override,
        metavar="SECTION.KEY=VALUE",
        help="override an ini option; repeatable",
    )
    return parser.parse_args(argv)


def start_bootstrap_logging(debug):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    )
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    root.addHandler(console)

    # holds every record for the log files, which cannot exist until the output dirs do;
    # flushLevel above CRITICAL so it never flushes on its own
    buffer = logging.handlers.MemoryHandler(
        capacity=sys.maxsize, flushLevel=logging.CRITICAL + 1
    )
    root.addHandler(buffer)
    return buffer


def start_file_logging(config, buffer, debug):
    timestamp = config._timestamp.isoformat().replace(":", ".")
    stem = f"{config.logFileDir}{os.path.basename(config.iniFileName)}_{timestamp}"
    log_filename = stem + ".log"
    dbg_filename = stem + ".dbg"

    log_file = logging.FileHandler(log_filename)
    log_file.setLevel(logging.DEBUG if debug else logging.INFO)
    dbg_file = logging.FileHandler(dbg_filename)
    dbg_file.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.removeHandler(buffer)
    for handler in (log_file, dbg_file):
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        root.addHandler(handler)
        for record in buffer.buffer:
            if record.levelno >= handler.level:
                handler.handle(record)
    buffer.close()

    logger.info(f"Model run started at {config._timestamp}")
    logger.info(f"Logging output to {log_filename}")
    logger.info(f"Debugging output to {dbg_filename}")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Python version:\n{sys.version}")
    pcraster_check_filename = stem + "_pcrcalc_output.txt"
    cmd = f"pcrcalc &> {pcraster_check_filename}"
    os.system(cmd)
    logger.info(
        f"PCRaster version (output from pcrcalc): see the file {pcraster_check_filename}"
    )
    logger.info(f'PATH={os.environ["PATH"]}')
    logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "N/A")}')
    logger.info(f'HOSTNAME: {os.environ.get("HOSTNAME", "N/A")}')
    logger.info(
        "PCRASTER_NR_WORKER_THREADS (set by export, only for PCRaster version >= 4.2): "
        f'{os.environ.get("PCRASTER_NR_WORKER_THREADS", "N/A")}'
    )
    logger.info(f"The system arguments for this run: {sys.argv}")


def main():

    args = parse_args()

    buffer = start_bootstrap_logging(args.debug)
    disclaimer.print_disclaimer(with_logger=True)

    configuration = Configuration(os.path.abspath(args.ini), args.overrides)

    if configuration.reportingOptions["is_sub_run"] != "True":
        os.makedirs(configuration.globalOptions["outputDir"], exist_ok=True)
        for path in (
            configuration.tmpDir,
            configuration.outNCDir,
            configuration.scriptDir,
            configuration.logFileDir,
            configuration.endStateDir,
            configuration.mapsDir,
        ):
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)

        # TODO: subfolders are not copied
        for filename in glob.glob(
            os.path.join(configuration.starting_directory, "*.py")
        ):
            shutil.copy(filename, configuration.scriptDir)

    # all pcr.report files are written to the working directory
    os.chdir(configuration.mapsDir)

    start_file_logging(configuration, buffer, args.debug)

    shutil.copy(
        configuration.iniFileName,
        configuration.logFileDir
        + os.path.basename(configuration.iniFileName)
        + "_"
        + str(configuration._timestamp.isoformat()).replace(":", ".")
        + ".ini",
    )

    spin_up = SpinUp(configuration)

    # spin-up
    noSpinUps = int(configuration.globalOptions["maxSpinUpsInYears"])
    initial_state = None
    if noSpinUps > 0:

        logger.info(f"Spin-Up #Total Years: {noSpinUps}")

        spinUpRun = 0
        has_converged = False
        while spinUpRun < noSpinUps and not has_converged:
            spinUpRun += 1
            currTimeStep = ModelTime.forSpinUp(
                configuration.globalOptions["startTime"], spinUpRun, noSpinUps
            )
            logger.info(f"Spin-Up Run No. {spinUpRun}")
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
    currTimeStep = ModelTime(
        configuration.globalOptions["startTime"], configuration.globalOptions["endTime"]
    )

    logger.info(f"Transient run started: ({currTimeStep.nrOfTimeSteps} time steps).")
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
