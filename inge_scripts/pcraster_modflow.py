#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pcraster as pcr

class PCRasterModflow():
	
	def __init__(self, cloneMap):
		
		self.cloneMap = cloneMap
		pcr.setclone(self.cloneMap)

	def initialize(self, modelTime, \
	                     input_bottom_l1, input_top_l1, input_top_l2, \
	                     input_ibound, \
	                     input_khoriz_l1, input_kvert_l1, \
	                     input_khoriz_l2, input_kvert_l2, \
	                     input_stor_prim, input_stor_sec, \
	                     initial_head_bottom, initial_head_top, \
	                     ):
		
		self.pcr_modflow = None
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
		self.pcr_modflow.setInitialHead(initial_head_bottom, 1)
		self.pcr_modflow.setInitialHead(initial_head_top,    2)	

		# simulation parameters
		NSTP   = modelTime.day
		PERLEN = modelTime.day
		self.pcr_modflow.setDISParameter(4,2,PERLEN,NSTP,1.0,0)
		
		# solver parameters
		HCLOSE = 1
		RCLOSE = 160000
		self.pcr_modflow.setPCG(1500,1250,1,HCLOSE,RCLOSE,0.98,2,1)	

	def run(self):
	
		self.pcr_modflow.run()
		
	def get_results(self):

		gw_head_1 = self.pcr_modflow.getHeads(1)
		gw_head_2 = self.pcr_modflow.getHeads(2)
		
		self.head_bottomMF = gw_head_1
		self.head_topMF    = gw_head_2

