# Sy_1 
# NOTE layers in PCR-MODFLOW : 1= bottom 2 = top 

import os
import sys
import shutil
import datetime

from pcraster.framework import *
import pcraster as pcr

import ncConverter as ncReport
import currTimeStep as modelTime
import virtualOS as vos


class mymodflow(DynamicModel):
	
	def __init__(self, cloneMap, modelTime, output_directory):
		DynamicModel.__init__(self)
		
		self.cloneMap = cloneMap
		pcr.setclone(self.cloneMap)
				
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
		self.netcdf_output = {}
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
	
		# preparing output directory
		self.outDir	= output_directory
		clean_output_directory = True
		try:
			os.makedirs(self.outDir)
		except:
			if clean_output_directory:
				cmd = 'rm -r ' + self.outDir + "/*" 
				os.system(cmd)
				shutil.rmtree(self.outDir)
		
		# preparing temporary directory (needed for resampling purpose):
		self.tmpDir = self.outDir + "/" + "tmp/"
		os.makedirs(self.tmpDir)	
		
		# make netcdf files    
		for variable in self.variable_output:
			self.netcdfReport.createNetCDF(ncFileName = str(self.outDir) + self.netcdf_output["file_name"][variable], \
										   varName = variable, 
		                                   varUnits = self.netcdf_output["unit"][variable])

	def initial (self):
		
		# Here I suggested to use the function vos.readPCRmapClone so that it can automatically resample pcraster maps to the given self.cloneMap)  													

		iHeadini			=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/modflow_coupling_global_natural/head_topMF.map",\
													self.cloneMap, self.tmpDir)
		# Why did you use only one initial head? You must define two initial head values, one for the 1st layer and the other for the 2nd layer. 
															
		landmask			=	pcr.boolean(\
								vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/maps__/landmask.map", \
													self.cloneMap, self.tmpDir, False, None, False, True))
		
		dem_ini				= 	pcr.cover(\
								vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_avg_05min.map",\
													self.cloneMap, self.tmpDir), 0.0)		
		
		min_dem				=	pcr.cover(\
								vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_min_05min.map",\
													self.cloneMap, self.tmpDir), 0.0)		
		
		cellarea			=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/cellArea_05min.map",\
													self.cloneMap, self.tmpDir)		
		
		riv_slope			=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/gradient_05min.map",\
													self.cloneMap, self.tmpDir)		
		
		Z0_floodplain		=	pcr.cover(\
								vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_floodplain_05min.map",\
													self.cloneMap, self.tmpDir), 0.0)		
		
		aqdepth				= 	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/damc_ave.map",\
													self.cloneMap, self.tmpDir)		
		
		spe_yi_inp_ori		=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/StorCoeff_NEW.map",\
													self.cloneMap, self.tmpDir)
		# Why are these values can be above 1.0? I suggest that you fix this map. 
		# Moreover, specific yield values for sand should be already below <= 0.35 (or even lower). To solve this issue, I add the following line (temporary solution).
		spe_yi_inp_ori		=	pcr.min(spe_yi_inp_ori, 0.30) 
															
		KQ3					=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/Recess_NEW.map",\
													self.cloneMap, self.tmpDir)
															
		conflayers			=	pcr.boolean(\
								vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/conflayers4.map",\
													self.cloneMap, self.tmpDir, False, None, False, True))

		ksat_log			=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/lkmc_ave.map",\
													self.cloneMap, self.tmpDir)		
		ksat_l1_conf_log	=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl1B_ave.map",\
													self.cloneMap, self.tmpDir)		
		ksat_l2_conf_log	=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl2B_ave.map",\
													self.cloneMap, self.tmpDir)		

		ldd					=	vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/maps__/ldd.map",\
													self.cloneMap, self.tmpDir, None, True, None, False)		

		qbank				=	pcr.cover(\
		                        vos.readPCRmapClone("/projects/0/dfguu/users/inge/inputMAPS/maps__/Qbankfull_edwinInputs.map",\
													self.cloneMap, self.tmpDir), 0.0)
		
		self.landmask		=	landmask
		self.dem			=	dem_ini
		self.cellarea		=	cellarea
		self.min_dem		=	min_dem
		
		aqdepth_ini			=	aqdepth
		self.aqdepth_ini	=	aqdepth_ini
		# What are the differences among "aqdepth", "aqdepth_ini" and "self.aqdepth_ini"? 
		
		aqdepth				=	pcr.cover(pcr.ifthenelse(aqdepth > 0.0, aqdepth, 200.0),200.0)			## over land max 200 m, over sea 200m			
		# If you want to limit the aquifer depth to 200.00, I suggest to add the following line.
		aqdepth				=	pcr.max(200.0, aqdepth)			
		
		dem					=	pcr.cover(pcr.ifthen(landmask, dem_ini),0.0)
		top_l2				=	dem
		bottom_l1			=	dem-aqdepth
		top_l1				=	top_l2- (aqdepth*0.1)				     								## layer 2 is 10% total thickness	
		
		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ mf.createBottomLayer(bottom_l1, top_l1)
		#~ mf.addLayer(top_l2)

		# The following lines are needed as Edwin moved all pcraster modflow operations to the dynamic section. 
		self.input_bottom_l1 = bottom_l1
		self.input_top_l1    = top_l1
		self.input_top_l2    = top_l2
	
		self.bottom_elevation_aquifer =	dem_ini - aqdepth												##** nodig voor groundwater storage
				
		#~ #* OLD - This is WRONG. - We are NOT using this one anymore.
		#~ # simulaton parameter
		#~ # mf.setDISParameter(4,2,1,1,1,0)	
		
		# set boundary conditions
		ibound_l1			= 	pcr.cover(pcr.ifthen(landmask, pcr.nominal(1)),pcr.nominal(-1))
		
		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ mf.setBoundary(ibound_l1,2)
		#~ mf.setBoundary(ibound_l1,1)
		
		# The following lines are needed as Edwin moved all pcraster modflow operations to the dynamic section. 
		self.input_ibound_l1 = ibound_l1
		self.input_ibound_l2 = ibound_l1

		## set initial values
		iHead				=	pcr.cover(iHeadini,0.0)
		# Why is there only one set of initial head values?
		# Note: If you still do not know the initial head condition values, you have to estimate them (both for the 1st and 2nd layer) from a steady-state simulation.  						 			

		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ mf.setInitialHead(iHead,2)	# Why did you put the same initial values for both layers?
		#~ mf.setInitialHead(iHead,1)	
		
		
		# The following lines are needed as Edwin moved all pcraster modflow operations to the dynamic section.
		# - As the current quick fix (temporary) solution, I just assume that the initial condition equal to top layer elevation. 
		self.input_head_top    = top_l1 
		self.input_head_bottom = top_l1 

		
		
		# set conductivities - I did NOT check this part as I trust your justification for this. 
		######################################################################################################################################### 

		rho_water			=	pcr.scalar(1000)
		miu_water			=	pcr.scalar(0.001)
		g_gravity			=	pcr.scalar(9.81)
		
		dikte_l2_ini		=	aqdepth*0.1								# top layer			
		dikte_l1_ini		=	aqdepth - dikte_l2_ini					# bottom layer		
		dikte_l2			=	pcr.ifthen(landmask, pcr.cover(dikte_l2_ini, 20.0))
		dikte_l1			=   pcr.ifthen(landmask, pcr.cover(dikte_l1_ini, 180.0))
		self.dikte_l1		= 	dikte_l1
		self.dikte_l2		= 	dikte_l2
		#-no confined layers
		ksat_inp_ini		=	rho_water* (10**ksat_log)* (g_gravity/ miu_water) *24.0 *3600.0		
		#-confining layers 	
		## conf maps are read in read maps 				
		conflayers			=	pcr.cover(conflayers, boolean(0))
		#-khorizontal 
		ksat_l1_conf		=	rho_water* (10**ksat_l1_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0    # fine grained    
		ksat_l2_conf		= 	rho_water* (10**ksat_l2_conf_log)* (g_gravity/ miu_water) *24.0 *3600.0	   # coarse grained		
		khoriz_l1_ini		=	pcr.cover(ksat_l1_conf, ksat_inp_ini)
		khoriz_l2_ini		=	pcr.cover(ksat_l2_conf, ksat_inp_ini)
		# minumim value for aquifer areas:
		khoriz_l1_ini		=	pcr.ifthenelse(aqdepth >-999.9, pcr.max(khoriz_l1_ini,0.01),khoriz_l1_ini)      #**
		khoriz_l2_ini		=	pcr.ifthenelse(aqdepth >-999.9, pcr.max(khoriz_l2_ini,0.01),khoriz_l2_ini)		#**			# minimum value = fine grained unc. sed.
		#k vertical
		#kvert_l2_ini		=	pcr.ifthenelse(khoriz_l2_ini > -999.9, (khoriz_l2_ini*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		#kvert_l1			=	pcr.ifthenelse(khoriz_l1_ini > -999.9, (10*cellarea)/((5.0/60.0)**2.0),(10.0*cellarea)/((5.0/60.0)**2.0))
		#kvert_l2				=	pcr.max(dikte_l2/5000, kvert_l2_ini)  #**
		#kvert_l2			=	pcr.cover(pcr.ifthenelse(conflayers == boolean(1), (0.008*cellarea)/((5.0/60.0)**2.0), kvert_l2_ini),kvert_l2_ini)
		kD_l2_ini			=	khoriz_l2_ini*(dikte_l2)
		kD_l1_ini			=	khoriz_l1_ini*(dikte_l1)	
		kD_l2				=	pcr.max(30,kD_l2_ini)
		kD_l1				=	pcr.max(30,kD_l1_ini)
		khoriz_l2_ori			=	pcr.cover(kD_l2/(dikte_l2),20.) 			#10.
		khoriz_l1_ori			=	pcr.cover(kD_l1/(dikte_l1),190.)	 		#90.	
		#################################
		khoriz_l2 = khoriz_l2_ori * 10**(0)
		khoriz_l1 = khoriz_l1_ori * 10**(0)
		kvert_l2_ori = khoriz_l2	#pcr.cover(kvert_l2,1E10)
		kvert_l1_ori = khoriz_l1	#pcr.cover(kvert_l1,1E10)
		# kvert range, but do make sure kvert <= khoriz
		kvert_l2 = pcr.min(kvert_l2_ori * 10**(-2), khoriz_l2)
		kvert_l1 = pcr.min(kvert_l1_ori * 10**(-2), khoriz_l1)
		kvert_l2 = pcr.cover((kvert_l2*cellarea)/((5.0/60.0)**2.0),1E10)
		kvert_l1 = pcr.cover(pcr.max(1E10,(kvert_l1*cellarea)/((5.0/60.0)**2.0)),1E10)  # kvert onderste laag is nu super hoog
		################################
		#~ pcr.report(kD_l2, "kD_l2.map")
		#~ pcr.report(kD_l1, "kD_l1.map")

		###################################################################################################################################################################### 
		# end of set conductivities - I did NOT check the above part as I trust your justification for this. 


		# make the vertical conductivities of the bottom layer very high 
		# such that the values of VCONT (1/resistance) depending only on the values given for the top layer  
		# see: http://inside.mines.edu/~epoeter/583/08/discussion/vcont/modflow_vcont.htm
		# - very high conductivity values for the bottom layer 
		kvert_l1 =  pcr.spatial(pcr.scalar(1e99)) * self.cellarea/\
													(pcr.clone().cellSize()*pcr.clone().cellSize())
        # - correcting the values for the top layer (see also pages 5-12 to 5-16 on http://pubs.usgs.gov/twri/twri6a1/#pdf)
		kvert_l2 =  0.5 * kvert_l2
		
		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ mf.setConductivity(00, khoriz_l2, kvert_l2,2)
		#~ mf.setConductivity(00, khoriz_l1, kvert_l1,1)

		# The following lines are needed as Edwin moved all pcraster modflow operations to the dynamic section.
		self.input_khoriz_l2 = khoriz_l2
		self.input_kvert_l2  = kvert_l2
		self.input_khoriz_l2 = khoriz_l1
		self.input_kvert_l1  = kvert_l1



		# set storage
		spe_yi_inp			=	pcr.ifthen(landmask, spe_yi_inp_ori * 0.5)
		# Why do you half this?

		spe_yi_inp			=	pcr.min(1.0, pcr.max(0.01,spe_yi_inp))	

		#- Limit for aquifer area
		spe_yi_inp			=	pcr.ifthenelse(aqdepth >-999.9, pcr.max(spe_yi_inp, 0.11), spe_yi_inp)    # if in aquifer spec yield is miminal fine grained
		#stor_coef			=	pcr.scalar(0.01)
		#stor_conf			=	pcr.cover(pcr.cover(pcr.ifthenelse(conflayers == boolean(1), stor_coef, spe_yi_inp),spe_yi_inp),1000.0)	 

		# I don't think it is a good idea to cover this map with 1000 (above 1.0).
		#~ stor_prim		=	pcr.cover(spe_yi_inp,1000.0) # I don't think it is a good idea to cover this map with 1000.
		#~ stor_sec			=	pcr.cover(spe_yi_inp,1000.0) # I don't think it is a good idea to cover this map with 1000.
		
		# I suggest to cover this with 0.35 (maximum specific yield for sand) and limit the value to 0.01 (which is also your minimum value)
		stor_prim =	pcr.cover(spe_yi_inp, 0.35)
		stor_sec  =	pcr.cover(spe_yi_inp, 0.35)
		
		
		# NOTE: The storage coefficient values MUST BE corrected with cell areas (as we use the LAT/LON coordinate system, see: http://www.hydrol-earth-syst-sci.net/15/2913/2011/hess-15-2913-2011.html)
		stor_prim =	stor_prim * self.cellarea/\
		                        (pcr.clone().cellSize()*pcr.clone().cellSize())
		stor_sec  =	stor_sec  * self.cellarea/\
		                        (pcr.clone().cellSize()*pcr.clone().cellSize())
		

		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ mf.setStorage(stor_prim, stor_sec,1)
		#~ mf.setStorage(stor_prim, stor_sec,2)
		
		# The following lines are needed as Edwin moved all pcraster modflow operations to the dynamic section.
		self.input_stor_prim = stor_prim
		self.input_stor_sec  = stor_sec


		# Edwin moved all pcraster modflow operations to the dynamic section (so that we can re-initialize the "mf" (pcraster modflow) object for every time step).
		#~ # solver
		#~ mf.setPCG(1500,1250,1,1,160000,0.98,2,1)	
		

		# adding river - Edwin did NOT carefully check this part.
		riv_manning			=	pcr.scalar(0.0450)
		self.riv_manning	=	riv_manning
		resistance			=	pcr.scalar(1.0)
		self.resistance		=	resistance
		riv_bedres_inp		=	pcr.scalar(1.0000)
		min_dem2			=	pcr.ifthenelse(min_dem < 0.0, 0.0, min_dem)
		Z0_floodplain2		= 	pcr.ifthenelse(Z0_floodplain < 0.0, pcr.max(min_dem2,Z0_floodplain),Z0_floodplain)
		riv_width			= 	4.8* ((qbank)**0.5)
		self.riv_width		=	pcr.max(riv_width,0.5) #*** minimum gegeven 
	    # RIVERS ONLY
		riv_slope			=	pcr.ifthen(riv_width > 0.0, riv_slope)
		self.riv_slope_used	= 	pcr.ifthen(riv_slope > 0.00005, riv_slope)	    #** bigger									
		self.riv_head_ini	= 	pcr.cover(pcr.ifthenelse(riv_width > 30.0, Z0_floodplain2,top_l2),0.0)
		self.riv_depth_bkfl	= 	((riv_manning*(qbank)**0.5)/(self.riv_width*self.riv_slope_used**0.5))**(3.0/5.0)
		self.riv_bot_bkfl	=	min_dem2- self.riv_depth_bkfl
	
		
		# adding drain - Edwin did NOT carefully check this part.
		# base of groundwater that contribute to baseflow
		DZS3INFLUENCED		=	pcr.scalar(5.0)
		BASE_S3				=	pcr.areaminimum(Z0_floodplain2, pcr.subcatchment(ldd, pcr.nominal(uniqueid(pcr.ifthen(Z0_floodplain2 > -999.9, boolean(1))))))
		BASE_S3				=	pcr.max(Z0_floodplain2- DZS3INFLUENCED, downstream(ldd,Z0_floodplain2),BASE_S3)			# for mountainous areas
		BASE_S3				=	pcr.ifthenelse(aqdepth > -9999.9, pcr.max(Z0_floodplain, BASE_S3), BASE_S3)				# for aquifers
		self.BASE_S3_used	=	pcr.cover(BASE_S3,-900000.0)
		storcoef_act		=	pcr.ifthenelse(landmask, spe_yi_inp,0.0)
		KQ3					=	pcr.cover(pcr.min(1.0,KQ3),0.0)		#**
		KQ3min				=	1.0e-4 						#**
		KQ3					=	pcr.max(KQ3min,KQ3)				#**
		KQ3_x_Sy			=	pcr.cover(KQ3* storcoef_act, 0.0)			#**
		self.KQ3_x_Sy_AR	=	pcr.cover(pcr.ifthenelse(self.BASE_S3_used == -900000.0, 0.0, KQ3_x_Sy*cellarea),0.0)
		#self.storcoef_act	=	stor_conf
		self.storcoef_act	= 	stor_prim
		
	def dynamic(self):
	
		self.modelTime.update(self.currentTimeStep())
		
		if self.modelTime.isLastDayOfMonth():
		
			dateInput = self.modelTime.fulldate		
			print(dateInput)		
			
			# number of days for this month
			number_of_days_in_the_month = self.modelTime.day

			#~ # - It seems this file is NOT CORRECT. This file has a daily resolution (not monthly one) and starting on 1960-01-01 and ending on 1961-09-03.
			#~ ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchhum2_05min.nc"
			#~ varName = "recharge"	
			#~ print(ncFile)
			#~ rch_human = vos.netcdf2PCRobjClone(ncFile,varName, dateInput, \
							#~ useDoy = None,
							#~ cloneMapFileName = self.cloneMap, \
							#~ )
			
			# another recharge file
			# - This file has a monthly resolution 
			# - Please check the unit. Is it true that the unit is: kg m-2 s-1? If it is true, then you have to convert it to m day-1
			#   Note that (assuming 1 kg of water = 1000 m3): 1 kg m-2 s-1 = 1000 m s-1 = 1000 * (24 * 3600) m day-1
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/Yoshi_rchnat_05min.nc"
			varName = "rechargeTotal"
			print(ncFile)
			rch_nat= vos.netcdf2PCRobjClone(ncFile,varName,dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			# discharge file
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/discharge_hum_monthAvg_output.nc"
			varName = "discharge"
			# - This file has a monthly resolution 
			print(ncFile)
			Qinp= vos.netcdf2PCRobjClone(ncFile,varName,dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			# groundwater abstraction file
			ncFile = "/projects/0/dfguu/users/inge/inputMAPS/maps__/gwab_m3_05min.nc"
			# - This file has a monthly resolution 
			# - The unit is: 10^6 m3 per month. Note that: 10^6 m3 per month = 10^6 / (number_of_days_in_the_month) m3 day-1
			varName = "gwab_m3_05min"
			print(ncFile)
			totGW = vos.netcdf2PCRobjClone(ncFile,varName, dateInput, \
							useDoy = None,
							cloneMapFileName = self.cloneMap, \
							)
			
			# river package
			# - qaverage
			qaverage			=	Qinp
			riv_depth_avg1		= 	((self.riv_manning*((qaverage)**0.5))/(self.riv_width*self.riv_slope_used**0.5))**(3.0/5.0)
			riv_depth_avg		=	pcr.ifthenelse(riv_depth_avg1 < 0.01, 0.0, riv_depth_avg1)
			riv_head			=	self.riv_bot_bkfl + riv_depth_avg
			riv_head2			= 	pcr.cover(riv_head,self.riv_head_ini)
			riv_cond			= 	pcr.cover((1/self.resistance)*pcr.ifthenelse(self.riv_width >= 30.0, self.riv_width*(self.cellarea*2.0)**0.5,0.0),0.0)
			drn_width			= 	pcr.ifthenelse(riv_cond == 0.0, pcr.max(10.0,self.riv_width),0.0)								
			drn_cond			=	pcr.cover(pcr.ifthenelse(riv_cond == 0.0,(1.0/self.resistance)*drn_width*(self.cellarea*2)**0.5,0.0),0.0) 
			drn_cond			=	pcr.ifthenelse(abs(drn_cond) < 1e-20, 0.0, drn_cond)						
			
			riv_head_comb		=	pcr.cover(pcr.ifthenelse(riv_cond > 0.0, riv_head2, self.riv_head_ini),0.0)
			riv_bot_comb		=	pcr.cover(pcr.ifthenelse(riv_cond > 0.0, self.riv_bot_bkfl, self.riv_head_ini),0.0)
			riv_cond_comb		=	pcr.cover(pcr.ifthenelse(riv_cond > 0.0, riv_cond, drn_cond),0.0)
			
			
			# abstraction package
			totGW_used = pcr.cover(pcr.ifthen(self.aqdepth_ini > -999.9, totGW),0.0) # unit: 10**6 m3 per month
			totGW_used_2 = (totGW_used*(10.0**6.0))     
			#~ totGW_used_m3d = pcr.cover((totGW_used_2/30.0)*-1.0,0.0)   						# this should be divided by days of the month (simplified to 30d)
			totGW_used_m3d = pcr.cover((totGW_used_2/number_of_days_in_the_month)*-1.0,0.0) 
			
			
			# recharge package
			rch_hum = rch_human
			#
			# Why do we have to do this? I think that this is inconsistent. (?)
			rch = pcr.cover(pcr.ifthen(totGW_used_m3d > -999.9, rch_hum), rch_nat)  			# if abstr dan rch abstr anders ruch nat 
			#
			# correcting recharge values as we use the LAT/LON coordinate system.  
			rch_inp = pcr.cover(pcr.max(0.0, (rch *self.cellarea)/(5.0/60.0)**2.0),0.0)		
			

			# go to the output directory so that all temporary pcraster modfow files will be written there
			os.chdir(self.outDir)

			# remove all previous pcraster modflow files (if there are any) 
			cmd = 'rm '+ self.outDir + "/pcrmf*"
			os.system(cmd)
			cmd = 'rm '+ self.outDir + "/fort*"
			os.system(cmd)
			cmd = 'rm '+ self.outDir + "/mf2kerr*"
			os.system(cmd)

			# initialize modflow
			# - deleting previous modflow object
			mf = None; del mf
			# - initialize a pcraster modflow object
			mf = pcr.initialise(pcr.clone())
			

			# bottom and layer elevations
			mf.createBottomLayer(self.input_bottom_l1, self.input_top_l1)
			mf.addLayer(self.input_top_l2)
			
			# boundary conditions  
			mf.setBoundary(self.input_ibound_l1, 1)
			mf.setBoundary(self.input_ibound_l2, 2)
	
			# horizontal and vertical conductivities 
			mf.setConductivity(00 , self.input_khoriz_l1, self.input_kvert_l1, 1)
			mf.setConductivity(00 , self.input_khoriz_l2, self.input_kvert_l2, 2)
			
			# storage coefficients 
			mf.setStorage(self.input_stor_prim, self.input_stor_sec,1)
			mf.setStorage(self.input_stor_prim, self.input_stor_sec,2)
			
			# initial heads
			initial_head_bottom = self.input_head_bottom   
			initial_head_top    = self.input_head_top
			mf.setInitialHead(pcr.scalar(initial_head_bottom), 1)
			mf.setInitialHead(pcr.scalar(initial_head_top),    2)	

			# set all modflow packages
			mf.setRiver(riv_head_comb, riv_bot_comb, riv_cond_comb,2)
			mf.setRecharge(rch_inp,1)			
			mf.setWell(totGW_used_m3d,1)
			mf.setDrain(self.BASE_S3_used, self.KQ3_x_Sy_AR, 2)         # Note: You may want to try to put the drain package also in the bottom (in order to make sure that recharged water will not be 'trapped'). 

			# execute MODFLOW
			mf.run()
			
			# retrieve outputs
			gw_head1			=	mf.getHeads(1)
			gw_head2			=	mf.getHeads(2)
			riv_baseflow		=	mf.getRiverLeakage(2)
			drn_baseflow		=	mf.getDrain(2)
			recharge			=	mf.getRecharge(2)
			
			# use the calculated head values for the next time step
			self.input_head_bottom = gw_head1
			self.input_head_top	   = gw_head2			

			gw_depth2			=	self.dem - gw_head2
			gw_depth1			=	self.dem - gw_head1
			head_diff			=	gw_head1 - gw_head2
			
			# reporting all outputs from MF to de netcdf-dir	
			# all outputs are masked		
			self.head_bottomMF	=	gw_head1 #pcr.max(-100, gw_head1)
			self.head_topMF 	= 	gw_head2 #pcr.max(-100, gw_head2)
			self.depth_bottomMF	= 	pcr.ifthen(self.landmask,gw_depth1)
			self.depth_topMF	= 	pcr.ifthen(self.landmask,gw_depth2)
			self.riv_baseflowMF	= 	pcr.ifthen(self.landmask,riv_baseflow)
			self.drn_baseflowMF	= 	pcr.ifthen(self.landmask,drn_baseflow)
			self.head_diffMF	= 	pcr.ifthen(self.landmask,head_diff)
			self.tot_baseflowMF	= 	pcr.ifthen(self.landmask,riv_baseflow + drn_baseflow)
			self.rechargeMF		= 	pcr.ifthen(self.landmask,recharge)
			head_topMF 		= 	gw_head2
			head_bottomMF 	= 	gw_head1
			tot_baseflowMF	=	riv_baseflow + drn_baseflow
			
			# reporting to pcraster maps 
			pcr.report(head_topMF    , self.outDir + "/" + "head_topMF.map")
			pcr.report(head_bottomMF , self.outDir + "/" + "head_bottomMF.map")							## --> can the dir-path be automatic  
			pcr.report(gw_depth2     , self.outDir + "/" + "depth_topMF.map")
			pcr.report(tot_baseflowMF, self.outDir + "/" + "tot_baseflowMF.map")
					
			timeStamp 	= 	datetime.datetime(self.modelTime.year,\
									self.modelTime.month,\
									self.modelTime.day,\
									0)
			# reporting to netcdf files
			for variable in self.variable_output:
				chosenVarField = pcr2numpy(self.__getattribute__(variable), vos.MV)
				self.netcdfReport.data2NetCDF(ncFile = str(self.outDir) + self.netcdf_output["file_name"][variable],\
										varName = variable,\
										varField = chosenVarField,
										timeStamp = timeStamp)

cloneMap 	    = "/projects/0/dfguu/users/inge/inputMAPS/Clone_05min.map" # "../MFinp/australia/australia_clone.map" "../../PCR-GLOBWB/MFinp/australia/australia_clone.map" #
cloneMap 	    = "/projects/0/dfguu/data/hydroworld/others/Mississippi/Mississippi05min.clone.map"
outputDirectory = "/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/"
strStartTime    = sys.argv[1]
strEndTime      = sys.argv[2]

# initiating modelTime object
modelTime 		= modelTime.ModelTime()
modelTime.getStartEndTimeSteps(strStartTime,strEndTime)
myModel			= mymodflow(cloneMap, modelTime, outputDirectory)
DynamicModel	= DynamicFramework(myModel,modelTime.nrOfTimeSteps)     #***
DynamicModel.run()			 
