#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pcraster as pcr
import os

class PCRasterModflow():
	
	def __init__(self, cloneMap):
		
		self.cloneMap = cloneMap
		pcr.setclone(self.cloneMap)
		
		self.first_time_step = True

	def initialize(self, modelTime, \
	                     input_bottom_l1, input_top_l1, input_top_l2, \
	                     input_ibound, \
	                     input_khoriz_l1, input_kvert_l1, \
	                     input_khoriz_l2, input_kvert_l2, \
	                     input_stor_prim, input_stor_sec, \
	                     initial_head_bottom, initial_head_top, \
	                     riv_head_comb, riv_bot_comb, riv_cond_comb, \
	                     self.BASE_S3_used, self.KQ3_x_Sy_AR, 
	                     rch_inp, \
	                     self.outDir)
		
		self.pcr_modflow = None
		del self.pcr_modflow
		
		# remove all previous pcraster modflow files
		cmd = 'rm '+ outDir + "/pcrmf*"
		os.system(cmd)
		cmd = 'rm '+ outDir + "/fort*"
		os.system(cmd)
		cmd = 'rm '+ outDir + "/mf2kerr*"
		os.system(cmd)
		
		self.pcr_modflow = pcr.initialise(pcr.clone())
		
		# bottom and layer elevations
		self.pcr_modflow.createBottomLayer(input_bottom_l1, input_top_l1)
		self.pcr_modflow.addLayer(input_top_l2)
		
		# boundary conditions  
		self.pcr_modflow.setBoundary(input_ibound, 1)
		self.pcr_modflow.setBoundary(input_ibound, 2)

		# horizontal and vertical conductivities 
		self.pcr_modflow.setConductivity(00, input_khoriz_l1, input_kvert_l1, 1)
		self.pcr_modflow.setConductivity(00, input_khoriz_l2, input_kvert_l2, 2)
		
		# storage coefficients 
		self.pcr_modflow.setStorage(input_stor_prim, input_stor_sec,1)
		self.pcr_modflow.setStorage(input_stor_prim, input_stor_sec,2)
		
		# initial heads
		self.pcr_modflow.setInitialHead(pcr.scalar(initial_head_bottom), 1)
		self.pcr_modflow.setInitialHead(pcr.scalar(initial_head_top),    2)	
		self.first_time_step = False

		# simulation parameters
		NSTP   = modelTime.day
		PERLEN = modelTime.day
		self.pcr_modflow.setDISParameter(4,2,PERLEN,NSTP,1.0,0)
		
		# solver parameters
		HCLOSE = 1      # 0.000000000000000000000001 # 1
		RCLOSE = 160000 # 0.000000000000000000000001 # 160000
		self.pcr_modflow.setPCG(500,250,1,HCLOSE,RCLOSE,0.98,2,1)	

		self.pcr_modflow.setRiver(riv_head_comb, riv_bot_comb, riv_cond_comb, 2)
		self.pcr_modflow.setDrain(self.BASE_S3_used, self.KQ3_x_Sy_AR, 2)
		
		self.pcr_modflow.setWell(totGW_used_m3d,1)
		self.pcr_modflow.setRecharge(rch_inp,1)			

	def run(self):
	
		self.pcr_modflow.run()
		
	def get_results(self):

		gw_head_1 = None
		gw_head_2 = None
		
		gw_head_1 = self.pcr_modflow.getHeads(1)
		gw_head_2 = self.pcr_modflow.getHeads(2)
		
		riv_baseflow = self.pcr_modflow.getRiverLeakage(2)
		drn_baseflow = self.pcr_modflow.getDrain(2)
		recharge	 = self.pcr_modflow.getRecharge(2)
		
		self.head_bottomMF = pcr.scalar(gw_head_1)
		self.head_topMF    = pcr.scalar(gw_head_2)

		del gw_head_1
		del gw_head_2 
		
		self.pcr_modflow = None
		del self.pcr_modflow
		self.pcr_modflow = 0.0
		
