# python script to run PCR-GLOBWB_MOD in LISA/SARA
#
# -  created by Edwin H. Sutanudjaja 19 March 2012 
#
# - modified by Edwin H. Sutanudjaja 02 April 2012:
#   - make sure that calculations produce correct and complete maps
#   - use pcrglobwb_rm_transient_02APR2012.mod to save the used KS1 and KS2
#
# - modified by Edwin H. Sutanudjaja -- 12 April 2012
#   - Including factor for changing WMIN.
#   - only saving the YEAR's folders, deleting PCRaster-MODFLOW files etc.
#
# - modified by Edwin H. Sutanudjaja -- 16 April 2012
#   - Including factor for changing Z (upper soil depths).
#
# - modified by Edwin H. Sutanudjaja -- 17 April 2012
#   - Including factor for changing TCL.
#
# - modified by Edwin H. Sutanudjaja -- 20 April 2012
#   - make a correction for copying the last time step map to the initial folder
#
# - finalized for the RUNS on 12 MAY 2012
#   - Generating 324 runs to do the first sensitivity analysis, see the logbook on 12 MAY 2012 
#
# - repaired on 13 May 2012: to include parameter.txt in the first year result
#
# - checked by E.H. Sutanudjaja on 17 May 2012
# - checked by E.H. Sutanudjaja on 19 May 2012 and in this script, we don't delete groundwater head output files
#
# - checked by E.H. Sutanudjaja on 21 May 2012 and in this script, we  DO   delete groundwater head output files (to reduce the filesize in SARA)
#
# - modified by Edwin H. Sutanudjaja -- 4 June 2012
#   - we changed the PCG parameter in pcrglobwb_rm_steadyst2_2012_06_04.mod
#
# - modified by Edwin H. Sutanudjaja -- 5 June 2012
#   - we changed the PCG parameter in pcrglobwb_rm_steadyst1_2012_06_05.mod
#
##########################################################################################################################################################

import  os, calendar, datetime, zlib, zipfile, sys, string

StartYear   = int(1992)
End__Year   = int(2000)

# obtaining the python arguments
output_fold     = str(sys.argv[ 1])+'_'+str(StartYear)+'_'+str(End__Year)
Ksat_factor_sed = str(sys.argv[ 2])
Ksat_factor_mon = str(sys.argv[ 3])
KD___factor_sed = str(sys.argv[ 4])
KD___factor_mon = str(sys.argv[ 5])
Wmin_factor_sed = str(sys.argv[ 6])
Wmin_factor_mon = str(sys.argv[ 7])
Z2___factor_sed = str(sys.argv[ 8])
Z2___factor_mon = str(sys.argv[ 9])
TCL__factor_sed = str(sys.argv[10])
TCL__factor_mon = str(sys.argv[11])
print sys.argv
os.system('rm -r results')						#
os.system('mkdir results')						# make sure that the results directory exist
os.system('mkdir '+str(output_fold))

# run the steady state model without the linear reservoir of S3
command = 'pcrcalc -f pcrglobwb_rm_steadyst1_2012_06_05.mod "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'"' 
status = False			# calculation status
while status == False:
  print command; os.system(command)
  status = os.path.isfile("results//gw_headd.ini")
os.system('rm -r '        +str(output_fold)+'//rsteady_*')
os.system('mkdir '        +str(output_fold)+'//rsteady_1st')
os.system('cp results//* '+str(output_fold)+'//rsteady_1st')

# run the steady state model   WITH  the linear reservoir of S3
command = 'pcrcalc -f pcrglobwb_rm_steadyst2_2012_06_04.mod "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'"' 
status = False			# calculation status
while status == False:
  print command; os.system(command)
  status = os.path.isfile("results//gw_headd.map")
os.system('rm -r '        +str(output_fold)+'//rsteady_2nd')
os.system('mkdir '        +str(output_fold)+'//rsteady_2nd')
os.system('cp results//* '+str(output_fold)+'//rsteady_2nd')

# run the transient model with constant input for at least 100 days
os.system('cp results//gw_headd.map   results//gw_headd.ini')				# copying the results of the steady state model 
command =   'pcrcalc -f pcrglobwb_rm_steadywbf_2012_03_00.mod "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'" "100"'
status = False			# calculation status
while status == False:
  print command; os.system(command)
  status = os.path.isfile("results//gw_headd.map")
os.system('rm -r '        +str(output_fold)+'//rsteady_3rd')
os.system('mkdir '        +str(output_fold)+'//rsteady_3rd')
os.system('cp results//* '+str(output_fold)+'//rsteady_3rd')

# run the transient model with constant input for 30 days
max_abs_delta_h = 9999
while max_abs_delta_h > 0.05:
  os.system('cp results//gw_headd.map results//gw_headd.ini')				# copying the results of the previous spinning-up process 
  command = 'pcrcalc -f pcrglobwb_rm_steadywbf_2012_03_00.mod "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'"  "30"' 
  status = False			# calculation status
  while status == False:
    print command; os.system(command)
    status = os.path.isfile("results//gw_hdcon.map")
  os.system('mapattr -p results//gw_hdcon.map -> results//convg.tmp')
  chfile = open("results//convg.tmp",'r')
  chmatr = chfile.readlines()
  line11 = string.split(chmatr[11],"val")
  minval = float(line11[1]); max_abs_delta_h = minval
  print(max_abs_delta_h)
  chfile.close()
os.system('rm -r '        +str(output_fold)+'//rsteady_4th')
os.system('mkdir '        +str(output_fold)+'//rsteady_4th')
os.system('cp results//* '+str(output_fold)+'//rsteady_4th')

# run the REAL transient model:
#
# initial conditions
os.system('rm -r initials                                                     ')
os.system('mkdir initials                                                     ')
#
os.system('cp results//gw_headd.map                     initials//headinit.ini')
os.system('cp ..//maps01//lake_08Jul2011_nc1109.wle.map initials//lkhdinit.ini')
#
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min01.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min02.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min03.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min04.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min05.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min06.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min07.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min08.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min09.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min10.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min11.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min12.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min13.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min14.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//QC_min15.ini')
#
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin15BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin14BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin13BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin12BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin11BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin10BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin09BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin08BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin07BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin06BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin05BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin04BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin03BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin02BS.ini')
os.system('cp ..//maps01//qm_avg_19701999.map           initials//Qmin01BS.ini')
#
os.system('cp ..//maps01//r3_avg_19701999.map           initials//rechinit.ini')
#
os.system('cp           results//rivheadd.map           initials//rivhinit.ini')
os.system('cp           results//rivheadd.map           initials//rh_min01.ini')
os.system('cp           results//rivheadd.map           initials//rh_min02.ini')
os.system('cp           results//rivheadd.map           initials//rh_min03.ini')
os.system('cp           results//rivheadd.map           initials//rh_min04.ini')
os.system('cp           results//rivheadd.map           initials//rh_min05.ini')
os.system('cp           results//rivheadd.map           initials//rh_min06.ini')
os.system('cp           results//rivheadd.map           initials//rh_min07.ini')
os.system('cp           results//rivheadd.map           initials//rh_min08.ini')
os.system('cp           results//rivheadd.map           initials//rh_min09.ini')
os.system('cp           results//rivheadd.map           initials//rh_min10.ini')
os.system('cp           results//rivheadd.map           initials//rh_min11.ini')
os.system('cp           results//rivheadd.map           initials//rh_min12.ini')
os.system('cp           results//rivheadd.map           initials//rh_min13.ini')
os.system('cp           results//rivheadd.map           initials//rh_min14.ini')
os.system('cp           results//rivheadd.map           initials//rh_min15.ini')
os.system('cp           results//rivheadd.map           initials//rh_min16.ini')
os.system('cp           results//rivheadd.map           initials//rh_min17.ini')
os.system('cp           results//rivheadd.map           initials//rh_min18.ini')
os.system('cp           results//rivheadd.map           initials//rh_min19.ini')
os.system('cp           results//rivheadd.map           initials//rh_min20.ini')
os.system('cp           results//rivheadd.map           initials//rh_min21.ini')
os.system('cp           results//rivheadd.map           initials//rh_min22.ini')
os.system('cp           results//rivheadd.map           initials//rh_min23.ini')
os.system('cp           results//rivheadd.map           initials//rh_min24.ini')
os.system('cp           results//rivheadd.map           initials//rh_min25.ini')
os.system('cp           results//rivheadd.map           initials//rh_min26.ini')
os.system('cp           results//rivheadd.map           initials//rh_min27.ini')
os.system('cp           results//rivheadd.map           initials//rh_min28.ini')
os.system('cp           results//rivheadd.map           initials//rh_min29.ini')
os.system('cp           results//rivheadd.map           initials//rh_min30.ini')
os.system('cp           results//rivheadd.map           initials//rh_min30.ini')
os.system('cp            ..//01_INITIAL/*.ini           initials              ')
os.system('cp           results//bsfl0000.030           initials//bsflinit.ini')
os.system('rm -r      results/*')
#
print "Writing the arguments in a text file."
text_file = open("results//parameter.txt", "w")
text_file.write("Ksat_factor_sed = "+str(Ksat_factor_sed)+"\n")
text_file.write("Ksat_factor_mon = "+str(Ksat_factor_mon)+"\n")
text_file.write("KD___factor_sed = "+str(KD___factor_sed)+"\n")
text_file.write("KD___factor_mon = "+str(KD___factor_mon)+"\n")
text_file.write("Wmin_factor_sed = "+str(Wmin_factor_sed)+"\n")
text_file.write("Wmin_factor_mon = "+str(Wmin_factor_mon)+"\n")
text_file.write("Z2___factor_sed = "+str(Z2___factor_sed)+"\n")
text_file.write("Z2___factor_mon = "+str(Z2___factor_mon)+"\n")
text_file.write("TCL__factor_sed = "+str(TCL__factor_sed)+"\n")
text_file.write("TCL__factor_mon = "+str(TCL__factor_mon)+"\n")
text_file.close()
#
YearOrd = StartYear
for YearOrd in range(StartYear,End__Year+1):
  #identify the starting, end dates, and the number of dates
  StartDate = datetime.date(YearOrd,1,1)
  EndDate   = datetime.date(YearOrd,12,31)
  YearDays  = datetime.date.toordinal(EndDate)-datetime.date.toordinal(StartDate)+1
  # YR2D
  if YearOrd<2000:
    YR2D   =  YearOrd - 1900
  else: #   >=2000
    YR2Din =  YearOrd - 2000
    YR2D   = '0'+str(YR2Din)
  print(YearOrd,' ',YR2D)
  #
  if YearDays==365:
    #command  = 'pcrcalc -f pcrglobwb_rm_transient*.mod "..\\00_FORCING\\EP0_8501\\'+str(YearOrd)+'\\cetpRM'+str(YR2D)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\tmpcru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\TMP_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ta'+str(YearOrd)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\precru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\PRE_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ra'+str(YearOrd)+'" 365 1,3,31,59,90,120,151,181,212,243,273,304,334,365 1,3,8,16,24,31,38,45,52,59,67,75,83,90,98,106,113,120,128,136,144,151,159,167,174,181,189,197,205,212,220,228,236,243,251,259,266,273,281,289,297,304,312,320,327,334,342,350,358,365'+' "'+str(Ksat_factor_sed)+'" "'+str(Ksat_factor_mon)+'"'+' "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'" "'+str(Wmin_factor_sed)+'" "'+str(Wmin_factor_mon)+'" 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365 "'    +str(Z2___factor_sed)+'" "'+str(Z2___factor_mon)+'" "'+str(TCL__factor_sed)+'" "'+str(TCL__factor_mon)+'" '+str(YearOrd)
    command   = 'pcrcalc -f pcrglobwb_rm_transient*.mod "..\\00_FORCING\\EP0_8501\\'+str(YearOrd)+'\\cetpRM'+str(YR2D)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\tmpcru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\TMP_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ta'+str(YearOrd)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\precru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\PRE_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ra'+str(YearOrd)+'" 365 1,3,31,59,90,120,151,181,212,243,273,304,334,365 1,3,8,16,24,31,38,45,52,59,67,75,83,90,98,106,113,120,128,136,144,151,159,167,174,181,189,197,205,212,220,228,236,243,251,259,266,273,281,289,297,304,312,320,327,334,342,350,358,365'+' "'+str(Ksat_factor_sed)+'" "'+str(Ksat_factor_mon)+'"'+' "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'" "'+str(Wmin_factor_sed)+'" "'+str(Wmin_factor_mon)+'" 365 "'+str(Z2___factor_sed)+'" "'+str(Z2___factor_mon)+'" "'+str(TCL__factor_sed)+'" "'+str(TCL__factor_mon)+'" '+str(YearOrd)
  else:     #==366:
    #command  = 'pcrcalc -f pcrglobwb_rm_transient*.mod "..\\00_FORCING\\EP0_8501\\'+str(YearOrd)+'\\cetpRM'+str(YR2D)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\tmpcru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\TMP_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ta'+str(YearOrd)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\precru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\PRE_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ra'+str(YearOrd)+'" 366 1,3,31,60,91,121,152,182,213,244,274,305,335,366 1,3,8,16,24,31,39,46,53,60,68,76,84,91,99,107,114,121,129,137,145,152,160,168,175,182,190,198,206,213,221,229,237,244,252,260,267,274,282,290,298,305,313,321,328,335,343,351,359,366'+' "'+str(Ksat_factor_sed)+'" "'+str(Ksat_factor_mon)+'"'+' "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'" "'+str(Wmin_factor_sed)+'" "'+str(Wmin_factor_mon)+'" 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366 "'+str(Z2___factor_sed)+'" "'+str(Z2___factor_mon)+'" "'+str(TCL__factor_sed)+'" "'+str(TCL__factor_mon)+'" '+str(YearOrd)
    command   = 'pcrcalc -f pcrglobwb_rm_transient*.mod "..\\00_FORCING\\EP0_8501\\'+str(YearOrd)+'\\cetpRM'+str(YR2D)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\tmpcru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\TMP_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ta'+str(YearOrd)+'" "..\\00_FORCING\\CRU_8501\\'+str(YearOrd)+'\\precru_m" "..\\00_FORCING\\E40_8501_m\\'+str(YearOrd)+'\\PRE_AVG0" "..\\00_FORCING\\E40_8501_d_TSS\\'+str(YearOrd)+'\\ra'+str(YearOrd)+'" 366 1,3,31,60,91,121,152,182,213,244,274,305,335,366 1,3,8,16,24,31,39,46,53,60,68,76,84,91,99,107,114,121,129,137,145,152,160,168,175,182,190,198,206,213,221,229,237,244,252,260,267,274,282,290,298,305,313,321,328,335,343,351,359,366'+' "'+str(Ksat_factor_sed)+'" "'+str(Ksat_factor_mon)+'"'+' "'+str(KD___factor_sed)+'" "'+str(KD___factor_mon)+'" "'+str(Wmin_factor_sed)+'" "'+str(Wmin_factor_mon)+'" 366 "'+str(Z2___factor_sed)+'" "'+str(Z2___factor_mon)+'" "'+str(TCL__factor_sed)+'" "'+str(TCL__factor_mon)+'" '+str(YearOrd)
  #
  status = False				# calculation status
  while status == False:
    #os.system('rm -r results/*'); 
    os.system('rm -r results/*[!.txt]');	# delete except parameter.txt
    print command; os.system(command)
    status = os.path.isfile(                  "results//gw_headd.365")
    if YearDays==366: status = os.path.isfile("results//gw_headd.366")
  #
  # converting the DAILY TSS groundwater head file to the MONTHLY one (using R)
  command = 'R -f convert_daily_to_monthly.R '+str(YearOrd); print(command); os.system(command)
  # os.system('rm -r results//gw_headd.tss')							# deleting daily groundwater head files	
  # 
  # copying the initial values:
  os.system('cp results//ints_000.'+str(YearDays)+' initials//ints_000.ini')
  os.system('cp results//sc_00000.'+str(YearDays)+' initials//sc_00000.ini')
  os.system('cp results//scf_0000.'+str(YearDays)+' initials//scf_0000.ini')
  os.system('cp results//s1_00000.'+str(YearDays)+' initials//s1_00000.ini')
  os.system('cp results//s2_00000.'+str(YearDays)+' initials//s2_00000.ini')
  os.system('cp results//stor3xmd.'+str(YearDays)+' initials//stor3_md.ini')
  os.system('cp results//sw_00000.'+str(YearDays)+' initials//sw_00000.ini')
  os.system('cp results//rivheadd.'+str(YearDays)+' initials//rivhinit.ini')
  os.system('cp results//lk_headd.'+str(YearDays)+' initials//lkhdinit.ini')
  os.system('cp results//gw_headd.'+str(YearDays)+' initials//headinit.ini')
  os.system('cp results//q2_00000.'+str(YearDays)+' initials//q2_00000.ini')
  os.system('cp results//bsfl0000.'+str(YearDays)+' initials//bsflinit.ini')
  os.system('cp results//QC_min01.'+str(YearDays)+' initials//QC_min01.ini'); os.system('cp results//QC_min06.'+str(YearDays)+' initials//QC_min06.ini'); os.system('cp results//QC_min11.'+str(YearDays)+' initials//QC_min11.ini');
  os.system('cp results//QC_min02.'+str(YearDays)+' initials//QC_min02.ini'); os.system('cp results//QC_min07.'+str(YearDays)+' initials//QC_min07.ini'); os.system('cp results//QC_min12.'+str(YearDays)+' initials//QC_min12.ini');
  os.system('cp results//QC_min03.'+str(YearDays)+' initials//QC_min03.ini'); os.system('cp results//QC_min08.'+str(YearDays)+' initials//QC_min08.ini'); os.system('cp results//QC_min13.'+str(YearDays)+' initials//QC_min13.ini');
  os.system('cp results//QC_min04.'+str(YearDays)+' initials//QC_min04.ini'); os.system('cp results//QC_min09.'+str(YearDays)+' initials//QC_min09.ini'); os.system('cp results//QC_min14.'+str(YearDays)+' initials//QC_min14.ini');
  os.system('cp results//QC_min05.'+str(YearDays)+' initials//QC_min05.ini'); os.system('cp results//QC_min10.'+str(YearDays)+' initials//QC_min10.ini'); os.system('cp results//QC_min15.'+str(YearDays)+' initials//QC_min15.ini');
  os.system('cp results//rh_min01.'+str(YearDays)+' initials//rh_min01.ini'); os.system('cp results//rh_min06.'+str(YearDays)+' initials//rh_min06.ini'); os.system('cp results//rh_min11.'+str(YearDays)+' initials//rh_min11.ini'); os.system('cp results//rh_min16.'+str(YearDays)+' initials//rh_min16.ini'); os.system('cp results//rh_min21.'+str(YearDays)+' initials//rh_min21.ini'); os.system('cp results//rh_min26.'+str(YearDays)+' initials//rh_min26.ini');
  os.system('cp results//rh_min02.'+str(YearDays)+' initials//rh_min02.ini'); os.system('cp results//rh_min07.'+str(YearDays)+' initials//rh_min07.ini'); os.system('cp results//rh_min12.'+str(YearDays)+' initials//rh_min12.ini'); os.system('cp results//rh_min17.'+str(YearDays)+' initials//rh_min17.ini'); os.system('cp results//rh_min22.'+str(YearDays)+' initials//rh_min22.ini'); os.system('cp results//rh_min27.'+str(YearDays)+' initials//rh_min27.ini');
  os.system('cp results//rh_min03.'+str(YearDays)+' initials//rh_min03.ini'); os.system('cp results//rh_min08.'+str(YearDays)+' initials//rh_min08.ini'); os.system('cp results//rh_min13.'+str(YearDays)+' initials//rh_min13.ini'); os.system('cp results//rh_min18.'+str(YearDays)+' initials//rh_min18.ini'); os.system('cp results//rh_min23.'+str(YearDays)+' initials//rh_min23.ini'); os.system('cp results//rh_min28.'+str(YearDays)+' initials//rh_min28.ini');
  os.system('cp results//rh_min04.'+str(YearDays)+' initials//rh_min04.ini'); os.system('cp results//rh_min09.'+str(YearDays)+' initials//rh_min09.ini'); os.system('cp results//rh_min14.'+str(YearDays)+' initials//rh_min14.ini'); os.system('cp results//rh_min19.'+str(YearDays)+' initials//rh_min19.ini'); os.system('cp results//rh_min24.'+str(YearDays)+' initials//rh_min24.ini'); os.system('cp results//rh_min29.'+str(YearDays)+' initials//rh_min29.ini');
  os.system('cp results//rh_min05.'+str(YearDays)+' initials//rh_min05.ini'); os.system('cp results//rh_min10.'+str(YearDays)+' initials//rh_min10.ini'); os.system('cp results//rh_min15.'+str(YearDays)+' initials//rh_min15.ini'); os.system('cp results//rh_min20.'+str(YearDays)+' initials//rh_min20.ini'); os.system('cp results//rh_min25.'+str(YearDays)+' initials//rh_min25.ini'); os.system('cp results//rh_min30.'+str(YearDays)+' initials//rh_min30.ini');
  os.system('cp results//Qmin01BS.'+str(YearDays)+' initials//Qmin01BS.ini'); os.system('cp results//Qmin06BS.'+str(YearDays)+' initials//Qmin06BS.ini'); os.system('cp results//Qmin11BS.'+str(YearDays)+' initials//Qmin11BS.ini');
  os.system('cp results//Qmin02BS.'+str(YearDays)+' initials//Qmin02BS.ini'); os.system('cp results//Qmin07BS.'+str(YearDays)+' initials//Qmin07BS.ini'); os.system('cp results//Qmin12BS.'+str(YearDays)+' initials//Qmin12BS.ini');
  os.system('cp results//Qmin03BS.'+str(YearDays)+' initials//Qmin03BS.ini'); os.system('cp results//Qmin08BS.'+str(YearDays)+' initials//Qmin08BS.ini'); os.system('cp results//Qmin13BS.'+str(YearDays)+' initials//Qmin13BS.ini');
  os.system('cp results//Qmin04BS.'+str(YearDays)+' initials//Qmin04BS.ini'); os.system('cp results//Qmin09BS.'+str(YearDays)+' initials//Qmin09BS.ini'); os.system('cp results//Qmin14BS.'+str(YearDays)+' initials//Qmin14BS.ini');
  os.system('cp results//Qmin05BS.'+str(YearDays)+' initials//Qmin05BS.ini'); os.system('cp results//Qmin10BS.'+str(YearDays)+' initials//Qmin10BS.ini'); os.system('cp results//Qmin15BS.'+str(YearDays)+' initials//Qmin15BS.ini');
  #
  # mv results to output_fold per year
  os.system('mkdir '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.0* '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.1* '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.2* '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.3* '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.m* '+str(output_fold)+'//'+str(YearOrd))
  os.system('mv    results//*.t* '+str(output_fold)+'//'+str(YearOrd))				# We must copy tss files. 
  if YearOrd == StartYear: os.system('mv results//K*.map '+str(output_fold)+'//'+str(YearOrd)) 
  if YearOrd == StartYear: os.system('mv results//S*.map '+str(output_fold)+'//'+str(YearOrd)) 
  if YearOrd == StartYear: os.system('mv results//T*.map '+str(output_fold)+'//'+str(YearOrd)) 
  if YearOrd == StartYear: os.system('mv results//W*.map '+str(output_fold)+'//'+str(YearOrd)) 
  if YearOrd == StartYear: os.system('mv results//Z*.map '+str(output_fold)+'//'+str(YearOrd)) 
  os.system('rm -r results')
  os.system('mkdir results')
os.system('rm -r '+str(output_fold)+'//rsteady*')
os.system('rm -r initials')
os.system('rm fort*')
os.system('rm mf2k*')
os.system('rm pcrm*')
os.system('rm fort*')
