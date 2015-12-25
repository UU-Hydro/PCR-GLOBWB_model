#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Sy_1 
# NOTE layers in PCR-MODFLOW : 1= bottom 2 = top 

import os
import sys
import datetime

from pcraster.framework import *
import pcraster as pcr

import pcraster_modflow

import ncConverter as ncReport
from currTimeStep import ModelTime
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
		self.outDir = output_directory
		os.chdir(self.outDir)
		try:
			os.makedirs("/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/")
		except:
			pass	
					 
		for variable in self.variable_output:
			self.netcdfReport.createNetCDF(ncFileName = str(self.outDir) + self.netcdf_output["file_name"][variable], \
										   varName = variable, 
		                                   varUnits = self.netcdf_output["unit"][variable])

	def initial (self):
		iHeadini			=	pcr.readmap("/projects/0/dfguu/users/inge/modflow_coupling_global_natural/head_topMF")		
		landmask			=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/landmask")
		dem_ini				= 	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_avg_05min")
		min_dem				=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_min_05min")
		cellarea			=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/cellArea_05min")
		riv_slope			=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/gradient_05min")
		Z0_floodplain		=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/surface_parameters_MF/dem_floodplain_05min")
		aqdepth				= 	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/damc_ave")
		spe_yi_inp_ori		=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/StorCoeff_NEW")
		KQ3					=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/Recess_NEW")
		conflayers			=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/conflayers4")				
		ksat_log			=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/lkmc_ave")
		ksat_l1_conf_log	=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl1B_ave")
		ksat_l2_conf_log	=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/aquifer_parameters_MF/kl2B_ave")		
		ldd					=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/ldd")
		qbank				=	pcr.readmap("/projects/0/dfguu/users/inge/inputMAPS/maps__/Qbankfull_edwinInputs")
		self.landmask		=	landmask
		self.dem			=	dem_ini
		self.cellarea		=	cellarea
		self.min_dem		=	min_dem
		aqdepth_ini			=	aqdepth
		self.aqdepth_ini	=	aqdepth_ini
		aqdepth				=	pcr.cover(pcr.ifthenelse(aqdepth > 0.0, aqdepth, 200.0),200.0)			## over land max 200 m, over sea 200m			
		dem					=	pcr.cover(pcr.ifthen(landmask, dem_ini),0.0)
		top_l2				=	dem
		bottom_l1			=	dem-aqdepth
		top_l1				=	top_l2- (aqdepth*0.1)				     						## layer 2 is 10% total thickness	
		
		self.input_bottom_l1 = bottom_l1
		self.input_top_l1    = top_l2
		self.input_top_l2    = top_l2 
		
		#~ pcr_modflow.createBottomLayer(bottom_l1,top_l1)
		#~ pcr_modflow.addLayer(top_l2)
	
		self.bottom_elevation_aquifer	=	dem_ini- aqdepth												##** nodig voor groundwater storage
				
		#* OLD
		# simulaton parameter
		# pcr_modflow.setDISParameter(4,2,1,1,1,0)	
		
		# set boundary conditions
		ibound_l1			= 	pcr.cover(pcr.ifthen(landmask, nominal(1)),nominal(-1))
		
		self.input_ibound = ibound_l1
		
		#~ pcr_modflow.setBoundary(ibound_l1,2)
		#~ pcr_modflow.setBoundary(ibound_l1,1)
		
		## set initial values
		iHead				=	pcr.cover(iHeadini,0.0)						 			
		
		#~ pcr_modflow.setInitialHead(iHead,2)
		#~ pcr_modflow.setInitialHead(iHead,1)	
		
		self.head_topMF    = iHead  # NOTE: THIS MUST BE FROM THE RESULT OF A STEADY STATE SIMULATION 	
		self.head_bottomMF = iHead  # NOTE: THIS MUST BE FROM THE RESULT OF A STEADY STATE SIMULATION

		# set conductivities
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
		kvert_l1 = pcr.cover(pcr.max(1E99,(kvert_l1*cellarea)/((5.0/60.0)**2.0)),1E10)  # kvert onderste laag is nu super hoog
		################################
		#~ pcr.report(kD_l2, "kD_l2.map")
		#~ pcr.report(kD_l1, "kD_l1.map")
		
		#~ pcr_modflow.setConductivity(00, khoriz_l2, kvert_l2, 2)
		#~ pcr_modflow.setConductivity(00, khoriz_l1, kvert_l1, 1)
		
		self.input_kvert_l2  = 0.5 * kvert_l2 # correction is needed here
		self.input_kvert_l1  = kvert_l1
		self.input_khoriz_l2 = khoriz_l2
		self.input_khoriz_l1 = khoriz_l1

		# set storage
		spe_yi_inp			=	pcr.ifthen(landmask, spe_yi_inp_ori * 0.5)
		spe_yi_inp			=	pcr.min(1.0, pcr.max(0.01,spe_yi_inp))	
		#- Limit for aquifer area
		spe_yi_inp			=	pcr.ifthenelse(aqdepth >-999.9, pcr.max(spe_yi_inp, 0.11), spe_yi_inp)    # if in aquifer spec yield is miminal fine grained
		#stor_coef			=	pcr.scalar(0.01)
		#stor_conf			=	pcr.cover(pcr.cover(pcr.ifthenelse(conflayers == boolean(1), stor_coef, spe_yi_inp),spe_yi_inp),1000.0)	 
		stor_prim			=	pcr.cover(spe_yi_inp,1000.0)
		stor_sec			=	pcr.cover(spe_yi_inp,1000.0)

		#~ pcr_modflow.setStorage(stor_prim, stor_sec,1)
		#~ pcr_modflow.setStorage(stor_prim, stor_sec,2)
		
		self.input_stor_prim = stor_prim
		self.input_stor_sec  = stor_sec
		
		# solver
		#~ pcr_modflow.setPCG(1500,1250,1,1,160000,0.98,2,1)	
		
		# adding river
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
	
		# adding drain
		# base of groundwater that contribute to baseflow
		DZS3INFLUENCED		=	pcr.scalar(5.0)
		BASE_S3				=	pcr.areaminimum(Z0_floodplain2, subcatchment(ldd, nominal(uniqueid(pcr.ifthen(Z0_floodplain2 > -999.9, boolean(1))))))
		BASE_S3				=	pcr.max(Z0_floodplain2- DZS3INFLUENCED, downstream(ldd,Z0_floodplain2),BASE_S3)			# for mountainous areas
		BASE_S3				=	pcr.ifthenelse(aqdepth > -9999.9, pcr.max(Z0_floodplain, BASE_S3), BASE_S3)					# for aquifers
		self.BASE_S3_used	=	pcr.cover(BASE_S3,-900000.0)
		storcoef_act		=	pcr.ifthenelse(landmask, spe_yi_inp,0.0)
		KQ3					=	pcr.cover(pcr.min(1.0,KQ3),0.0)		#**
		KQ3min				=	1.0e-4 						#**
		KQ3					=	pcr.max(KQ3min,KQ3)				#**
		KQ3_x_Sy			=	pcr.cover(KQ3* storcoef_act, 0.0)			#**
		self.KQ3_x_Sy_AR	=	pcr.cover(pcr.ifthenelse(self.BASE_S3_used == -900000.0, 0.0, KQ3_x_Sy*cellarea),0.0)
		#self.storcoef_act	=	stor_conf
		self.storcoef_act	= 	stor_prim
		
		#~ test = True
		#~ if test:

	def dynamic(self):
	
		self.modelTime.update(self.currentTimeStep())
		
		if self.modelTime.isLastDayOfMonth():
		
			pcr_modflow = None
			pcr_modflow = pcraster_modflow.PCRasterModflow(self.cloneMap)
			pcr_modflow.initialize( \
			             self.modelTime, \
	                     self.input_bottom_l1, self.input_top_l1, self.input_top_l2, \
	                     self.input_ibound, \
	                     self.input_khoriz_l1, self.input_kvert_l1, \
	                     self.input_khoriz_l2, self.input_kvert_l2, \
	                     self.input_stor_prim, self.input_stor_sec, \
	                     self.head_bottomMF, self.head_topMF)

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
			
			#~ pcr_modflow.setRiver(riv_head_comb, riv_bot_comb, riv_cond_comb,2)
			#~ 
			#~ pcr_modflow.setDrain(self.BASE_S3_used, self.KQ3_x_Sy_AR,2)
			
			
			totGW_used = pcr.cover(pcr.ifthen(self.aqdepth_ini > -999.9, totGW),0.0) # unit: 10**6 m3 per month
			totGW_used_2 = (totGW_used*(10.0**6.0))
			totGW_used_m3d = pcr.cover((totGW_used_2/30.0)*-1.0,0.0)   # this should be devided by days of the month (simplified to 30d)
			
			#~ pcr_modflow.setWell(totGW_used_m3d,1)
			
			rch_hum = rch_human
			rch = pcr.cover(pcr.ifthen(totGW_used_m3d > -999.9, rch_hum), rch_nat)  # if abstr dan rch abstr anders ruch nat 
			rch_inp = pcr.cover(pcr.max(0.0, (rch *self.cellarea)/(5.0/60.0)**2.0),0.0)		
			
			#~ pcr_modflow.setRecharge(rch_inp,1)			
					
			print('before modflow')

			# execuate MODFLOW
			#~ pcr_modflow.run()
			pcr_modflow.run()
			
			print('after modflow')
			
			#~ pcr_modflow.get_results()
			#~ self.head_bottomMF = pcr.scalar(pcr_modflow.head_bottomMF)
			#~ self.head_topMF    = pcr.scalar(pcr_modflow.head_topMF)
			
			pcr_modflow = None
			del pcr_modflow

			#~ # retrieve outputs
			#~ gw_head1			=	pcr_modflow.getHeads(1)
#~ 
			#~ gw_head2			=	pcr_modflow.getHeads(2)
			#~ riv_baseflow		=	pcr_modflow.getRiverLeakage(2)
			#~ drn_baseflow		=	pcr_modflow.getDrain(2)
			#~ recharge			=	pcr_modflow.getRecharge(2)
							#~ 
			#~ gw_depth2			=	self.dem- gw_head2
			#~ gw_depth1			=	self.dem- gw_head1
			#~ head_diff			=	gw_head1-gw_head2
			#~ 
			#~ # reporting all outputs from MF to de netcdf-dir	
			#~ # all outputs are masked		
			#~ self.head_bottomMF	=	gw_head1 #pcr.pcr.max(-100, gw_head1)
			#~ self.head_topMF 	= 	gw_head2 #pcr.pcr.max(-100, gw_head2)
#~ 
			#~ self.depth_bottomMF	= 	pcr.ifthen(self.landmask,gw_depth1)
			#~ self.depth_topMF	= 	pcr.ifthen(self.landmask,gw_depth2)
			#~ self.riv_baseflowMF	= 	pcr.ifthen(self.landmask,riv_baseflow)
			#~ self.drn_baseflowMF	= 	pcr.ifthen(self.landmask,drn_baseflow)
			#~ self.head_diffMF	= 	pcr.ifthen(self.landmask,head_diff)
			#~ self.tot_baseflowMF	= 	pcr.ifthen(self.landmask,riv_baseflow + drn_baseflow)
			#~ self.rechargeMF		= 	pcr.ifthen(self.landmask,recharge)
			#~ head_topMF 		= 	gw_head2
			#~ head_bottomMF 	= 	gw_head1
			#~ tot_baseflowMF	=	riv_baseflow + drn_baseflow
			
			#~ # - report new initial conditions 
			#~ pcr.report(head_topMF, "/projects/0/dfguu/users/inge/modflow_Sy1/tmp/head_topMF.map")
			#~ pcr.report(head_topMF, "/projects/0/dfguu/users/inge/modflow_Sy1/tmp/ini/head_topMF")
			#~ pcr.report(head_bottomMF, "/projects/0/dfguu/users/inge/modflow_Sy1/tmp/head_bottomMF.map")							## --> can the dir-path be automatic  
			#~ pcr.report(gw_depth2, "/projects/0/dfguu/users/inge/modflow_Sy1/tmp/depth_topMF.map")
			#~ pcr.report(tot_baseflowMF, "/projects/0/dfguu/users/inge/modflow_Sy1/tmp/tot_baseflowMF.map")
					
			#~ timeStamp 	= 	datetime.datetime(self.modelTime.year,\
									#~ self.modelTime.month,\
									#~ self.modelTime.day,\
									#~ 0)
			
			#~ # reporting to netcdf files
			#~ for variable in self.variable_output:
				#~ chosenVarField = pcr2numpy(self.__getattribute__(variable), vos.MV)
				#~ self.netcdfReport.data2NetCDF(
				                        #~ str(self.outDir) + self.netcdf_output["file_name"][variable],\
										#~ variable, \
										#~ chosenVarField, \
										#~ timeStamp)

			# clear the modflow object
			pcr_modflow = None
			del pcr_modflow

cloneMap 	 = "/projects/0/dfguu/users/inge/inputMAPS/Clone_05min.map" # "../MFinp/australia/australia_clone.map" "../../PCR-GLOBWB/MFinp/australia/australia_clone.map" #
cloneMap 	 = "/projects/0/dfguu/data/hydroworld/others/Japan/Japan05min.clone.map"
strStartTime = sys.argv[1]
strEndTime   = sys.argv[2]

output_directory = "/projects/0/dfguu/users/edwin/modflow_Sy1/tmp/"

# initiating modelTime object
modelTime = ModelTime()
modelTime.getStartEndTimeSteps(strStartTime,strEndTime)

myModel			= mymodflow(cloneMap,modelTime,output_directory)
DynamicModel	= DynamicFramework(myModel,modelTime.nrOfTimeSteps)     #***
DynamicModel.run()			 
