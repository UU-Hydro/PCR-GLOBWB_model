#! /usr/bin/python

import os
import sys


# ~ sutan101@gpu040.cluster:/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/1.50$ ls -lah begin_from_1981/M0000001/netcdf/*daily*
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/temperature_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesDischarge_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesET_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesP_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesQrRunoff_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesQsm_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesSMUpp_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesSM_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesSWE_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssesSnowFraction_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssessCropPET_dailyTot_output.nc
# ~ -r--r--r-- 1 sutan101 depfg 770M Jan 10 22:39 begin_from_1981/M0000001/netcdf/ulyssessRefPET_dailyTot_output.nc


# ~ ulyssesET,ulyssesQrRunoff,ulyssesQsm,ulyssesSMUpp,ulyssesSM,ulyssesSWE,ulyssesSnowFraction,ulyssessCropPET


main_folder = "/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/1.50/"


start_years = [1981, 1991, 2001, 2011] 
final_year = 2019

# ~ main_folder = sys.argv[1]
# ~ start_years = map(int, list(set(sys.argv[2].split(","))))
# ~ start_years.sort()
# ~ final_year  = int(sys.argv[3])

print(start_years)

outp_folder = "/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/merged_all_daily_1981-2019/b1p50/"

# ~ outp_folder = str(sys.argv[4])

#~ cmd = "rm -rf " + outp_folder
#~ print(cmd)
#~ os.system(cmd)
cmd = "mkdir -p " + outp_folder
print(cmd)
os.system(cmd)
cmd = "cp merge_netcdf_6_arcmin_ulysses.py " + outp_folder
print(cmd)
os.system(cmd)
os.chdir(outp_folder)


cmd = ""

for i_year in range(0, len(start_years)):
    
    # - input sub folder
    inp_sub_folder = "begin_from_" + str(start_years[i_year]) 
    if i_year > 0: inp_sub_folder = "continue_from_" + str(start_years[i_year])
    
    input_folder = main_folder + "/" + inp_sub_folder + "/"
    
    sta_year = int(start_years[i_year])
    if i_year == (len(start_years)-1):
        end_year = final_year
    else:
        end_year = int(start_years[i_year+1]) - 1
    
    for year in range(sta_year, end_year + 1):
    
        # ~ python3 merge_netcdf_6_arcmin_ulysses.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outDailyTotNC ${STARTING_DATE} ${END_DATE} ulyssesQrRunoff,ulyssesDischarge NETCDF4 False 12 Global default_lats
        
        cmd_mkdir = "mkdir -p " + outp_folder + "/" + str(year)
        os.system(cmd_mkdir)
        
        cmd = cmd + "python3 merge_netcdf_6_arcmin_ulysses.py " + \
              input_folder + " " + \
              outp_folder + "/" + str(year) + " " + \
              "outDailyTotNC " + \
              str(year)+"-01-01" + " " + str(year)+"-12-31" + " " + \
              "ulyssesET,ulyssesQrRunoff,ulyssesQsm,ulyssesSMUpp,ulyssesSM,ulyssesSWE,ulyssesSnowFraction,ulyssessCropPET" NETCDF4 True 8 Global default_lats &"
    
        if str(year)[3] == "9": cmd = cmd + " wait ;"
    
print(cmd)
os.system(cmd)
        
