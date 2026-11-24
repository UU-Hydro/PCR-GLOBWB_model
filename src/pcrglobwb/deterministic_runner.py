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
    for token, flag in [("START_DATE", "-sd"), ("END_DATE", "-ed")]:
        if token in file_ini_content:
            sys.exit(
                f"{original_ini_file} uses the placeholder {token}; pass it with {flag}"
            )

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
            f"The clonemap is set based on the system argument (-clonemap): {clonemap}"
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

    if os.path.exists(folder_for_ini_files):
        shutil.rmtree(folder_for_ini_files)
    os.makedirs(folder_for_ini_files)

    shutil.copy(
        original_ini_file,
        os.path.join(
            folder_for_ini_files, f"{os.path.basename(original_ini_file)}.original"
        ),
    )

    new_ini_file_name = os.path.join(
        folder_for_ini_files, f"{os.path.basename(original_ini_file)}.modified_and_used"
    )
    new_ini_file = open(new_ini_file_name, "w")
    new_ini_file.write(file_ini_content)
    new_ini_file.close()

    return new_ini_file_name


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

    debug_mode = len(sys.argv) > 2 and sys.argv[2] == "debug"

    buffer = start_bootstrap_logging(debug_mode)
    disclaimer.print_disclaimer(with_logger=True)

    iniFileName = os.path.abspath(sys.argv[1])

    # modify the ini file and save it to a new location
    if "-mod" in sys.argv:
        iniFileName = modify_ini_file(
            original_ini_file=iniFileName, system_argument=sys.argv
        )

    configuration = Configuration(iniFileName=iniFileName)
    start_file_logging(configuration, buffer, debug_mode)

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
