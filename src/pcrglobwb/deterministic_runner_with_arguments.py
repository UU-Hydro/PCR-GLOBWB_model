import argparse
import logging
import os
import sys

import pcraster as pcr
from pcraster.framework import DynamicFramework, DynamicModel

from pcrglobwb.common import virtualOS as vos
from pcrglobwb.common.arguments import (
    PLACEHOLDER_FLAGS,
    add_placeholder_arguments,
    fill_placeholders,
    placeholder_values,
)
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

INI_FLAGS = [flag for flag in PLACEHOLDER_FLAGS if flag != "--pcrglobwb-output-dir"]


class DeterministicRunner(DynamicModel):

    def __init__(
        self,
        configuration,
        modelTime,
        initialState=None,
        adjparm=None,
        spinUpRun=False,
    ):
        DynamicModel.__init__(self)

        self.modelTime = modelTime
        self.model = PCRGlobWB(configuration, modelTime, initialState, spinUpRun)
        self.reporting = Reporting(configuration, self.model, modelTime)

        # the model parameters may be modified
        self.parameter_adjusment = False
        if adjparm is not None or "prefactorOptions" in configuration.allSections:
            self.adusting_parameters(configuration, adjparm)
            self.parameter_adjusment = True

        self.configuration = configuration
        self.progress = TimeStepProgress(modelTime.nrOfTimeSteps)

    def adusting_parameters(self, configuration, adjparm):

        # global pre-multipliers given as arguments
        if adjparm is not None:

            logger.info(
                "Adjusting some model parameters based on given values in the system argument."
            )

            # pre-multipliers for minSoilDepthFrac (linear), kSat (log), recessionCoeff (log), storCap
            # (linear) and degreeDayFactor (linear)
            multiplier_for_minSoilDepthFrac = float(adjparm[0])
            multiplier_for_kSat = float(adjparm[1])
            multiplier_for_recessionCoeff = float(adjparm[2])
            multiplier_for_storCap = float(adjparm[3])
            multiplier_for_degreeDayFactor = float(adjparm[4])

            # pre-multiplier for the reference potential ET (linear)
            self.multiplier_for_refPotET = float(adjparm[5])

            # pre-multiplier for manningsN (linear)
            multiplier_for_manningsN = float(adjparm[6])

            storGroundwaterIni_file = str(adjparm[7])

        # pre-factors can also be defined in the ini file; these overwrite the pre-multipliers
        if "prefactorOptions" in configuration.allSections:

            logger.info(
                "Adjusting some model parameters based on given values in the ini/configuration file."
            )

            # linear; note: does not work for the changing WMIN or Joyce land cover options
            self.multiplier_for_refPotET = float(
                configuration.prefactorOptions["linear_multiplier_for_refPotET"]
            )
            # linear
            multiplier_for_degreeDayFactor = float(
                configuration.prefactorOptions["linear_multiplier_for_degreeDayFactor"]
            )
            # linear
            multiplier_for_minSoilDepthFrac = float(
                configuration.prefactorOptions["linear_multiplier_for_minSoilDepthFrac"]
            )
            # log
            multiplier_for_kSat = float(
                configuration.prefactorOptions["log_10_multiplier_for_kSat"]
            )
            # linear
            multiplier_for_storCap = float(
                configuration.prefactorOptions["linear_multiplier_for_storCap"]
            )
            # log
            multiplier_for_recessionCoeff = float(
                configuration.prefactorOptions["log_10_multiplier_for_recessionCoeff"]
            )
            # linear
            multiplier_for_manningsN = float(
                configuration.prefactorOptions["multiplier_for_manningsN"]
            )

            # file location (use the full path)
            storGroundwaterIni_file = str(
                configuration.prefactorOptions["storGroundwaterIni_file"]
            )

        # log the global pre-multipliers
        msg = "\n"
        msg += "\n"
        msg += "Multiplier values used: " + "\n"
        msg += (
            "For minSoilDepthFrac           : "
            + str(multiplier_for_minSoilDepthFrac)
            + "\n"
        )
        msg += "For kSat (log-scale)           : " + str(multiplier_for_kSat) + "\n"
        msg += (
            "For recessionCoeff (log-scale) : "
            + str(multiplier_for_recessionCoeff)
            + "\n"
        )
        msg += "For storCap                    : " + str(multiplier_for_storCap) + "\n"
        msg += (
            "For degreeDayFactor            : "
            + str(multiplier_for_degreeDayFactor)
            + "\n"
        )
        msg += (
            "For refPotET                   : "
            + str(self.multiplier_for_refPotET)
            + "\n"
        )
        msg += (
            "For multiplier_for_manningsN   : " + str(multiplier_for_manningsN) + "\n"
        )
        msg += "For storGroundwaterIni_file    : " + str(storGroundwaterIni_file) + "\n"
        logger.info(msg)
        # and write them to a text file in the "maps" folder of outputDir (the cwd, see configuration.py)
        f = open("multiplier.txt", "w")
        f.write(msg)
        f.close()

        if storGroundwaterIni_file != "Default":
            self.model.groundwater.storGroundwater = vos.readPCRmapClone(
                storGroundwaterIni_file, configuration.cloneMap, configuration.tmpDir
            )
            self.model.groundwater.storGroundwater = pcr.ifthen(
                self.landmask, pcr.cover(self.model.groundwater.storGroundwater, 0.0)
            )
        pcr.report(self.model.groundwater.storGroundwater, "storGroundwaterIni.map")

        # adjust the parameters with the pre-multipliers and save the adjusted maps to the "maps"
        # folder of outputDir (the cwd, see configuration.py)
        # manningsN: minimum zero, log scale
        self.model.routing.manningsN = (
            multiplier_for_manningsN * self.model.routing.manningsN
        )
        pcr.report(self.model.routing.manningsN, "manningsN.map")

        # recessionCoeff: minimum zero, log scale
        self.model.groundwater.recessionCoeff = pcr.max(
            0.0,
            (10 ** (multiplier_for_recessionCoeff))
            * self.model.groundwater.recessionCoeff,
        )
        self.model.groundwater.recessionCoeff = pcr.min(
            1.0, self.model.groundwater.recessionCoeff
        )
        pcr.report(self.model.groundwater.recessionCoeff, "recessionCoeff.map")

        for coverType in self.model.landSurface.coverTypes:

            self.model.landSurface.landCoverObj[coverType].degreeDayFactor = pcr.max(
                0.0,
                multiplier_for_degreeDayFactor
                * self.model.landSurface.landCoverObj[coverType].degreeDayFactor,
            )
            pcraster_filename = "degreeDayFactor" + "_" + coverType + ".map"
            pcr.report(
                self.model.landSurface.landCoverObj[coverType].degreeDayFactor,
                pcraster_filename,
            )

            # kSat and storCap for the 2-layer model
            if self.model.landSurface.numberOfSoilLayers == 2:

                # kSat: minimum zero, log scale
                self.model.landSurface.landCoverObj[coverType].parameters.kSatUpp = (
                    pcr.max(
                        0.0,
                        (10 ** (multiplier_for_kSat))
                        * self.model.landSurface.landCoverObj[
                            coverType
                        ].parameters.kSatUpp,
                    )
                )
                self.model.landSurface.landCoverObj[coverType].parameters.kSatLow = (
                    pcr.max(
                        0.0,
                        (10 ** (multiplier_for_kSat))
                        * self.model.landSurface.landCoverObj[
                            coverType
                        ].parameters.kSatLow,
                    )
                )
                pcraster_filename = "kSatUpp" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[coverType].parameters.kSatUpp,
                    pcraster_filename,
                )
                pcraster_filename = "kSatLow" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[coverType].parameters.kSatLow,
                    pcraster_filename,
                )

                # storCap: minimum zero
                self.model.landSurface.landCoverObj[coverType].parameters.storCapUpp = (
                    pcr.max(
                        0.0,
                        multiplier_for_storCap
                        * self.model.landSurface.landCoverObj[
                            coverType
                        ].parameters.storCapUpp,
                    )
                )
                self.model.landSurface.landCoverObj[coverType].parameters.storCapLow = (
                    pcr.max(
                        0.0,
                        multiplier_for_storCap
                        * self.model.landSurface.landCoverObj[
                            coverType
                        ].parameters.storCapLow,
                    )
                )
                pcraster_filename = "storCapUpp" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp,
                    pcraster_filename,
                )
                pcraster_filename = "storCapLow" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapLow,
                    pcraster_filename,
                )

            # kSat and storCap for the 3-layer model
            if self.model.landSurface.numberOfSoilLayers == 3:

                # kSat: minimum zero, log scale
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.kSatUpp000005 = pcr.max(
                    0.0,
                    (10 ** (multiplier_for_kSat))
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatUpp000005,
                )
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.kSatUpp005030 = pcr.max(
                    0.0,
                    (10 ** (multiplier_for_kSat))
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatUpp005030,
                )
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.kSatLow030150 = pcr.max(
                    0.0,
                    (10 ** (multiplier_for_kSat))
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatLow030150,
                )
                pcraster_filename = "kSatUpp000005" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatUpp000005,
                    pcraster_filename,
                )
                pcraster_filename = "kSatUpp005030" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatUpp005030,
                    pcraster_filename,
                )
                pcraster_filename = "kSatLow030150" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.kSatLow030150,
                    pcraster_filename,
                )

                # storCap: minimum zero
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.storCapUpp000005 = pcr.max(
                    0.0,
                    multiplier_for_storCap
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp000005,
                )
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.storCapUpp005030 = pcr.max(
                    0.0,
                    multiplier_for_storCap
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp005030,
                )
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.storCapLow030150 = pcr.max(
                    0.0,
                    multiplier_for_storCap
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapLow030150,
                )
                pcraster_filename = "storCapUpp000005" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp000005,
                    pcraster_filename,
                )
                pcraster_filename = "storCapUpp005030" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp005030,
                    pcraster_filename,
                )
                pcraster_filename = "storCapLow030150" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapLow030150,
                    pcraster_filename,
                )

            # recalculate rootZoneWaterStorageCap (WMAX in the oldcalc script) after modifying storCap
            if self.model.landSurface.numberOfSoilLayers == 2:
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.rootZoneWaterStorageCap = (
                    self.model.landSurface.landCoverObj[coverType].parameters.storCapUpp
                    + self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapLow
                )
            if self.model.landSurface.numberOfSoilLayers == 3:
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.rootZoneWaterStorageCap = (
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp000005
                    + self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapUpp005030
                    + self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.storCapLow030150
                )
            pcraster_filename = "rootZoneWaterStorageCap" + "_" + coverType + ".map"
            pcr.report(
                self.model.landSurface.landCoverObj[
                    coverType
                ].parameters.rootZoneWaterStorageCap,
                pcraster_filename,
            )

            if multiplier_for_minSoilDepthFrac != 1.0:

                # minimum zero
                self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = (
                    pcr.max(
                        0.0,
                        multiplier_for_minSoilDepthFrac
                        * self.model.landSurface.landCoverObj[
                            coverType
                        ].minSoilDepthFrac,
                    )
                )
                # limited by maxSoilDepthFrac
                self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = (
                    pcr.min(
                        self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac,
                        self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac,
                    )
                )
                # maximum 1.0
                self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = (
                    pcr.min(
                        1.0,
                        self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac,
                    )
                )
                pcraster_filename = "minSoilDepthFrac" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac,
                    pcraster_filename,
                )

                # recalculate arnoBeta after modifying minSoilDepthFrac
                self.model.landSurface.landCoverObj[coverType].arnoBeta = pcr.max(
                    0.001,
                    (
                        self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac
                        - 1.0
                    )
                    / (
                        1.0
                        - self.model.landSurface.landCoverObj[
                            coverType
                        ].minSoilDepthFrac
                    )
                    + self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.orographyBeta
                    - 0.01,
                )
                self.model.landSurface.landCoverObj[coverType].arnoBeta = pcr.cover(
                    pcr.max(
                        0.001, self.model.landSurface.landCoverObj[coverType].arnoBeta
                    ),
                    0.001,
                )
                pcraster_filename = "arnoBeta" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[coverType].arnoBeta,
                    pcraster_filename,
                )

                # recalculate rootZoneWaterStorageMin (WMIN in the oldcalc script: minimum local soil
                # water capacity within the cell, in m) after modifying minSoilDepthFrac
                self.model.landSurface.landCoverObj[
                    coverType
                ].rootZoneWaterStorageMin = (
                    self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac
                    * self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.rootZoneWaterStorageCap
                )
                pcraster_filename = "rootZoneWaterStorageMin" + "_" + coverType + ".map"
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].rootZoneWaterStorageMin,
                    pcraster_filename,
                )

                # recalculate rootZoneWaterStorageRange (WMAX - WMIN, in m) after modifying storCap and minSoilDepthFrac
                self.model.landSurface.landCoverObj[
                    coverType
                ].rootZoneWaterStorageRange = (
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].parameters.rootZoneWaterStorageCap
                    - self.model.landSurface.landCoverObj[
                        coverType
                    ].rootZoneWaterStorageMin
                )
                pcraster_filename = (
                    "rootZoneWaterStorageRange" + "_" + coverType + ".map"
                )
                pcr.report(
                    self.model.landSurface.landCoverObj[
                        coverType
                    ].rootZoneWaterStorageRange,
                    pcraster_filename,
                )

    def initial(self):
        pass

    def dynamic(self):

        # update the model time from the current PCRaster time step
        self.modelTime.update(self.currentTimeStep())
        self.progress.start_step(self.currentTimeStep(), self.modelTime.currTime)

        # read the forcing (uses the current model time)
        self.model.read_forcings()

        # adjust the reference potential ET with the pre-multiplier
        if self.parameter_adjusment:
            self.model.meteo.referencePotET = (
                self.model.meteo.referencePotET * self.multiplier_for_refPotET
            )

        # update the model
        self.model.update(report_water_balance=True)

        self.reporting.report()

        self.progress.end_step(self.modelTime.isLastDayOfYear())


@log_run_status
def main():

    parser = argparse.ArgumentParser(
        description="Run PCR-GLOBWB with ini placeholders filled from the command line.",
        allow_abbrev=False,
    )
    parser.add_argument("ini_file", help="PCR-GLOBWB ini file")
    add_placeholder_arguments(parser, INI_FLAGS)
    parser.add_argument(
        "--clone-code",
        type=int,
        help="run clone N of a set of parallel runs; output goes to outputDir/MNN",
    )
    parser.add_argument(
        "--adjust-parameters",
        nargs=8,
        metavar=(
            "MINSOILDEPTHFRAC",
            "KSAT",
            "RECESSIONCOEFF",
            "STORCAP",
            "DEGREEDAYFACTOR",
            "REFPOTET",
            "MANNINGSN",
            "STORGROUNDWATERINI",
        ),
        help="pre-multipliers for seven parameters, then a storGroundwaterIni file",
    )
    add_log_level_arguments(parser)
    args = parser.parse_args()

    if args.adjust_parameters is not None:
        try:
            [float(value) for value in args.adjust_parameters[:7]]
        except ValueError as error:
            parser.error("--adjust-parameters: %s" % error)

    iniFileName = os.path.abspath(args.ini_file)

    start_logging(args.log_level, args.file_level)

    replacements = placeholder_values(args, INI_FLAGS)
    for token, value in replacements.items():
        logger.info(
            "The placeholder %s is set based on the system argument: %s", token, value
        )
    with open(iniFileName) as ini_file:
        ini_text = fill_placeholders(
            ini_file.read(), replacements, INI_FLAGS, iniFileName
        )

    configuration = Configuration(iniFileName=iniFileName, ini_text=ini_text)

    # a parallel run (e.g. 5 and 6 arcmin runs) gets a specific directory based on the clone code:
    if args.clone_code is not None:
        # modify outputDir, clone map, landmask, etc. based on the command-line arguments
        configuration.globalOptions["outputDir"] += "/M%02i" % args.clone_code
        configuration.globalOptions["cloneMap"] %= args.clone_code
        # landmask for the model calculation
        if configuration.globalOptions["landmask"] != "None":
            configuration.globalOptions["landmask"] %= args.clone_code

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
                configuration,
                currTimeStep,
                initial_state,
                args.adjust_parameters,
                spinUpRun=True,
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

        # TODO: for a parallel run, merge when the spin-up is done and keep the states in a separate folder

    # run the model (excluding the DA scheme)
    currTimeStep.getStartEndTimeSteps(
        configuration.globalOptions["startTime"], configuration.globalOptions["endTime"]
    )

    logger.info("Transient simulation run started.")
    deterministic_runner = DeterministicRunner(
        configuration,
        currTimeStep,
        initial_state,
        args.adjust_parameters,
        spinUpRun=False,
    )

    dynamic_framework = DynamicFramework(
        deterministic_runner, currTimeStep.nrOfTimeSteps
    )
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()


if __name__ == "__main__":
    sys.exit(main())
