#!/bin/bash 

sbatch --export  STA=1,END=6  -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export  STA=7,END=13 -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=14,END=21 -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=22,END=29 -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=30,END=37 -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=38,END=45 -J eu1k_m1 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
