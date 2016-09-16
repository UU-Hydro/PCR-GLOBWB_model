# the command lines:

# load a special version of pcraster that is optimized for pcraster-modflow (provided by Oliver)
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model

python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_kinematicwave_without_modflow_miroc-esm-chem/spin-up_natural_with_accutraveltime/setup_05min_watch_pcrglobwb_2_land_covers_natural_edwin_parameter_set_accutraveltime_global_miroc-esm-chem_spin_up_climatology_1951-1990.ini

python merge_pcraster_maps.py 1951-12-31 /scratch-shared/edwinhs/05min_runs_2016_aug/pcrglobwb_4_land_covers_edwin_parameter_set_miroc-esm-chem/no_correction/natural/spin-up_with_climatology_1951-1990_accutraveltime/ states 8 Global

python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_kinematicwave_without_modflow_miroc-esm-chem/spin-up_natural_with_kinematicwave/setup_05min_watch_pcrglobwb_2_land_covers_natural_edwin_parameter_set_kinematicwave_global_miroc-esm-chem_spin_up_climatology_1951-1990.ini

python merge_pcraster_maps.py 1951-12-31 /scratch/shared/edwinhs/05min_runs_2016_aug/pcrglobwb_4_land_covers_edwin_parameter_set_miroc-esm-chem/no_correction/natural/spin-up_with_climatology_1951-1990_kinematicwave/  states 8 Global
