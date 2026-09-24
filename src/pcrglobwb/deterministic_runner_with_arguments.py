import logging
import os
import shutil
import sys

import pcraster as pcr
from pcraster.framework import DynamicFramework, DynamicModel

from pcrglobwb.common.currTimeStep import ModelTime
from pcrglobwb.configuration import Configuration
from pcrglobwb.pcrglobwb import PCRGlobWB
from pcrglobwb.reporting import Reporting
from pcrglobwb.spinUp import SpinUp

logger = logging.getLogger(__name__)

from pcrglobwb.common import disclaimer


class DeterministicRunner(DynamicModel):

    def __init__(
        self,
        configuration,
        modelTime,
        initialState=None,
        system_argument=None,
        spinUpRun=False,
    ):
        DynamicModel.__init__(self)

        self.modelTime = modelTime
        self.model = PCRGlobWB(configuration, modelTime, initialState, spinUpRun)
        self.reporting = Reporting(configuration, self.model, modelTime)

        # the model parameters may be modified
        self.parameter_adjusment = False
        if ("-adjparm" in list(system_argument)) or (
            "prefactorOptions" in configuration.allSections
        ):
            self.adusting_parameters(configuration, system_argument)
            self.parameter_adjusment = True

        self.configuration = configuration

    def adusting_parameters(self, configuration, system_argument):

        # global pre-multipliers given as arguments
        if "-adjparm" in list(system_argument):

            # start index of the adjustment arguments
            sai = system_argument.index("-adjparm")

            logger.info(
                "Adjusting some model parameters based on given values in the system argument."
            )

            # pre-multipliers for minSoilDepthFrac (linear), kSat (log), recessionCoeff (log), storCap
            # (linear) and degreeDayFactor (linear)
            multiplier_for_minSoilDepthFrac = float(system_argument[sai + 1])
            multiplier_for_kSat = float(system_argument[sai + 2])
            multiplier_for_recessionCoeff = float(system_argument[sai + 3])
            multiplier_for_storCap = float(system_argument[sai + 4])
            multiplier_for_degreeDayFactor = float(system_argument[sai + 5])

            # pre-multiplier for the reference potential ET (linear)
            self.multiplier_for_refPotET = float(system_argument[sai + 6])

            # pre-multiplier for manningsN (linear)
            multiplier_for_manningsN = float(system_argument[sai + 7])

            storGroundwaterIni_file = str(system_argument[sai + 8])

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


def modify_ini_file(original_ini_file, system_argument):

    # created by Edwin H. Sutanudjaja in August 2020 for the Ulysses project

    file_ini = open(original_ini_file, "rt")
    file_ini_content = file_ini.read()
    file_ini.close()

    # output directory (-mod); always required
    main_output_dir = system_argument[system_argument.index("-mod") + 1]
    file_ini_content = file_ini_content.replace("MAIN_OUTPUT_DIR", main_output_dir)
    msg = (
        "The output folder 'outputDir' is set based on the system argument (-mod): "
        + main_output_dir
    )
    print(msg)

    # input directory (-mid)
    if "-mid" in system_argument:
        main_input_dir = system_argument[system_argument.index("-mid") + 1]
        file_ini_content = file_ini_content.replace("MAIN_INPUT_DIR", main_input_dir)
        msg = (
            "The input folder 'inputDir' is set based on the system argument (-mid): "
            + main_input_dir
        )
        print(msg)

    # optional start (-sd) and end (-ed) dates
    if "-sd" in system_argument:
        starting_date = system_argument[system_argument.index("-sd") + 1]
        file_ini_content = file_ini_content.replace("START_DATE", starting_date)
        msg = (
            "The starting date 'startTime' is set based on the system argument (-sd): "
            + starting_date
        )
        print(msg)
    if "-ed" in system_argument:
        end_date = system_argument[system_argument.index("-ed") + 1]
        file_ini_content = file_ini_content.replace("END_DATE", end_date)
        msg = (
            "The end date 'END_DATE' is set based on the system argument (-ed): "
            + end_date
        )
        print(msg)

    # optional initial conditions: main initial state folder (-misd)
    if "-misd" in system_argument:
        main_initial_state_folder = system_argument[system_argument.index("-misd") + 1]
        file_ini_content = file_ini_content.replace(
            "MAIN_INITIAL_STATE_FOLDER", main_initial_state_folder
        )
        msg = (
            "The main folder for all initial states is set based on the system argument (-misd): "
            + main_initial_state_folder
        )
        print(msg)
    # date for initial states (-dfis)
    if "-dfis" in system_argument:
        date_for_initial_states = system_argument[system_argument.index("-dfis") + 1]
        file_ini_content = file_ini_content.replace(
            "DATE_FOR_INITIAL_STATES", date_for_initial_states
        )
        msg = (
            "The date for all initial state files is set based on the system argument (-dfis): "
            + date_for_initial_states
        )
        print(msg)

    # DOMAIN_CONNECTIONS
    if "-clone_connections" in system_argument:
        clone_connections = system_argument[
            system_argument.index("-clone_connections") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "CLONE_CONNECTIONS", clone_connections
        )
        msg = (
            "The clone_connections is set based on the system argument (-clone_connections): "
            + clone_connections
        )
        print(msg)

    # optional forcing files; precipitationNC = PRECIPITATION_FORCING_FILE
    if "-pff" in system_argument:
        precipitation_forcing_file = system_argument[system_argument.index("-pff") + 1]
        file_ini_content = file_ini_content.replace(
            "PRECIPITATION_FORCING_FILE", precipitation_forcing_file
        )
        msg = (
            "The precipitation forcing file 'precipitationNC' is set based on the system argument (-pff): "
            + precipitation_forcing_file
        )
        print(msg)

    # temperatureNC = TEMPERATURE_FORCING_FILE
    if "-tff" in system_argument:
        temperature_forcing_file = system_argument[system_argument.index("-tff") + 1]
        file_ini_content = file_ini_content.replace(
            "TEMPERATURE_FORCING_FILE", temperature_forcing_file
        )
        msg = (
            "The temperature forcing file 'temperatureNC' is set based on the system argument (-tff): "
            + temperature_forcing_file
        )
        print(msg)

    # refETPotFileNC = REF_POT_ET_FORCING_FILE
    if "-rpetff" in system_argument:
        ref_pot_et_forcing_file = system_argument[system_argument.index("-rpetff") + 1]
        file_ini_content = file_ini_content.replace(
            "REF_POT_ET_FORCING_FILE", ref_pot_et_forcing_file
        )
        msg = (
            "The reference potential ET forcing file 'refETPotFileNC' is set based on the system argument (-tff): "
            + ref_pot_et_forcing_file
        )
        print(msg)

    # atmospheric_pressure = PRESSURE_FORCING_FILE
    if "-presff" in system_argument:
        pressure_forcing_file = system_argument[system_argument.index("-presff") + 1]
        file_ini_content = file_ini_content.replace(
            "PRESSURE_FORCING_FILE", pressure_forcing_file
        )
        msg = (
            "The pressure forcing file 'atmospheric_pressure' is set based on the system argument (-presff): "
            + pressure_forcing_file
        )
        print(msg)

    # wind_speed_10m = WIND_FORCING_FILE
    if "-windff" in system_argument:
        wind_forcing_file = system_argument[system_argument.index("-windff") + 1]
        file_ini_content = file_ini_content.replace(
            "WIND_FORCING_FILE", wind_forcing_file
        )
        msg = (
            "The wind forcing file 'wind_speed_10m' is set based on the system argument (-windff): "
            + wind_forcing_file
        )
        print(msg)

    # shortwave_radiation = SHORTWAVE_RADIATION_FORCING_FILE
    if "-swradff" in system_argument:
        shorwave_radiation_forcing_file = system_argument[
            system_argument.index("-swradff") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "SHORTWAVE_RADIATION_FORCING_FILE", shorwave_radiation_forcing_file
        )
        msg = (
            "The shortwave radiation forcing file 'shortwave_radiation' is set based on the system argument (-windff): "
            + shorwave_radiation_forcing_file
        )
        print(msg)

    # relative_humidity = RELATIVE_HUMIDITY_FORCING_FILE
    if "-relhumff" in system_argument:
        relative_humidity_forcing_file = system_argument[
            system_argument.index("-relhumff") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "RELATIVE_HUMIDITY_FORCING_FILE", relative_humidity_forcing_file
        )
        msg = (
            "The relative humidity forcing file 'relative_humidity' is set based on the system argument (-relhumff): "
            + relative_humidity_forcing_file
        )
        print(msg)

    # optional baseflow exponent
    if "-bfexp" in system_argument:
        baseflow_exponent = system_argument[system_argument.index("-bfexp") + 1]
        file_ini_content = file_ini_content.replace(
            "BASEFLOW_EXP_INPUT", baseflow_exponent
        )
        msg = (
            "The groundwater baseflow exponent 'bfexp' is set based on the system argument (-bfexp): "
            + baseflow_exponent
        )
        print(msg)

    # NUMBER_OF_SPINUP_YEARS
    if "-num_of_sp_years" in system_argument:
        number_of_spinup_years = system_argument[
            system_argument.index("-num_of_sp_years") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "NUMBER_OF_SPINUP_YEARS", number_of_spinup_years
        )
        msg = (
            "The number_of_spinup_years is set based on the system argument (-num_of_sp_years): "
            + number_of_spinup_years
        )
        print(msg)

    # CLONEMAP
    if "-clonemap" in system_argument:
        clonemap = system_argument[system_argument.index("-clonemap") + 1]
        file_ini_content = file_ini_content.replace("CLONEMAP", clonemap)
        msg = (
            "The clonemap is set based on the system argument (-clonemap): " + clonemap
        )
        print(msg)

    # USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI
    if "-use_max_fossil_gw_ini" in system_argument:
        use_max_fossil_gw_ini = system_argument[
            system_argument.index("-use_max_fossil_gw_ini") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI", use_max_fossil_gw_ini
        )
        msg = (
            "The option 'useMaximumStorGroundwaterFossilIni' is set based on the system argument (-use_max_fossil_gw_ini): "
            + use_max_fossil_gw_ini
        )
        print(msg)

    # ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE
    if "-est_stor_gw_from_rch" in system_argument:
        est_stor_gw_from_rch = system_argument[
            system_argument.index("-est_stor_gw_from_rch") + 1
        ]
        file_ini_content = file_ini_content.replace(
            "ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE", est_stor_gw_from_rch
        )
        msg = (
            "The option 'estimateStorGroundwaterIniFromRecharge' is set based on the system argument (-est_stor_gw_from_rch): "
            + est_stor_gw_from_rch
        )
        print(msg)

    # dailyGroundwaterRechargeIni / DAILY_GROUNDWATER_RECHARGE_INI
    if "-day_gw_rch_ini" in system_argument:
        day_gw_rch_ini = system_argument[system_argument.index("-day_gw_rch_ini") + 1]
        file_ini_content = file_ini_content.replace(
            "DAILY_GROUNDWATER_RECHARGE_INI", day_gw_rch_ini
        )
        msg = (
            "The option 'dailyGroundwaterRechargeIni' is set based on the system argument (-day_gw_rch_ini): "
            + day_gw_rch_ini
        )
        print(msg)

    # configuration_file_for_qualloc / QUALLOC_CONFIG_FILE
    if "-qcf" in system_argument:
        qualloc_config_file = system_argument[system_argument.index("-qcf") + 1]
        file_ini_content = file_ini_content.replace(
            "QUALLOC_CONFIG_FILE", qualloc_config_file
        )
        msg = (
            "The configuration file to run QUAlloc is set based on the system argument (-qcf): "
            + qualloc_config_file
        )
        print(msg)

    # folder for the original and modified ini files
    folder_for_ini_files = os.path.join(main_output_dir, "ini_files")
    # for a run that is part of a set of parallel (clone) runs
    if (
        system_argument[2] == "parallel"
        or system_argument[2] == "debug_parallel"
        or system_argument[2] == "debug-parallel"
    ):
        clone_code = str(system_argument[3])
        output_folder_with_clone_code = "M%02i" % int(clone_code)
        folder_for_ini_files = os.path.join(
            main_output_dir, output_folder_with_clone_code, "ini_files"
        )

    if os.path.exists(folder_for_ini_files):
        shutil.rmtree(folder_for_ini_files)
    os.makedirs(folder_for_ini_files)

    shutil.copy(
        original_ini_file,
        os.path.join(
            folder_for_ini_files, os.path.basename(original_ini_file) + ".original"
        ),
    )

    new_ini_file_name = os.path.join(
        folder_for_ini_files, os.path.basename(original_ini_file) + ".modified_and_used"
    )
    new_ini_file = open(new_ini_file_name, "w")
    new_ini_file.write(file_ini_content)
    new_ini_file.close()

    return new_ini_file_name


def main():

    disclaimer.print_disclaimer()

    iniFileName = os.path.abspath(sys.argv[1])

    # modify the ini file and save it to a new location
    if "-mod" in sys.argv:
        iniFileName = modify_ini_file(
            original_ini_file=iniFileName, system_argument=sys.argv
        )

    debug_mode = False
    if len(sys.argv) > 2:
        if (
            sys.argv[2] == "debug"
            or sys.argv[2] == "debug_parallel"
            or sys.argv[2] == "debug-parallel"
        ):
            debug_mode = True

    this_run_is_part_of_a_set_of_parallel_run = False
    if len(sys.argv) > 2:
        if (
            sys.argv[2] == "parallel"
            or sys.argv[2] == "debug_parallel"
            or sys.argv[2] == "debug-parallel"
        ):
            this_run_is_part_of_a_set_of_parallel_run = True

    configuration = Configuration(
        iniFileName=iniFileName, debug_mode=debug_mode, no_modification=False
    )

    # a parallel run (e.g. 5 and 6 arcmin runs) gets a specific directory based on the clone code:
    if this_run_is_part_of_a_set_of_parallel_run:
        # modify outputDir, clone map, landmask, etc. based on the command-line arguments
        clone_code = str(sys.argv[3])
        output_folder_with_clone_code = "M%02i" % int(clone_code)
        configuration.globalOptions["outputDir"] += "/" + output_folder_with_clone_code
        configuration.globalOptions["cloneMap"] = configuration.globalOptions[
            "cloneMap"
        ] % (int(clone_code))
        # landmask for the model calculation
        if configuration.globalOptions["landmask"] != "None":
            configuration.globalOptions["landmask"] = configuration.globalOptions[
                "landmask"
            ] % (int(clone_code))

    configuration.set_configuration(system_arguments=sys.argv)

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
        while spinUpRun < noSpinUps and has_converged == False:
            spinUpRun += 1
            currTimeStep.getStartEndTimeStepsForSpinUp(
                configuration.globalOptions["startTime"], spinUpRun, noSpinUps
            )
            logger.info("Spin-Up Run No. " + str(spinUpRun))
            deterministic_runner = DeterministicRunner(
                configuration, currTimeStep, initial_state, sys.argv, spinUpRun=True
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
        configuration, currTimeStep, initial_state, sys.argv, spinUpRun=False
    )

    dynamic_framework = DynamicFramework(
        deterministic_runner, currTimeStep.nrOfTimeSteps
    )
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()


if __name__ == "__main__":
    disclaimer.print_disclaimer(with_logger=True)
    sys.exit(main())
