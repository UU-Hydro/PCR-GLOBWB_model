# Sy_1 
# NOTE layers in PCR-MODFLOW : 1= bottom 2 = top 

import os
import sys
import datetime

from pcraster import *
from pcraster.framework import *
import pcraster as pcr

import ncConverter as ncReport
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
									"rechargeMF"] 
									 
		# initiate netcdf report class
		specificAttributeDictionary = {}
		specificAttributeDictionary['institution'] = 'test'
		specificAttributeDictionary['title'      ] = 'test'
		specificAttributeDictionary['description'] = 'test'		
		self.netcdfReport = ncReport.PCR2netCDF(self.cloneMap, specificAttributeDictionary)
		
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
		outDir	=	"/projects/0/dfguu/users/edwin/modflow_Sy1/tmp_ori/"
		os.makedirs(outDir)
					 
		for variable in self.variable_output:
			self.netcdfReport.createNetCDF(ncFileName = str(outDir) + self.netcdf_output["file_name"][variable], \
										   varName = variable, 
		                                   varUnits = self.netcdf_output["unit"][variable])

	def initial (self):
		iHeadini			=	self.readmap("/projects/0/dfguu/users/inge/modflow_coupling_global_natural/head_topMF")		
		landmask			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/landmask")
		dem_ini				= 	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_avg_05min")
		min_dem				=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_min_05min")
		cellarea			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/cellArea_05min")
		riv_slope			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/gradient_05min")
		Z0_floodplain		=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_floodplain_05min")
		aqdepth				= 	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/damc_ave")
		spe_yi_inp_ori			=	self.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/StorCoeff_NEW")
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
				
		#* OLD
		# simulaton parameter
		# mf.setDISParameter(4,2,1,1,1,0)	
		
		# set boundary conditions
		ibound_l1			= 	cover(ifthen(landmask, nominal(1)),nominal(-1))
		#pcr.report(ibound_l1, "test.map") ; os.system("aguila test.map")  
		
		mf.setBoundary(ibound_l1,2)
		mf.setBoundary(ibound_l1,1)
		
		## set initial values
		iHead				=	cover(iHeadini,0.0)						 			
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
		#-khorizontal 
		ksat_l1_conf		=	rho_water* (10**ksat_l1_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0    # fine grained    
		ksat_l2_conf		= 	rho_water* (10**ksat_l2_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0	   # coarse grained		
		khoriz_l1_ini		=	cover(ksat_l1_conf, ksat_inp_ini)
		khoriz_l2_ini		=	cover(ksat_l2_conf, ksat_inp_ini)
		# minumim value for aquifer areas:
		khoriz_l1_ini		=	ifthenelse(aqdepth >-999.9, max(khoriz_l1_ini,0.01),khoriz_l1_ini)      #**
		khoriz_l2_ini		=	ifthenelse(aqdepth >-999.9, max(khoriz_l2_ini,0.01),khoriz_l2_ini)		#**			# minimum value = fine grained unc. sed.
		#k vertical
		#kvert_l2_ini		=	ifthenelse(khoriz_l2_ini > -999.9, (khoriz_l2_ini*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		#kvert_l1			=	ifthenelse(khoriz_l1_ini > -999.9, (10*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		#kvert_l2				=	max(dikte_l2/5000, kvert_l2_ini)  #**
		#kvert_l2			=	cover(ifthenelse(conflayers == boolean(1), (0.008*cellarea)/((5.0/60.0)**2.0), kvert_l2_ini),kvert_l2_ini)
		kD_l2_ini			=	khoriz_l2_ini*(dikte_l2)
		kD_l1_ini			=	khoriz_l1_ini*(dikte_l1)	
		kD_l2				=	max(30,kD_l2_ini)
		kD_l1				=	max(30,kD_l1_ini)
		khoriz_l2_ori			=	cover(kD_l2/(dikte_l2),20.) 			#10.
		khoriz_l1_ori			=	cover(kD_l1/(dikte_l1),190.)	 		#90.	
		#################################
		khoriz_l2 = khoriz_l2_ori * 10**(0)
		khoriz_l1 = khoriz_l1_ori * 10**(0)
		kvert_l2_ori = khoriz_l2	#cover(kvert_l2,1E10)
		kvert_l1_ori = khoriz_l1	#cover(kvert_l1,1E10)
		# kvert range, but do make sure kvert <= khoriz
		kvert_l2 = min(kvert_l2_ori * 10**(-2), khoriz_l2)
		kvert_l1 = min(kvert_l1_ori * 10**(-2), khoriz_l1)
		kvert_l2 = cover((kvert_l2*cellarea)/((5.0/60.0)**2.0),1E10)
		kvert_l1 = cover(max(1E10,(kvert_l1*cellarea)/((5.0/60.0)**2.0)),1E10)  # kvert onderste laag is nu super hoog
		################################
		pcr.report(kD_l2, "kD_l2.map")
		pcr.report(kD_l1, "kD_l1.map")
		mf.setConductivity(00,khoriz_l2, kvert_l2,2)
		mf.setConductivity(00,khoriz_l1, kvert_l1,1)
		
		# set storage
		spe_yi_inp			=	ifthen(landmask, spe_yi_inp_ori * 0.5)
		spe_yi_inp			=	min(1.0, max(0.01,spe_yi_inp))	
		#- Limit for aquifer area
		spe_yi_inp			=	ifthenelse(aqdepth >-999.9, max(spe_yi_inp, 0.11), spe_yi_inp)    # if in aquifer spec yield is miminal fine grained
		#stor_coef			=	scalar(0.01)
		#stor_conf			=	cover(cover(ifthenelse(conflayers == boolean(1), stor_coef, spe_yi_inp),spe_yi_inp),1000.0)	 
		stor_prim			=	cover(spe_yi_inp,1000.0)
		stor_sec			=	cover(spe_yi_inp,1000.0)
		mf.setStorage(stor_prim, stor_sec,1)
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
		self.riv_width		=	max(riv_width,0.5) #*** minimum gegeven 
	    # RIVERS ONLY
		riv_slope			=	ifthen(riv_width > 0.0, riv_slope)
		self.riv_slope_used	= 	ifthen(riv_slope > 0.00005, riv_slope)	    #** bigger									
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
		KQ3					=	cover(min(1.0,KQ3),0.0)		#**
		KQ3min				=	1.0e-4 						#**
		KQ3					=	max(KQ3min,KQ3)				#**
		KQ3_x_Sy			=	cover(KQ3* storcoef_act, 0.0)			#**
		self.KQ3_x_Sy_AR	=	cover(ifthenelse(self.BASE_S3_used == -900000.0, 0.0, KQ3_x_Sy*cellarea),0.0)
		#self.storcoef_act	=	stor_conf
		self.storcoef_act	= 	stor_prim
		
		mf.setDISParameter(4,2,1,1,1,0)
		
	def dynamic(self):
	
		self.modelTime.update(self.currentTimeStep())
		
		#~ # simulation parameter
		#~ ## this does not work:     
		#~ NSTP= self.currentTimeStep.day
		#~ PERLEN= currentTimeStep.day
		#~ mf.setDISParameter(4,2,PERLEN,NSTP,1,0)
		
		if self.modelTime.isLastDayOfMonth():
		
			dateInput = self.modelTime.fulldate		
			print(dateInput)		
			
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchhum2_05min.nc"
			varName = "recharge"	
			print(ncFile)
			rch_human = vos.netcdf2PCRobjClone(ncFile,varName, dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchnat_05min.nc"
			varName = "rechargeTotal"
			print(ncFile)
			rch_nat= vos.netcdf2PCRobjClone(ncFile,varName,dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/discharge_hum_monthAvg_output.nc"
			varName = "discharge"
			print(ncFile)
			Qinp= vos.netcdf2PCRobjClone(ncFile,varName,dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/gwab_m3_05min.nc"
			varName = "gwab_m3_05min"
			print(ncFile)
			totGW = vos.netcdf2PCRobjClone(ncFile,varName, dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
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
			
			
			totGW_used = cover(ifthen(self.aqdepth_ini > -999.9, totGW),0.0) # unit: 10**6 m3 per month
			totGW_used_2 = (totGW_used*(10.0**6.0))
			totGW_used_m3d = cover((totGW_used_2/30.0)*-1.0,0.0)   # this should be devided by days of the month (simplified to 30d)
			
			mf.setWell(totGW_used_m3d,1)
			
			rch_hum = rch_human
			rch = cover(ifthen(totGW_used_m3d > -999.9, rch_hum), rch_nat)  # if abstr dan rch abstr anders ruch nat 
			rch_inp = cover(max(0.0, (rch *self.cellarea)/(5.0/60.0)**2.0),0.0)		
			
			mf.setRecharge(rch_inp,1)			
					
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
			head_topMF 		= 	gw_head2
			head_bottomMF 	= 	gw_head1
			tot_baseflowMF	=	riv_baseflow + drn_baseflow
			# - report new initial conditions 
			pcr.report(head_topMF, "/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/head_topMF.map")
			pcr.report(head_topMF, "/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/ini/head_topMF")
			pcr.report(head_bottomMF, "/projects/0/dfguu/edwin/inge/modflow_Sy1/tmp/head_bottomMF.map")							## --> can the dir-path be automatic  
			pcr.report(gw_depth2, "/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/depth_topMF.map")
			pcr.report(tot_baseflowMF, "/projects/0/dfguu/edwin/inge/modflow_Sy1/tmp/tot_baseflowMF.map")
					
			timeStamp 	= 	datetime.datetime(self.modelTime.year,\
									self.modelTime.month,\
									self.modelTime.day,\
									0)
			
			# reporting to netcdf files
			#self.outNCDir  = iniItems.outNCDir
			outDir	=	"/projects/0/dfguu/users/edwin/modflow_Sy1/tmp_ori/"
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


