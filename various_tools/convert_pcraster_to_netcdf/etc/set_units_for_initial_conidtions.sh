
#~ sutan101@gpu002.cluster:/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_05min/initialConditions/non-natural$ ls -lah
#~ total 6.5K
#~ drwxr-xr-x 12 sutan101 depfg  11 Nov 11 12:11 .
#~ drwxr-xr-x  3 sutan101 depfg   1 Nov 11 12:09 ..
#~ drwxr-xr-x  4 sutan101 depfg 100 Nov 14 00:35 1960
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:09 1965
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:11 1978
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:09 1981
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:10 1989
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:10 1995
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:11 1999
#~ drwxr-xr-x  2 sutan101 depfg  99 Nov 11 12:10 1999_master
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:11 2002
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:09 2005
#~ -rw-r--r--  1 sutan101 depfg 164 Nov 11 12:11 source.txt

MAINFOLDER="/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_05min/initialConditions/non-natural/1999/"

#~ sutan101@gpu002.cluster:/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/initialConditions/non-natural/consistent_run_201903XX$ ls -lah 
#~ total 6.5K
#~ drwxr-xr-x 12 sutan101 depfg  11 Nov 11 12:20 .
#~ drwxr-xr-x  4 sutan101 depfg   2 Nov 11 12:19 ..
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:19 1960
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:19 1965
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:20 1978
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:19 1981
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:20 1989
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:20 1995
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:20 1999
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:20 2002
#~ drwxr-xr-x  2 sutan101 depfg  98 Nov 11 12:19 2005
#~ -rw-r--r--  1 sutan101 depfg 236 Nov 11 12:20 source.txt

#~ MAINFOLDER="/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/initialConditions/non-natural/consistent_run_201903XX/2005/"


#~ sutan101@gpu002.cluster:/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/initialConditions/non-natural/original$ ls -lah
#~ total 1.5K
#~ drwxr-xr-x 3 sutan101 depfg  1 Nov 11 12:19 .
#~ drwxr-xr-x 4 sutan101 depfg  2 Nov 11 12:19 ..
#~ drwxr-xr-x 2 sutan101 depfg 99 Nov 11 12:19 1999

#~ MAINFOLDER="/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/initialConditions/non-natural/original/1999/"


set -x

cd ${MAINFOLDER}

mkdir nc_without_units
cp -rv *.nc nc_without_units
chmod -R a-w nc_without_units

cdo setunit,"m3 s-1"    nc_without_units/avgBaseflowLong_*-12-31.nc                        avgBaseflowLong_*-12-31.nc
cdo setunit,"m3 s-1"    nc_without_units/avgDischargeLong_*-12-31.nc                       avgDischargeLong_*-12-31.nc
cdo setunit,"m3 s-1"    nc_without_units/avgDischargeShort_*-12-31.nc                      avgDischargeShort_*-12-31.nc
cdo setunit,"m3 s-1"    nc_without_units/avgLakeReservoirInflowShort_*-12-31.nc            avgLakeReservoirInflowShort_*-12-31.nc
cdo setunit,"m3 s-1"    nc_without_units/avgLakeReservoirOutflowLong_*-12-31.nc            avgLakeReservoirOutflowLong_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/avgNonFossilGroundwaterAllocationLong_*-12-31.nc  avgNonFossilGroundwaterAllocationLong_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/avgNonFossilGroundwaterAllocationShort_*-12-31.nc avgNonFossilGroundwaterAllocationShort_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/avgTotalGroundwaterAbstraction_*-12-31.nc         avgTotalGroundwaterAbstraction_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/avgTotalGroundwaterAllocationLong_*-12-31.nc      avgTotalGroundwaterAllocationLong_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/avgTotalGroundwaterAllocationShort_*-12-31.nc     avgTotalGroundwaterAllocationShort_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/baseflow_*-12-31.nc                               baseflow_*-12-31.nc
cdo setunit,"m3"        nc_without_units/channelStorage_*-12-31.nc                         channelStorage_*-12-31.nc
cdo setunit,"m"         nc_without_units/interceptStor_forest_*-12-31.nc                   interceptStor_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/interceptStor_grassland_*-12-31.nc                interceptStor_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/interceptStor_irrNonPaddy_*-12-31.nc              interceptStor_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/interceptStor_irrPaddy_*-12-31.nc                 interceptStor_irrPaddy_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/interflow_forest_*-12-31.nc                       interflow_forest_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/interflow_grassland_*-12-31.nc                    interflow_grassland_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/interflow_irrNonPaddy_*-12-31.nc                  interflow_irrNonPaddy_*-12-31.nc
cdo setunit,"m day-1"   nc_without_units/interflow_irrPaddy_*-12-31.nc                     interflow_irrPaddy_*-12-31.nc
cdo setunit,"m6 day-2"  nc_without_units/m2tDischargeLong_*-12-31.nc                       m2tDischargeLong_*-12-31.nc
cdo setunit,"m3"        nc_without_units/readAvlChannelStorage_*-12-31.nc                  readAvlChannelStorage_*-12-31.nc
cdo setunit,"m"         nc_without_units/relativeGroundwaterHead_*-12-31.nc                relativeGroundwaterHead_*-12-31.nc
cdo setunit,"m3 day-1"  nc_without_units/riverbedExchange_*-12-31.nc                       riverbedExchange_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowCoverSWE_forest_*-12-31.nc                    snowCoverSWE_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowCoverSWE_grassland_*-12-31.nc                 snowCoverSWE_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowCoverSWE_irrNonPaddy_*-12-31.nc               snowCoverSWE_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowCoverSWE_irrPaddy_*-12-31.nc                  snowCoverSWE_irrPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowFreeWater_forest_*-12-31.nc                   snowFreeWater_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowFreeWater_grassland_*-12-31.nc                snowFreeWater_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowFreeWater_irrNonPaddy_*-12-31.nc              snowFreeWater_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/snowFreeWater_irrPaddy_*-12-31.nc                 snowFreeWater_irrPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/storGroundwater_*-12-31.nc                        storGroundwater_*-12-31.nc
cdo setunit,"m"         nc_without_units/storGroundwaterFossil_*-12-31.nc                  storGroundwaterFossil_*-12-31.nc
cdo setunit,"m"         nc_without_units/storLow_forest_*-12-31.nc                         storLow_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/storLow_grassland_*-12-31.nc                      storLow_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/storLow_irrNonPaddy_*-12-31.nc                    storLow_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/storLow_irrPaddy_*-12-31.nc                       storLow_irrPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/storUpp_forest_*-12-31.nc                         storUpp_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/storUpp_grassland_*-12-31.nc                      storUpp_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/storUpp_irrNonPaddy_*-12-31.nc                    storUpp_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/storUpp_irrPaddy_*-12-31.nc                       storUpp_irrPaddy_*-12-31.nc
cdo setunit,"m3 s-1"    nc_without_units/subDischarge_*-12-31.nc                           subDischarge_*-12-31.nc
cdo setunit,"day"       nc_without_units/timestepsToAvgDischarge_*-12-31.nc                timestepsToAvgDischarge_*-12-31.nc
cdo setunit,"m"         nc_without_units/topWaterLayer_forest_*-12-31.nc                   topWaterLayer_forest_*-12-31.nc
cdo setunit,"m"         nc_without_units/topWaterLayer_grassland_*-12-31.nc                topWaterLayer_grassland_*-12-31.nc
cdo setunit,"m"         nc_without_units/topWaterLayer_irrNonPaddy_*-12-31.nc              topWaterLayer_irrNonPaddy_*-12-31.nc
cdo setunit,"m"         nc_without_units/topWaterLayer_irrPaddy_*-12-31.nc                 topWaterLayer_irrPaddy_*-12-31.nc
cdo setunit,"m3"        nc_without_units/waterBodyStorage_*-12-31.nc                       waterBodyStorage_*-12-31.nc

ncview *.nc

cd -

set +x

