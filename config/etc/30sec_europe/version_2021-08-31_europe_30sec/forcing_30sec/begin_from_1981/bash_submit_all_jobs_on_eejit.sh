#!/bin/bash 

sbatch --export  STA=1,END=6  -J e1k01-06 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export  STA=7,END=13 -J e1k07-13 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=14,END=21 -J e1k14-21 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=22,END=29 -J e1k22-29 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=30,END=37 -J e1k30-37 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
sbatch --export STA=38,END=45 -J e1k38-45 job_script_sbatch_30sec_runs_per_basin_on_eejit.sh
