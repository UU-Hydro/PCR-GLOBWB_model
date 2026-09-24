import os
import sys

# command-line arguments
config_file_folder = sys.argv[1]
config_file_name = sys.argv[2]
system_arguments = sys.argv[3:]

original_ini_file = os.path.join(config_file_folder, config_file_name)

file_ini = open(original_ini_file, "rt")
file_ini_content = file_ini.read()
file_ini.close()

# clone code (-mod)
clone_code = "M" + system_arguments[system_arguments.index("-mod") - 1]
file_ini_content = file_ini_content.replace("CLONE_CODE", clone_code)

# output directory (-mod)
qualloc_output_dir = system_arguments[system_arguments.index("-mod") + 1]
file_ini_content = file_ini_content.replace("QUALLOC_OUTPUT_DIR", qualloc_output_dir)
msg = (
    "The output folder 'outputpath' is set based on the system argument (-mod): "
    + qualloc_output_dir
)
print(msg)

# optional start (-sy) and end years
if "-sy" in system_arguments:
    start_year = system_arguments[system_arguments.index("-sy") + 1]
    file_ini_content = file_ini_content.replace("START_DATE", start_year)
    msg = (
        "The starting date 'startyear' is set based on the system argument (-sy): "
        + start_year
    )
    print(msg)
if "-ey" in system_arguments:
    end_year = system_arguments[system_arguments.index("-ey") + 1]
    file_ini_content = file_ini_content.replace("END_DATE", end_year)
    msg = (
        "The end date 'endyear' is set based on the system argument (-ey): " + end_year
    )
    print(msg)

# optional initial conditions: main initial state folder (-qisd)
if "-qisd" in system_arguments:
    initial_state_folder = system_arguments[system_arguments.index("-qisd") + 1]
    file_ini_content = file_ini_content.replace(
        "INITIAL_STATE_FOLDER", initial_state_folder
    )
    msg = (
        "The main folder for all initial states is set based on the system argument (-qisd): "
        + initial_state_folder
    )
    print(msg)

# date for initial states (-dfis)
if "-dfis" in system_arguments:
    date_for_initial_states = system_arguments[system_arguments.index("-dfis") + 1]
    file_ini_content = file_ini_content.replace(
        "DATE_FOR_INITIAL_STATES", date_for_initial_states
    )
    msg = (
        "The date for all initial state files is set based on the system argument (-dfis): "
        + date_for_initial_states
    )
    print(msg)

# water quality requirements (-wqf)
if "-wqf" in system_arguments:
    water_quality_flag = system_arguments[system_arguments.index("-wqf") + 1]
    file_ini_content = file_ini_content.replace("WQ_FLAG", water_quality_flag)
    msg = (
        "The consideration of sectoral water quality requirements is set based on the system argument (-wqf): "
        + water_quality_flag
    )
    print(msg)

# folder for the original and modified ini files
new_ini_file_name = os.path.join(
    config_file_folder,
    f"{start_year}_wq{water_quality_flag}",
    f'{config_file_name.split(".")[0]}_{clone_code}.cfg',
)

if os.path.isfile(new_ini_file_name):
    os.remove(new_ini_file_name)
print(new_ini_file_name)

new_ini_file = open(new_ini_file_name, "w")
new_ini_file.write(file_ini_content)
new_ini_file.close()
