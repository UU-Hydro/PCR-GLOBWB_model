#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

#~ # preparing initial conditions
#~ python MCmergeMaps.py 1935-12-31 /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/

#~ # preparing input for the steady-state simulation: 
#~ # -  discharge
#~ python nc_basin_merge.py /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/ /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/global/netcdf/1935 1 1935-12-31 1935-12-31 selected discharge_annuaAvg_output.nc
#~ # -  gwRecharge
#~ python nc_basin_merge.py /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/ /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/global/netcdf/1935 1 1935-12-31 1935-12-31 selected gwRecharge_annuaTot_output.nc
#~ # - ccnverting to pcraster maps: discharge in m3/s and gwRecharge in m/day
#~ cd /scratch-shared/edwinhs/05min_runs_february_2016_continue/pcrglobwb_only_from_1901_6LCs_original_parameter_set_natural/adjusted_ksat/continue_from_1929/global/netcdf/1935
#~ pcrcalc  discharge_annuaAvg_output.map = "scalar( discharge_annuaAvg_output.nc)"
#~ pcrcalc gwRecharge_annuaAvg_output.map = "scalar(gwRecharge_annuaTot_output.nc) / 365"
#~ # - do not forget to change the mapattr 
#~ mapattr -c /projects/0/dfguu/data/hydroworld/PCRGLOBWB20/input5min/routing/lddsound_05min.map *.map

# steady state run (this has been performed)
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python deterministic_runner_for_monthly_merging_and_modflow.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_modflow_parallel_6LCs_original_parameter_set_adjusted_ksat_from_1935.STEADYSTATE.ini debug steady-state-only

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_march_2016.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_modflow_parallel_6LCs_original_parameter_set_adjusted_ksat_from_1935.ini


# Note: pcrglobwb modflow with adjusted_ksat - start from 1935
