#!/bin/bash
#SBATCH -t 24:00:00
#SBATCH -p rome
#SBATCH -N 1
#SBATCH -n 16

# initiate conda by activating base
source activate base
conda activate geo

# merging outputs
# wqr = True
cd /gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_dynqual_qualloc_wqTrue/
cd /gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_qualloc_wqTrue/
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/channelStorage_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/channelStorage_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedTDS_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedTDS_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/discharge_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/discharge_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/salinity_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/salinity_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/dissolved_oxygen_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/dissolved_oxygen_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/thermoelectricGrossDemand_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/thermoelectricGrossDemand_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/organic_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/organic_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/thermoelectricWaterWithdrawal_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/thermoelectricWaterWithdrawal_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/pathogen_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/pathogen_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/totalWaterStorageVolume_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/totalWaterStorageVolume_monthAvg_output_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedBOD_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedBOD_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/waterTemp_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/waterTemp_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedFC_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedFC_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/domestic_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/domestic_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/irrigation_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/irrigation_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/livestock_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/livestock_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/manufacture_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/manufacture_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/thermoelectric_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/thermoelectric_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_renewable_groundwater_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_livestock_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_livestock_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_livestock_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_manufacture_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_manufacture_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_manufacture_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_thermoelectric_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withd rawal_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
wait

# wqr = False
cd /gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_dynqual_qualloc_wqFalse/
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/channelStorage_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/channelStorage_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedTDS_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedTDS_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/discharge_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/discharge_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/salinity_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/salinity_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/dissolved_oxygen_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/dissolved_oxygen_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/thermoelectricGrossDemand_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/thermoelectricGrossDemand_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/organic_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/organic_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/thermoelectricWaterWithdrawal_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/thermoelectricWaterWithdrawal_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/pathogen_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/pathogen_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/totalWaterStorageVolume_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/totalWaterStorageVolume_monthAvg_output_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedBOD_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedBOD_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/waterTemp_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/waterTemp_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/pcrglobwb/routedFC_monthAvg_output_*-01-01_to_*-12-01.nc global/pcrglobwb/routedFC_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/domestic_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/domestic_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/irrigation_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/irrigation_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/livestock_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/livestock_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/manufacture_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/manufacture_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/thermoelectric_gross_demand_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/thermoelectric_gross_demand_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_renewable_groundwater_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/potential_withdrawal_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/potential_withdrawal_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_domestic_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_domestic_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_irrigation_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_irrigation_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_livestock_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_livestock_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_manufacture_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_manufacture_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/demand_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/demand_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_domestic_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_domestic_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_irrigation_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_irrigation_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_livestock_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
wait
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_livestock_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_livestock_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_livestock_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_manufacture_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_manufacture_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_manufacture_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_manufacture_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_thermoelectric_allocated_to_desalinated_water_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_desalinated_water_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_groundwater_monthly_avg_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_*-01-01_to_*-12-01.nc global/qualloc/withdrawal_thermoelectric_allocated_to_renewable_surfacewater_monthly_avg_1980_2019.nc &
wait
echo "Done!"

# pseudo-naturalized run
cd /gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_pseudo_naturalized/
cdo -v -z zip_9 -f nc4 -mergetime */global/baseflow_monthAvg_output_*-01-01_to_*-12-31.nc global/baseflow_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/channelStorage_monthAvg_output_*-01-01_to_*-12-31.nc global/channelStorage_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/directRunoff_monthAvg_output_*-01-01_to_*-12-31.nc global/directRunoff_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/discharge_monthAvg_output_*-01-01_to_*-12-31.nc global/discharge_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/interflowTotal_monthAvg_output_*-01-01_to_*-12-31.nc global/interflowTotal_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/surfaceWaterInf_monthAvg_output_*-01-01_to_*-12-31.nc global/surfaceWaterInf_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/totalWaterStorageVolume_monthAvg_output_*-01-01_to_*-12-31.nc global/totalWaterStorageVolume_monthAvg_output_1980_2019.nc &
cdo -v -z zip_9 -f nc4 -mergetime */global/waterBodyActEvaporation_monthAvg_output_*-01-01_to_*-12-31.nc global/waterBodyActEvaporation_monthAvg_output_1980_2019.nc &
wait
echo "Done!"