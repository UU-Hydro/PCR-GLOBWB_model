#!/bin/bash

set -x

bash complete_job_scripts_for_a_run.sh "1.00" "1.00" "gpu036"
bash complete_job_scripts_for_a_run.sh "1.05" "1.05" "gpu037"
bash complete_job_scripts_for_a_run.sh "1.10" "1.10" "gpu038"
bash complete_job_scripts_for_a_run.sh "1.25" "1.25" "gpu039"
bash complete_job_scripts_for_a_run.sh "1.50" "1.50" "gpu040"

set +x
