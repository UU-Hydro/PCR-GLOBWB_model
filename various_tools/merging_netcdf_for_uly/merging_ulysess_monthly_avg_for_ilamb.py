#! /usr/bin/python

import os
import sys


# ~ cyes@cca-login4:/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv> ls -lah
# ~ total 28K
# ~ drwxr-x---  6 cyes copext 4.0K Dec  4 10:52 .
# ~ drwxr-x---  4 cyes copext 4.0K Dec  7 12:57 ..
# ~ lrwxrwxrwx  1 cyes copext   98 Dec  2 10:13 _spinup -> /scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_uly-lcv/spinup
# ~ drwxr-x--- 76 cyes copext 4.0K Dec  2 10:02 begin_from_1981
# ~ drwxr-x--- 76 cyes copext 4.0K Dec  3 02:28 continue_from_1991
# ~ drwxr-x--- 76 cyes copext 4.0K Dec  3 19:50 continue_from_2001
# ~ drwxr-x--- 76 cyes copext 4.0K Dec  4 10:59 continue_from_2011


main_folder = "/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv/"

start_years = [1981, 1991, 2001, 2011] 
final_year = 2019

# ~ main_folder = sys.argv[1]
# ~ start_years = map(int, list(set(sys.argv[2].split(","))))
# ~ start_years.sort()
# ~ final_year  = int(sys.argv[3])

print(start_years)

outp_folder = "/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/monthly_averages/"

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
    

    cmd = ""

    for year in range(sta_year, end_year + 1):
    
        cmd_mkdir = "mkdir -p " + outp_folder + "/" + str(year)
        os.system(cmd_mkdir)
        
        cmd = cmd + "python3 merge_netcdf_6_arcmin_ulysses.py " + \
              input_folder + " " + \
              outp_folder + "/" + str(year) + " " + \
              "outMonthAvgNC " + \
              str(year)+"-01-31" + " " + str(year)+"-12-31" + " " + \
              "ulyssesP,ulyssesET,ulyssesSWE,ulyssesQsm,ulyssesSM,ulyssesQrRunoff,ulyssessRefPET,ulyssessCropPET,ulyssesSnowFraction,ulyssesSMUpp,totalWaterStorageThickness,surfaceWaterStorage,interceptStor,snowFreeWater,snowCoverSWE,storGroundwater NETCDF4 True 8 Global default_lats ;"

        print(cmd)
        os.system(cmd)
        
