#===============================================================================================================================
# PCRGLOB-WB-MOD for Rhine and Meuse Basin:
# - This is a steady state model for estimating the initial groundwater heads.
# - This must be combined by the other script: pcrglobwb_rm_steadywbf_MAR2012.mod 
#
# -   created by Edwin H. Sutanudjaja --- 19 March 2012
# - modfified by Edwin H. Sutanudjaja --- 05  June 2012 set PCG HCLOSE = 0.100 (to ease the convergence) 
# 
#===============================================================================================================================

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
# LAKES (only for big/large ones)
#================================================================================================================================================================================================
# LAK_BOTTOM     = 						;		# +m   		assumption for lake bottom elevation # NOT USED, we assume deep lakes always containing water.
  LAK_SILLEL     =   ..\maps01\lake_08Jul2011_nc1109.wle.map	;		# +m   		assumption for lake   sill elevation = estimated water level from HYDROSHEDS
  LAK__INLET_ID  =   ..\maps01\lake_24Mar2011_nc1109.inlet.map	;		#  - 		boolean map for lake  inlet locations 		# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  LAK_OUTLET_ID  =   ..\maps01\lake_24Mar2011_nc1109.outlt.map	;		#  -    	boolean map for lake outlet locations 		# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  LAK_NUMIDSinp  =   ..\maps01\lake_24Mar2011_nc1109.ids.map	;		#  -    	ids for lakes
  LAK_UP_IDSnom  =   ..\maps01\lake_24Mar2011_nc1109.cat.map	;		#  - 		ids for streams located upstream the lakes	# FRACWAT ne 1
  LAK_SHORES     =   ..\maps01\lake_24Mar2011_nc1109.shr.map	;		#  - 		boolean map for lakeshores			# IBOUND = 1 but FRACWAT = 1 # RIV PAC IS DEFINED
  CLAKE          =   scalar(1)					;		#  -    	constant for lake discharge
#
# river/channel properties
#================================================================================================================================================================================================
  RIVbedresi_inp =      scalar(1.0000)				;               #  day		bed resistance values
  RIVmanning 	 =      scalar(0.0450)				;		# [m**(1/3)]/s	river manning coeffients
  RIV__WIDTH_inp =   ..\maps01\riv_width_30july_2011.map	;		#  m		river width			(only defined in some cells)
  RIV__SLOPE_inp =   ..\maps01\riv_slope_30july_2011.map	;		#  m/m		river longitudinal slope	(only defined in some cells)
  RIV_BOTTOM_inp =   ..\maps01\rivbottom_30july_2011.map	;		#  m		bed elevation 			(only defined in some cells)
  RIV_DEPTH__inp =   ..\maps01\riv_depth_30july_2011.map	;		#  m		river depth (bankfull)		(     defined in alle cells) 
  RIV_BOTTOM_out =   results\rivbott_allcells.map		;		#  m		drain bed elevation		(     defined in alle cells)
#
# aquifer properties
#================================================================================================================================================================================================
  aquifer_map    =   ..\maps01\aquifer_28JULY2011.map		;		#  m		aquifer classification map	Note: #1 for productive aquifer
  aquifthick	 =      scalar(50.000)				;               #  m		aquifer thickness
  log_Pm_inp     =   ..\maps01\mean_logP_06MAR2012.map		;		#  m		mean of log permeability			(Gleeson et al., 2011)
# log_Pstdev     =   						;		#  		standard deviation of log permeability		(Gleeson et al., 2011)			# not USED
# log_Pm_add     =     						;		#  		additional values to modify permeability	 			range = [-2,2]	
  log_Pm_add_sed =     $1					;		#  		additional values to modify permeability of the sedimentary basin 	range = [-2,2]	
  log_Pm_add_mon =     $2					;		#  		additional values to modify permeability of the mountainous areas 	range = [-2,2]	
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
#================================================================================================================================================================================================
# TIME SERIES OUTPUT MAPS and TSSs:
  gw_head	 =   results\gw_headd.ini    			;		#  m 		groundwater head - daily   # from MODFLOW

areamap
 LANDMASK;

timer
 1 1 1;                                    					#  starting step, end step, daily time step
 rep_y = endtime;				    				#  yearly report, end report, for time series

initial

# G E N E R A L
#=============================================================================================================================================================
#
  DEM30s	= if(LANDMASK,DEM30s_inp)			;		# +m		DEM 30 arc-second 

# report Z0_floodplain 	        =  cover(WLESMOOTH, MIN_DEM3s, DEM30s)	     								; 	# +m	flood plain elevation
# report Z0_floodplain          =  cover(cover(WLESMOOTH, min(Z0_fldpln_inp,DEM30s)), MIN_DEM3s, DEM30s)				;	# +m	flood plain elevation (USED)	
         Z0_floodplain          =  cover(cover(WLESMOOTH, min(Z0_fldpln_inp,DEM30s)), MIN_DEM3s, DEM30s)				;	# +m	flood plain elevation (USED)	
#      
# Base of groundwater storage (that can contribute to ):
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
#
#
####################################################################################################################################################################################################################################################################################################################################
#  MODFLOW MODEL								
####################################################################################################################################################################################################################################################################################################################################
#
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
# l1_ibound_set =    if(LAK_SHORES, scalar(1), cover(l1_ibound_set, if(BIGLAKES, scalar(0))))		;	# NO FLOW in lake areas, only lakeshore (ACTIVE AS RIVER).	# not USED
  l1_ibound     =    nominal(cover(if(LANDMASK,l1_ibound_set), scalar(0)))				;	# NO FLOW outside basin
  res = mf::setBoundary(l1_ibound, 1);

# SHEAD (starting head)
# gw_head_INI_FULL =  cover(gw_head_INI     ,-9999)							;	# used only for transient MODFLOW runs
  gw_head_INI_FULL =  cover(         BASE_S3,-9999)							;
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
# RIVER and LAKE CONDUCTANCE:
  RIVbedresi 	 = RIVbedresi_inp;
# rivcond = cover(if(BIGLAKES, (1/1000000000)*CELLAREA), (1/RIVbedresi)*        RIV__WIDTH *((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # high bed resistance in large lakes (no water exchanges)			   # not USED .
# rivcond = cover(if(BIGLAKES, (1/RIVbedresi)*CELLAREA), (1/RIVbedresi)*        RIV__WIDTH *((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # same bed resistance values for lakes & rivers				   # not USED
  rivcond = cover(if(BIGLAKES, (1/RIVbedresi)*CELLAREA), (1/RIVbedresi)*max(0.5,RIV__WIDTH)*((CELLAREA*2)**(0.5)), scalar(0)); #  m2/day  # same bed resistance values for lakes & rivers, with minimum values of rivcond  #     USED	
  rivcond = cover(if(rivbott gt -50000,rivcond), scalar(0))					;
  rivcond = cover(if(BIGLAKES, rivcond, if(RIV__WIDTH gt 25, rivcond, scalar(0))), scalar(0))	; # RIVER PACKAGE only defined in lakes and major rivers (where there are water exchanges in two directions: surface and ground-water)
  rivcond = if(abs(rivcond) lt 1e-20, scalar(0) , rivcond )					; # rivbott is THE VARIABLE SUPPLIED to RIVER PACKAGE
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

  res = mf::setPCG(500, 250, 1, 0.100, 10, 0.98, 2, 1)	;	# res    = mf::setPCG(MXITER, ITERI, NPCOND, HCLOSE, RCLOSE, RELAX, NBPOL, DAMP) ;
								# NPCOND = 1 ; Modified Incomplete Cholesky 			# Confirm to PTM!
								# NBPOL  = 2 ; but we do not use it (since NPCOND = 1)
								# DAMP   = 1 ; no damping (DAMP introduced in MODFLOW 2000) 	# Confirm to PTM!
#
  res   = mf::setDISParameter(4, 2, 1, 1, 1, 1)		;	# res = mf::setDISParameter(ITMUNI,LENUNI,PERLEN,NSTP,TSMULT,SSTR);
								# ITMUNI indicates the time unit (0: undefined, 1: seconds, 2: minutes, 3: hours, 4: days, 5: years);
								# LENUNI indicates the length unit (0: undefined, 1: feet, 2: meters, 3: centimeters);
								# PERLEN is the duration of a stress period;
								# NSTP is number of timestep within a stress period;
								# TSMULT is the multiplier for the length of the successive iterations;
								# SSTR 0 - transient, 1 - steady state.

# CONSTANT CHANNEL DISCHARGE and WATER LEVELS:
###################################################################################################################################################
  QCHANNEL	= AVGDISCH;
#
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
  lake_hd     =  LAK_SILLEL									; # +m  WATER LEVELS at lakes
#
  rivhead_ALL = if(LANDMASK,cover(lake_hd, rivhead_ALL))	;	
  rivhead     =  cover(rivhead_ALL, scalar(-88888))		;
#
# CONSTANT RIVER and DRAIN PACKAGE  
###################################################################################################################################################
# adding the RIV package and DRN PACKAGE		;
  res = mf::setRiver( rivhead, rivbott, rivcond,     1)	;
  res = mf::setDrain( rivhead, drncond, 1)		;
#
# INITIAL CONDITION of AVERAGE RECHARGE (constant, without fast component of baseflow):
###################################################################################################################################################
  R3  		= AVG_RECH				;

dynamic

################################################################################
#-------------------------------------------------------------------------------
#  M O D F L O W   M O D E L
#-------------------------------------------------------------------------------
################################################################################
#
#
# adding the RCH package
  RCH = cover((R3      )*CELLAREA/(3000*3000),scalar(0));
  RCH = if(abs(RCH) lt 1e-20, scalar(0), RCH)				;
  res = mf::setRecharge(RCH, 1) 					;
#
#===============================================================================================================================================================
  res = mf::run()						   	;	# running MODFLOW
#===============================================================================================================================================================
#
# retrieve head values:
#
                 gw_head_mod = mf::getHeads(1)				;
  report         gw_head     =           if(LANDMASK, gw_head_mod)	;
