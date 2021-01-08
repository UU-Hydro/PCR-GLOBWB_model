#!/bin/bash

set -x

bash complete_job_scripts_for_a_run.sh "1.00" "1.00" "gpu034"
bash complete_job_scripts_for_a_run.sh "1.05" "1.05" "gpu035"
bash complete_job_scripts_for_a_run.sh "1.10" "1.10" "gpu036"
bash complete_job_scripts_for_a_run.sh "1.25" "1.25" "gpu037"
bash complete_job_scripts_for_a_run.sh "1.50" "1.50" "gpu038"

set +x
