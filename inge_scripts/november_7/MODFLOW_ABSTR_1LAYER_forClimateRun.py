#### before running this script coupled check if indeed new crated discharge and recharge files are read!!

# MODFLOW_2L_TRANS_5min.py
# using data resampled from 5 min
# run_II ; confined_B
# 
# NOTE layers in PCR-MODFLOW : 1= bottom 2 = top 

import os
import sys
import datetime

from pcraster import *
from pcraster.framework import *
import pcraster as pcr

import ncConverter2 as ncReport
import currTimeStep as modelTime
import virtualOS as vos


class mymodflow(DynamicModel):
	
	def __init__(self, cloneMap, modelTime):
		DynamicModel.__init__(self)
		self.cloneMap = cloneMap
		setclone(self.cloneMap)
				
		self.modelTime = modelTime
		
		# list the variable that you want to report:      
		self.variable_output 	= 	["head_bottomMF","head_topMF", "depth_bottomMF", "depth_topMF", \
									"head_diffMF", "riv_baseflowMF","drn_baseflowMF", "tot_baseflowMF", \
									"rechargeMF", "storage_GWMF", "relativeHead_topMF"]   #, 
									 #"totGW_BOTTOMMF", "totGW_TOPMF",\ "RATIOMF"  ,"abstractionMF"
		# initiate netcdf report class
		self.netcdfReport 		= 	ncReport.PCR2netCDF(self.cloneMap)
		
		# output netcdf files; variable names and units:
		self.netcdf_output 	= 	{}
		self.netcdf_output["file_name"] = 	{}
		self.netcdf_output["unit"] = 	{}
		
		self.netcdf_output["file_name"]["head_bottomMF"] = "head_bottomMF.nc" 
		self.netcdf_output["unit"]["head_bottomMF"] = "m" 
		self.netcdf_output["file_name"]["head_topMF"] = "head_topMF.nc" 
		self.netcdf_output["unit"]["head_topMF"] = "m" 
		self.netcdf_output["file_name"]["depth_bottomMF"] = "depth_bottomMF.nc" 
		self.netcdf_output["unit"]["depth_bottomMF"] = "m"
		self.netcdf_output["file_name"]["depth_topMF"] = "depth_topMF.nc" 
		self.netcdf_output["unit"]["depth_topMF"] = "m"
		self.netcdf_output["file_name"]["head_diffMF"] = "head_diffMF.nc" 
		self.netcdf_output["unit"]["head_diffMF"] = "m"
		self.netcdf_output["file_name"]["riv_baseflowMF"] = "riv_baseflowMF.nc" 
		self.netcdf_output["unit"]["riv_baseflowMF"] = "m3d-1"
		self.netcdf_output["file_name"]["drn_baseflowMF"] = "drn_baseflowMF.nc" 
		self.netcdf_output["unit"]["drn_baseflowMF"] = "m3d-1"				
		self.netcdf_output["file_name"]["tot_baseflowMF"] = "tot_baseflowMF.nc" 
		self.netcdf_output["unit"]["tot_baseflowMF"] = "m3d-1"
		self.netcdf_output["file_name"]["rechargeMF"] = "rechargeMF.nc" 
		self.netcdf_output["unit"]["rechargeMF"] = "m3d-1"
		self.netcdf_output["file_name"]["storage_GWMF"] = "storage_GWMF.nc" 
		self.netcdf_output["unit"]["storage_GWMF"] = "m3d-1"
		self.netcdf_output["file_name"]["relativeHead_topMF"] = "relativeHead_topMF.nc" 
		self.netcdf_output["unit"]["relativeHead_topMF"] = "m"		
		self.netcdf_output["file_name"]["totGW_BOTTOMMF"] = "totGW_BOTTOMMF.nc" 
		self.netcdf_output["unit"]["totGW_BOTTOMMF"] = "m"	
		self.netcdf_output["file_name"]["totGW_TOPMF"] = "totGW_TOPMF.nc" 
		self.netcdf_output["unit"]["totGW_TOPMF"] = "m"			
		self.netcdf_output["file_name"]["RATIOMF"] = "RATIOMF.nc" 
		self.netcdf_output["unit"]["RATIOMF"] = "nounit"	
				
		self.netcdf_output["file_name"]["abstractionMF"] = "abstractionMF.nc" 
		self.netcdf_output["unit"]["abstractionMF"] = "m"	
		
	
		# make netcdf file    
		outDir	=	"/projects/0/dfguu/users/inge/Natural_Climate/tmp/"
					 
		for variable in self.variable_output:
			self.netcdfReport.createNetCDF(ncFileName = str(outDir) + self.netcdf_output["file_name"][variable], \
										   varName = variable, 
		                                   varUnits = self.netcdf_output["unit"][variable])

	def initial (self):
		#landmask			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/landmask_tmp_australia")       ##** landmask made for this test case
		
		iHeadini			=	self.readmap("/projects/0/dfguu/users/inge/modflow_coupling_global_human/head_topMF")		
		# maps
		landmask			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/landmask")
		dem_ini				= 	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_avg_05min")
		min_dem				=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_min_05min")
		cellarea			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/cellArea_05min")
		riv_slope			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/gradient_05min")
		Z0_floodplain		=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_floodplain_05min")
		aqdepth				= 	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/damc_ave")
		spe_yi_inp			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/StorCoeff_NEW")
		KQ3					=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/Recess_NEW")
		conflayers			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/conflayers4")				
		ksat_log			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/lkmc_ave")
		ksat_l1_conf_log	=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl1B_ave")
		ksat_l2_conf_log	=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl2B_ave")		
		ldd					=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/ldd")
		qbank				=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/Qbankfull_edwinInputs")
		self.landmask		=	landmask
		self.dem			=	dem_ini
		self.cellarea		=	cellarea
		self.min_dem		=	min_dem
		aqdepth_ini			=	aqdepth
		self.aqdepth_ini	=	aqdepth_ini
		aqdepth				=	cover(ifthenelse(aqdepth > 0.0, aqdepth, 200.0),200.0)			## over land max 200 m, over sea 200m			
		dem					=	cover(ifthen(landmask, dem_ini),0.0)
		top_l2				=	dem
		bottom_l1			=	dem-aqdepth
		top_l1				=	top_l2- (aqdepth*0.1)				     						## layer 2 is 10% total thickness	
		
		mf.createBottomLayer(bottom_l1,top_l1)
		mf.addLayer(top_l2)
	
		self.bottom_elevation_aquifer	=	dem_ini- aqdepth												##** nodig voor groundwater storage
				
		# simulaton parameter
		mf.setDISParameter(4,2,1,1,1,0)	
		
		# set boundary conditions
		ibound_l1			= 	cover(ifthen(landmask, nominal(1)),nominal(-1))
		#pcr.report(ibound_l1, "test.map") ; os.system("aguila test.map")  
		
		mf.setBoundary(ibound_l1,2)
		mf.setBoundary(ibound_l1,1)
		
		## set initial values
		#iHead				=	dem 									## Dit gaat denk ik niet goed, want nu zet ie um toch voor iedere tijdstap voor op dem?? 
		
		iHead				=	cover(iHeadini,0.0)							## Hoe krijg ik dit in dynamic dan?? 			
		mf.setInitialHead(iHead,2)
		mf.setInitialHead(iHead,1)	
		
		# set conductivities
		rho_water			=	scalar(1000)
		miu_water			=	scalar(0.001)
		g_gravity			=	scalar(9.81)
		
		dikte_l2_ini		=	aqdepth*0.1								# top layer			
		dikte_l1_ini		=	aqdepth - dikte_l2_ini					# bottom layer		
		dikte_l2			=	ifthen(landmask, cover(dikte_l2_ini, 20.0))
		dikte_l1			=   ifthen(landmask, cover(dikte_l1_ini, 180.0))
		self.dikte_l1		= 	dikte_l1
		self.dikte_l2		= 	dikte_l2
		#-no confined layers
		ksat_inp_ini		=	rho_water* (10**ksat_log)* (g_gravity/ miu_water) *24.0 *3600.0		
		#-confining layers 	
		## conf maps are read in read maps 				
		conflayers			=	cover(conflayers, boolean(0))
		
		ksat_l1_conf		=	rho_water* (10**ksat_l1_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0
		ksat_l2_conf		= 	rho_water* (10**ksat_l2_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0
		#ksat_l2_conf		=	ksat_l2_conf_log    																# ksat_2  is al omgerekend  FF checken nog !!
		khoriz_l1_ini		=	cover(ksat_l1_conf, ksat_inp_ini)
		khoriz_l2_ini		=	cover(ksat_l2_conf, ksat_inp_ini)
		kvert_l2_ini		=	ifthenelse(khoriz_l2_ini > -999.9, (khoriz_l2_ini*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		kvert_l1			=	ifthenelse(khoriz_l1_ini > -999.9, (10*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		kvert_l2			=	cover(ifthenelse(conflayers == boolean(1), (0.008*cellarea)/((5.0/60.0)**2.0), kvert_l2_ini),kvert_l2_ini)
		kD_l2_ini			=	khoriz_l2_ini*(dikte_l2)
		kD_l1_ini			=	khoriz_l1_ini*(dikte_l1)	
		kD_l2				=	max(30,kD_l2_ini)
		kD_l1				=	max(30,kD_l1_ini)
		# KD hoger maken voor confining layer....

		#kD_l2				=	max(30,kD_l2_ini)
		#kD_l1				=	max(30,kD_l2_ini)
		khoriz_l2			=	cover(kD_l2/(dikte_l2),20.) 			#10.
		khoriz_l1			=	cover(kD_l1/(dikte_l1),190.)	 		#90.	
		## test
		kvert_l2			= 	cover(kvert_l2,1E10)
		kvert_l1			= 	cover(kvert_l1,1E10)
		pcr.report(kD_l2, "kD_l2.map")
		pcr.report(kD_l1, "kD_l1.map")
		mf.setConductivity(00,khoriz_l2, kvert_l2,2)
		mf.setConductivity(00,khoriz_l1, kvert_l1,1)
		# lakes moeten er nog in als ik abstracties ga gebruiken
		
		# set storage
		spe_yi_inp			=	ifthen(landmask, spe_yi_inp)
		spe_yi_inp			=	min(1.0, max(0.01,spe_yi_inp))			## check this minimal value: think this is too low 	
		stor_coef			=	scalar(0.01)
		stor_conf			=	cover(cover(ifthenelse(conflayers == boolean(1), stor_coef, spe_yi_inp),spe_yi_inp),1000.0)	 
		##pcr.report("stor_conf.map")
		stor_prim			=	cover(spe_yi_inp,1000.0)
		stor_sec			=	cover(spe_yi_inp,1000.0)
		stor_confinedaquifer		=       cover(1000.0, cover(ifthenelse(conflayers == boolean(1), 0.360, spe_yi_inp), spe_yi_inp))	
		
		
		mf.setStorage(stor_prim, stor_sec,1)
#		mf.setStorage(stor_conf, stor_sec,1)							# confined aquifer has storage coefficient unconfined is specific yield
		mf.setStorage(stor_prim, stor_sec,2)
		
		# solver
		mf.setPCG(1500,1250,1,1,160000,0.98,2,1)	
		
		# adding river
		riv_manning			=	scalar(0.0450)
		self.riv_manning	=	riv_manning
		resistance			=	scalar(1.0)
		self.resistance		=	resistance
		riv_bedres_inp		=	scalar(1.0000)
		min_dem2			=	ifthenelse(min_dem < 0.0, 0.0, min_dem)
		Z0_floodplain2		= 	ifthenelse(Z0_floodplain < 0.0, max(min_dem2,Z0_floodplain),Z0_floodplain)
		
		riv_width			= 	4.8* ((qbank)**0.5)
		self.riv_width		=	riv_width
	    # RIVERS ONLY
		riv_slope			=	ifthen(riv_width > 0.0, riv_slope)
		self.riv_slope_used	= 	ifthen(riv_slope > 1e-8, riv_slope)										
		self.riv_head_ini	= 	cover(ifthenelse(riv_width > 30.0, Z0_floodplain2,top_l2),0.0)
		self.riv_depth_bkfl	= 	((riv_manning*(qbank)**0.5)/(self.riv_width*self.riv_slope_used**0.5))**(3.0/5.0)
		self.riv_bot_bkfl	=	min_dem2- self.riv_depth_bkfl
	
		# adding drain
		# base of groundwater that contribute to baseflow
		DZS3INFLUENCED		=	scalar(5.0)
		BASE_S3				=	areaminimum(Z0_floodplain2, subcatchment(ldd, nominal(uniqueid(ifthen(Z0_floodplain2 > -999.9, boolean(1))))))
		BASE_S3				=	max(Z0_floodplain2- DZS3INFLUENCED, downstream(ldd,Z0_floodplain2),BASE_S3)			# for mountainous areas
		BASE_S3				=	ifthenelse(aqdepth > -9999.9, max(Z0_floodplain, BASE_S3), BASE_S3)					# for aquifers
		self.BASE_S3_used	=	cover(BASE_S3,-900000.0)
		storcoef_act		=	ifthenelse(landmask, spe_yi_inp,0.0)
		KQ3_x_Sy			=	min(1.0,cover(KQ3* storcoef_act, 0.0))
		self.KQ3_x_Sy_AR	=	cover(ifthenelse(self.BASE_S3_used == -900000.0, 0.0, KQ3_x_Sy*cellarea),0.0)
		self.storcoef_act	=	stor_conf
		
	def dynamic(self):		
		
		self.modelTime.update(self.currentTimeStep())
		
		if self.modelTime.isLastDayOfMonth():
		
			# read netcdf file  : monthly averaged outputs from PCR-GLOBWB
			dateInput = self.modelTime.fulldate
			print(dateInput)
			lastDateofFirstMonth = "2005-01-31"  			## FIX ME
			
			if dateInput == lastDateofFirstMonth:
				print("fistMonth")
				
				
				ncFile	=	"/projects/0/dfguu/users/inge/inputMAPS/maps__/discharge_hum_monthAvg_output.nc"
				##ncFile	=	"/projects/0/dfguu/users/inge/Natural_Climate/merged/netcdf/discharge_monthAvg_output.nc"     
				varName = 	"discharge"
				Qinp 	= 	vos.netcdf2PCRobjCloneOnlyOneTimeStep(ncFile,varName)
				
				ncFile	=	"/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchnat_05min.nc"
				##ncFile	=	"/projects/0/dfguu/users/inge/Natural_Climate/merged/netcdf/gwRecharge_monthAvg_output.nc"     
				varName = 	"groundwater_recharge" #"groundwater_recharge"
				rch 	= 	vos.netcdf2PCRobjCloneOnlyOneTimeStep(ncFile,varName)
				
				##ncFile	=	"/projects/0/dfguu/users/inge/inputMAPS/maps__/d.nc"
				##ncFile	=	"/projects/0/dfguu/users/inge/Natural_Climate/merged/netcdf/totalGroundwaterAbstraction_monthAvg_output.nc"   # unit = [md-1]    
				#varName = 	"total_groundwater_abstraction"
				#totGW 	= 	vos.netcdf2PCRobjCloneOnlyOneTimeStep(ncFile,varName)
				
				#- FOR ABSTRACTION RATIO
				#- Irrigation gross demand
				#ncFile		=	"/projects/0/dfguu/users/inge/modflow_coupling_global_human_Climate/merged/netcdf/irrGrossDemand_monthTot_output.nc" 
				#varName		=	"irrigation_gross_demand"																							
				#irrDemand	=	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
				#						useDoy = None,
				#						cloneMapFileName = self.cloneMap) 
										
				#- nonIrrigation gross demand
				#ncFile		=	"/projects/0/dfguu/users/inge/modflow_coupling_global_human_Climate/merged/netcdf/totalPotentialMaximumGrossDemand_monthTot_output.nc" 
				#varName		=	"totalPotentialMaximumGrossDemand"																							
				#totDemand	=	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
				#						useDoy = None,
				#						cloneMapFileName = self.cloneMap) 						
				
			else:
				print("not firstMonth")
				
				#-DISCHARGE : natural/ water consumption
				##ncFile	=	"/projects/0/dfguu/users/inge/Natural_Climate/merged/netcdf/discharge_monthAvg_output.nc"     
				ncFile	=	"/projects/0/dfguu/users/inge/inputMAPS/maps__/discharge_hum_monthAvg_output.nc"
				varName = 	"discharge"
				Qinp 	= 	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
											useDoy = None,
											cloneMapFileName = self.cloneMap)
				
				#-RECHARCE : natural / water consumption		
				#ncFile_nat 		=	"/projects/0/dfguu/users/inge/Natural_Climate/merged/netcdf/gwRecharge_monthAvg_output.nc"	 	 
				NcFile_nat	=	"/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchnat_05min.nc"
				varName_nat		= 	"groundwater_recharge" 	#"groundwater_recharge"
				rch 	 		= vos.netcdf2PCRobjClone(ncFile_nat,varName_nat,dateInput,\
											useDoy = None,
											cloneMapFileName = self.cloneMap) 

				#-ABSTRACTIONS :  gross groundwater abstractions 
				#ncFile		=	"/projects/0/dfguu/users/inge/Natural_human_Climate/merged/netcdf/totalGroundwaterAbstraction_monthAvg_output.nc" 
				#varName		=	"total_groundwater_abstraction"																							
				#totGW		=	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
				#						useDoy = None,
				#						cloneMapFileName = self.cloneMap) 
										
				#- FOR ABSTRACTION RATIO
				#- Irrigation gross demand
				#ncFile		=	"/projects/0/dfguu/users/inge/modflow_coupling_global_human_Climate/merged/netcdf/irrGrossDemand_monthTot_output.nc" 
				#varName		=	"irrigation_gross_demand"																							
				#irrDemand	=	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
				#						useDoy = None,
				#						cloneMapFileName = self.cloneMap) 
										
				#- nonIrrigation gross demand
				#ncFile		=	"/projects/0/dfguu/users/inge/modflow_coupling_global_human_Climate/merged/netcdf/totalPotentialMaximumGrossDemand_monthTot_output.nc" 
				#varName		=	"totalPotentialMaximumGrossDemand"																							
				#totDemand	=	vos.netcdf2PCRobjClone(ncFile,varName,dateInput,\
				#						useDoy = None,
				#						cloneMapFileName = self.cloneMap) 						
							
			
			# river package
			#-aqverage
			qaverage			=	Qinp
			riv_depth_avg1		= 	((self.riv_manning*((qaverage)**0.5))/(self.riv_width*self.riv_slope_used**0.5))**(3.0/5.0)
			riv_depth_avg		=	ifthenelse(riv_depth_avg1 < 0.01, 0.0, riv_depth_avg1)
			riv_head			=	self.riv_bot_bkfl + riv_depth_avg
			riv_head2			= 	cover(riv_head,self.riv_head_ini)
			riv_cond			= 	cover((1/self.resistance)*ifthenelse(self.riv_width >= 30.0, self.riv_width*(self.cellarea*2.0)**0.5,0.0),0.0)
			drn_width			= 	ifthenelse(riv_cond == 0.0, max(10.0,self.riv_width),0.0)								
			drn_cond			=	cover(ifthenelse(riv_cond == 0.0,(1.0/self.resistance)*drn_width*(self.cellarea*2)**0.5,0.0),0.0) 
			drn_cond			=	ifthenelse(abs(drn_cond) < 1e-20, 0.0, drn_cond)						
			
			riv_head_comb		=	cover(ifthenelse(riv_cond > 0.0, riv_head2, self.riv_head_ini),0.0)
			riv_bot_comb		=	cover(ifthenelse(riv_cond > 0.0, self.riv_bot_bkfl, self.riv_head_ini),0.0)
			riv_cond_comb		=	cover(ifthenelse(riv_cond > 0.0, riv_cond, drn_cond),0.0)
			
			mf.setRiver(riv_head_comb, riv_bot_comb, riv_cond_comb,2)
			
			mf.setDrain(self.BASE_S3_used, self.KQ3_x_Sy_AR,2)
			
			#-specify recharge
			rch		=	max(rch,0.0)
			rch_m3d		=	rch*self.cellarea
			#totGWused_m3d	=	cover((totGW*self.cellarea),0.0)
			
			rch_cor_m3d=		max(0.0,rch_m3d)#==	max(0.0, rch_m3d- totGWused_m3d)
			rch_cor_md		=	cover(((rch_cor_m3d)/(5.0/60.0)**2.0),0.0)
			
			#GWused_cor	=	ifthenelse(totGWused_m3d > 0.0, ifthenelse(rch_m3d > 0.0, totGWused_m3d -(rch_m3d- rch_cor_m3d),0.0) ,0.0) 
			#totGWused	=	cover(GWused_cor* -1.0,0.0)
			mf.setWell(totGWused,1)
			mf.setRecharge(rch_cor_md,1)			
			
			#GWused_cor	=	totGWused_m3d- (rch_m3d- rch_cor_m3d)
			#totGWused	=	cover(GWused_cor* -1.0,0.0)
			#mf.setWell(totGWused,1)

				
			# well package
			#- abstracties
			#-totGW 
			# limited for aquifer area  ----> this should be done in landCover.py ; FIX ME
			##totGW_used			=	cover(ifthen(self.aqdepth_ini > -999.9, totGW),0.0)  	 # unit: m per month    #unit: million cubic meter per month   ##(totGW_used*(10.0**6.0))	
			# limited for aquifer area  ----> this should be done in landCover.py ; FIX ME
			#totGW_used  		=	cover(totGW *self.cellarea,0.0) # unit m3d-1
			#self.totGW_used_report	=	totGW_used  
			#totGW_used			=	totGW_used* -1.0				# abstraction should be nagative	
			##totGW_used  		=	cover(0.0 *self.cellarea,0.0)
			#mf.setWell(totGW_used,1)											# abstractie in aquifer 
			
		#	totGWused	=	cover((totGW*self.cellarea),0.0)
	#		totGWused	=	cover(totGWused* -1.0,0.0)
			#ratio		=	cover(irrDemand/ totDemand,0.0)			
			#totGW_BOTTOM= totGWused * (1.0-ratio) *-1
			#totGW_TOP	= totGWused * ratio *-1
			#self.ratio = ratio
			#
			#mf.setWell(totGW_BOTTOM,1)
			#mf.setWell(totGW_TOP,2)	
			
						

			
			# execuate MODFLOW
			mf.run()
			
			# retrieve outputs
			gw_head1			=	mf.getHeads(1)
			gw_head2			=	mf.getHeads(2)
			riv_baseflow		=	mf.getRiverLeakage(2)
			drn_baseflow		=	mf.getDrain(2)
			recharge			=	mf.getRecharge(2)
							
			gw_depth2			=	self.dem- gw_head2
			gw_depth1			=	self.dem- gw_head1
			head_diff			=	gw_head1-gw_head2
			
			# calculate storage (forPCRGLOB_WB)
			water_thickness		=	gw_head2- self.bottom_elevation_aquifer
			pcr.report(water_thickness, "/projects/0/dfguu/users/inge/Natural_Climate/waterthick.map")
			storGW				=	pcr.max(0,water_thickness*self.storcoef_act*self.cellarea)  ##** 
			#storGW				=	pcr.max(0,water_thickness*self.cellarea)
			relativeHead_top	=	pcr.max(0,gw_head2- self.min_dem)
			#totGWmd = self.totGW_used_report
			#totGWmd				=	totGW_used/ self.cellarea
			rechargemd			=	recharge/ self.cellarea
			
			# reporting all outputs from MF to de netcdf-dir	
			# all outputs are masked		
			self.head_bottomMF	=	gw_head1 #pcr.max(-100, gw_head1)
			self.head_topMF 	= 	gw_head2 #pcr.max(-100, gw_head2)
			self.depth_bottomMF	= 	ifthen(self.landmask,gw_depth1)
			self.depth_topMF	= 	ifthen(self.landmask,gw_depth2)
			self.riv_baseflowMF	= 	ifthen(self.landmask,riv_baseflow)
			self.drn_baseflowMF	= 	ifthen(self.landmask,drn_baseflow)
			self.head_diffMF	= 	ifthen(self.landmask,head_diff)
			self.tot_baseflowMF	= 	ifthen(self.landmask,riv_baseflow + drn_baseflow)
			self.rechargeMF		= 	ifthen(self.landmask,recharge)
			self.storage_GWMF	=	ifthen(self.landmask,storGW)
			self.relativeHead_topMF	=	ifthen(self.landmask,relativeHead_top)
			
			#self.abstractionMF	=	ifthen(self.landmask,totGWmd)
			self.rechargeMF		= 	ifthen(self.landmask,rechargemd)
			
			# report ini conditions for PCR-GLOBWB as .map 
			# pcr.report(ibound_l1, "test.map") ; os.system("aguila test.map")
			head_topMF 		= 	gw_head2
			head_bottomMF 	= 	gw_head1
			tot_baseflowMF	=	riv_baseflow + drn_baseflow
			# - report new initial conditions 
			pcr.report(head_topMF, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/head_topMF.map")
			pcr.report(head_topMF, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/ini/head_topMF")
			pcr.report(head_bottomMF, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/head_bottomMF.map")							## --> can the dir-path be automatic  
			pcr.report(gw_depth2, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/depth_topMF.map")
			pcr.report(tot_baseflowMF, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/tot_baseflowMF.map")
			pcr.report(storGW, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/storage_GWMF.map")
			pcr.report(relativeHead_top, "/projects/0/dfguu/users/inge/Natural_Climate/tmp/relativeHead_topMF.map")
						
			timeStamp 	= 	datetime.datetime(self.modelTime.year,\
										self.modelTime.month,\
										self.modelTime.day,\
										0)
	
			# reporting to netcdf files
			#self.outNCDir  = iniItems.outNCDir
			outDir	=	"/projects/0/dfguu/users/inge/Natural_Climate/tmp/"													## --> output dir
			for variable in self.variable_output:
				chosenVarField = pcr2numpy(self.__getattribute__(variable), vos.MV)
				self.netcdfReport.data2NetCDF(ncFile = str(outDir) + self.netcdf_output["file_name"][variable],\
											varName = variable,\
											varField = chosenVarField,
											timeStamp = timeStamp)

cloneMap 		= "/projects/0/dfguu/users/inge/inputMAPS/Clone_05min.map" # "../MFinp/australia/australia_clone.map" "../../PCR-GLOBWB/MFinp/australia/australia_clone.map" #
strStartTime = sys.argv[1]
strEndTime   = sys.argv[2]

# initiating modelTime object
modelTime 		= modelTime.ModelTime()
modelTime.getStartEndTimeSteps(strStartTime,strEndTime)

myModel			= mymodflow(cloneMap,modelTime)
mf				=	initialise(clone())	
DynamicModel	= DynamicFramework(myModel,modelTime.nrOfTimeSteps)     #***
DynamicModel.run()			 


