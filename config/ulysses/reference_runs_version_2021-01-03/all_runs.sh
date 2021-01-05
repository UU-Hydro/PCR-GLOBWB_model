#!/bin/bash

set -x

bash complete_job_scripts_for_a_run.sh "b1.0" "1.0" "gpu030"
bash complete_job_scripts_for_a_run.sh "b1.1" "1.1" "gpu031"
bash complete_job_scripts_for_a_run.sh "b1.2" "1.2" "gpu032"
bash complete_job_scripts_for_a_run.sh "b1.3" "1.3" "gpu033"
bash complete_job_scripts_for_a_run.sh "b1.4" "1.4" "gpu034"
bash complete_job_scripts_for_a_run.sh "b1.5" "1.5" "gpu035"
bash complete_job_scripts_for_a_run.sh "b1.6" "1.6" "gpu036"
bash complete_job_scripts_for_a_run.sh "b1.7" "1.7" "gpu037"
bash complete_job_scripts_for_a_run.sh "b1.8" "1.8" "gpu038"
bash complete_job_scripts_for_a_run.sh "b1.9" "1.9" "gpu039"
bash complete_job_scripts_for_a_run.sh "b2.0" "2.0" "gpu040"

set +x
