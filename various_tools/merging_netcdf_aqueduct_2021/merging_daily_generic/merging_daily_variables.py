#! /usr/bin/python

import os
import sys

main_folder = "/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gswp3-w5e5/historical-reference/"
start_years = [1960] 
final_year = 2019

main_folder = sys.argv[1]
# ~ start_years = map(int, list(set(sys.argv[2].split(","))))
start_years = [int(sys.argv[2])]
start_years.sort()
final_year  = int(sys.argv[3])

print(start_years)

outp_folder = "/datadrive/edwin/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gswp3-w5e5/historical-reference/merged_daily_variables"

outp_folder = str(sys.argv[4])

#~ cmd = "rm -rf " + outp_folder
#~ print(cmd)
#~ os.system(cmd)
cmd = "mkdir -p " + outp_folder
print(cmd)
os.system(cmd)
cmd = "cp merge_netcdf_general.py " + outp_folder
print(cmd)
os.system(cmd)
os.chdir(outp_folder)



# command line for merging
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
    
        # ~ # annual total
        # ~ cmd += "python merge_netcdf_general.py " + \
               # ~ input_folder + " " + \
               # ~ outp_folder + " " + \
               # ~ "outAnnuaTotNC " + \
               # ~ str(year)+"-12-31" + " " + str(year)+"-12-31" + " " + \
               # ~ "evaporation_from_irrigation,precipitation_at_irrigation " + \
               # ~ "NETCDF4 True 8 53 all_lats default & "

        # ~ # monthly total
        # ~ cmd += "python merge_netcdf_general.py " + \
               # ~ input_folder + " " + \
               # ~ outp_folder + " " + \
               # ~ "outMonthTotNC " + \
               # ~ str(year)+"-01-31" + " " + str(year)+"-12-31" + " " + \
               # ~ "irrGrossDemand " + \
               # ~ "NETCDF4 True 8 53 all_lats default"
       
# ~ (base) edwin@pcrglobwb-azure:/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gswp3-w5e5/historical-reference/begin_from_1960$ ls -lah M0000001/netcdf/*daily*
# ~ -rw-rw-r-- 1 pcrglobwb-azure pcrglobwb-azure 6.5G Sep 29 14:57 M0000001/netcdf/baseflow_dailyTot_output.nc
# ~ -rw-rw-r-- 1 pcrglobwb-azure pcrglobwb-azure 6.5G Sep 29 14:57 M0000001/netcdf/directRunoff_dailyTot_output.nc
# ~ -rw-rw-r-- 1 pcrglobwb-azure pcrglobwb-azure 6.5G Sep 29 14:57 M0000001/netcdf/interflowTotal_dailyTot_output.nc
# ~ -rw-rw-r-- 1 pcrglobwb-azure pcrglobwb-azure 6.5G Sep 29 14:57 M0000001/netcdf/referencePotET_dailyTot_output.nc

        # daily total
        cmd += "python merge_netcdf_general.py " + \
               input_folder + " " + \
               outp_folder + " " + \
               "outDailyTotNC " + \
               str(year)+"-01-01" + " " + str(year)+"-12-31" + " " + \
               "referencePotET,baseflow,directRunoff,interflowTotal " + \
               "NETCDF4 True 8 53 all_lats default &"

        run_just_per_year = False
        if str(year)[3] == "9" or str(year)[3] == "6" or str(year)[3] == "3" or year == end_year or run_just_per_year == True:
            cmd += "wait"
            print(cmd)
            os.system(cmd)
            cmd = ""
