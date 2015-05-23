#====================================================================================================================================================================
# PCRGLOB-WB-MOD for Rhine and Meuse Basin:
# - This is the REAL transient model. 
# - Before running this script, we have to run pcrglobwb_rm_steadysta_MAR2012.mod and pcrglobwb_rm_steadywbf_MAR2012.mod (to estimate the initial groundwater head).
#
# - created by Edwin H. Sutanudjaja ---  9 March 2012
#   - This is for the coupled model.
#   - PCR-GLOBWB and MODFLOW are DAILY calculated!
#   - Cell size and unit: 3000 arc centiseconds x  3000 arc centiseconds
#   - We abandoned the linear reservoir S3. Baseflow is from MODFLOW (taken from the previous time step).
#   - However, we still use the linear reservoir of S3 to estimate the baseflow contribution from the mountainous areas
#   - For CR fluxes, we use the GE method 1 (assumption: a completely dry condition at the soil surface).
#
# - modified by Edwin H. Sutanudjaja -- 12 April 2012
#   - Including factor for changing WMIN.
#
# - modified by Edwin H. Sutanudjaja -- 16 April 2012
#   - Including factor for changing Z (soil depth) and WMIN.
#
# - modified by Edwin H. Sutanudjaja -- 20 April 2012
#   - IMP_LDCOV = scalar(0) -CANCELLED on 17 May 2012 -RE-APPLIED on 19 May 2012
#
# - modified by Edwin H. Sutanudjaja --  7   May 2012
#   - Providing some alternative for the source folders of maps.
#   - Adding discharge calculation using actual Basel's discharge.
#
# - modified by Edwin H. Sutanudjaja -- 12   May 2012
#   - using my soil depth assumption: Maximum total soil thickness = 1.0 m: Z1__030_07MAY2012.edwin.map and maps01\Z1__100_07MAY2012.edwin.map
#   - returning to the previous parameter values of KCMIN = (1.0) ; KCINT = (1.0) ; INTCAPACIT_VEG = (0.001); INTCAPACIT_NVG = scalar(0.001);
#   - introducing P2_IMP (as the function of b, WMAX and WMIN)
#
# - modified by Edwin H. Sutanudjaja 17 May 2012
#   - Q2_L can occur anytime (as assumed in the original Rens's model)                                   -CANCELLED on 19 May 2012
#   - including some soil moisture output files separating results in sedimentary and mountainous areas
#   - using IMP_LDCOV                                                                                    -CANCELLED on 19 May 2012 
#   - using precipitation downscaling to 30 arc-second                                                   
#   - using temperatureTA downscaling to 30 arc-second to reduce evaporation in higher elevation areas    
#   - SNOW module: refreezing formula returns to the original Rens's model (fast rate in refreezing)     -CANCELLED on 19 May 2012 
#
# - re-modified by Edwin H. Sutanudjaja 19 May 2012
#   - Q2_L can occour only if S2 > FC
#   - IMP_LDCOV = scalar(0)
#   - SNOW module: slower refreezing rate (see above), using my principle
#
#====================================================================================================================================================================

binding

#

# G E N E R A L
#===============================================================================================================================
#
  Duration       =      scalar(1)				;		# 		daily time step calculation
  CLONEMAP       =   ..\maps01\cl112309_3000cs.map		;		# 		lat-lon coordinate system, cellsize = 3000 arc-centiseconds
  LANDMASK       =   ..\maps01\basinv03_nc1109_3000cs.map	;		# 		model area in the Upper Rhine Graben
  CELLAREA       =   ..\maps01\cellsize_nc1109_3000cs.map	;   		#  m2		cell area (entirely, not distinguishing land or water cells)
  LDD         	 =   ..\maps01\ldd_v04_nc1109_3000cs.map	;		#		local drainage direction map
#
  TANSLOPE    	=    ..\maps01\slope_nonstream_nc1109_3000cs.map;		#  m/m	gradient of slope
  DEM30s_inp   	 =   ..\maps01\eu_dem_30s_nc1109_3000cs.map	;		# +m		DEM 30s from HYDROSHEDS (void filled)
#
  DZ0001	 =   ..\maps01\dzrel_08JUL2011_0001.map		;		# +m		maps of relative elevation above the minimum elevation, in percent
  DZ0005	 =   ..\maps01\dzrel_08JUL2011_0005.map		;		# 
  DZ0010	 =   ..\maps01\dzrel_08JUL2011_0010.map		;
  DZ0020	 =   ..\maps01\dzrel_08JUL2011_0020.map		;
  DZ0030	 =   ..\maps01\dzrel_08JUL2011_0030.map		;
  DZ0040	 =   ..\maps01\dzrel_08JUL2011_0040.map		;
  DZ0050	 =   ..\maps01\dzrel_08JUL2011_0050.map		;
  DZ0060	 =   ..\maps01\dzrel_08JUL2011_0060.map		;
  DZ0070	 =   ..\maps01\dzrel_08JUL2011_0070.map		;
  DZ0080	 =   ..\maps01\dzrel_08JUL2011_0080.map		;
  DZ0090	 =   ..\maps01\dzrel_08JUL2011_0090.map		;
  DZ0100	 =   ..\maps01\dzrel_08JUL2011_0100.map		;
#
  WLESMOOTH      =   ..\maps01\sm_wlv_rh_me_30july2011.map	;		# +m	 	estimated flood plain (bankfull) elevation in main rivers and large lakes (only in the river network)
  MIN_DEM3s	 =   ..\maps01\minDEM_08JUL2011_USED_EFF.map	;		# +m	 	minimum elevation values based on the 3 arc-second DEM
  Z0_fldpln_inp	 =   ..\maps01\riv_flpn_30july_2011.map		;		# +m	 	floodplain elevation input	(based on the DEM percentiles)
  Z0_floodplain  =   results\floodplaindem.map			;		# +m	 	floodplain elevation		(contained WLESMOOTH)
#
  DZS3INFLUENCED =   scalar(5.0)				;		#  m	 	additional buffer of groundwater zone that can contribute to baseflow
  BASE_S3	 =   results\baseS3.map				;		# +m	 	base/lower limit elevation of groundwater storage that can contribute to baseflow	
#
  LSLOPE      	 =   ..\maps01\b_horovrldfl_05AUG2011.bas.map	;		#  m	 	hill-slope length (horizontal distance)
  BF_DISCH    	 =   ..\maps01\qv130max_1_0.33333.map		;		#  m3/s	 	bankfull discharge
  AVGDISCH	 =   ..\maps01\qm_avg_19701999.map		;		#  m3/s	 	average discharge (for steady state model)
  AVG_RECH	 =   ..\maps01\r3_avg_19701999.map		;		#  m/day 	average  recharge (for steady state model)
#
  TLA         	 =   scalar(-0.65)				;	        #  degC/100m	temperature lapse rate as an addition in �C per 100 m
#
  FRACWAT_inp    =   ..\maps01\fwat_24Mar2011_nc1109_3000cs.map	;     		#  -		FRACWAT = 1 if a cell is assumed as a "water cell"
  FRACWAT        =   results\fracwat.map			;
#
#
# CROP FACTORS and Vegetation parameters
#===============================================================================================================================
#
  KC_WATSTACK    =   scalar(1.0)				;		# 		crop factor for FRACWAT eq 1 (surface water bodies)
  KCLANDSTACK    =   ..\maps01\KC_CV_LAI_25Mar2011\n$8\kc_land0	;		# 		crop factor for FRACWAT ne 1
  KCMIN          =   scalar(1.0)				;		# 		minimum bare soil crop factor (used to separate soil evaporation from transpiration)
  KCINT          =   scalar(1.0)				;		# 		crop factor for wet interception area
  CF___STACK     =   ..\maps01\KC_CV_LAI_25Mar2011\n$8\CV_land0	;		# 		fractional vegetation cover
  LAI__STACK     =   ..\maps01\KC_CV_LAI_25Mar2011\n$8\LAI_land	;		# 		leaf area index = the ratio of total upper leaf surface of vegetation divided by cell area
#
# Interception parameters:
#
  INTCAPACIT_VEG =   scalar(0.001); 						#  m		interception capacity for vegetated areas = 0.001 m = 1 mm
  INTCAPACIT_NVG =   scalar(0.001);						#				      non vegetated areas
#
#
# Snow routine parameters: constants
#===============================================================================================================================
#
  TT    = scalar(0.0)		;		     				#   degC	threshold temperature for freezing/thawing
  CFMAX = scalar(0.0055)	;		     				# m.degC-1.d-1	degree-day factor
  SFCF  = scalar(1.00)		;		     				# 		snowfall correction factor
  CWH   = scalar(0.10)		;		     				# 		water holding capacity snow cover
  CFR   = scalar(0.05)		;		     				# 		refreezing coefficient
#
#
# Soil parameters:
#===============================================================================================================================
#
  BCH1      = ..\maps01\BP30_07MAY2012.map		;			#   -		pore size distribution parameter (-) Clapp & Hornberger (1978)
  BCH2      = ..\maps01\BP100_07MAY2012.map		;			# 		first and second layer
#
  KS1_inp   = ..\maps01\KS30_07MAY2012.map		;			#   m.day-1	saturated hydraulic conductivity
  KS2_inp   = ..\maps01\KS100_07MAY2012.map		;
  log_KS_add_sed = $11					;			#   		additional values to modify the upper soil saturated conductivity of the sedimentary basin --- range = [-2,2]	
  log_KS_add_mon = $12					;			#   		additional values to modify the upper soil saturated conductivity of the mountainous areas --- range = [-2,2]	
  KS1       = results\KS1_used.map			;			#   m.day-1	
  KS2       = results\KS2_used.map 			;			#   m.day-1	saved maps of saturated hydraulic conductivity
#
  PSI_A1    = ..\maps01\HAP30_07MAY2012.map		;			#   m		air entry value (m) SWRC of Clapp & Hornberger (1978)
  PSI_A2    = ..\maps01\HAP100_07MAY2012.map		;
#
  THETASAT1 = ..\maps01\THS30_07MAY2012.map		;			#   m3.m-3	saturated volumetric moisture content (m3.m-3)
  THETASAT2 = ..\maps01\THS100_07MAY2012.map		;
#
  THETARES1 = ..\maps01\THR30_07MAY2012.map		;	        	#   m3.m-3	 residual volumetric moisture content (m3.m-3)
  THETARES2 = ..\maps01\THR100_07MAY2012.map		;
#
  Z1_inp    = ..\maps01\Z1__030_07MAY2012.edwin.map	;			#   m		soil thickness (m)
  Z2_inp    = ..\maps01\Z1__030_07MAY2012.edwin.map	;
  Z2_modSED = $18					;
  Z2_modMON = $19					;
  Z1_out    = results\Z1used.map			;
  Z2_out    = results\Z2used.map			;
#
  SC1       = results\SC1_used.map			;			#   m		storage per layer (m): SC = Z * (THETASAT - THETARES)
  SC2       = results\SC2_used.map			;			# 		calculated based on thickness and theta
#
# P2_IMP    = 				 scalar( 1.0)	;                       #   -		fraction area where percolation to groundwater store is impeded 			#     USED
  P2_IMP    = results\P2_IMP.map			;
#
# IMP_LDCOV = ..\maps01\impermeable_area3000cs.map	; 			#   -		boolean map indicating impermeable areas: URBAN and GLACIER ICE (and water bodies, FRACWAT eq 1)
  IMP_LDCOV = boolean(0)					;
#
  ROOTDEPTH = ..\maps01\rootdepth_2may2011.map		;			#   m		estimated root depths (based on Rens)
  RFW1	    = results\rootlyr01_2may2011.map		;			#   -		estimated root fractions
  RFW2      = results\rootlyr02_2may2011.map		;			#   -		first and second layer
#
# WMIN_INP  = 						;			#   m												# not USED
# WMIN_INP  = scalar(0)					;			#   m		WMIN = 0 because we assume that every 30 arc-second cell contain a stream	# not USED
  WMIN_SED  = $15					;			#   - 		fraction of  WMAX  to modify WMIN values in sedimentary basins
  WMIN_MON  = $16					;			#   - 		fraction of  WMAX  to modify WMIN values in mountainous areas
  WMIN_OUT  = results\WMIN_USED.map			;			#   m		WMIN values for the Improved Arno Scheme					# 
#
  B_ORO     =  ..\maps01\b_oro_v2_012009_nc1109_3000cs.map;			#   -		shape coefficient related to orography
# B_FRA_INP =  ..\maps01\arno_coef_b.map			;			#   -		shape coefficient related to variabilities of soil water capacities		# not USED
  B_FRA_INP =  scalar(0)				;			#
  BCF       =  results\bcf.map				;			#   -		final b coefficient in the Improved Arno Scheme
#
  PSI_FC    = scalar(1.00);			    				#   m		matric suction at field capacity
  PSI_50    = scalar(3.33);			    				#   m		matric suction at which transpiration is halved
  BCH_ADD   = scalar(3.00);			    				#   -		addition for kr-relationship of Clapp & Hornberger (1978; default 3)
#
# Water consumptions/abstractions (m3/day) from surface water and groundwater
#
  POTABSTR_S0 = scalar(0);	 						#   m3/day	from surface water
  POTABSTR_S3 = scalar(0);	    						#   m3/day	from   groundwater
#
# LAKES (only for big/large ones)
#================================================================================================================================================================================================
# LAK_BOTTOM     = 						;		#  +m		assumption for lake bottom elevation # NOT USED, we assume deep lakes always containing water.
  LAK_SILLEL     =   ..\maps01\lake_08Jul2011_nc1109.wle.map	;		#  +m		assumption for lake   sill elevation = estimated water level from HYDROSHEDS
  LAK__INLET_ID  =   ..\maps01\lake_24Mar2011_nc1109.inlet.map	;		#   -		boolean map for lake  inlet locations 		# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  LAK_OUTLET_ID  =   ..\maps01\lake_24Mar2011_nc1109.outlt.map	;		#   -		boolean map for lake outlet locations 		# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  LAK_NUMIDSinp  =   ..\maps01\lake_24Mar2011_nc1109.ids.map	;		#   -		ids for lakes
  LAK_UP_IDSnom  =   ..\maps01\lake_24Mar2011_nc1109.cat.map	;		#   -		ids for streams located upstream the lakes	# FRACWAT ne 1
  LAK_SHORES     =   ..\maps01\lake_24Mar2011_nc1109.shr.map	;		#   -		boolean map for lakeshores			# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  CLAKE          =   scalar(1)					;		#   -		constant for lake discharge
#
  TCL       	=    results\TCL.map				;		# day-1		time centroid lag    (for interflow generation)
  TCL_FAC_sed	=    $20					;
  TCL_FAC_mon	=    $21					;
#
# river/channel properties
#================================================================================================================================================================================================
  RIVbedresi_inp =      scalar(1.0000)				;               #  day		bed resistance values
  RIVmanning 	 =      scalar(0.0450)				;		# [m**(1/3)]/s	river manning coeffients
  RIV__WIDTH_inp =   ..\maps01\riv_width_30july_2011.map		;		#  m		river width			(only defined in some cells)
  RIV__SLOPE_inp =   ..\maps01\riv_slope_30july_2011.map		;		#  m/m		river longitudinal slope	(only defined in some cells)
  RIV_BOTTOM_inp =   ..\maps01\rivbottom_30july_2011.map		;		#  m		bed elevation 			(only defined in some cells)
  RIV_DEPTH__inp =   ..\maps01\riv_depth_30july_2011.map		;		#  m		river depth (bankfull)		(     defined in alle cells) 
  RIV_BOTTOM_out =   results\rivbott_allcells.map		;		#  m		drain bed elevation		(     defined in alle cells)
#
# aquifer properties
#=================================================================================================================================================================================================
  aquifer_map    =   ..\maps01\aquifer_28JULY2011.map		;		#  m		aquifer classification map	Note: #1 for productive aquifer
  aquifthick	 =      scalar(50.000)				;               #  m		aquifer thickness
  log_Pm_inp     =   ..\maps01\mean_logP_06MAR2012.map		;		#  		mean of log permeability			(Gleeson et al., 2011)
# log_Pstdev     =   						;		#  		standard deviation of log permeability		(Gleeson et al., 2011)			# not USED
# log_Pm_add     =     						;		#  		additional values to modify permeability	 			range = [-2,2]	
  log_Pm_add_sed =     $13					;		#  		additional values to modify permeability of the sedimentary basin 	range = [-2,2]	
  log_Pm_add_mon =     $14					;		#  		additional values to modify permeability of the mountainous areas 	range = [-2,2]	
  g__gravity     =     scalar( 9.81)				;		#  m2/s		gravity acceleration 
  rho__water     =     scalar( 1000)				;		#  kg/m3	water density 
  miu__water     =     scalar(0.001)				;		#  Ns/m2	water dynamic viscosity
  spe_yi_inp   	 =   ..\maps01\stocospeyi06MAR2012.map		;		#  - 		storage coefficient (actual values)
#
  h_cond_aqu   	 =   results\hcond.map				;		#  m/day	aquifer (horizontal) conductivity
  KD_aquifer	 =   results\KD_aquifer.map			;		#  m2/day	aquifer transmissivity for modflow input
  h_cond_KQ3_inp =   results\hcKQ3.map				;		#  m/day	aquifer (horizontal) conductivity for KQ3 (higher)
  KQ3            =   results\KQ3.map				;		#  day-1	linear recession coefficient for groundwater (store 3)
#
# ANI_input      =   						;		#  -		ANI input maps 
  ANI_input      =   scalar(0.651486)				;		# 
#
# Gauging stations
#====================================================================================================================================================================================================
  STATIONS_DS   =    ..\maps01\dischstats.22JUL2011.map			;	# 		IDs of gauging stations (discharge)
  STATIONS_HD   =    ..\maps01\head_stat.22JUL2011.ids.map		;	# 		IDs of head stations    (33393 pixels chosen, see logbook 24 March 2010)
  CLIMSTAT      =    ..\maps01\id_30min_nc1109_3000cs_center_new.map	;	# 		IDs of locations to monitor soil (center of each 30 arc-min cell)
  CLIMSTAT_10m  =    ..\maps01\id_10min_nc1109_3000cs.center.NEW.map	;	# 		IDs of locations to monitor soil (center of each 10 arc-min cell)
  STATIONS_LK   =    results\lake_outlet.sta.ids.map		 	;	# 		IDs of locations to monitor lake outflows and lake heads
  ST_ERS_SWI	=    ..\maps01\ers_ids_3000cs.map				;	# 		IDs of center points of ERS SWI pixels
#
  ID_10mincell  =    ..\maps01\id_10min_nc1109_3000cs.NEW.map		;       # 		ID of every 10 min cell							 	# NEW IDS defined by EH Sutanudjaja
  ID_30mincell  =    ..\maps01\id_30min_nc1109_3000cs_clids__new.map	;       # 		ID of every 30 min cell							 	# NEW IDS defined by EH Sutanudjaja
# ID_ERA40      =    ..\maps01\id_30min_nc1109_3000cs_clids__new.map	;       # 		ID of the ERA40 cell in half degree resolution (resampled by Rens van Beek) 	# NEW IDS defined by EH Sutanudjaja
# ID_ERS_SWI	=    ..\maps01\						;       # 		ID of the ERS SWI
#
#
#=====================================================================================================================================================================================================
# F O R C I N G  (climatic input)						Note: Daily values will be supplied in TSS files
# ETP, TMP and PREC forcing data:
#=====================================================================================================================================================================================================
#
# Reference Potential Evaporation:
#===============================================================================
  EP0_FORCE_M    	= $1	;	              				#  -		Monthly reference potential evaporation [m/day]
#
# Temperature:
#===============================================================================
  T_CRU21_M 		= $2	;	                     			#  -		CRU TS-2.1 monthly temperature      [10* deg C]	BE CAREFUL WITH THE UNIT !!!!!
  T_ECMWF_M 		= $3	;                             			#  -		ERA40 / OA monthly temperature          [deg C]
  T_ECMWF_D 		= $4.tss;                              			#  -		ERA40 / OA   daily temperature          [deg C]	TSS FILES !!!!!
#
#-Precipitation (rainfall + snow):
#===============================================================================
  P_CRU21_M 		= $5	;	                     			#  -		CRU TS-2.1 monthly precipitation [10* mm/month]	BE CAREFUL WITH THE UNIT !!!!!
  P_ECMWF_M 		= $6	;                              			#  -		ERA40 / OA monthly precipitation      [m/month]     ../month = TOTAL (not average)
  P_ECMWF_D 		= $7.tss;                              			#  -		ERA40 / OA   daily precipitation      [m/day  ]	TSS FILES !!!!!
#
# CRU CL 2.0 (1961-1990)
#===============================================================================
  P_CRUCL_M  		= ..\maps01\CRU_CL20\PRE_12month_$8\precrucl	;	#  -		CRU CL-2.0 monthly precipitation     [mm/month]	10 arc-min resolution (for downscaling purpose)
  P_CRUCL_30s_input	= ..\maps01\CRU_CL20\PRE_12month_30sec_$8\precr30s;	#  -		CRU CL-2.0 monthly precipitation     [mm/month]	30 arc-sec resolution (for downscaling purpose)
  T_CRUCL_M  		= ..\maps01\CRU_CL20\TMP_12month_$8\tmpcrucl	;	#  -		CRU CL-2.0 monthly temperature          [deg C]	10 arc-min resolution (for downscaling purpose)
#
#
# UNIT HYDROGRAPH ROUTING:
#================================================
  min00_inp  	= ..\maps01\min00.map;
  min01_inp  	= ..\maps01\min01.map;
  min02_inp  	= ..\maps01\min02.map;
  min03_inp  	= ..\maps01\min03.map;
  min04_inp  	= ..\maps01\min04.map;
  min05_inp  	= ..\maps01\min05.map;
  min06_inp  	= ..\maps01\min06.map;
  min07_inp  	= ..\maps01\min07.map;
  min08_inp  	= ..\maps01\min08.map;
  min09_inp  	= ..\maps01\min09.map;
  min10_inp  	= ..\maps01\min10.map;
  min11_inp  	= ..\maps01\min11.map;
  min12_inp  	= ..\maps01\min12.map;
  min13_inp  	= ..\maps01\min13.map;
  min14_inp  	= ..\maps01\min14.map;
  min15_inp  	= ..\maps01\min15.map;
#
#===========================================================================================================

# initial storages for local variables:
#
   SW_INI  	= initials\sw_00000.ini;	# initial surface water storage (only for BIG LAKES)	(m) ...	can be negative
   SC_INI  	= initials\sc_00000.ini;	# initial snow cover 					(m)
  SCF_INI  	= initials\scf_0000.ini;	# initial liquid water stored in snow cover  		(m)
 INTS_INI  	= initials\ints_000.ini;	# initial interception storage 				(m)
   S1_INI  	= initials\s1_00000.ini;	# initial storage in upper store 			(m)
   S2_INI  	= initials\s2_00000.ini;	# initial storage in second store 			(m)
   Q2_INI  	= initials\q2_00000.ini;	# initial drainage from second store 			(m)
S3_MD_INI  	= initials\stor3_md.ini;	# initial storage in modflow groundwater store 		(m) ...	can be negative

# initizalization for MODFLOW model:
#
  gw_head_INI      = initials\headinit.ini;           				# +m       initial groundwater head
  rivhead_INI  	   = initials\rivhinit.ini;           				# (m)      initial river head (for the RIVER package)
# CRFRAC_RIV_INI   = initials\crfracrv.ini;					# (-)	   fractions of saturated/flooded areas based on surface water levels
  lake_hd_INI      = initials\lkhdinit.ini;	# elevation			# (m)      initial lakehead (from the previous time step)
# gw_rech_INI      = initials\rechinit.ini;     # NOT NEEDED      				# (m/day)  initial recharge (from the previous time step)
  gw_baseflow_INI  = initials\bsflinit.ini;                                     # (m3/day) initial baseflow (from the previous time step)

# initizalization for routing (UNIT HYDROGRAPH METHOD):
#
  QCmin01_INI  = initials\QC_min01.ini;
  QCmin02_INI  = initials\QC_min02.ini;
  QCmin03_INI  = initials\QC_min03.ini;
  QCmin04_INI  = initials\QC_min04.ini;
  QCmin05_INI  = initials\QC_min05.ini;
  QCmin06_INI  = initials\QC_min06.ini;
  QCmin07_INI  = initials\QC_min07.ini;
  QCmin08_INI  = initials\QC_min08.ini;
  QCmin09_INI  = initials\QC_min09.ini;
  QCmin10_INI  = initials\QC_min10.ini;
  QCmin11_INI  = initials\QC_min11.ini;
  QCmin12_INI  = initials\QC_min12.ini;
  QCmin13_INI  = initials\QC_min13.ini;
  QCmin14_INI  = initials\QC_min14.ini;
  QCmin15_INI  = initials\QC_min15.ini;
#                           
  QCmin01_BS_INI = initials\Qmin01BS.ini;
  QCmin02_BS_INI = initials\Qmin02BS.ini;
  QCmin03_BS_INI = initials\Qmin03BS.ini;
  QCmin04_BS_INI = initials\Qmin04BS.ini;
  QCmin05_BS_INI = initials\Qmin05BS.ini;
  QCmin06_BS_INI = initials\Qmin06BS.ini;
  QCmin07_BS_INI = initials\Qmin07BS.ini;
  QCmin08_BS_INI = initials\Qmin08BS.ini;
  QCmin09_BS_INI = initials\Qmin09BS.ini;
  QCmin10_BS_INI = initials\Qmin10BS.ini;
  QCmin11_BS_INI = initials\Qmin11BS.ini;
  QCmin12_BS_INI = initials\Qmin12BS.ini;
  QCmin13_BS_INI = initials\Qmin13BS.ini;
  QCmin14_BS_INI = initials\Qmin14BS.ini;
  QCmin15_BS_INI = initials\Qmin15BS.ini;
#
  rhmin01_INI  = initials\rh_min01.ini ;
  rhmin02_INI  = initials\rh_min02.ini ;
  rhmin03_INI  = initials\rh_min03.ini ;
  rhmin04_INI  = initials\rh_min04.ini ;
  rhmin05_INI  = initials\rh_min05.ini ;
  rhmin06_INI  = initials\rh_min06.ini ;
  rhmin07_INI  = initials\rh_min07.ini ;
  rhmin08_INI  = initials\rh_min08.ini ;
  rhmin09_INI  = initials\rh_min09.ini ;
  rhmin10_INI  = initials\rh_min10.ini ;
  rhmin11_INI  = initials\rh_min11.ini ;
  rhmin12_INI  = initials\rh_min12.ini ;
  rhmin13_INI  = initials\rh_min13.ini ;
  rhmin14_INI  = initials\rh_min14.ini ;
  rhmin15_INI  = initials\rh_min15.ini ;
  rhmin16_INI  = initials\rh_min16.ini ;
  rhmin17_INI  = initials\rh_min17.ini ;
  rhmin18_INI  = initials\rh_min18.ini ;
  rhmin19_INI  = initials\rh_min19.ini ;
  rhmin20_INI  = initials\rh_min20.ini ;
  rhmin21_INI  = initials\rh_min21.ini ;
  rhmin22_INI  = initials\rh_min22.ini ;
  rhmin23_INI  = initials\rh_min23.ini ;
  rhmin24_INI  = initials\rh_min24.ini ;
  rhmin25_INI  = initials\rh_min25.ini ;
  rhmin26_INI  = initials\rh_min26.ini ;
  rhmin27_INI  = initials\rh_min27.ini ;
  rhmin28_INI  = initials\rh_min28.ini ;
  rhmin29_INI  = initials\rh_min29.ini ;
  rhmin30_INI  = initials\rh_min30.ini ;

#===========================================================================================================
#
#
# Maps & TSS - output
#
 SC       	= results\snowcov;						# (m) snow cover
 SC_L     	= results\sc_;							#     idem, local value
 SCTSS    	= results\snowtot.tss;						# (m) total snow storage in equivalent water height, timeseries
 SCF      	= results\snowliq;						# (m) liquid water stored in snow cover
 SCF_L    	= results\scf_;							#     idem, local value
#
 SW		= results\sw_0;							# (m) surface water storage, but only for big lakes
#
 INTS     	= results\intstor;						# (m) interception storage
 INTS_L         = results\ints_;						#     idem, local value
 INTSTSS      	= results\ints.tss;						#     as above, timeseries
 INTSFLUX     	= results\intflux;                    				# (m) interception flux						# NOT REPORTED
 INTSFLUXTSS  	= results\ints.tss;						#     as above, timeseries
#
 ETPOT    	= results\etpot; 	# (m) total potential evapotranspiration = soil evap + interception + transpiration + waterbody evap 	# NOT REPORTED
 EFRAC          = results\efrac;	# (-) fraction of actual over potential evapotranspiration						# NOT REPORTED
 EACT     	= results\eact;		# (m) total actual evapotranspiration at land surface
 EACTTSS  	= results\eact.tss;	#     as above, timeseries
 EWAT           = results\ewat;		# (m) total actual evaporation at water bodies								# NOT REPORTED
 EWATTSS        = results\ewat.tss;	#     as above, timeseries
 EACTFLUX       = results\eact_all;	# (m) total actual evapotranspiration (at land surface + water body cells)				# NOT REPORTED
 EACTFLUXTSS    = results\eact_all.tss;	#     as above, timeseries
#
 ESPOT          = results\espot;	# (m) potential energy for soil evaporation								# NOT REPORTED
 ESACT    	= results\esact;	# (m) idem, actual											# NOT REPORTED
 ESACTTSS       = results\esact.tss;	#     as above, timeseries
#
 T1POT    	= results\t1pot;	# (m) potential transpiration drawn from first soil layer						# NOT REPORTED
 T1ACT    	= results\t1act;	#     idem, actual											# NOT REPORTED
 T1ACTTSS	= results\t1act.tss;	#     as above, timeseries
#
 T2POT    	= results\t2pot;	# (m) potential transpiration drawn from second soil layer						# NOT REPORTED
 T2ACT    	= results\t2act;	#     idem, actual											# NOT REPORTED
 T2ACTTSS	= results\t2act.tss;	#     as above, timeseries
#
 SATFRAC  	= results\satf;		# (-) fraction saturated area										# NOT REPORTED
 SATFRACTSS     = results\satf.tss;	#     as above, timeseries
 WACT     	= results\wact;		# (m) actual water storage within root zone 								# NOT REPORTED
 WACTTSS     	= results\wact.tss;	#     as above, timeseries
#
 Q1       	= results\q1x;		# (m) direct runoff
 Q1TSS    	= results\q1.tss;	#     idem, timeseries
 Q1d_chn	= results\q1dchn;	# (m) precipitation falling in a channel
 Q1S      	= results\q1s;		# (m) direct runoff attributable to snow melt
 Q1STSS   	= results\q1snow.tss;	#     idem, timeseries
 Q2       	= results\q2x;		# (m) runoff from second store (interflow)
 Q2_L     	= results\q2_;		#     idem, local value											# NOT REPORTED
 Q2TSS    	= results\q2.tss;	#     idem, timeseries
#
 gw_baseflow	= results\\bsfl;	# (m3/day) Groundwater baseflow from RIV + DRN package (positive entering the aquifer)			# ONLY END REPORT (MUST)
 gw_base_mpd	= results\\bsfl_mpd;	# (m1/day) Groundwater baseflow from RIV + DRN package (positive entering the aquifer)											
#
 Q3MOD       	= results\q3xmod;	# (m) runoff from 3rd store (baseflow) from MODFLOW
 Q3MODTSS    	= results\q3xmod.tss;	#     idem, timeseries
					#     Q3MOD = QRIV / cellarea  (m/day)	# NOTE: The original baseflow from MODFLOW (QRIV) have unit : m3/day.
										# Latter, this Q3MOD (m/day) will be multipied by again by cell area.
#
 QLOC          = results\qloc;		# (m) specific runoff, QLOC = Q1+Q2+Q3 (Q3 from MODFLOW) and QW
#
 S1            = results\stor1x;	# (m) storage in upper store
 S1_L          = results\s1_;		#     idem, local value
 S1TSS         = results\stor1.tss;	#     as above, timeseries
#
 S2            = results\stor2x;	# (m) storage in second store
 S2_L          = results\s2_;		#     idem, local value
 S2TSS         = results\stor2.tss;	#     as above, timeseries
#
 S1TSS_30min   = results\stor1_30m.tss; # (%) degree of saturation (from zero to saturated) = S1/SC1 in 30 arc-min resolution
 S2TSS_30min   = results\stor2_30m.tss; # (%) degree of saturation (from zero to saturated) = S2/SC2 in 30 arc-min resolution
 STTSS_30min   = results\sto12_30m.tss; # (%) degree of saturation (from zero to saturated) = average S1/SC1 and S2/SC1 in 30 arc-min resolution
#
 S1TSS_30m_sd  = results\stor1_30m_sed.tss; # only from sedimentary areas
 S1TSS_30m_mn  = results\stor1_30m_mon.tss; # only from mountainous areas
 S2TSS_30m_sd  = results\stor2_30m_sed.tss; # only from sedimentary areas
 S2TSS_30m_mn  = results\stor2_30m_mon.tss; # only from mountainous areas
 STTSS_30m_sd  = results\sto12_30m_sed.tss; # only from sedimentary areas
 STTSS_30m_mn  = results\sto12_30m_mon.tss; # only from mountainous areas
#
 S1TSS_FC_WP_30min = results\stor1_30m_FC_WP.tss; # (%) as above, but from wilting point to field capacity
 S2TSS_FC_WP_30min = results\stor2_30m_FC_WP.tss; # (%)
 STTSS_FC_WP_30min = results\sto12_30m_FC_WP.tss; # (%)
#
 S1TSS_30m_wa20       = results\stor1_30m_wa20.tss		;
 S2TSS_30m_wa20       = results\stor2_30m_wa20.tss		;
 STTSS_30m_wa20       = results\sto12_30m_wa20.tss		;
#
 S1TSS_FC_WP_30m_wa20 = results\stor1_30m_wa20_FC_WP.tss	;
 S2TSS_FC_WP_30m_wa20 = results\stor2_30m_wa20_FC_WP.tss	;
 STTSS_FC_WP_30m_wa20 = results\sto12_30m_wa20_FC_WP.tss	;
#
 S1TSS_30m_wa25       = results\stor1_30m_wa25.tss		;
 S2TSS_30m_wa25       = results\stor2_30m_wa25.tss		;
 STTSS_30m_wa25       = results\sto12_30m_wa25.tss		;
#
 S1TSS_FC_WP_30m_wa25 = results\stor1_30m_wa25_FC_WP.tss	;
 S2TSS_FC_WP_30m_wa25 = results\stor2_30m_wa25_FC_WP.tss	;
 STTSS_FC_WP_30m_wa25 = results\sto12_30m_wa25_FC_WP.tss	;
#
 S1TSS_30m_wa35       = results\stor1_30m_wa35.tss		;
 S2TSS_30m_wa35       = results\stor2_30m_wa35.tss		;
 STTSS_30m_wa35       = results\sto12_30m_wa35.tss		;
#
 S1TSS_FC_WP_30m_wa35 = results\stor1_30m_wa35_FC_WP.tss	;
 S2TSS_FC_WP_30m_wa35 = results\stor2_30m_wa35_FC_WP.tss	;
 STTSS_FC_WP_30m_wa35 = results\sto12_30m_wa35_FC_WP.tss	;
#
 S1TSS_30m_wa50       = results\stor1_30m_wa50.tss		;
 S2TSS_30m_wa50       = results\stor2_30m_wa50.tss		;
 STTSS_30m_wa50       = results\sto12_30m_wa50.tss		;
#
 S1TSS_FC_WP_30m_wa50 = results\stor1_30m_wa50_FC_WP.tss	;
 S2TSS_FC_WP_30m_wa50 = results\stor2_30m_wa50_FC_WP.tss	;
 STTSS_FC_WP_30m_wa50 = results\sto12_30m_wa50_FC_WP.tss	;
#
 S1TSS_30m_wa70       = results\stor1_30m_wa70.tss		;
 S2TSS_30m_wa70       = results\stor2_30m_wa70.tss		;
 STTSS_30m_wa70       = results\sto12_30m_wa70.tss		;
#
 S1TSS_FC_WP_30m_wa70 = results\stor1_30m_wa70_FC_WP.tss	;
 S2TSS_FC_WP_30m_wa70 = results\stor2_30m_wa70_FC_WP.tss	;
 STTSS_FC_WP_30m_wa70 = results\sto12_30m_wa70_FC_WP.tss	;
#
 S3_MD          = results\stor3xmd;						# (m) storage in modflow gw store -- VERYHIGH CANNOT BE 0
 S3_MDTSS       = results\stor3xmd.tss; 					#     as above, timeseries
 S3FPL		= results\stor3fpl;						# (m) groundwater storage above the flood plain elevation
 S3_DEFICIT	= results\s3_defi ;						# (m) river deficit because of infiltration to gw bodies
#
 P1TSS		= results\P1.tss      ;
 CR1TSS         = results\CR1.tss     ;
 CR1_ADD        = results\CR1_ADD     ;	# (m) Do we have additional CR1? (because of excess of S2)	# should be close to zero
 CR1_ADDTSS     = results\CR1_ADD.tss ;	# (m) Do we have additional CR1? (because of excess of S2)	# should be close to zero
  Q1_ADD        = results\Q1__ADD     ;	# (m) Do we have additional CR1? (because of excess of S2)	# should be close to zero
  Q1_ADDTSS     = results\Q1__ADD.tss ;	# (m) Do we have additional CR1? (because of excess of S2)	# should be close to zero
 P2TSS		= results\P2.tss      ;
 CR2map		= results\CR2map      ; 	
 CR2TSS         = results\CR2.tss     ;
 CR2_POT	= results\CR2POT      ;	
#
 R3       	= results\r3x      ;	# (m/day) recharge to third store
 R3TSS		= results\r3.tss   ;	#         time series
 R3AVG          = results\r3avg.map;	# (m/day) average yearly recharge
#			   	
 CRFRAC_RIV     = results\crfracrv ; 	
 CRFRAC_used    = results\crfrac   ;
 DZS3           = results\dzs3 	   ;
 ADDQ3		= results\r3add    ;	# (m/day) additional (negative) recharge that will be routed to the river
 ADDQ3TSS	= results\r3add.tss;	# 	  time series
#
 QW       	= results\qw;		# (m) change in storage of freshwater surface								#      NOT REPORTED
#
 QCHANNELWR_ALL = results\qc_wr       ;	# (m3/s) channel discharge - daily 	# without routing
 QCHANNELWR_TSS = results\qc_wr.tss   ;	#        timeseries 			# without routing
#
 QCHQ1___WR_ALL = results\qc_wrQ1     ;	# (m3/s)                                # without routing
 QCHQ1___WR_TSS = results\qc_wrQ1.tss ;	# (m3/s) timeseries		 	# without routing
#
 QCHQ1ADDWR_ALL = results\qc_wrQ1a    ;	# (m3/s)				# without routing
 QCHQ1ADDWR_TSS = results\qc_wrQ1a.tss;	# (m3/s) timeseries			# without routing
#
 QCHQ2___WR_ALL = results\qc_wrQ2     ;	# (m3/s)				# without routing
 QCHQ2___WR_TSS = results\qc_wrQ2.tss ;	# (m3/s) timeseries			# without routing
#
 QCHQ3MODWR_ALL = results\qc_wrQ3     ;	# (m3/s)				# without routing
 QCHQ3MODWR_TSS = results\qc_wrQ3.tss ;	# (m3/s) timeseries			# without routing
#
 QCHADDQ3WR_ALL = results\qc_wrQ3a    ;	# (m3/s)				# without routing
 QCHADDQ3WR_TSS = results\qc_wrQ3a.tss;	# (m3/s) timeseries			# without routing
#
 QCHQW___WR_ALL = results\qc_wrQW     ;	# (m3/s)				# without routing
 QCHQW___WR_TSS = results\qc_wrQW.tss ;	# (m3/s) timeseries			# without routing
#
 QCHANNEL    	= results\qc;		# (m3/s) channel discharge - daily 	#   after routing (baseflow from MODFLOW)
 QCHANNELTSS 	= results\qchannel.tss; #        timeseries
#
 gw_head	= results\gw_headd    ;	# (m) 					groundwater head - daily   					# from MODFLOW
 gw_head_TSS	= results\gw_headd.tss;	#        				    as above, timeseries
#
 gw_head_DEM    = results\gw_hddem    ; #					groundwater head relative to DEM = gw_head - DEM		# PURPOSE: to ease the analysis
#
 lake_hd	= results\lk_headd    ;	# (m)        				lake  waterlevel - daily					# ONLY END REPORT
 lake_hd_TSS	= results\lk_headd.tss;	#        				    as above, timeseries
#
 rivhead        = results\rivheadd    ; # (m)				        river waterlevel - daily 					# ONLY END REPORT
 rivhead_TSS    = results\rivheadd.tss; #					    as above, timeseries
#
 QLAKEOUTALL    = results\lk_outfd    ;	# (m3/s or m3/day or m/day) 		lake   discharge - daily					# NOT REPORTED
 QLAKEOUTTSS    = results\lk_outfd.tss;	# 					    as above, timeseries
#
#
# ==============================================================================
# catchment storage (tss files)
#
 INTS_BAS	= results\INTS_BAS.tss;
 SC___BAS	= results\SC___BAS.tss;
 SCF__BAS	= results\SCF__BAS.tss;
 S1___BAS	= results\S1___BAS.tss;
 S2___BAS	= results\S2___BAS.tss;
 S3_MDBAS	= results\S3_MDBAS.tss;
 SW___BAS	= results\SW___BAS.tss;
 TOTALSBS	= results\TOTALSBS.tss;
#
#
# ==============================================================================
# for reporting WEEKLY  average values
#
 week_Duration 	= ..\maps01\week_duration$8.tss	;      				# (days)    	number of days in each week
#										#		------ STILL NOT BEING USED					
#
# ==============================================================================
# for reporting MONTHLY average values
#
 monthDuration 	= ..\maps01\monthduration$8.tss	;      				# (days)    	number of days in each month
#			   
 TA_month       = results\TA_month		;
 ETPmonth       = results\ETPmonth		;
 PRPTOTmn       = results\PRPTOTmn		;
 EACTFLmn       = results\EACTFLmn		;
 INFL__mn       = results\INFL__mn		;
 SNOW__mn       = results\SNOW__mn		;
 PRP___mn       = results\PRP___mn		;
 Q1month        = results\Q1month		;
 QSmonth        = results\QSmonth		;
 Q1_ADDmn       = results\Q1_ADDmn		;
 Q2month        = results\Q2month		;
 Q3month        = results\Q3month		;
 Q3_ADDmn       = results\Q3_ADDmn		;
 QWmonth        = results\QWmonth		;
 QLmonth        = results\QLmonth		;
 ESa___mn       = results\ESa___mn		;
 ESas__mn       = results\ESas__mn		;
 T1ACT_mn       = results\T1ACT_mn		;
 T2ACT_mn       = results\T2ACT_mn		;
 R2month        = results\R2month		;
 R3month        = results\R3month		;
 P0month        = results\P0month		;
 P1month        = results\P1month		;
 P2month        = results\P2month		;
 CR1__mn        = results\CR1__mn		;
 CR2__mn        = results\CR2__mn		;
 CR1_ADDm       = results\CR1_ADDm		;
#
 Qmonth     	= results\qmonthch		;				# (m3/sec)    	channel discharge - monthly (average) values
 QmonthTSS  	= results\qmonthch.tss		;				# 	    	as above, timeseries
#
# budget check included here
 PTOTTSS  	= results\ptot.tss		;				# (km3) 	total cumulative rainfall and initial accumulated storage
 ETOT     	= results\etot.map		;				# (m)   	total cumulative actual "evapotranspiration" (m)
 ETOTTSS  	= results\etot.tss		;				# (km3) 	idem, as timeseries
 QTOTTSS  	= results\qtot.tss		;				# (km3) 	total cumulative discharge
 STOTTSS  	= results\stot.tss		;				# (km3) 	total accumulated storage
 STOT_ACT 	= results\stot.map		;				# (km3) 	total active storage
 MBE      	= results\mbe			;				# (m)   	absolute local mass balance error
 MBR      	= results\mbcheck		;				# (-)   	relative, local mass balance error
 MBRTSS   	= results\mbcheck.tss		;		  		# (-)   	idem, as time series
#
# maximum and minimum water balance error
  maxwberror    = results\maxabse.map;              	# (m) maximum and minimum water balance error
  minwberror    = results\minabse.map;              	#     for the entire year cycle
  maxINerror    = results\maxaINe.map;
  minINerror    = results\minaINe.map;
  maxSCerror    = results\maxaSCe.map;
  minSCerror    = results\minaSCe.map;
  maxSFerror    = results\maxaSFe.map;
  minSFerror    = results\minaSFe.map;
  maxS1error    = results\maxaS1e.map;
  minS1error    = results\minaS1e.map;
  maxS2error    = results\maxaS2e.map;
  minS2error    = results\minaS2e.map;

# reporting at the end of timestep:
#
  QCmin01  = results\QC_min01 ; QCmin06  = results\QC_min06 ; QCmin11  = results\QC_min11 ;
  QCmin02  = results\QC_min02 ; QCmin07  = results\QC_min07 ; QCmin12  = results\QC_min12 ;
  QCmin03  = results\QC_min03 ; QCmin08  = results\QC_min08 ; QCmin13  = results\QC_min13 ;
  QCmin04  = results\QC_min04 ; QCmin09  = results\QC_min09 ; QCmin14  = results\QC_min14 ;
  QCmin05  = results\QC_min05 ; QCmin10  = results\QC_min10 ; QCmin15  = results\QC_min15 ;
#
  rhmin01  = results\rh_min01 ;     rhmin16  = results\rh_min16 ;
  rhmin02  = results\rh_min02 ;     rhmin17  = results\rh_min17 ;
  rhmin03  = results\rh_min03 ;     rhmin18  = results\rh_min18 ;
  rhmin04  = results\rh_min04 ;     rhmin19  = results\rh_min19 ;
  rhmin05  = results\rh_min05 ;     rhmin20  = results\rh_min20 ;
  rhmin06  = results\rh_min06 ;     rhmin21  = results\rh_min21 ;
  rhmin07  = results\rh_min07 ;     rhmin22  = results\rh_min22 ;
  rhmin08  = results\rh_min08 ;     rhmin23  = results\rh_min23 ;
  rhmin09  = results\rh_min09 ;     rhmin24  = results\rh_min24 ;
  rhmin10  = results\rh_min10 ;     rhmin25  = results\rh_min25 ;
  rhmin11  = results\rh_min11 ;     rhmin26  = results\rh_min26 ;
  rhmin12  = results\rh_min12 ;     rhmin27  = results\rh_min27 ;
  rhmin13  = results\rh_min13 ;     rhmin28  = results\rh_min28 ;
  rhmin14  = results\rh_min14 ;     rhmin29  = results\rh_min29 ;
  rhmin15  = results\rh_min15 ;     rhmin30  = results\rh_min30 ;
#
  basel_disch     = ..\00_FORCING\BASEL_DISCHARGE\base$22.tss	;
  QCHactBS_RT_TSS = results\QCHactBS_RT_TSS.tss;
#                      
  QCmin15_BS = results\Qmin15BS;
  QCmin14_BS = results\Qmin14BS;
  QCmin13_BS = results\Qmin13BS;
  QCmin12_BS = results\Qmin12BS;
  QCmin11_BS = results\Qmin11BS;
  QCmin10_BS = results\Qmin10BS;
  QCmin09_BS = results\Qmin09BS;
  QCmin08_BS = results\Qmin08BS;
  QCmin07_BS = results\Qmin07BS;
  QCmin06_BS = results\Qmin06BS;
  QCmin05_BS = results\Qmin05BS;
  QCmin04_BS = results\Qmin04BS;
  QCmin03_BS = results\Qmin03BS;
  QCmin02_BS = results\Qmin02BS;
  QCmin01_BS = results\Qmin01BS;


areamap
 LANDMASK;

timer
 1 $8 1;                                    						#  starting step, end step, daily time step
#1  3 1;                                    						#  starting step, end step, daily time step
#1  1 1;                                    						#  starting step, end step, daily time step
#rep_y =  $8;					    					#  yearly report, end report, for time series
 rep_y = $17;	# alternative timely report (e.g. daily to check states & fluxes)  
 rep_m =  $9;				    						# monthly report
 rep_w = $10;				    						#  weekly report
 rep_r = 1,5,10,100,300,$8;								#  random report (for budget checking)

initial

# G E N E R A L
#=============================================================================================================================================================
#
  DEM30s      = if(LANDMASK,DEM30s_inp)					;	# +m	DEM 30 arc-second     # alternative: DEM30s = if(LANDMASK,DEM30s_inp)
  DEM10min    = areaaverage(DEM30s, nominal(ID_10mincell))		;      	# 	DEM 10 minutes (upscaled from DEM 30 seconds)
# DEMERA40    = areaaverage(DEM30s, nominal(ID_ERA40))			;      	# 	DEM ERA40

# report Z0_floodplain 	        =  cover(WLESMOOTH, MIN_DEM3s, DEM30s)	     								; 	# +m	flood plain elevation
# report Z0_floodplain          =  cover(cover(WLESMOOTH, min(Z0_fldpln_inp,DEM30s)), MIN_DEM3s, DEM30s)				;	# +m	flood plain elevation (USED)	
         Z0_floodplain          =  cover(cover(WLESMOOTH, min(Z0_fldpln_inp,DEM30s)), MIN_DEM3s, DEM30s)				;	# +m	flood plain elevation (USED)	
#      
# Base of groundwater storage (that can contribute to fast response baseflow)								:
         BASE_S3		=  areaminimum(WLESMOOTH,subcatchment(LDD,nominal(uniqueid(if(WLESMOOTH gt -9999, boolean(1))))))	;
	 BASE_S3		=  max(Z0_floodplain-DZS3INFLUENCED,downstream(LDD, Z0_floodplain), BASE_S3)				;	# +m	  for mountainous areas
	 BASE_S3		=  cover(if(scalar(aquifer_map) eq 1, max(Z0_floodplain, BASE_S3)), BASE_S3)				;	# +m	 plus sedimentary pockets / flat areas
# report BASE_S3		=  cover(                             WLESMOOTH     		  , BASE_S3)				;	# +m	 plus river networks
         BASE_S3		=  cover(                             WLESMOOTH     		  , BASE_S3)				;	# +m	 plus river networks
#
  chanel_area 			= (max( 2, 4.8*(BF_DISCH**(0.5))))*((2*CELLAREA)**(0.5)) 						;	#  -     channel area in a cell (should always be saturated) 
#
  BIGLAKES    			= cover(if(cover(scalar(LAK_NUMIDSinp), scalar(0)) gt 1, boolean(1), boolean(0)), boolean(0))		;	#  -	 a boolean map indicating large lake locations
#
  LAK__INLET  			= cover(if(cover(scalar(LAK__INLET_ID), scalar(0)) gt 1, boolean(1), boolean(0)),boolean(0))		;	#	 location of lake  inlets
  LAK_OUTLET  			= cover(if(cover(scalar(LAK_OUTLET_ID), scalar(0)) gt 1, boolean(1), boolean(0)),boolean(0))		;	#	 location of lake outlets
#
         STATIONS_LK 	= nominal(uniqueid(if(scalar(LAK_OUTLET) gt 0, boolean(1))))					;
#
  LAK_UP_IDS  		= cover(scalar(LAK_UP_IDSnom), 20000000);		# 20000000 for lakes
  LAK_NUMIDS  		= cover(scalar(LAK_NUMIDSinp), 20000000);
#
  WID_OUTLET  		= (CELLAREA*2)**(0.5)		      	;		# outlet width of LAKES: estimated from cell         diagonal length
  WID_OUTLET  		= if(LAK_OUTLET, RIV__WIDTH_inp)	;		# outlet width of LAKES: estimated from bankfull discharge magnitude
# WID_OUTLET  		= (CELLAREA*2)**(0.5)*100000000	      	;		# outlet width of LAKES: VERY HIGH ... (all water levels above sills will be released)
#
         FRACWAT    = if(BIGLAKES, scalar(1), FRACWAT_inp)	;		# surface water fraction (including LARGE RIVERS and SMALL LAKES, not only BIG LAKES)
#
#
# S O I L  P A R A M E T E R S
#=============================================================================================================================================================
#
         Z1	  	= if( IMP_LDCOV , 0 , Z1_inp                       )*(1-FRACWAT);	# for impermeable areas (urban and glacier) and suface water bodies, Z = 0 and SC = 0
         Z2         	= if( IMP_LDCOV , 0 , Z2_inp                       )*(1-FRACWAT);
#
         Z1	  	= if( IMP_LDCOV , 0 , Z1_inp*scalar(1)             );
         Z2_mod        	= if( scalar(aquifer_map) eq 1, Z2_modSED, if( scalar(aquifer_map) eq 6, Z2_modSED, Z2_modMON));
         Z2         	= if( IMP_LDCOV , 0 , Z2_inp*scalar(Z2_mod)        );
 report  Z1_out	  	= if( LANDMASK , Z1);
 report  Z2_out        	= if( LANDMASK , Z2);
#
 report  SC1        	= if( IMP_LDCOV , 0 , Z1 * (THETASAT1 - THETARES1) )*(1-FRACWAT);
 report  SC2        	= if( IMP_LDCOV , 0 , Z2 * (THETASAT2 - THETARES2) )*(1-FRACWAT);
#
         SED_MON        = if( scalar(aquifer_map) eq 1, nominal(1), if( scalar(aquifer_map) eq 6, nominal(1), nominal(2)));
         SC1_SED        = if( scalar(SED_MON) eq 1    , SC1 );
         SC1_MON        = if( scalar(SED_MON) eq 2    , SC1 );
         SC2_SED        = if( scalar(SED_MON) eq 1    , SC2 );
         SC2_MON        = if( scalar(SED_MON) eq 2    , SC2 );
#
	 KSATFACTOR	= 10**(if( scalar(aquifer_map) eq 1, log_KS_add_sed, if( scalar(aquifer_map) eq 6,  log_KS_add_sed, log_KS_add_mon	))); 
report	 KS1		= KS1_inp*KSATFACTOR;
report	 KS2		= KS2_inp*KSATFACTOR;
#
   	 LAMBDA1    	= 1/BCH1;
   	 LAMBDA2    	= 1/BCH2;
   	 BCB1       	= 2*BCH1 + BCH_ADD;							# Campbell's (1974) coef to calculate the relative unsaturated hydraulic conductivity
   	 BCB2       	= 2*BCH2 + BCH_ADD;
#
    	 THEFF1_FC 	=       (PSI_FC/PSI_A1)**(-1/BCH1);					# degree of saturation at field capacity for first and second layer
        KTHEFF1_FC 	=  max(0,THEFF1_FC**BCB1*KS1);						# and corresponding unstaturated hydraulic conductivity
         THEFF2_FC 	=       (PSI_FC/PSI_A2)**(-1/BCH2);
        KTHEFF2_FC 	=  max(0,THEFF2_FC**BCB2*KS2);
#
            PSI_WP      =  0.01*(10**(4.2));							#  m  matric suction at wilting point (based on the FAO soil table of Rens)
    	 THEFF1_WP 	=       (PSI_WP/PSI_A1)**(-1/BCH1);					#  -  degree of saturation at wilting point for the    1st layer
    	 THEFF2_WP 	=       (PSI_WP/PSI_A2)**(-1/BCH2);					#  -  degree of saturation at wilting point for the    2nd layer
    	THEFF12_WP 	= cover(((THEFF1_WP*SC1)+(THEFF2_WP*SC2))/(SC1+SC2),0); 		#  -  degree of saturation at wilting point for the entire layer
#
#  Effective soil parameters needed for calculating the equilibrium soil profile:
#
#   	KTHEFF12FC 	= cover((Z1+Z2)/((Z1/KTHEFF1_FC) + (Z2/KTHEFF2_FC)),0)	  ;	# m/day	unsaturated conductivities at FC condition (for the entire soil profile, use weighted mean harmonic)
#        THEFF12FC 	= cover(((THEFF1_FC*Z1)+(THEFF2_FC*Z2))/(Z1+Z2),0)	  ;	# -	and corresponding unstaturated hydraulic conductivity (for the entire soil profile)
#
  	KTHEFF12FC 	= cover((SC1+SC2)/((SC1/KTHEFF1_FC) + (SC2/KTHEFF2_FC)),0); 	# m/day as above, but instead of using soil depth Z, this is using soil storage SC
         THEFF12FC 	= cover(((THEFF1_FC*SC1)+(THEFF2_FC*SC2))/(SC1+SC2),0)	  ;	# -	as above, but instead of using soil depth Z, this is using soil storage SC
#
#       KS12 		= cover(( Z1+ Z2)/(( Z1/KS1) + ( Z2/KS2)),0)		  ; 	# m/day	saturated conductivities		   (for the entire soil profile, use weighted mean harmonic)
        KS12 		= cover((SC1+SC2)/((SC1/KS1) + (SC2/KS2)),0)		  ; 	# m/day	as above, but instead of using soil depth Z, this is using soil storage SC
#
        BCB12   	= cover((ln(KTHEFF12FC/KS12))/(ln(THEFF12FC)),0)	  ;
        BCH12   	= cover((BCB12-BCH_ADD)/2,0)				  ;
        LAMBDA12   	= cover((1/BCH12),0)					  ;
        PSI_A12   	= cover((PSI_FC/(THEFF12FC**(-BCH12))),0)		  ;
#
#
#  Root fractions (RENS METHOD)
#
#  tmp_beta   = ln(0.0001)/ROOTDEPTH					;		# We assume that at the maximum root depth, the cummulative root fraction is 99.99%.
   tmp_rfrac1 = if((Z1+Z2)>0, min(1,1-exp((ln(0.0001)/ROOTDEPTH)*Z1)),0);		# tmp_rfrac1 = if((Z1+Z2)>0, min(1, 1 - exp(tmp_beta * Z1)), 0)	;
   tmp_rfrac2 = if((Z1+Z2)>0, min(1,1-tmp_rfrac1),0)			;
#
         RFW1 = if(LANDMASK, cover(tmp_rfrac1, 0))			;
         RFW2 = if(LANDMASK, cover(tmp_rfrac2, 0))			;
#
#
#  Average degree of saturation at which actual transpiration is halved:
#
     	THEFF_50 	= (SC1*RFW1*(PSI_50/PSI_A1)**(-1/BCH1)+SC2*RFW2*(PSI_50/PSI_A2)**(-1/BCH2))/(SC1*RFW1+SC2*RFW2);
     	THEFF_50 	=  cover(THEFF_50, 0);
     	BCH_50   	= (SC1*RFW1*BCH1+SC2*RFW2*BCH2)/(SC1*RFW1+SC2*RFW2);
     	BCH_50   	=  cover(  BCH_50, 0);
#
#
#  Interflow parameter;
   	TCL_DEF = Duration*(2*KS2*TANSLOPE)/(LSLOPE*(1-THEFF2_FC)*(THETASAT2-THETARES2))				;
        TCL_FAC = if( scalar(aquifer_map) eq 1, TCL_FAC_sed, if( scalar(aquifer_map) eq 6, TCL_FAC_sed, TCL_FAC_mon))	;
 report TCL     = if(LANDMASK, cover(min(TCL_DEF*TCL_FAC,1), 0))*(1-FRACWAT)		        			;	# day-1		time centroid lag
#
#  Storage parameters related to (Improved) Arno Scheme
        WSMAX     = SC1						;				# m	storage in top soil limiting bare soil evapotranspiration
 	WMAX      = SC1 + SC2					;				# m	WMAX = SCTOT = SC1 + SC2 = total storage for entire soil profile
#
	WMIN_FRAC = if( scalar(aquifer_map) eq 1, WMIN_SED, if( scalar(aquifer_map) eq 6,  WMIN_SED, WMIN_MON )); 
        WMIN      = min(cover(WMIN_FRAC*WMAX,scalar(0)),WMAX)	;				# m	minimum storage capacity
 report WMIN_OUT  = if(LANDMASK,WMIN)				;
        WRANGE    = if(IMP_LDCOV, 0, WMAX -WMIN) 		;				# m	range in storage capacity
#
#  Shape coefficient for distribution of maximum storage capacity, maximum set to fraction of total
#         B_FRA =  scalar(0)		   	;					# 	B_FRA NOT USED
          B_FRA =  cover(B_FRA_INP, scalar(0)) 	;
          BCF   =  max(0.01,B_FRA + B_ORO) 	;                                	# m	shape coefficient for Improved Arno Scheme
#         BCF   =  min(     BCF, 0.500)	   	;					# 	Do we need this one?
          BCF   =     if(LANDMASK, BCF)   	;
#
#  P2_IMP (fraction area where percolation to groundwater store is impeded)
#
       local_wmax   = (BCF+1)*WMAX - BCF*WMIN	;
report P2_IMP       = if(LANDMASK, cover(scalar(1)-(((local_wmax - WMAX)/(local_wmax - WMIN))**(BCF)), scalar(0)))	;
     # P2_IMP	    = scalar(1)						      ;
#
#
#################################################################################
#-------------------------------------------------------------------------------#
#  MODFLOW MODEL								#
#-------------------------------------------------------------------------------#
#################################################################################

  object mf 	= pcraster_modflow::initialise();
#
# grid specification												# one layer model
  l1_top    	= cover(DEM30s,-1000)									;	# +m	top    elevations
  bottom    	= l1_top - aquifthick									;	# +m	bottom elevations
  res 		= mf::createBottomLayer(bottom, l1_top) 						;
#
# IBOUND
  l1_ibound_set =    if(LANDMASK, scalar(1))								;
  l1_ibound_set =    cover(l1_ibound_set, if(BIGLAKES, scalar(1)))					;	# Groundwater bodies are also found below   the BIG LAKES.	#     USED
# l1_ibound_set =    cover(l1_ibound_set, if(BIGLAKES, scalar(0)))					;	# NO FLOW  within lakes
# l1_ibound_set =    if(LAK_SHORES, scalar(1), cover(l1_ibound_set, if(BIGLAKES, scalar(0))))		;	# NO FLOW in lake areas, only lakeshore (ACTIVE AS RIVER).	# not USED
  l1_ibound     =    nominal(cover(if(LANDMASK,l1_ibound_set), scalar(0)))				;	# NO FLOW outside basin
  res = mf::setBoundary(l1_ibound, 1);

# SHEAD (starting head)
  gw_head_INI_FULL =  cover(gw_head_INI     ,-9999)							;
  gw_head_INI_FULL = if(abs(gw_head_INI_FULL  ) lt 1e-20, scalar(0), gw_head_INI_FULL)			;
  res  = mf::setInitialHead(gw_head_INI_FULL,1)								;
#
# the (horizontal) conductivities to the MODFLOW model
#######################################################################################################################################
       log_Pm_add = if( scalar(aquifer_map) eq 1, log_Pm_add_sed, if( scalar(aquifer_map) eq 6, log_Pm_add_sed, log_Pm_add_mon));
       h_cond_inp = rho__water * (10**(log_Pm_inp+log_Pm_add)) * (g__gravity /miu__water) * 24 * 3600	; 
       h_cond     = max(0.01,h_cond_inp)								;
       hcond_l1   = if(scalar(LAK_NUMIDSinp) gt -9999, mapmaximum(h_cond)) 				; # aquifers beneath lakes
       hcond_l1   = cover(hcond_l1, h_cond,            mapminimum(h_cond)) 				; # aquifers
       hcond_l1   = cover(hcond_l1, 100)								;
report KD_aquifer = if(LANDMASK, hcond_l1 * aquifthick)							;
       vcond_dm   = if(hcond_l1 gt -999, scalar(10000))							;
 res = mf::setConductivity(00, hcond_l1, vcond_dm, 1)  							;	

# adding the storage coefficients to the MODFLOW model
#######################################################################################################################################
  spe_yi          = spe_yi_inp								;
  scoef_act       = if(scalar(LAK_NUMIDSinp) gt -9999, mapmaximum(spe_yi)) 		; # aquifers beneath lakes;
  scoef_act       = cover(scoef_act, spe_yi,           mapminimum(spe_yi)) 		; # aquifers
  storage_coeff   = scoef_act*CELLAREA/(3000*3000) 		  			; # cellarea is 3000 x 3000 arc-centiseconds.
  storage_coeff   = cover(storage_coeff,scalar(0.02))		  			;
  res = mf::setStorage(storage_coeff,storage_coeff,1)  					;
#
# ANISOTROPHY input values:
#######################################################################################################################################
#      ani_value  = cover(ANI_input, scalar(1))						;
       ani_value  = cover(ANI_input, scalar(1))						;
  res = mf::setHorizontalAnisotropy(ani_value,1)					;
#
#
# RIVER PACKAGE:
#######################################################################################################################################################################
  RIV__WIDTH      = RIV__WIDTH_inp							; # river/channel widths (only defined in river network  cells)
  RIV__SLOPE      = if(RIV__WIDTH gt 0, RIV__SLOPE_inp)					; # river/channel slopes
#
# RIV_BOTTOM for LAKE and RIVER
  RIV_BOTTOM      = if(scalar(LAK_NUMIDSinp)  gt -9999, -10000)				; # lakes - assumed to have very deep bottom then QRIV always = K * (HRIV-HEAD)
# RIV_BOTTOM      = cover(RIV_BOTTOM,      WLESMOOTH-RIV_DEPTH)				; # river (combined with lakes)
  RIV_BOTTOM      = cover(RIV_BOTTOM,           RIV_BOTTOM_inp)				; # river (combined with lakes), using pre-defined RIVER BOTTOM inputs	# USED
#
  RIV_DEPTH	  = cover(RIV_DEPTH__inp, scalar(0))					; #  m		river depth (bankfull)		(     defined in alle cells) 
#
# rivbott = cover(RIV_BOTTOM,  (DEM30s-0.25)  )						;
# rivbott = cover(RIV_BOTTOM,  (DEM30s-0.00)  )						;
# rivbott = cover(RIV_BOTTOM,  cover(DEM30s-RIV_DEPTH,DEM30s))				;
  rivbott = cover(RIV_BOTTOM, Z0_floodplain-RIV_DEPTH        )				; # although we defined the river bottom elevation values
  rivbott = cover( rivbott, scalar( -88888)   )						; # for the entire map, RIV PAC is only active if rivcond > 0
  rivbott = if(abs(rivbott) lt 1e-20, scalar(0), rivbott)				; # rivbott is THE VARIABLE SUPPLIED to thw RIVER PACKAGE
#
# RIVER AND LAKE CONDUCTANCE:
#
         RIVbedresi 	= RIVbedresi_inp;
#        RIVbedresi 	= max(min(20,1/hcond_l1),1) 				; # resistance = bed_thickness/hcond (with bed_thickness =  1 m)
# report RIVbedresi_out = if(LANDMASK,RIVbedresi);
#
# RIVER and LAKE CONDUCTANCE:
  RIVbedresi 	 = RIVbedresi_inp;
# rivcond = cover(if(BIGLAKES, (1/1000000000)*CELLAREA), (1/RIVbedresi)*        RIV__WIDTH *((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # high bed resistance in large lakes (no water exchanges)			   # not USED .
# rivcond = cover(if(BIGLAKES, (1/RIVbedresi)*CELLAREA), (1/RIVbedresi)*        RIV__WIDTH *((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # same bed resistance values for lakes & rivers				   # not USED
  rivcond = cover(if(BIGLAKES, (1/RIVbedresi)*CELLAREA), (1/RIVbedresi)*max(0.5,RIV__WIDTH)*((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # same bed resistance values for lakes & rivers, with minimum values of rivcond  #     USED	
  rivcond = cover(if(rivbott gt -50000,rivcond), scalar(0))					;
  rivcond = cover(if(BIGLAKES, rivcond, if(RIV__WIDTH gt 25, rivcond, scalar(0))), scalar(0))	; # RIVER PACKAGE only defined in lakes and major rivers (where there are water exchanges in two directions: surface and ground-water)
  rivcond = if(abs(rivcond) lt 1e-20, scalar(0) , rivcond )					; # rivbott is THE VARIABLE SUPPLIED to RIVER PACKAGE
#
#
# DRAIN PACKAGE:
###################################################################################################################################################################################
# drncond = cover(if(rivcond eq 0,cover((1/RIVbedresi)*        RIV__WIDTH *((CELLAREA*2)**(0.5)),(1/RIVbedresi)*        mapminimum(RIV__WIDTH) *((CELLAREA*2)**(0.5)))),scalar(0)); # same resistance                      # not USED
  drncond = cover(if(rivcond eq 0,cover((1/RIVbedresi)*max(0.5,RIV__WIDTH)*((CELLAREA*2)**(0.5)),(1/RIVbedresi)*max(0.5,mapminimum(RIV__WIDTH))*((CELLAREA*2)**(0.5)))),scalar(0)); # same resistance, with minimum values #     USED
  drncond = if(abs(drncond) lt 1e-20, scalar(0), drncond)								     ;		 
  drncond = cover(if(LANDMASK, drncond), scalar(0))	 								     ;		 # drncond is THE VARIABLE SUPPLIED to RIVER PACKAGE  
#
# drndelv = cover((DEM30s-0.25),      scalar(-88888))	;		# drain elevation = 0.25 meter below DEM30s
# drndelv = cover((DEM30s-RIV_DEPTH), scalar(-88888))	;		# based on channel depth (and calculated from DEM30s)
  drndelv = rivbott 					;		# as defined for the RIVER PACKAGE (see above)           # NOTE: "drndelv" is not directly supplied to DRAIN PACKAGE

# MODFLOW simulation parameter:
###################################################################################################################################################

  res = mf::setPCG(500, 250, 1, 0.005, 10, 0.98, 2, 1)	;	# res    = mf::setPCG(MXITER, ITERI, NPCOND, HCLOSE, RCLOSE, RELAX, NBPOL, DAMP) ;
								# NPCOND = 1 ; Modified Incomplete Cholesky 			# Confirm to PTM!
								# NBPOL  = 2 ; but we do not use it (since NPCOND = 1)
								# DAMP   = 1 ; no damping (DAMP introduced in MODFLOW 2000) 	# Confirm to PTM!
#
  res   = mf::setDISParameter(4, 2, 1, 1, 1, 0)		;	# res = mf::setDISParameter(ITMUNI,LENUNI,PERLEN,NSTP,TSMULT,SSTR);
								# ITMUNI indicates the time unit (0: undefined, 1: seconds, 2: minutes, 3: hours, 4: days, 5: years);
								# LENUNI indicates the length unit (0: undefined, 1: feet, 2: meters, 3: centimeters);
								# PERLEN is the duration of a stress period;
								# NSTP is number of timestep within a stress period;
								# TSMULT is the multiplier for the length of the successive iterations;
								# SSTR 0 - transient, 1 - steady state.

# Groundwater recession coefficient
###################################################################################################################################################
          PI    =  3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067;
          hcKQ3 = hcond_l1      ;
          KQ3   = min(1, (PI)*(PI) * hcKQ3 * aquifthick / (4*scoef_act*LSLOPE*LSLOPE)) ;
   report KQ3   = if(LANDMASK, cover(KQ3, scalar(0)))				       ;         # day-1   groundwater linear recession coefficient

#
# Initial conditions
 SC         = scalar(0);							# m
 SCF        = scalar(0);							# m
 INTS       = scalar(0);							# m
 S1         = scalar(0);							# m
 S2         = scalar(0);							# m
 S3_MD      = S3_MD_INI;							# m
 SW	    = SW_INI   ;							# m3

   # Initial conditions								# Note: Local variables are maintained to check the consistency with the original model.
   #
   # - states and fluxes
   #
   SC_L     = SC_INI		*(1-FRACWAT); 					# (m)     initial snow cover
   SCF_L    = SCF_INI		*(1-FRACWAT); 					# (m)     initial liquid water stored in snow cover
   INTS_L   = INTS_INI		*(1-FRACWAT); 					# (m)     initial interception storage
   S1_L     = min(SC1,S1_INI)	*(1-FRACWAT); 					# (m)     initial storage in the first store
   S2_L     = min(SC2,S2_INI)	*(1-FRACWAT); 					# (m)     initial storage in the second store
   Q2_L     = Q2_INI		*(1-FRACWAT); 					# (m/day) initial drainage from second store (interflow)
   #
   # - total storages
   #
   SC       = SC   + SC_L;        						#  = 0 + SC_L = SC_INI, see and understand above
   SCF      = SCF  + SCF_L;       						# 			idem, see above
   INTS     = INTS + INTS_L;      						# 			idem, see above
   S1       = S1   + S1_L;        						# 			idem, see above
   S2       = S2   + S2_L;        						# 			idem, see above
   #
#
  gw_head  = gw_head_INI_FULL;
#
#
# FOR ROUTING:
#
  min00    = cover(min00_inp, scalar(0));	  min01    = cover(min01_inp, scalar(0));	  min02    = cover(min02_inp, scalar(0));
  min03    = cover(min03_inp, scalar(0));	  min04    = cover(min04_inp, scalar(0));	  min05    = cover(min05_inp, scalar(0));
  min06    = cover(min06_inp, scalar(0));	  min07    = cover(min07_inp, scalar(0));	  min08    = cover(min08_inp, scalar(0));
  min09    = cover(min09_inp, scalar(0));	  min10    = cover(min10_inp, scalar(0));	  min11    = cover(min11_inp, scalar(0));
  min12    = cover(min12_inp, scalar(0));	  min13    = cover(min13_inp, scalar(0));	  min14    = cover(min14_inp, scalar(0));
  min15    = cover(min15_inp, scalar(0));
#
  QCmin01  = QCmin01_INI; QCmin06  = QCmin06_INI; QCmin11  = QCmin11_INI;
  QCmin02  = QCmin02_INI; QCmin07  = QCmin07_INI; QCmin12  = QCmin12_INI;
  QCmin03  = QCmin03_INI; QCmin08  = QCmin08_INI; QCmin13  = QCmin13_INI;
  QCmin04  = QCmin04_INI; QCmin09  = QCmin09_INI; QCmin14  = QCmin14_INI;
  QCmin05  = QCmin05_INI; QCmin10  = QCmin10_INI; QCmin15  = QCmin15_INI;
#
  QCmin01_BS = QCmin01_BS_INI; QCmin06_BS = QCmin06_BS_INI; QCmin11_BS = QCmin11_BS_INI;
  QCmin02_BS = QCmin02_BS_INI; QCmin07_BS = QCmin07_BS_INI; QCmin12_BS = QCmin12_BS_INI;
  QCmin03_BS = QCmin03_BS_INI; QCmin08_BS = QCmin08_BS_INI; QCmin13_BS = QCmin13_BS_INI;
  QCmin04_BS = QCmin04_BS_INI; QCmin09_BS = QCmin09_BS_INI; QCmin14_BS = QCmin14_BS_INI;
  QCmin05_BS = QCmin05_BS_INI; QCmin10_BS = QCmin10_BS_INI; QCmin15_BS = QCmin15_BS_INI;
#
  BASEL_CATCH = catchment(LDD,if(scalar(STATIONS_DS) eq 66, boolean(1)));
#
  rhmin01  = rhmin01_INI; rhmin06  = rhmin06_INI; rhmin11  = rhmin11_INI; rhmin16  = rhmin16_INI; rhmin21  = rhmin21_INI; rhmin26  = rhmin26_INI;
  rhmin02  = rhmin02_INI; rhmin07  = rhmin07_INI; rhmin12  = rhmin12_INI; rhmin17  = rhmin17_INI; rhmin22  = rhmin22_INI; rhmin27  = rhmin27_INI;
  rhmin03  = rhmin03_INI; rhmin08  = rhmin08_INI; rhmin13  = rhmin13_INI; rhmin18  = rhmin18_INI; rhmin23  = rhmin23_INI; rhmin28  = rhmin28_INI;
  rhmin04  = rhmin04_INI; rhmin09  = rhmin09_INI; rhmin14  = rhmin14_INI; rhmin19  = rhmin19_INI; rhmin24  = rhmin24_INI; rhmin29  = rhmin29_INI;
  rhmin05  = rhmin05_INI; rhmin10  = rhmin10_INI; rhmin15  = rhmin15_INI; rhmin20  = rhmin20_INI; rhmin25  = rhmin25_INI; rhmin30  = rhmin30_INI;
#
#
# initialization related to MODFLOW and GE-CR models:
# =======================================================================================================================================================
  rivhead 	= rivhead_INI						;
  lake_hd	= lake_hd_INI						;
# gw_rech	= gw_rech_INI		# NOT NEEDED			;	# m1/day
  gw_baseflow	= gw_baseflow_INI					;	# m3/day	# positive sign for flow entering aquifers
  Q3MOD         = if(LANDMASK,gw_baseflow*scalar(-1)/(CELLAREA))	;	# m1/day	# positive sign for flow entering rivers
# CRFRAC_RIV    = CRFRAC_RIV_INI					;	# -		# fractions of saturated/flooded areas based on surface water levels
#
# initialization related to cumulative fluxes for average discharge & budget check
# =======================================================================================================================================================
  QCUM     	=   scalar(0);
  R3CUM    	=   scalar(0);
  STOT_CUM 	=   scalar(0);
  SLOCINI  	= (1-FRACWAT)*(S1+S2+S3_MD+INTS+SC+SCF) + FRACWAT*if(BIGLAKES,scalar(0),S3_MD);	# Note: Storage for big lakes will be treated separately.
  PTOT     	=   scalar(0);
  ETOT     	=   scalar(0);
  QTOT     	=   scalar(0);
#
  maxwberror    = if(LANDMASK, scalar(0));
  minwberror    = if(LANDMASK, scalar(0));
  maxINerror    = if(LANDMASK, scalar(0));
  minINerror    = if(LANDMASK, scalar(0));
  maxSCerror    = if(LANDMASK, scalar(0));
  minSCerror    = if(LANDMASK, scalar(0));
  maxSFerror    = if(LANDMASK, scalar(0));
  minSFerror    = if(LANDMASK, scalar(0));
  maxS1error    = if(LANDMASK, scalar(0));
  minS1error    = if(LANDMASK, scalar(0));
  maxS2error    = if(LANDMASK, scalar(0));
  minS2error    = if(LANDMASK, scalar(0));
  maxSWerror    = if(LANDMASK, scalar(0));
  minSWerror    = if(LANDMASK, scalar(0));

dynamic

  NUMDAYS_month = timeinputscalar(monthDuration,1);	
# NUMDAYS_week  = timeinputscalar(week_Duration,1);	

#----------------
#  M E T E O
#----------------
# Meteorological input as total/average per time step
# TA		(deg C):	average temperature
# PRPTOT	(m)    :	total precipitation
# EVAP		(m)    :	reference potential evaporation+transpiration+interception+etc..(total)
# EWAT		(m)    :	as above, but that will be imposed on water surface
# PRP		(m)    :	liquid precipitation
# SNOW		(m)    :	snow in water equivalent
#
# Temperature (final unit must be in deg C)
#===============================================================================
  T_CRUCL_month      =  timeinputsparse(T_CRUCL_M);  								# monthly temperature of CRU CL-2.0           	[deg C]   10 arc-minute
  T_ECMWF_daily      =  timeinputscalar(T_ECMWF_D,ID_30mincell);						#   daily temperature of ERA40 or ECMWF OA    	[deg C]  0.5 arc-degree
  T_ECMWF_month      =  timeinputsparse(T_ECMWF_M);								# monthly temperature of ERA40 or ECMWF OA    	[deg C]  0.5 arc-degree
  T_CRU21_month	     = (timeinputsparse(T_CRU21_M))/(10);							# monthly temperature of CRU TS-2.1	      	[deg C]  0.5 arc-degree
#
  TA10min_month      = (T_CRU21_month + 273.15) * ((T_CRUCL_month + 273.15)/(areaaverage((T_CRUCL_month + 273.15),nominal(ID_30mincell)))) - 273.15;	      #	[deg C]   10 arc-minute	MONTHLY
  TA10min_daily      = (T_ECMWF_daily + 273.15) * ((T_CRU21_month + 273.15)/(T_ECMWF_month + 273.15))  -  273.15 ;	   				      # [deg C]   10 arc-minute	  DAILY
#
# TA                 = if(LANDMASK, TA10min_daily)
  TA                 = if(LANDMASK, TA10min_daily + TLA*0.01*(DEM30s-DEM10min));       				# downscaled by lapse rate 			[deg C]   30 arc-second	  DAILY
#
# Total Precipitation  (rainfall + snow):
#===============================================================================
  P_CRUCL_month      =        timeinputsparse(P_CRUCL_M);                           				# CRU CLIM 1960-1990 (unit: mm/month)			  10 arc-minute	MONTHLY
  P_CRUCL_30s	     =	      timeinputsparse(P_CRUCL_30s_input); 						#							  30 arc-second	MONTHLY
#
  P_ECMWF_daily      = (max(0,timeinputscalar(P_ECMWF_D,ID_30mincell))*Duration*timeslice());			# unit: m/day
  P_ECMWF_month      =       (timeinputsparse(P_ECMWF_M))/(NUMDAYS_month);  					# unit: m/day
  P_CRU21_month      =       (timeinputsparse(P_CRU21_M))/(10*1000*NUMDAYS_month);      			# unit: m/day
#
  PRPTOT__month      =  P_CRU21_month *((P_CRUCL_month)/(areaaverage((P_CRUCL_month),nominal(ID_30mincell)))); 	# unit: m/day						  10 arc-minute	MONTHLY
#
  PRPTOT             =  P_ECMWF_daily * ( PRPTOT__month / P_ECMWF_month ) * Duration*timeslice();   		# unit: m/day						  10 arc-minute   DAILY
  PRPTOT	     =  if(LANDMASK,PRPTOT*(P_CRUCL_30s/(areaaverage((P_CRUCL_30s  ),nominal(ID_30mincell)))));	# unit: m/day						  30 arc-second   DAILY
#
# Reference Potential Evaporation:
#===============================================================================
  EVX       	     =  timeinputsparse(EP0_FORCE_M);                            				# monthly reference potential evapotranspiration [m/day] 0.5 arc-degree
  EVX                =  EVX *((  TA10min_month+273.15)  /(T_CRU21_month+273.15));     				# monthly (downscaled into 10 arc-min)		 [m/day]  10 arc-minute
  EVAP               =  EVX *((((TA10min_daily+273.15)))/(TA10min_month+273.15))*Duration*timeslice();          #   daily      					 [m/day]  10 arc-minute - DAILY
  EVAP               =  EVAP*((((TA           +273.15)))/(TA10min_daily+273.15));                               #   daily (downscaled into 30 arc-sec)           [m/day]  30 arc-second - DAILY
#
  EVAP        	     =  if(LANDMASK, EVAP)			;						# only for FRACWAT ne 0 ... FINAL FORCING (10 arc-minute resolution)
  EWAT        	     =  cover(KC_WATSTACK*EVAP,0)		;						# only for FRACWAT eq 0 ... cover(if(FRACWAT gt 0.5, KC_WATSTACK*EVAP),0);
#
  KC          	     =  cover(timeinputsparse(KCLANDSTACK),0)	;
#
#========================================================================================================================================================================================

#- partitioning rain and snow and converting reference evaporation
#
 PRPTOT  = max(0,PRPTOT)	;
 SNOW    = if(TA<TT,PRPTOT,0)	;
 PRP     = PRPTOT-SNOW		;		#   liquid precipitation
 SNOW    = SFCF*SNOW		; # SFCF = 1  	# snowfall precipitation
 PRPTOT  = PRP+SNOW		;		#    total precipitation

#--------------------------
#  L A N D  S U R F A C E
#--------------------------

# Note: - NOT spliting in two horizontal compartments for (1) short and (2) tall vegetation
#       - '_L' indicates local values, which are used in the original version.

# Previous time storages for water balance checking:
 INTS_PRE = INTS*(1-FRACWAT);
   SC_PRE =   SC*(1-FRACWAT);
  SCF_PRE =  SCF*(1-FRACWAT);
   S1_PRE =   S1*(1-FRACWAT);
   S2_PRE =   S2*(1-FRACWAT);
   SW_PRE =   SW*(  FRACWAT);

#-----------------------------------------------------
#  F R E S H W A T E R   S U R F A C E
#-----------------------------------------------------
#
# QW (m) : local change in storage of fresh water surface, can be negative 	#     only considering precipitation and evaporation
  QW     = if(LANDMASK,PRPTOT-(EWAT+POTABSTR_S0))*FRACWAT;			# (m) we assume that all water bodies can not be empty

#--------------------------
#  L A N D  S U R F A C E
#--------------------------

# Note: - NOT spliting in two horizontal compartments for (1) short and (2) tall vegetation
#       - '_L' indicates local values, which are used in the original version.

# Previous time storages for water balance checking:
 INTS_PRE = INTS*(1-FRACWAT);
   SC_PRE =   SC*(1-FRACWAT);
  SCF_PRE =  SCF*(1-FRACWAT);
   S1_PRE =   S1*(1-FRACWAT);
   S2_PRE =   S2*(1-FRACWAT);
   SW_PRE =   SW*(  FRACWAT);

#-initialization of states and fluxes for the present time step

 SC       = scalar(0);
 SCF      = scalar(0);
 INTS     = scalar(0);
 ETPOT    = scalar(0);
 ESPOT    = scalar(0);
 ESACT    = scalar(0);
 T1POT    = scalar(0);
 T1ACT    = scalar(0);
 T2POT    = scalar(0);
 T2ACT    = scalar(0);
 EACT     = scalar(0);
 SATFRAC  = scalar(0);
 WACT     = scalar(0);
 S1       = scalar(0);
 S2       = scalar(0);
 P0       = scalar(0);
 P1       = scalar(0);
 P2       = scalar(0);
 CR1      = scalar(0);
 CR2      = scalar(0);
 Es       = scalar(0);
 Ta       = scalar(0);
 Q1       = scalar(0);
 Q1S      = scalar(0);
 Q2       = scalar(0);

  # - Vegetation cover fraction
  #   CFRAC	(-): vegetation cover fraction
      CFRAC    = timeinputsparse(CF___STACK);
      CFRAC    = cover(CFRAC, 0);

  # - LAI (leaf area index)
      LAI      = timeinputsparse(LAI__STACK);
      LAI      = cover(LAI, 0);

  # - Potential bare soil evaporation and transpiration
  #   ET_p	(m):	potential evapotranspiration (total)
  #   T_p	(m):	potential transpiration
  #   ES_p	(m):	potential bare soil evaporation
  #   EACT	(m):	total actual evapotranspiration
  #
      ET_p     =        ((CFRAC)*KC*EVAP + (1-CFRAC)*(KCMIN)*EVAP               )  * (1-FRACWAT);	# Potential evaporation (TOTAL, but only for land surface cells): original: ET_p = KC*EVAP;
      ET_p_ALL =                                             EWAT * FRACWAT + ET_p * (1-FRACWAT);	#                                        for alle cells

  # - Interception
  # ==============================
  #   ICC	(m) :	equivalent interception storage capacity for non-vegetated and vegetated areas
  #   INTS	(m) :	           interception storage (stage)
  #   PRP	(m) :  precipitation passing the canopy
  #
      INTCMAX       = (max(timeinputsparse(LAI__STACK), 1))*INTCAPACIT_VEG;	#   for vegetated area
      INTCMAX       =  cover(INTCMAX,0)*(1-FRACWAT);
      ICC           =          CFRAC * INTCMAX +  (1-CFRAC)*INTCAPACIT_NVG;

      PRP           = max(PRPTOT+INTS_L-ICC,0); 				# = surplus above the interception storage threshold
      INTS_L        = max(0,INTS_L+PRPTOT-PRP);
      SNOW          = SNOW*if(PRPTOT>0,PRP/PRPTOT,0);                           #   SNOW precipitation
      PRP           = PRP-SNOW;                                                 # LIQUID precipitation

      EACT_L        = min(INTS_L,((min(ET_p,EVAP*KCINT))*if(ICC>0,INTS_L/ICC,0)**(2/3)));   # actual interception flux (constrained by available energy)
#     EACT_L        = min(INTS_L,  min(ET_p,EVAP*KCINT))				;   # actual interception flux (constrained by available energy)
      EACT_L        = min(ET_p, EACT_L);

           INTSFLUX = EACT_L*(1-FRACWAT);                                       # **** interception flux for reporting ***
             INTS_L = if(LANDMASK, INTS_L - EACT_L);                            # interception storage (at THE end of TIME STEP)

             ET_p   = max(0,ET_p - EACT_L);                                     # update remaining potential evaporation (after interception)
             ES_p   = (1-CFRAC)* ET_p;						#        remaining potential bare soil evaporation
             T_p    =    CFRAC * ET_p;                                          #        remaining potential transpiration

  # - Snow accumulation and melt
  #   SC		(m)  :	snow cover
  #   SCF		(m)  :	free water stored in snow cover
  #   DSC		(m)  :	change in snow cover, - melt, + gain in snow or refreezing (CFR)
  #   Pn		(m)  :	net liquid water transferred to soil
  #   DSCR		(-)  :	relative contribution of snow melt to net liquid water transfer
  #   ES_a		(m)  :	actual bare soil evaporation, here used to subtract any evaporation
  #                                                                from LIQUID PHASE of snow cover
            # DSC    = if(TA<=TT, SCF_L*CFR,      -min(SC_L,max(TA-TT,0)*CFMAX*Duration*timeslice())); 	#--> Rens's original formula
              DSC    = if(TA<=TT, max(0   ,min(SCF_L*CFR,CFR*CFMAX*(TT-TA))),
                                 -min(SC_L,max(TA-TT,0)*CFMAX*Duration*timeslice()));			# TT-TA =  0-TA = -TA > 0 (since TA < 0, refreezing)
            #                     									# TA-TT = TA-0  =  TA > 0 (since TA > 0, melting   )

              SC_L   = if(LANDMASK, SC_L  + DSC + SNOW);                       	# snow cover (at the end of time step)

              SCF_L  = SCF_L - DSC + PRP;

              Pn     = max(0,SCF_L-CWH*SC_L);       # Pn = net liquid water transferred to soil >= 0
              DSCR   = if(Pn>0,max(-DSC,0)/Pn,0);   # DSCR is used to calculate relative contribution of snow melt.
                                                    #                           to Q1S_L : direct/surface runoff
                                                    #                                      directly attributable to snow melt
                                                    # Note: Later, you will find:  Q1S_L = min(1,DSCR)*Q1_L
              SCF_L  = max(0,SCF_L-Pn);
              ES_a   = min(SCF_L,ES_p);             # bare soil evaporation flux from "liquid phase" of snow cover
              ES_SCF = ES_a*(1-FRACWAT);

              SCF_L  = if(LANDMASK,SCF_L - ES_a);   # free water stored in snow cover (AT THE END OF TIME STEP)
              ES_p   = max(0,ES_p-ES_a);            # update remaining potential bare soil evaporation (after evaporation from snowpack water)
              EACT_L = EACT_L + ES_a;               # update total evaporation:
                                                    # after interception and bare soil evaporation from "liquid" of snow cover

  # - Direct runoff and infiltration based on (IMPROVED) ARNO SCHEME
  #   partial runoff when not entirely saturated (condition 1), else complete saturation excess
  #   BCF	  (-)  : b coefficient of soil water storage capacity distribution
  #   WMIN, WMAX  (m)  : root zone water storage capacity, area-averaged values.  Note: WMIN = 0 and WMAX = SCTOT = SC1+SC2
  #   W		  (m)  : actual water storage = S1 + S2
  #   WRANGE, DW,                                                       WRANGE = WMAX - WMIN = WMAX - 0 = WMAX
  #   and WFRAC	  (m)  : computation steps to ease runoff calculation:  DW     = WMAX - W
  #			                                                            WFRAC  = DW / WRANGE = DW / WMAX
  #			                                                            WFRAC is capped at 1
  #   WFRACB  (--, nd) : DW/WRANGE raised to the power (1/(b+1))
  #   SATFRAC      (-) : fractional saturated area                      SATFRAC is the "x" in the Rens's document.
  #   WACT		   (m) : actual water storage (within rootzone)
  #   THEFF(i)	   (-) : effective degree of saturation      = S(i)/SC(i)
  #   Pn		   (m) : net liquid precipitation (reduced if WMIN not exceeded, for Improved Arno Scheme)
  #   Q1		   (m) : direct or surface runoff
  #   Q1S		   (-) : direct or surface runoff directly attributable to snow melt
  #   P0		   (m) : infiltration
  #
      THEFF1           = max(0,S1_L/SC1);                # effective degree of saturation,
      THEFF1           = cover(THEFF1, 0);
      THEFF2           = max(0,S2_L/SC2);                #    1st and 2nd layers
      THEFF2           = cover(THEFF2, 0);
      W                = max(0,S1_L+S2_L);
      P0_L             = Pn;
      Pn               = W+Pn;                           # Note: WMIN = 0 (Arno Scheme).
      Pn               = Pn-max(WMIN,W);                 #  ==> Pn(2nd_line)= Pn(1st_line) - W
                                                         #                  = W + Pn - W
                                                         #  ==> Pn(2nd_line)= Pn(1st_line) >= 0
       W               =  if(Pn<0,WMIN+Pn,max(W,WMIN));  #  ==> W           = W
       Pn              =  max(0,Pn);                     #  ==> Pn          = Pn
       DW              =  max(0,WMAX-W);
       WFRAC           =  if(WRANGE ne 0, min(1,DW/WRANGE), 0);
       WFRACB          =        WFRAC**(1/(1+BCF));
       SATFRAC_L       =  if(WFRACB>0,1-WFRACB**BCF,0);
  #    SATFRAC_L       =  max(SATFRAC_L,cover(CRFRAC_used,scalar(0)));									# not USED
       WACT_L          = (BCF+1)*WMAX-BCF*WMIN-(BCF+1)*WRANGE*WFRACB;  # WACT_L = (BCF+1)*WMAX - (BCF+1)*WMAX*(DW/WMAX)**(1/(b+1))
                                                                       # if WRANGE = 0 ==> WACT_L = 0
  #   Q1_L according to Equation 10-14 in Rens's document
      Q1_L             =  max(0,    Pn - (WMAX-W) +
                           if(Pn>=(BCF+1)*WRANGE*WFRACB, 0, WRANGE*(WFRACB-Pn/((BCF+1)*WRANGE))**(BCF+1)));
#=============================================================================================================================
  #   added on 30 September 2011:
      Q1_L             =  if(WRANGE ne 0, Q1_L, scalar(0));
#=============================================================================================================================
  #   Q1_L             =  max(Q1_L,cover(CRFRAC_used*Pn,scalar(0)));									# not USED
     Q1S_L             =  min(1,DSCR)*Q1_L;  		# direct or surface runoff directly attributable to snow melt
      P0_L             =  P0_L-Q1_L;         		# water that infiltrates into soil

  # - saturated and unsaturated hydraulic conductivity
  #   KS(i)	 (m/d) :    saturated hydraulic conductivity
  #   KTHEFF(i)	 (m/d) :  unsaturated hydraulic conductivity
  #   BCH(i)	   (-) :  pore size distribution factor of Clapp and Hornberger (1978)
  #   BCB(i)	   (-) :  Campbell's (1974) coefficient to calculate the relative,
  #			  unsaturated hydraulic conductivity
      KTHEFF1          = max(0, THEFF1**BCB1*KS1);
      KTHEFF2          = max(0, THEFF2**BCB2*KS2);

  # - Actual bare soil evaporation and transpiration based on the remainder of the potential
  #   and limited to the available moisture content; top soil for ES, entire root zone for T
  #   Note:       To understand about this, please also read "Forcing PCRGLOB with CRU.doc",
  #                                         do not only read "PCRGLOBWB.doc"
  #   RFW(i)	   (-) : root fraction per layer, corrected to 100%
  #    WF(i)       (-) : weighing factor for fractioning transpiration per layer,
  #			      		 based on total available moisture storage in soil, or else RFW
  #   ES_p	   (m) : potential bare soil evaporation
  #   ES_a	   (m) : actual bare soil evaporation
  #   T_a(i)	   (m) : actual transpiration per layer
  #
               WF1    = if((S1_L+S2_L)>0, RFW1*S1_L/max(1e-9,RFW1*S1_L+RFW2*S2_L), RFW1);
               WF2    = if((S1_L+S2_L)>0, RFW2*S2_L/max(1e-9,RFW1*S1_L+RFW2*S2_L), RFW2);
  #
  #           FRACTA       (-) : fraction of actual over potential transpiration
            #===========================================================================================================
              FRACTA = (WMAX + BCF*WRANGE*(1-(1+BCF)/BCF*WFRACB))/(WMAX+BCF*WRANGE*(1-WFRACB));   #  Equation 17, effective degree of saturation
              FRACTA =  cover(FRACTA, 0);
              FRACTA = (1-SATFRAC)/(1+(max(0.01,FRACTA)/THEFF_50)**(-3*BCH_50));                #  Equation 18
              FRACTA =  cover(FRACTA,1);
              FRACTA =    min(FRACTA,1);
            #===========================================================================================================
            # FRACTA = scalar(1);  #  FRACTA is set to 1 to account for ERA40 re-analysis of actual "evapotranspiration"

              T_a1   = FRACTA*WF1*T_p;
              T_a2   = FRACTA*WF2*T_p;
            #===========================================================================================================

            #========================================================================================================================
              ES_a   =     SATFRAC_L * min(ES_p,KS1*Duration*timeslice()) + (1-SATFRAC_L)* min(ES_p,KTHEFF1*Duration*timeslice());
            #========================================================================================================================

  # - Percolation, subsurface storm flow and capillary rise
  #    P(i)		(m) :    percolation from layer(i) to layer(i+1)
  #   CR(i)	        (m) : capillary rise   to layer(i) from layer (i+1)
  #    Q2		(m) : lateral drainage from second store:
  #			      --  dependent on net recharge to saturated wedge
  #			      --  and centroid lag (Sloan and Moore, 1984)
  #			      --  simplified by considering drainable pore space only
  #    RQ2		(m) : recharge adding to or drawing from saturated wedge
  #
  # - fluxes
       P1_L        = max(0,    P0_L  -   (SC1-S1_L));                   # Note: If the total infiltration execeeds the storage
                                                                        #       capacity of store1, it is handed down to store2.
                                                                        #
       Q1_L        =   Q1_L  +  max(0, P0_L-KS1*Duration*timeslice());  #       If the infiltration (rate) exceeds the saturated
       P0_L        = min(P0_L, KS1*Duration*timeslice());               #       hydraulic conductivity of the first layer, the
                                                                        #       excess is passed onto the direct runoff.
       CR1_L       = if((SC1+SC2)>0, max(0,if(THEFF2>THEFF1,(1-THEFF1)*KTHEFF2*Duration*timeslice(),0)), scalar(0))	; # CR1 is only for cell with soil capacities higher than ZERO.

     # original CR2 model	# not USED
     # =================
     # CR2_L       = min((1-THEFF2)*sqrt(KS2*KTHEFF2)*Duration*timeslice(),max(0,THEFF2_FC-THEFF2)*SC2);
     # CR2_L       = if((DEM30s-gwtable) gt thres_cap, 0, CR2_L);       # If groundwater table is too deep, no capillary rise may occur.
     # CR2_L       =         0;                                         # capillary rise from groundwater table is ignored
     # ================================================================ #

     # GE model 1
     # CR2_L       = function of grounwater head			# (m)
     #
     # calculated based on average DEM
       CR2_L       = min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,DEM30s     -gw_head)))**(2+(3/BCH2)));	# CR2_L is limited to saturated hydraulic conductivity
       CR2_L       = if((DEM30s-gw_head) gt 0, CR2_L, KS2) ;								# if gw_head above or equal surface elev => CR2_L = KS2
     #
     # calculated based on minimum DEM --- not USED --
     # CR2_L       = min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used-gw_head)))**(2+(3/BCH2)));
     # CR2_L       = if((MINDEM_used-gw_head) gt 0, CR2_L, KS2)*(CRFRAC_used)					 ;	# corrected by CRFRAC
     #
     # considering the sub-grid variability of DEM:
     # CR2_L       =         cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(0     +DZ0001)-gw_head)))**(2+(3/BCH2))))*0.01;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0001+DZ0005)-gw_head)))**(2+(3/BCH2))))*0.04;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0005+DZ0010)-gw_head)))**(2+(3/BCH2))))*0.05;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0010+DZ0020)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0020+DZ0030)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0030+DZ0040)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0040+DZ0050)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0050+DZ0060)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0060+DZ0070)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0070+DZ0080)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0080+DZ0090)-gw_head)))**(2+(3/BCH2))))*0.10;
     # CR2_L       = CR2_L + cover(KS2,min(KS2, KS2 * (1 + (3)/(2+(6/BCH2))) * (PSI_A2/(max(0,MINDEM_used+0.5*(DZ0090+DZ0100)-gw_head)))**(2+(3/BCH2))))*0.10;
     #
     # limit of CR2_L (based on unsaturated hydraulic conductivity of S2 and make sure that it cannot make S2 > FC)	# RENS method, not USED
     #   CR2_L     = min(CR2_L,(1-THEFF2)*sqrt(KS2*KTHEFF2)*Duration*timeslice(),max(0,THEFF2_FC-THEFF2)*SC2);		# limited by FC					
     #   CR2_L     = min(CR2_L,(1-THEFF2)*sqrt(KS2*KTHEFF2)*Duration*timeslice());					# limited by unsaturated hydraulic conductivity
# report CR2_POT   = if(LANDMASK,CR2_L); # 
#
       CR2_L       = max(0,CR2_L)			   ;
       CR2_L       = if((SC1+SC2)>0, CR2_L, scalar(0))	   ; # CR2 is only for cell with soil capacities higher than ZERO.
       CR2_L       = cover(CR2_L, scalar(0))		   ;
  
     # GE model 2
     # CR2_L       = function of grounwater head and moisture content 	# (m)
     # to be done later

       KTHEFF1     = if(KTHEFF1>KTHEFF1_FC, sqrt(KTHEFF1*KTHEFF1_FC), KTHEFF1);
       KTHEFF2     = if(KTHEFF2>KTHEFF2_FC, sqrt(KTHEFF2*KTHEFF2_FC), KTHEFF2);
       P1_L        =         sqrt(KTHEFF1*KTHEFF2)*Duration*timeslice() + P1_L; # gravitational driven percolation from store1
                                                                                # + hand over from first store (see note above,
                                                                                #   if total infiltration exceeds storage capacity
       P1_L         = if((SC1+SC2)>0, P1_L, scalar(0))	   		      ;
       P2_L         =                      KTHEFF2 *Duration*timeslice()      ; # gravitational driven percolation from store2
       P2_L         = if((SC1+SC2)>0, P2_L, scalar(0))	   		      ;

     #
       RQ2          = P2_IMP*(P1_L+CR2_L -(P2_L+CR1_L))							;
       Q2_L         =     max(TCL*RQ2 + (1-TCL)*Q2_L,0)							;
       Q2_L	    = if( ((S2_L+P1_L+CR2_L-(P2_L+CR1_L+T_a2))/(SC2)) > THEFF2_FC,Q2_L,scalar(0))	; # if activated Q2 can only occur if S2 above FC
       Q2_L	    = cover(Q2_L,scalar(0))								;
   #
   # - water balance: scaled fluxes and new states
#============================================================================================================================================================
   #   first layer
       ADJUST       = ES_a + T_a1 + P1_L				;	# Note: "ADJUST" is needed if the available storage is limited.
       ADJUST       = if(ADJUST>0, min(1,(max(0,S1_L+P0_L))/ADJUST), 0)	;
       ES_a         = ADJUST*ES_a					;
       T_a1         = ADJUST*T_a1					;
       P1_L         = ADJUST*P1_L					;
#==============================================================================================================================
            FRACEA  = if(LANDMASK, cover(ES_a/ES_p, 1));
#==========================================================
   #   second layer NOT LIMITTING Q2_L
                Q2_L  = min(Q2_L,S2_L+P1_L)				;
 report (rep_y) Q2_L = if(LANDMASK, Q2_L)*(1-FRACWAT)			;     	#              corrected with the available storage
        ADJUST       = T_a2 +P2_L					;
        ADJUST       = if(ADJUST>0,min(1,max(S2_L+P1_L-Q2_L,0)/ADJUST),0);
        T_a2         = ADJUST*T_a2					;
        P2_L         = ADJUST*P2_L					;
#==========================================================
#  #   second layer
#      ADJUST        = T_a2 +P2_L +Q2_L					;
#      ADJUST        = if(ADJUST>0,min(1,max(S2_L+P1_L,0)/ADJUST),0)	;
#      T_a2          = ADJUST*T_a2					;
#      P2_L          = ADJUST*P2_L					;
#               Q2_L = ADJUST*Q2_L					;      	#  final Q2_L (lateral drainage from second store)
#report (rep_y) Q2_L = if(LANDMASK, Q2_L)*(1-FRACWAT)			;     	#              corrected with the available storage


     # CAPILLARY RISE CANNOT MAKE SOIL MOISTURE CONTENT HIGHER THAN ITS EQUILIBRIUM PROFILE
     #
     # - We use the model of Clapp and Hornberger (1978), see Koster et al, 2000
     # - integration: W(z) = -(psi_s+z)*((psi_s+z)/psi_s)^(-lambda) / (lambda-1) and z 
     # - where lambda is the pore size distribution index (1/b)
     #
     # Calculate EQUILIBRIUM SOIL PROFILE
     # =============================================================================================================================================================
     # - Height above water table (z_awt), z_awt at water table = 0 and z_awt at surface level = (DEM30s-gw_head)
         z_awt_gro = max(0, (DEM30s-gw_head));
     #
     # - 1ST CASE: groundwater head below the bottom of S2: z_awt_gro ge (Z1+Z2)
     #
         z_awt_bS1 = if(z_awt_gro ge (Z1+Z2), z_awt_gro - (Z1+ 0));							# boundary at the bottom of the  first layer
         z_awt_bS2 = if(z_awt_gro ge (Z1+Z2), z_awt_gro - (Z1+Z2));							# boundary at the bottom of the second layer
     #
         SC_EQU_1  = ((((PSI_A1+z_awt_gro)/PSI_A1)**(-LAMBDA1/(1)))*(PSI_A1+z_awt_gro) - (((PSI_A1+z_awt_bS1)/PSI_A1)**(-LAMBDA1/(1)))*(PSI_A1+z_awt_bS1))*-1/(LAMBDA1-1); 	# 1st layer
         SC_EQU_2  = ((((PSI_A2+z_awt_bS1)/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+z_awt_bS1) - (((PSI_A2+z_awt_bS2)/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+z_awt_bS2))*-1/(LAMBDA2-1); 	# 2nd layer
         SC_EQU_23 = ((((PSI_A2+z_awt_bS2)/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+z_awt_bS2) - (((PSI_A2+0        )/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+0        ))*-1/(LAMBDA2-1);	# water tbl & 2nd layer
         SC_EQU_23 = max(0,if(z_awt_gro ge (Z1+Z2), SC_EQU_23*(1)));														# - used only for reduction CR2
	 SC_EQU_23 = cover(SC_EQU_23,scalar(1));			# USED AS REDUCTION FACTOR										#   if watertable below 2nd lyr
	 SC_EQU_2  = if(z_awt_gro ge (Z1+Z2), min(SC_EQU_2,SC2) *(1));														# - WHY? Because the water needs
	 SC_EQU_1  = if(z_awt_gro ge (Z1+Z2), min(SC_EQU_1,SC1) *(1));														#   to fill the space between 2n3.
     #
     # - 2ND CASE: groundwater head between the bottom of S1 and S2: z_awt_gro lt (Z1+Z2) and z_awt_gro le (Z1)
     #
         z_awt_bS1 = if(z_awt_gro lt (Z1+Z2) and z_awt_gro le (Z1), z_awt_gro - (Z1+ 0));				# boundary at the bottom of the  first layer
         z_awt_bS2 = if(z_awt_gro lt (Z1+Z2) and z_awt_gro le (Z1), 0		       );				# boundary at the bottom of the second layer
     #
         SC_EQU_1  = cover(SC_EQU_1,((((PSI_A1+z_awt_gro)/PSI_A1)**(-LAMBDA1/(1)))*(PSI_A1+z_awt_gro) - (((PSI_A1+z_awt_bS1)/PSI_A1)**(-LAMBDA1/(1)))*(PSI_A1+z_awt_bS1))*-1/(LAMBDA1-1)); 	# 1st layer
         SC_EQU_2  = cover(SC_EQU_2,((((PSI_A2+z_awt_bS1)/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+z_awt_bS1) - (((PSI_A2+z_awt_bS2)/PSI_A2)**(-LAMBDA2/(1)))*(PSI_A2+z_awt_bS2))*-1/(LAMBDA2-1) 
													      +  (((Z2-(z_awt_gro-Z1))/Z2)*SC2));	               				# 2nd layer
     #
     # - 3RD CASE: groundwater head between the bottom of S1 and S2: z_awt_gro lt (Z1+Z2) and z_awt_gro le (Z1)
     #
         z_awt_bS1 = if(z_awt_gro lt (Z1), 0);										# boundary at the bottom of the  first layer
     #
         SC_EQU_1  = cover(SC_EQU_2,((((PSI_A1+z_awt_gro)/PSI_A1)**(-LAMBDA1/(LAMBDA1-1)))*(PSI_A1+z_awt_gro) - (((PSI_A1+z_awt_bS1)/PSI_A1)**(-LAMBDA1/(LAMBDA1-1)))*(PSI_A1+z_awt_bS1))*-1/(LAMBDA1-1) 
													      +  (((Z1-(z_awt_gro-0 ))/Z1)*SC1));	               				# 1st layer
         SC_EQU_2  = cover(SC_EQU_2,									         (((Z2-(          0 ))/Z2)*SC2));	               				# 2nd layer
         SC_EQU_1  = max(0,SC_EQU_1);
         SC_EQU_2  = max(0,SC_EQU_2);
         SC_EQU_2  = min(cover(SC_EQU_2,0),SC2); # integrated with constrained of SC2
         SC_EQU_1  = min(cover(SC_EQU_1,0),SC1); # integrated with constrained of SC1
#
     # Reduce CR2_L because water needs to fill the space between second and third layer (only if gw table below the 2nd layer):
       CR2_L       = (cover(SC_EQU_23/(SC_EQU_1+SC_EQU_2+SC_EQU_23),scalar(1)))*(CR2_L);
       CR2_L       = max(0,CR2_L);

     # Estimate S2 (before CR2) and S1 (before CR1)
       S2_bf_CR2   =     max(0,S2_L+P1_L+0    -(P2_L+Q2_L+CR1_L+T_a2));		# Q2 from the CURRENT time step.
     # S2_bf_CR2   =     max(0,S2_L+P1_L+0    -(P2_L+   0+CR1_L+T_a2));		# Q2 is not used (to reduce CR2)
       S1_bf_CR1   =     max(0,S1_L+P0_L+0    -(P1_L+           T_a1+ES_a));	# Both of them are estimation. Both can be larger than SC (storage capacity).

     # CR2 and CR1 cannot make S larger than SC_EQU:
       CR2_L       = min(CR2_L, max(0,SC_EQU_2-S2_bf_CR2) + max(0,SC_EQU_1-S1_bf_CR1));
       CR2_L       = max(0,CR2_L);
       CR1_L       = min(CR1_L, max(0,SC_EQU_1-S1_bf_CR1));
       CR1_L       = max(0,CR1_L);

     # Make sure that CR1 and CR2 do not make S1 and S2 exceed their equilibrium profile:
     # Estimate S1 and S2 after CR1 and CR2
       S2_af_CR2   =     max(0,S2_L+P1_L+CR2_L-(P2_L+Q2_L+CR1_L+T_a2));		# Q2 from the CURRENT time step
     # S2_af_CR2   =     max(0,S2_L+P1_L+CR2_L-(P2_L+   0+CR1_L+T_a2));		# Q2 is not considered.
       S1_af_CR1   =     max(0,S1_L+P0_L+CR1_L-(P1_L+           T_a1+ES_a));
     #
       CR2_L       = if( ((P2_L-CR2_L) lt 0) and (S2_af_CR2 gt (SC_EQU_2)), max(0, CR2_L - (S2_af_CR2-SC_EQU_2)), CR2_L);	# constrained by SC_EQU_2
       CR2_L       = max(0,CR2_L);
       CR2_L       = cover(CR2_L,0);
       CR1_L       = if( ((P1_L-CR1_L) lt 0) and (S1_af_CR1 gt (SC_EQU_1)), max(0, CR1_L - (S1_af_CR1-SC_EQU_1)), CR1_L);	# constrained by SC_EQU_1
       CR1_L       = max(0,CR1_L);
       CR1_L       = cover(CR1_L,0);

     # Make sure that CR1 and CR2 do not make S1 and S2 higher than their FC:							
     # Estimate S1 and S2 after CR1 and CR2
       S2_af_CR2   =     max(0,S2_L+P1_L+CR2_L-(P2_L+Q2_L+CR1_L+T_a2));		# Q2 from the CURRENT time step
       S2_af_CR2   =     max(0,S2_L+P1_L+CR2_L-(P2_L+   0+CR1_L+T_a2));		# Q2 is not considered.
       S1_af_CR1   =     max(0,S1_L+P0_L+CR1_L-(P1_L+           T_a1+ES_a));
     #
       CR2_L       = if( ((P2_L-CR2_L) lt 0) and (S2_af_CR2 gt (THEFF2_FC*SC2)), max(0, CR2_L - (S2_af_CR2-THEFF2_FC*SC2)), CR2_L);	# constrained by FC
       CR2_L       = max(0,CR2_L);
       CR2_L       = cover(CR2_L,0);
       CR1_L       = if( ((P1_L-CR1_L) lt 0) and (S1_af_CR1 gt (THEFF1_FC*SC1)), max(0, CR1_L - (S1_af_CR1-THEFF1_FC*SC1)), CR1_L);	# constrained by FC
       CR1_L       = max(0,CR1_L);
       CR1_L       = cover(CR1_L,0);

     # Correction with available source storage
     # CR2_L       = min(S3+P2_L,CR2_L);                                	# CR2 corrected with the available source storage # NOT NEEDED, we assume there is always
										#						       enough water in groundwater bodies.
       CR1_L       = min(max(0,S2_L+P1_L+CR2_L-(T_a2+P2_L+Q2_L)),CR1_L);      	# CR1 corrected with the available source storage # (original formula)
#      CR1_L       = min(max(0,S2_L+P1_L+    0-(T_a2+P2_L+Q2_L)),CR1_L);      	# CR1 corrected with the available source storage # (make it extreme, do not include CR2)
       CR1_L       = max(0,CR1_L);

     # Updating S2_L:
        S2_ESTM    =     max(0,S2_L+P1_L+CR2_L-(P2_L+Q2_L+CR1_L+T_a2));
        P1_L       =     if(S2_ESTM>SC2, max(0, P1_L - (S2_ESTM-SC2)),  P1_L);	# reduce  P1 if S2 higher than SC2
        P1_L       =     max(0,P1_L);
        S2_ESTM    =     max(0,S2_L+P1_L+CR2_L-(P2_L+Q2_L+CR1_L+T_a2));
        CR2_L      =     if(S2_ESTM>SC2, max(0,CR2_L - (S2_ESTM-SC2)), CR2_L);	# reduce CR2 if S2 higher than SC2	# not needed (???)
        CR2_L      =     max(0,CR2_L);
        S2_L       =     max(0,S2_L+P1_L+CR2_L-(P2_L+Q2_L+CR1_L+T_a2));

     # Updating S1_L:
        S1_L       =     max(0,S1_L+P0_L+CR1_L-(P1_L+T_a1+ES_a)+max(0,S2_L-SC2));
                                                              # max(0,S2_L-SC2)) = excees water of SC2 is given to S1 = must always be zero (?)

               CR1_ADD 	= max(0,S2_L-SC2);
               CR1_L   	= max(0, CR1_L + CR1_ADD);

               S2_L 	=     min(S2_L,SC2);
               S2_L 	= if(LANDMASK,S2_L);                                #  final S2_L, corrected with the storage capacity

               Q1_ADD   = max(0,S1_L-SC1   )	* (1-FRACWAT);		    #  additional Q1 because of excess S1			    	
               Q1_L     = max(0,Q1_L+Q1_ADD)	* (1-FRACWAT);
#
               S1_L 	= min(S1_L,SC1)		;
               S1_L 	= if(LANDMASK,S1_L)	;                            #  final S1_L, corrected with the storage capacity

  # - total actual evapotranspiration
            EACT_L = EACT_L + ES_a + T_a1 + T_a2;

  # - adding local fluxes and states (only for land surface cells)

   SC      = (  SC      +   SC_L	) * (1-FRACWAT)		;
   SCF     = (  SCF     +  SCF_L	) * (1-FRACWAT)		;
   S1      = (  S1      +   S1_L	) * (1-FRACWAT)		;
   S2      = (  S2      +   S2_L	) * (1-FRACWAT)		;
   INTS    = (  INTS    + INTS_L	) * (1-FRACWAT)		;
#
   ETPOT   = (  ETPOT   + ET_p		) * (1-FRACWAT)		;
   EACT    = (  EACT    + EACT_L	) * (1-FRACWAT)		;
   ESPOT   = (  ESPOT   + ES_p  	) * (1-FRACWAT)		;
#
   ESACT   = (  ESACT   + ES_a  	) * (1-FRACWAT)		;	     #  bare soil evaporation fluxes (not including evaporation from the liquid phase snow cover)
   ESACT_T = (  ESACT   + ES_SCF	) * (1-FRACWAT)		;	     #  			     (--- including evaporation from the liquid phase snow cover)
#
   T1POT   = (  T1POT   + WF1*T_p	) * (1-FRACWAT)		;
   T1ACT   = (  T1ACT   +     T_a1	) * (1-FRACWAT)		;
   T2POT   = (  T2POT   + WF2*T_p	) * (1-FRACWAT)		;
   T2ACT   = (  T2ACT   +     T_a2	) * (1-FRACWAT)		;
#
   SATFRAC = (  SATFRAC + SATFRAC_L	) * (1-FRACWAT)		;
   WACT    = (  WACT    + WACT_L	) * (1-FRACWAT)		;
#
   P0      = (  P0      +  P0_L		) * (1-FRACWAT)		;
   P1      = (  P1      +  P1_L		) * (1-FRACWAT)		;
   P2      = (  P2      +  P2_L		) * (1-FRACWAT)		;
   CR1     = (  CR1     + CR1_L		) * (1-FRACWAT)		;
   CR2     = (  CR2     + CR2_L		) * (1-FRACWAT)		;
#
   Q1      = (  Q1      +  Q1_L		) * (1-FRACWAT)		;
   Q1S     = (  Q1S     + Q1S_L		) * (1-FRACWAT)		;
   Q2      = (  Q2      +  Q2_L		) * (1-FRACWAT)		;

#  EFRAC   = if(ETPOT>0,EACT/ETPOT,1);					     #  fraction of actual evaporation to potential evaporation (only in land surface cells)

# --------------------------
# Overall fluxes third store
# --------------------------
# Third reservoir
# R3		  (m) : groundwater recharge
# R3AVG		  (m) : average recharge
# Q3MOD       	  (m) : runoff from 3rd store (baseflow) FROM MODFLOW
# S3_MD           (m) : storage in modflow groundwater store (m)  VERY HIGH CANNOT BE 0

                    R3 =     P2 - CR2;
                 R3CUM =     R3CUM+R3;
  report (rep_y) R3AVG =    (R3CUM/time())*(1-FRACWAT);       	             #  yearly average recharge (m/day)

# Calculating fast response baseflow component taken from the (ground)water above the flood plain elevation:
# ADDQ3 	  (m) : additional (negative) RCH or baseflow 
#
                S3FPL =  if(BIGLAKES,0,max(0,gw_head-BASE_S3      )*scoef_act)	;  	# m/day groundwater storage that can contribute to fast response baseflow
                ADDQ3 = min(S3FPL,S3FPL*min(KQ3,1)) ;  					# m/day additional baseflow taken from S3FPL
#
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
           ABSTR_S3   =  scalar(0)				;	 	# In the original version of Rens's model: ABSTR_S3 = min(POTABSTR_S3,S3)
              S3_MD   = (S3_MD + P2-ABSTR_S3 -CR2)		;    	 	# Note: - Water abstraction = zero
              Q3MOD   =  Q3MOD + ADDQ3				;	 	#       - Baseflow is taken from the previous time step (m/day). POSITIVE for flows entering the aquifer.
              S3_MD   =  S3_MD - Q3MOD       	 		;	 	# S3_MD can be negative
  # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------------#
# Water exchange between groundwater bodies & large lakes (positive for flows entering the aquifer)    	#
#-------------------------------------------------------------------------------------------------------#
  QLAKBAS     = cover( if(BIGLAKES, Q3MOD*(scalar(-1)),0), scalar(0))		;			# (m/day) inflitration to groundwater bodies from the lakes

#---------------------------------------------------------------------------------------#
# Total evaporation									#
#---------------------------------------------------------------------------------------#
               EACTFLUX =        (FRACWAT*EWAT+(1-FRACWAT)*EACT);


#--------------------------------------------------------
# Specific local discharge : QLOC (m) : local discharge #
#--------------------------------------------------------
# QLOC (m) specific runoff , QLOC = Q1+Q2+Q3  	   		      	# Q3 from MODFLOW (from the previous time step)

                QLOC         =              Q1+Q2+Q3MOD;
                QLOC         = (1-FRACWAT)*(QLOC )      + FRACWAT*if(BIGLAKES,scalar(0),QW+Q3MOD)	; # m/day NOTE: Here big lakes will not be routed directly.

#----------------------------------------------------
# B U D G E T  C H E C K (only done in local stores )
#----------------------------------------------------
# PTOT		    (m)    :		total accumulated precipitation
# ETOT		    (m)    :		total accumulated evapotranspiration
# QTOT		    (m)    :		total accumulated local discharge
# INTOT, OUTTOT	    (km3)  :		total incoming and outgoing water volumes per catchment
# SLOC, SLOCINI	    (m)    :		local storage at any timestep and initially
# STOT_ACT	    (km3)  :		total active storage (e.g, excluding snow cover) to decide whether equilibrium has been
#				              achieved (also included STOT_AVG, average total storage in (m) for soil,
#				              which excludes snow accumulation
# MBE		    (m)    :		local mass balance error
# MBR		    (-)    :		total mass balance error per catchment, relative to total input
#
#                PTOT     =  PTOT + if(BIGLAKES,scalar(0),PRPTOT);
#                ETOT     =  ETOT +(FRACWAT*if(BIGLAKES,scalar(0),EWAT))+(1-FRACWAT)*EACT;
#                QTOT     =  QTOT + QLOC;
#                SLOC     = (1-FRACWAT)*(S1+S2+S3_MD+INTS+SC+SCF) +          FRACWAT*if(BIGLAKES,scalar(0),S3_MD);
# report         MBE      =              (PTOT+SLOCINI-(ETOT+QTOT+SLOC));						# LOCAL MBE ERROR FOR ALL STORAGES 		(must be zero)
#
#                INTOT    = catchmenttotal(1E-9*CELLAREA*(SLOCINI+PTOT),LDD);
#                OUTTOT   = catchmenttotal(1E-9*CELLAREA*(POTABSTR_S0+ABSTR_S3+ETOT+QTOT+SLOC),LDD);
# report         MBR      = 1-if(INTOT>0,(INTOT-OUTTOT)/INTOT,0);							# MBE ERROR FOR THE BASIN (relative to input)	(must be  ONE)
# report (rep_y) MBRTSS   = timeoutput(STATIONS_DS,MBR);
#
##report         STOT_ACT = if(LANDMASK,1E-9,1E-9)*maptotal((1-FRACWAT)*CELLAREA*(S1+S2+S3_MD+INTS));			# NOT USED
##               STOT_CUM =  STOT_CUM+(S1+S2+S3_MD);									# NOT USED
##report         STOT_AVG = if(LANDMASK,STOT_CUM/time());								# NOT USED
#
# report of on total volumes as timeseries per catchment
# report (rep_y) PTOTTSS  = timeoutput(STATIONS_DS,catchmenttotal(1E-9*CELLAREA*(SLOCINI+PTOT),LDD));
# report (rep_y) ETOTTSS  = timeoutput(STATIONS_DS,catchmenttotal(1E-9*CELLAREA*ETOT,LDD));
# report (rep_y) QTOTTSS  = timeoutput(STATIONS_DS,catchmenttotal(1E-9*CELLAREA*QTOT,LDD));
# report (rep_y) STOTTSS  = timeoutput(STATIONS_DS,catchmenttotal(1E-9*CELLAREA*SLOC,LDD));
#
# - maximum and minimum error water balance
#                PTOTchk  = if(LANDMASK,catchmenttotal(1E-9*CELLAREA*(SLOCINI+PTOT),LDD));
#                ETOTchk  = if(LANDMASK,catchmenttotal(1E-9*CELLAREA*ETOT,LDD));
#                QTOTchk  = if(LANDMASK,catchmenttotal(1E-9*CELLAREA*QTOT,LDD));
#                STOTchk  = if(LANDMASK,catchmenttotal(1E-9*CELLAREA*SLOC,LDD));
#                currchk  = PTOTchk-ETOTchk-QTOTchk-STOTchk;
# report       maxwberror = if(currchk gt maxwberror, currchk, maxwberror);				# must be zero
# report       minwberror = if(currchk lt minwberror, currchk, minwberror);				# must be zero
#
# CHECK ON EACH STORAGE:
#
#				IN (interception)
#                  INchk   = ((INTS-INTS_PRE)-(PRPTOT-PRP-SNOW-INTSFLUX))*(1-FRACWAT)	;
# report       maxINerror  = if(INchk gt maxINerror, INchk, maxINerror)			;		# must be zero
# report       minINerror  = if(INchk lt minINerror, INchk, minINerror)			;		# must be zero
#
#				snow storage (not including liquid water stored)
#                  SCchk   = ((SC-SC_PRE)-(SNOW+DSC))*(1-FRACWAT)			;
# report       maxSCerror  = if(SCchk gt maxSCerror, SCchk, maxSCerror)			;		# must be zero
# report       minSCerror  = if(SCchk lt minSCerror, SCchk, minSCerror)			;		# must be zero
#
#				S1
#                  S1chk   = (S1-S1_PRE) - (P0+CR1-P1-T1ACT-ESACT-Q1_ADD)		;
# report       maxS1error  = if(S1chk gt maxS1error, S1chk, maxS1error)			;		# must be zero
# report       minS1error  = if(S1chk lt minS1error, S1chk, minS1error)			;		# must be zero
#
#				S2
#                  S2chk   = (S2-S2_PRE) - (P1+CR2-P2-CR1-T2ACT-Q2)			;
# report       maxS2error  = if(S2chk gt maxS2error, S2chk, maxS2error)			;		# must be zero
# report       minS2error  = if(S2chk lt minS2error, S2chk, minS2error)			;		# must be zero
#

################################################################################
#------------------------------------------------------------------------------#
#  R  O  U  T  I  N  G 							       #
#------------------------------------------------------------------------------#
################################################################################
#
 report (rep_y) QCHANNELWR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,QLOC   )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s) --- WR = before routing
 report (rep_y) QCHQ1___WR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,Q1     )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
 report (rep_y) QCHQ1ADDWR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,Q1_ADD )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
 report (rep_y) QCHQ2___WR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,Q2     )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
 report (rep_y) QCHQ3MODWR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,Q3MOD  )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
 report (rep_y) QCHADDQ3WR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,ADDQ3  )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
 report (rep_y) QCHQW___WR_ALL = max(0,catchmenttotal(if(BIGLAKES,0,QW     )*CELLAREA,LDD)/(3600*24*Duration*timeslice())); # (m3/s)
															    #  NOTE: all neglecting all processes in BIG LAKES
#
 lake_hd_pre = lake_hd													  ; # (m)    --- initial lake heads

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# 0 < NUMIDS < 1000
#-------------------------------------------------------------------------------
# for all streams interrupted by only one lake
#-------------------------------------------------------------------------------
# ROUTING STREAMS LOCATED UPSTREAM
#--------------------------------------------------------------------------------------------------------------------------------------------------
  QCHANNEL_WR =  if(((LAK_UP_IDS gt 15) and (LAK_UP_IDS lt 1000)), QCHANNELWR_ALL, 0);
  QCHANmem_WR =  cover(QCHANNEL_WR, 0);      					# memory for next timestep
#
  QCHANNEL_RT = min00*QCHANNEL_WR + min01*QCmin01 + min02*QCmin02 + min03*QCmin03 + min04*QCmin04 + min05*QCmin05 + min06*QCmin06 + min07*QCmin07 +
		 		    min08*QCmin08 + min09*QCmin09 + min10*QCmin10 + min11*QCmin11 + min12*QCmin12 + min13*QCmin13 + min14*QCmin14 +
				    min15*QCmin15;
  QCHANNEL_RT =  if(((LAK_UP_IDS gt 15) and (LAK_UP_IDS lt 1000)), QCHANNEL_RT  , 0);
  QCHANNEL    =  cover(QCHANNEL_RT, 0);
#--------------------------------------------------------------------------------------------------------------------------------------------------
# BIG LAKES
#-------------------------------------------------------------------------------
  QLAKEINF    = cover(if(((LAK__INLET) and ((LAK_NUMIDS gt 15) and (LAK_NUMIDS lt 1000))), upstream(LDD,QCHANNEL*24*3600/CELLAREA),0),scalar(0));	# (m/day)  inflow
  lake_hd_1   = if((                       ((LAK_NUMIDS gt 15) and (LAK_NUMIDS lt 1000))), lake_hd_pre   )	;					# (m)
  lake_hd_2   = if(  lake_hd_1 gt -99999, areaaverage(lake_hd_1+QW+QLAKEINF-QLAKBAS,LAK_NUMIDSinp))		; 					# (m)
  lake_hd_out = 0.5*(lake_hd_1+lake_hd_2)									; 					# (m)
#
# estimating QLAKEOUT (lake outflow)
  QLAKEOUT    = -9999;
  QLAKEOUT    = if(LAK_OUTLET, 1.7*CLAKE*WID_OUTLET*((max(0,lake_hd_out-LAK_SILLEL))**(1.5)), 0)		; # m3/s -- estimated lake outflow
#
# updating lake storage after all fluxes
  SW_INIT     = areaaverage(if(lake_hd_1 gt -99999, SW),LAK_NUMIDSinp)						; # m3   initial storage (only in the lakes being analyzed)
  SW_BOUT     = SW_INIT + areatotal((QW +cover(QLAKEINF,scalar(0)) -QLAKBAS)*CELLAREA,LAK_NUMIDSinp)		; # m3   before QLAKEOUT
  SW_ESTI     = SW_BOUT - areatotal(     cover(QLAKEOUT,scalar(0))*24*3600,LAK_NUMIDSinp)			; # m3   estimated storage after outflow
  SW__END     = if(SW_ESTI > 0, SW_ESTI, if(SW_BOUT > 0, 0, SW_BOUT ))						; # m3	 -- end storage after outflow
  SW__ALL     = SW__END												; # m3	 -- end storage  for reporting
  QLAKEOUT    = if(LAK_OUTLET, max(0,SW_BOUT-SW__END))/(24*3600)						; # m3/s -- lake outflow
  QLAKEOUTALL = QLAKEOUT 											; # m3/s -- lake outflow for reporting
  QLAKEOUT    = cover(QLAKEOUT, scalar(0))									;
#
# new lake heads (for MODFLOW calculation):
#-----------------------------------------------------------------------------------------------------------------------------
  lake_hd     =	if( lake_hd_1 gt -99999, (lake_hd_1 + (SW__END-SW_INIT)/(areatotal(CELLAREA,LAK_NUMIDSinp)) ))	; # m
#-----------------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# 1000 < NUMIDS < 100000
#-------------------------------------------------------------------------------
# for all streams interrupted by two lakes
#-------------------------------------------------------------------------------
# ROUTING STREAMS LOCATED UPSTREAM
#--------------------------------------------------------------------------------------------------------------------------------------------------
  QCHANNEL_WR =  if(((LAK_UP_IDS gt 1000) and (LAK_UP_IDS lt 100000)), QCHANNELWR_ALL + catchmenttotal(QLAKEOUT,LDD),0);
  QCHANmem_WR =  QCHANmem_WR + cover(QCHANNEL_WR,0);      			# memory for next timestep
#
  QCHANNEL_RT =  -9999;
  QCHANNEL_RT = min00*QCHANNEL_WR + min01*QCmin01 + min02*QCmin02 + min03*QCmin03 + min04*QCmin04 + min05*QCmin05 + min06*QCmin06 + min07*QCmin07 +
		 		    min08*QCmin08 + min09*QCmin09 + min10*QCmin10 + min11*QCmin11 + min12*QCmin12 + min13*QCmin13 + min14*QCmin14 +
				    min15*QCmin15;
  QCHANNEL_RT =  if(((LAK_UP_IDS gt 1000) and (LAK_UP_IDS lt 100000)), QCHANNEL_RT   , 0);
  QCHANNEL    =  QCHANNEL + cover(QCHANNEL_RT, 0);
#--------------------------------------------------------------------------------------------------------------------------------------------------
# BIG LAKES
#-------------------------------------------------------------------------------
  QLAKEINF    = cover(if(((LAK__INLET) and ((LAK_NUMIDS gt 1000) and (LAK_NUMIDS lt 100000))), upstream(LDD,QCHANNEL*24*3600/CELLAREA),0), scalar(0)); 	 	# (m/day)
  lake_hd_1   = if((                 ((LAK_NUMIDS gt 1000) and (LAK_NUMIDS lt 100000))), lake_hd_pre          )	;	 # (m)
  lake_hd_2   = if(  lake_hd_1 gt -99999, areaaverage(lake_hd_1+QW+QLAKEINF-QLAKBAS,LAK_NUMIDSinp))		; 	 # (m)
  lake_hd_out = 0.5*(lake_hd_1+lake_hd_2)									; 	 # (m)
#
# estimating QLAKEOUT (lake outflow)
  QLAKEOUT    = -9999;
  QLAKEOUT    = if(LAK_OUTLET, 1.7*CLAKE*WID_OUTLET*((max(0,lake_hd_out-LAK_SILLEL))**(1.5)), 0)		; # m3/s -- estimated lake outflow
#
# updating lake storage after all fluxes
  SW_INIT     = areaaverage(if(lake_hd_1 gt -99999, SW),LAK_NUMIDSinp)									; # m)   initial storage (only in the lakes being analyzed)
  SW_BOUT     = SW_INIT + areatotal((QW +cover(QLAKEINF,scalar(0)) -QLAKBAS)*CELLAREA,LAK_NUMIDSinp)					; # m3   before QLAKEOUT
  SW_ESTI     = SW_BOUT - areatotal(     cover(QLAKEOUT,scalar(0))*24*3600,LAK_NUMIDSinp)						; # m3   estimated storage after outflow
  SW__END     = if(SW_ESTI > 0, SW_ESTI, if(SW_BOUT > 0, 0, SW_BOUT ))						; # m3	 -- end storage after outflow
  SW__ALL     = cover(SW__ALL,SW__END)										; # m3	 -- end storage  for reporting
  QLAKEOUT    = if(LAK_OUTLET, max(0,SW_BOUT-SW__END))/(24*3600)						; # m3/s -- lake outflow
  QLAKEOUTALL = cover(QLAKEOUTALL,QLAKEOUT)									; # m3/s -- lake outflow for reporting
  QLAKEOUT    = cover(QLAKEOUT, scalar(0))									;
#
# new lake heads (for MODFLOW calculation):
#----------------------------------------------------------------------------------------------------------------------------------------------
  lake_hd     =	cover(lake_hd,if( lake_hd_1 gt -99999, (lake_hd_1 + (SW__END-SW_INIT)/(areatotal(CELLAREA,LAK_NUMIDSinp)) )))	; # m
#----------------------------------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# 100000 < NUMIDS < 10000000
#-------------------------------------------------------------------------------
# for all streams interrupted by three lakes
#-------------------------------------------------------------------------------
# ROUTING STREAMS LOCATED UPSTREAM
#--------------------------------------------------------------------------------------------------------------------------------------------------
  QCHANNEL_WR =  if(((LAK_UP_IDS gt 100000) and (LAK_UP_IDS lt 10000000)), QCHANNELWR_ALL + catchmenttotal(QLAKEOUT,LDD),0);
  QCHANmem_WR =  QCHANmem_WR + cover(QCHANNEL_WR,0);      			# memory for next timestep
#
  QCHANNEL_RT =  -9999;
  QCHANNEL_RT = min00*QCHANNEL_WR + min01*QCmin01 + min02*QCmin02 + min03*QCmin03 + min04*QCmin04 + min05*QCmin05 + min06*QCmin06 + min07*QCmin07 +
		 		        min08*QCmin08 + min09*QCmin09 + min10*QCmin10 + min11*QCmin11 + min12*QCmin12 + min13*QCmin13 + min14*QCmin14 +
				        min15*QCmin15;
  QCHANNEL_RT =  if(((LAK_UP_IDS gt 100000) and (LAK_UP_IDS lt 10000000)), QCHANNEL_RT   , 0);
  QCHANNEL    =  QCHANNEL + cover(QCHANNEL_RT, 0);
#--------------------------------------------------------------------------------------------------------------------------------------------------
# BIG LAKES
#-------------------------------------------------------------------------------
  QLAKEINF    = cover(if(((LAK__INLET) and ((LAK_NUMIDS gt 100000) and (LAK_NUMIDS lt 10000000))), upstream(LDD,QCHANNEL*24*3600/CELLAREA), 0), scalar(0));	# (m/day)
  lake_hd_1   = if((                 ((LAK_NUMIDS gt 100000) and (LAK_NUMIDS lt 10000000))), lake_hd_pre      )	;	# (m)
  lake_hd_2   = if(  lake_hd_1 gt -99999, areaaverage(lake_hd_1+QW+QLAKEINF-QLAKBAS,LAK_NUMIDSinp))		; 	# (m)
  lake_hd_out = 0.5*(lake_hd_1+lake_hd_2)									; 	# (m)
#
# estimating QLAKEOUT (lake outflow)
  QLAKEOUT    = -9999;
  QLAKEOUT    = if(LAK_OUTLET, 1.7*CLAKE*WID_OUTLET*((max(0,lake_hd_out-LAK_SILLEL))**(1.5)), 0)		; # m3/s -- estimated lake outflow
#
# updating lake storage after all fluxes
  SW_INIT     = areaaverage(if(lake_hd_1 gt -99999, SW),LAK_NUMIDSinp)						; # m    initial storage (only in the lakes being analyzed)
  SW_BOUT     = SW_INIT + areatotal((QW +cover(QLAKEINF,scalar(0)) -QLAKBAS)*CELLAREA,LAK_NUMIDSinp)		; # m3   before QLAKEOUT
  SW_ESTI     = SW_BOUT - areatotal(     cover(QLAKEOUT,scalar(0))*24*3600,LAK_NUMIDSinp)			; # m3   estimated storage after outflow
  SW__END     = if(SW_ESTI > 0, SW_ESTI, if(SW_BOUT > 0, 0, SW_BOUT ))						; # m3	 -- end storage after outflow
  SW__ALL     = cover(SW__ALL,SW__END)										; # m3	 -- end storage  for reporting
  QLAKEOUT    = if(LAK_OUTLET, max(0,SW_BOUT-SW__END))/(24*3600)						; # m3/s -- lake outflow
  QLAKEOUTALL = cover(QLAKEOUTALL,QLAKEOUT)									; # m3/s -- lake outflow for reporting
  QLAKEOUT    = cover(QLAKEOUT, scalar(0))									;
#
# new lake heads (for MODFLOW calculation):
#----------------------------------------------------------------------------------------------------------------------------------------------
  lake_hd     =	cover(lake_hd,if( lake_hd_1 gt -99999, (lake_hd_1 + (SW__END-SW_INIT)/(areatotal(CELLAREA,LAK_NUMIDSinp)) )))	; # m
#----------------------------------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------
# NUMIDS = 10
#-------------------------------------------------------------------------------------
# for the REMAINING STREAMS (including all streams that are not interrupted by lakes)
#-------------------------------------------------------------------------------------
# ROUTING STREAMS: UPSTREAM
#--------------------------------------------------------------------------------------------------------------------------------------------------
  QCHANNEL_WR =  if(((LAK_UP_IDS lt 12)), QCHANNELWR_ALL + catchmenttotal(QLAKEOUT,LDD),0);
  QCHANmem_WR =  QCHANmem_WR + cover(QCHANNEL_WR,0);      			# memory for next timestep
#
  QCHANNEL_RT =  -9999;
  QCHANNEL_RT = min00*QCHANNEL_WR + min01*QCmin01 + min02*QCmin02 + min03*QCmin03 + min04*QCmin04 + min05*QCmin05 + min06*QCmin06 + min07*QCmin07 +
		 		    min08*QCmin08 + min09*QCmin09 + min10*QCmin10 + min11*QCmin11 + min12*QCmin12 + min13*QCmin13 + min14*QCmin14 +
				    min15*QCmin15;
  QCHANNEL_RT =  if(((LAK_UP_IDS lt 12)), QCHANNEL_RT   , 0);
  QCHANNEL    =  QCHANNEL + cover(QCHANNEL_RT, 0);
#--------------------------------------------------------------------------------------------------------------------------------------------------

# FOR THE NEXT TIME STEP:
#
 report (rep_y)	QCmin15  = QCmin14;
 report (rep_y) QCmin14  = QCmin13;
 report (rep_y)	QCmin13  = QCmin12;
 report (rep_y)	QCmin12  = QCmin11;
 report (rep_y)	QCmin11  = QCmin10;
 report (rep_y)	QCmin10  = QCmin09;
 report (rep_y)	QCmin09  = QCmin08;
 report (rep_y)	QCmin08  = QCmin07;
 report (rep_y)	QCmin07  = QCmin06;
 report (rep_y)	QCmin06  = QCmin05;
 report (rep_y)	QCmin05  = QCmin04;
 report (rep_y)	QCmin04  = QCmin03;
 report (rep_y)	QCmin03  = QCmin02;
 report (rep_y)	QCmin02  = QCmin01;
 report (rep_y)	QCmin01  = QCHANmem_WR;

#---------------------------------------------------------
# Reporting the states and fluxes in the map format:
#---------------------------------------------------------
  report (rep_y) INTS     = if(LANDMASK, INTS)  *(1-FRACWAT);
  report (rep_y) INTS_L   = if(LANDMASK, INTS_L)*(1-FRACWAT);
  report (rep_y) SC       = if(LANDMASK, SC)    *(1-FRACWAT);
  report (rep_y) SC_L     = if(LANDMASK, SC_L)  *(1-FRACWAT);
  report (rep_y) SCF      = if(LANDMASK, SCF)   *(1-FRACWAT);
  report (rep_y) SCF_L    = if(LANDMASK, SCF_L) *(1-FRACWAT);
  report (rep_y) S1       = if(LANDMASK, S1)    *(1-FRACWAT);			# (m)	   daily reporting
  report (rep_y) S1_L     = if(LANDMASK, S1_L)  *(1-FRACWAT);
  report (rep_y) S2       = if(LANDMASK, S2)    *(1-FRACWAT);			# (m)	   daily reporting
  report (rep_y) S2_L     = if(LANDMASK, S2_L)  *(1-FRACWAT);
#
  report (rep_y) S3_MD    = if(LANDMASK, S3_MD)		    ;			# (m)	   Note: groundwater bodies are found everywhere (including in lakes and all cells with FRACWAT eq 1).
#
  report (rep_y) SW       = if(LANDMASK, SW__ALL)	    ;			# (m3)
#
  report (rep_y) EACT     = if(LANDMASK, EACT)  *(1-FRACWAT);			# (m/day)  total actual evaporation at  land surface bodies
  report (rep_y) EWAT     = if(LANDMASK, EWAT)  *   FRACWAT ;			# (m/day)  total actual evaporation at surface water bodies
  report (rep_y) EACTFLUX = if(LANDMASK, EACTFLUX)	    ;			# (m/day)  total actual evaporation at surface water bodies + land surface bodies
#
  report (rep_y) Q1       = if(LANDMASK, Q1   )*(1-FRACWAT) ;
  report (rep_y) Q1S      = if(LANDMASK, Q1S  )*(1-FRACWAT) ;
  report (rep_y) Q2       = if(LANDMASK, Q2   )*(1-FRACWAT) ;
  report (rep_y) Q3MOD    = if(LANDMASK, Q3MOD)		    ;			# (m/day)
#
  report (rep_y) ADDQ3    = if(LANDMASK, ADDQ3 )	    ;			# (m/day) 
  report (rep_y) QW       = if(LANDMASK, QW    )	    ;			# (m/day)
  report (rep_y) Q1_ADD   = if(LANDMASK, Q1_ADD)	    ;			# (m/day) 
#
  report         QCHANNEL = if(LANDMASK, QCHANNEL)	    ;			# AFTER ROUTING
#
  report (rep_y) R3       = if(LANDMASK, R3  )  *(1-FRACWAT);			# (m/day)   RCH only for the land surface cell
#                R3       = if(LANDMASK, R3  )  *(1-FRACWAT);
#
# report (rep_y) CR2map	  = if(LANDMASK, CR2   )*(1-FRACWAT); 
  report (rep_y) SATFRAC  = if(LANDMASK,SATFRAC)*(1-FRACWAT);

#----------------------
# Reporting timeseries
#----------------------

# report (rep_y) INTSTSS        = timeoutput(CLIMSTAT   ,INTS)  	;	# (m) 		all storages
# report (rep_y) SCTSS          = timeoutput(CLIMSTAT   ,SC+SCF)	;
# report (rep_y) S1TSS          = timeoutput(STATIONS_HD,S1)    	;
# report (rep_y) S2TSS          = timeoutput(STATIONS_HD,S2)    	;
# report (rep_y) S3_MDTSS       = timeoutput(CLIMSTAT   ,S3_MD) 	;
                                                                	
# report (rep_y) WACTTSS        = timeoutput(CLIMSTAT,WACT)   		;	# (m)		actual storage within rootzone  (IAS)
# report (rep_y) SATFRACTSS     = timeoutput(CLIMSTAT,SATFRAC)		;	# (-)		fraction saturated area		(IAS)

# report (rep_y) INTSFLUXTSS    = timeoutput(CLIMSTAT,INTSFLUX)		;	# (m/day)	evaporation fluxes
# report (rep_y) ESACTTSS       = timeoutput(CLIMSTAT,ESACT)   		;
# report (rep_y) T1ACTTSS       = timeoutput(CLIMSTAT,T1ACT)   		;
# report (rep_y) T2ACTTSS       = timeoutput(CLIMSTAT,T2ACT)   		;
# report (rep_y) EACTTSS        = timeoutput(CLIMSTAT,EACT)    		;	# only at land surface cells
# report (rep_y) EWATTSS        = timeoutput(CLIMSTAT,EWAT)    		;	# at all surface water cells (including BIG LAKES)
# report (rep_y) EACTFLUXTSS    = timeoutput(CLIMSTAT,EACTFLUX)    	;	# at all celss
  
# report (rep_y) Q1TSS          = timeoutput(CLIMSTAT,Q1)      		;
# report (rep_y) Q1STSS         = timeoutput(CLIMSTAT,Q1S)     		;
# report (rep_y) Q2TSS          = timeoutput(CLIMSTAT,Q2)      		;
# report (rep_y) Q3MODTSS       = timeoutput(CLIMSTAT,Q3MOD)   		;
  
  report (rep_y) QCHANNELTSS    = timeoutput(STATIONS_DS,QCHANNEL)	;
  report (rep_y) QCHANNELWR_TSS = timeoutput(STATIONS_DS,QCHANNELWR_ALL);
  report (rep_y) QCHQ1___WR_TSS = timeoutput(STATIONS_DS,QCHQ1___WR_ALL);
  report (rep_y) QCHQ1ADDWR_TSS = timeoutput(STATIONS_DS,QCHQ1ADDWR_ALL);
  report (rep_y) QCHQ2___WR_TSS = timeoutput(STATIONS_DS,QCHQ2___WR_ALL);
  report (rep_y) QCHQ3MODWR_TSS = timeoutput(STATIONS_DS,QCHQ3MODWR_ALL);
  report (rep_y) QCHADDQ3WR_TSS = timeoutput(STATIONS_DS,QCHADDQ3WR_ALL);
  report (rep_y) QCHQW___WR_TSS = timeoutput(STATIONS_DS,QCHQW___WR_ALL);
  
# report (rep_y) P1TSS	        = timeoutput(CLIMSTAT,P1)     		;
# report (rep_y) CR1TSS         = timeoutput(CLIMSTAT,CR1)    		;
# report (rep_y) CR1_ADDTSS     = timeoutput(CLIMSTAT,CR1_ADD)		;
# report (rep_y) P2TSS	        = timeoutput(CLIMSTAT,P2)     		;
# report (rep_y) CR2TSS         = timeoutput(CLIMSTAT,CR2)    		;


################################################################################
# Calculation channel discharge with ACTUAL inflow in Basel
################################################################################
  basel_infl  = timeinputscalar(basel_disch,1)*scalar(LANDMASK)								;
  QCHactBS_WR = catchmenttotal( if(BASEL_CATCH, scalar(0), if(BIGLAKES,0,QLOC)*CELLAREA),LDD)/(3600*24*Duration*timeslice()) 	;
  QCHactBS_WR = max(0,QCHactBS_WR + catchmenttotal(cover(if(scalar(STATIONS_DS) eq 66, basel_infl), scalar(0)),LDD))		; 
#
  QCHactBS_RT = min00*QCHactBS_WR + min01*QCmin01_BS + min02*QCmin02_BS + min03*QCmin03_BS + min04*QCmin04_BS + min05*QCmin05_BS + min06*QCmin06_BS + min07*QCmin07_BS +
		 		    min08*QCmin08_BS + min09*QCmin09_BS + min10*QCmin10_BS + min11*QCmin11_BS + min12*QCmin12_BS + min13*QCmin13_BS + min14*QCmin14_BS +
		 		    min15*QCmin15_BS;
  report (rep_y) QCHactBS_RT_TSS = timeoutput(STATIONS_DS,QCHactBS_RT);
#
#--------------------------------------------------------------------------------------------------------------------------------------------------
# FOR THE NEXT TIME STEP:
#
 report (rep_y)	QCmin15_BS = QCmin14_BS ;
 report (rep_y) QCmin14_BS = QCmin13_BS ;
 report (rep_y)	QCmin13_BS = QCmin12_BS ;
 report (rep_y)	QCmin12_BS = QCmin11_BS ;
 report (rep_y)	QCmin11_BS = QCmin10_BS ;
 report (rep_y)	QCmin10_BS = QCmin09_BS ;
 report (rep_y)	QCmin09_BS = QCmin08_BS ;
 report (rep_y)	QCmin08_BS = QCmin07_BS ;
 report (rep_y)	QCmin07_BS = QCmin06_BS ;
 report (rep_y)	QCmin06_BS = QCmin05_BS ;
 report (rep_y)	QCmin05_BS = QCmin04_BS ;
 report (rep_y)	QCmin04_BS = QCmin03_BS ;
 report (rep_y)	QCmin03_BS = QCmin02_BS ;
 report (rep_y)	QCmin02_BS = QCmin01_BS ;
 report (rep_y)	QCmin01_BS = QCHactBS_WR;
#
################################################################################
#-------------------------------------------------------------------------------
#  M O D F L O W   M O D E L
#-------------------------------------------------------------------------------
################################################################################

  waterlv = (RIV__WIDTH**(-3/5)) * (QCHANNEL**(3/5)) * ((RIV__SLOPE)**(-3/10)) *(RIVmanning**(3/5))	;	# river water level (m)
  waterlv = if(waterlv lt 0.01, scalar(0), waterlv)							;	# if there are only 1 cm water in the channel, the water in the channel will not infiltrate
  waterlv = cover(waterlv, scalar(0))									;	# for RIV__WIDTH = 0, water level = 0 (no river)
#
  rivhead_ALL = cover(         max(rivbott, rivbott + waterlv), drndelv, scalar(-88888))		;	# for ALL CELLS
#
# CALCULATING WATER LEVEL ABOVE THE FLOOD PLAIN
  DZRIV_FPL   = max(0,  rivhead_ALL - Z0_floodplain)							; 	#  m  water level above the floodplain (not distributed)
  DZRIV_FPL   = DZRIV_FPL * chanel_area/CELLAREA							; 	#  m  water level above the floodplain (distributed within the cell)
#
  DZRIV       = max(0,Z0_floodplain-MIN_DEM3s) + DZRIV_FPL						;	#  m  water level above the minimum DEM
# DZRIV       = 				 DZRIV_FPL						;	#  m  water level above the flood plain		# not USED
#
#- Fractions of SATURATED/FLOODED AREA (in percentage) based on surface water levels:
#------------------------------------------------------------------------------------------------
   CRFRAC_RIV =         min(1.0,1.00-(DZ0100-DZRIV)*0.10/max(1e-3,DZ0100-DZ0090)       	    )	;
   CRFRAC_RIV = if(DZRIV<DZ0090,0.90-(DZ0090-DZRIV)*0.10/max(1e-3,DZ0090-DZ0080),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0080,0.80-(DZ0080-DZRIV)*0.10/max(1e-3,DZ0080-DZ0070),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0070,0.70-(DZ0070-DZRIV)*0.10/max(1e-3,DZ0070-DZ0060),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0060,0.60-(DZ0060-DZRIV)*0.10/max(1e-3,DZ0060-DZ0050),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0050,0.50-(DZ0050-DZRIV)*0.10/max(1e-3,DZ0050-DZ0040),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0040,0.40-(DZ0040-DZRIV)*0.10/max(1e-3,DZ0040-DZ0030),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0030,0.30-(DZ0030-DZRIV)*0.10/max(1e-3,DZ0030-DZ0020),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0020,0.20-(DZ0020-DZRIV)*0.10/max(1e-3,DZ0020-DZ0010),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0010,0.10-(DZ0010-DZRIV)*0.05/max(1e-3,DZ0010-DZ0005),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0005,0.05-(DZ0005-DZRIV)*0.04/max(1e-3,DZ0005-DZ0001),CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV<DZ0001,0.01-(DZ0001-DZRIV)*0.01/max(1e-3,DZ0001)       ,CRFRAC_RIV )	;
   CRFRAC_RIV = if(DZRIV le 0,0,  CRFRAC_RIV )							;
#
   CRFRAC_RIV = cover(max(0,min(1,max(CRFRAC_RIV,(chanel_area/CELLAREA)))),scalar(0))		;
#  CRFRAC_RIV = scalar(0)									;
#
# waterlvadd  = max(0,cover(if(LANDMASK,DZRIV_FPL + (1-          CRFRAC_RIV) *DZRIV_FPL),0))	; #  m 	additional water level above the flood plain									# not USED
  waterlvadd  = max(0,cover(if(LANDMASK,DZRIV_FPL + (1-min(1,1.5*CRFRAC_RIV))*DZRIV_FPL),0))	; #  m 	additional water level above the flood plain	# NOTE: The "1.5" is introduced as the correction factor.  	#     USED  
# waterlvadd  = scalar(0)									; #  m  ignoring additional water above the flood plain									# not USED
#
  rivhead_ALL =     if(rivhead_ALL gt Z0_floodplain, waterlvadd + Z0_floodplain, rivhead_ALL)	; # +m  WATER LEVELS at river networks
# rivhead_ALL =    min(rivhead_ALL, cover(WLESMOOTH, DEM30s, scalar(-88888)))			; # +m	maximum river level = flood plain elevation									# not USED
  rivhead_ALL =  cover(lake_hd, rivhead_ALL)							;
  rivhead_ALL = if( abs(rivhead_ALL) lt 1e-20, scalar(0), rivhead_ALL)				;
#
  rivhead     = (1/31)*(rivhead_ALL + rhmin01 + rhmin02 + rhmin03 + rhmin04 + rhmin05 + rhmin06 + rhmin07 + rhmin08 + rhmin09 + rhmin10 + rhmin11 + rhmin12 + rhmin13 + rhmin14 + rhmin15 + rhmin16 + rhmin17 + rhmin18 + rhmin19 + rhmin20 + rhmin21 + rhmin22 + rhmin23 + rhmin24 + rhmin25 + rhmin26 + rhmin27 + rhmin28 + rhmin29 + rhmin30);
# rivhead     = (1/10)*(rivhead_ALL + rhmin01 + rhmin02 + rhmin03 + rhmin04 + rhmin05 + rhmin06 + rhmin07 + rhmin08 + rhmin09)			;
#
# FOR THE NEXT TIME STEP:
#
 report (rep_y)	rhmin30  = rhmin29	;	 report (rep_y)	rhmin29  = rhmin28	;	 report (rep_y)	rhmin28  = rhmin27	;
 report (rep_y)	rhmin27  = rhmin26	;	 report (rep_y)	rhmin26  = rhmin25	;	 report (rep_y)	rhmin25  = rhmin24	;
 report (rep_y)	rhmin24  = rhmin23	;	 report (rep_y)	rhmin23  = rhmin22	;	 report (rep_y)	rhmin22  = rhmin21	;
 report (rep_y)	rhmin21  = rhmin20	;	 report (rep_y)	rhmin20  = rhmin19	;	 report (rep_y)	rhmin19  = rhmin18	;
 report (rep_y)	rhmin18  = rhmin17	;	 report (rep_y)	rhmin17  = rhmin16	;	 report (rep_y)	rhmin16  = rhmin15	;
 report (rep_y)	rhmin15  = rhmin14	;	 report (rep_y)	rhmin14  = rhmin13	;	 report (rep_y)	rhmin13  = rhmin12	;
 report (rep_y)	rhmin12  = rhmin11	;	 report (rep_y)	rhmin11  = rhmin10	;	 report (rep_y)	rhmin10  = rhmin09	;
 report (rep_y)	rhmin09  = rhmin08	;	 report (rep_y)	rhmin08  = rhmin07	;	 report (rep_y)	rhmin07  = rhmin06	;
 report (rep_y)	rhmin06  = rhmin05	;	 report (rep_y)	rhmin05  = rhmin04	;	 report (rep_y)	rhmin04  = rhmin03	;
 report (rep_y)	rhmin03  = rhmin02	;	 report (rep_y)	rhmin02  = rhmin01	;	 report (rep_y)	rhmin01  = rivhead_ALL	;
#
 rivhead     =  cover(rivhead, scalar(-88888))		;
#
# adding the RIV package
  res = mf::setRiver( rivhead, rivbott, rivcond,     1)	;
#
# adding the DRN package
  res = mf::setDrain( rivhead, drncond, 1)		;
#
# adding the RCH package
  RCH = cover((R3-ADDQ3)*CELLAREA/(3000*3000),scalar(0));
# RCH = cover((R3      )*CELLAREA/(3000*3000),scalar(0));
  RCH = if(abs(RCH) lt 1e-20, scalar(0), RCH)		;
  res = mf::setRecharge(RCH, 1) 			;
#
  report (rep_y) lake_hd     = lake_hd					;
  report (rep_y) rivhead     = if(LANDMASK, rivhead)			;
  report (rep_y) lake_hd_TSS = timeoutput(STATIONS_LK, lake_hd	  )	;
  report (rep_y) QLAKEOUTALL =         if(   LANDMASK, QLAKEOUTALL)	;
  report (rep_y) QLAKEOUTTSS = timeoutput(STATIONS_LK, QLAKEOUTALL)	;
#
  report (rep_y) rivhead_TSS = timeoutput(STATIONS_DS, rivhead    )	;
#
#===============================================================================================================================================================
  res = mf::run()						   	;	# running MODFLOW
#===============================================================================================================================================================
#
# retrieve head values:
                 gw_head_mod = mf::getHeads(1)				;
  report         gw_head     =           if(LANDMASK, gw_head_mod)	;
  report (rep_y) gw_head_TSS = timeoutput(STATIONS_HD,gw_head)		;

# retrieve  baseflow values:
  gw_baseflow_riv  	     = mf::getRiverLeakage(1)			;	# unit: m3/day	POSITIVE entering the aquifer
  gw_baseflow_drn  	     = mf::getDrain(1)				;	# unit: m3/day	POSITIVE entering the aquifer
  report (rep_y) gw_baseflow = gw_baseflow_riv + gw_baseflow_drn	;	# unit: m3/day	POSITIVE entering the aquifer
  report (rep_y) gw_base_mpd = if(LANDMASK,gw_baseflow/(CELLAREA))	;	# unit: m1/day	POSITIVE entering the aquifer
#
  Q3MOD          	     = gw_baseflow*scalar(-1)/(CELLAREA)	;	# unit: m1/day	NEGATIVE entering the aquifer	
  Q3MOD          	     = if(LANDMASK,cover(Q3MOD,scalar(0)))	;	# unit: m1/day	NEGATIVE entering the aquifer
#
#=========================================================================================================================================================================================

# REPORTING percentage of S1, S2 and S1+S2 in 30 arc-min resolution (tss files,	unit in %)
   report         S1TSS_30min = timeoutput(CLIMSTAT,areaaverage(( S1    /(max(1E-9,SC1)))    *(1-FRACWAT),ID_30mincell));
   report         S2TSS_30min = timeoutput(CLIMSTAT,areaaverage(( S2    /(max(1E-9,SC2)))    *(1-FRACWAT),ID_30mincell));
   report         STTSS_30min = timeoutput(CLIMSTAT,areaaverage(((S1+S2)/(max(1E-9,SC1+SC2)))*(1-FRACWAT),ID_30mincell));
#
#
# separating areas belonging to sedimentary and mountainous areas:
#
   report (rep_y) S1TSS_30m_sd = timeoutput(CLIMSTAT,areaaverage(( S1    /(max(1E-9,SC1_SED)))        *(1-FRACWAT),ID_30mincell));
   report (rep_y) S2TSS_30m_sd = timeoutput(CLIMSTAT,areaaverage(( S2    /(max(1E-9,SC2_SED)))        *(1-FRACWAT),ID_30mincell));
   report (rep_y) STTSS_30m_sd = timeoutput(CLIMSTAT,areaaverage(((S1+S2)/(max(1E-9,SC1_SED+SC2_SED)))*(1-FRACWAT),ID_30mincell));
#
   report (rep_y) S1TSS_30m_mn = timeoutput(CLIMSTAT,areaaverage(( S1    /(max(1E-9,SC1_MON)))        *(1-FRACWAT),ID_30mincell));
   report (rep_y) S2TSS_30m_mn = timeoutput(CLIMSTAT,areaaverage(( S2    /(max(1E-9,SC2_MON)))        *(1-FRACWAT),ID_30mincell));
   report (rep_y) STTSS_30m_mn = timeoutput(CLIMSTAT,areaaverage(((S1+S2)/(max(1E-9,SC1_MON+SC2_MON)))*(1-FRACWAT),ID_30mincell));

