#-script
class pcrglobRoutingScheme(pcrm.DynamicModel):

	def __init__(self,currentDate,endDate,\
		nrIterDef= 12,nrIterBuf= 1.25):
		pcrm.DynamicModel.__init__(self)
		#-initialization (binding section)
		#-the model is called with some objects
		# used to define the sub-loop for the routing scheme
		#-maps are read in here using global file names
		#-constants
		# duration of timestep in seconds and counter of subtime steps
		self.timeSec= 86400
		# betaQ [-]: constant of kinematic wave momentum equation
		self.betaQ= 0.6
		#-definition of start and end date and
		# parameters for sub-loop definition
		self.currentDate= currentDate
		self.endDate= endDate
		self.nrIterBuf= nrIterBuf
		self.nrIterDef= nrIterDef
		#-clone and cell area in m2
		self.clone= pcr.readmap(cloneMap)
		self.cellArea= pcr.readmap(cellAreaMap)
		#-drainage direction (ldd) and
		# channel characteristics (static)
		self.ldd= pcr.readmap(lddMap)
		self.gradChannel= pcr.readmap(gradChannelMap)
		self.manN= pcr.readmap(combChannelManNMap)
		self.channelWidth= pcr.readmap(combChannelWidthMap)
		self.channelLength= pcr.readmap(combChannelLengthMap)
		#-lake characteristics: 
		# IDs of selected lakes, their area as contained by the GLWD1 dataset
		# or as imposed by ldd (km2), estimated volume (km3) and average flooded fraction
		self.lakeID= pcr.readmap(lakeIDMap)
		self.lakeArea= pcr.readmap(lakeAreaMap)
		self.lakeFrac= pcr.readmap(lakeFracMap)
		self.lakeOutlet= pcr.readmap(lakeOutletMap)
		#self.lakeID= pcr.spatial(pcr.nominal(0))
		#self.lakeArea= pcr.scalar(0)
		#self.lakeFrac= pcr.scalar(0)
		#self.lakeOutlet= pcr.boolean(0)
		#-maximal iceThickness
		self.maxIceThickness= pcr.readmap(maxIceThicknessMap)
		#-locations for water balance evaluation and basin outlets
		self.massBalEval= pcr.readmap(massBalEvalMap)
		self.basinOutlet= pcr.readmap(basinOutletMap)
		#-inital channel discharge and
		# available storage per surface water component
		# as well as initial water temperature and ice thickness
		self.QC= pcr.readmap(iniQCFileName)
		self.channelStor= pcr.readmap(iniChannelStorFileName)
		self.lakeStor= pcr.readmap(iniLakeStorFileName)
		self.tw= pcr.readmap(iniTWFileName)
		self.wi= pcr.readmap(iniWIFileName)
		#-energy balance, proxy for temperature of groundwater store: mean annual temperature
		# and reduction in the temperature for falling rain
		self.avgT= pcr.readmap(avgTMap)+273.15
		self.deltaTPrec= pcr.scalar(1.5)
		#-table to convert cloud cover to sunshine hours
		# and constants to calculate radiation according to
		# Doornkamp & Pruitt
		#~ self.sunFracTBL= os.path.join(pathMaps,'sunhoursfrac.tbl')
		#~ self.radCon= 0.25
		#~ self.radSlope= 0.50
		#-stefan-boltzman constant [W/m2/K]
		self.sigma= 5.87e-8
		#-conversion factor
		self.convEnergy= 1.

	def initial(self):
		#-initial section
		#-counter of elapsed subtimesteps
		self.timer= 0
		self.lastValidTimeStep= 0
		#-creation of channel LDD and mask for mass balance check
		self.lakeMask= self.lakeID != 0
		self.channelLDD= pcr.lddrepair(pcr.ifthen(pcr.pcrnot(self.lakeMask),self.ldd))
		self.channelLDD= pcr.ifthen(self.clone,pcr.cover(self.channelLDD,\
			pcr.ldd(5)))
		#-fraction of static channels
		self.channelFrac= self.channelWidth*\
			self.channelLength/self.cellArea
		#-check on initial storages and channel discharge
		self.QC= pcr.ifthenelse(pcr.pcrnot(self.lakeMask),\
		self.QC,0)
		self.channelStor= pcr.ifthenelse(pcr.pcrnot(self.lakeMask),\
		pcr.cover(self.channelStor,0),0)
		self.lakeStor= pcr.ifthenelse(self.lakeMask,\
		pcr.cover(self.lakeStor,0),0)
		#-initialization of cumulative volumes and initial storage
		# for mass balance check
		self.totStor= self.channelStor+self.lakeStor
		self.totStorIni= pcr.catchmenttotal(self.totStor+\
			pcr.ifthenelse(self.lakeMask,self.lakeFrac*self.wi,\
			self.channelFrac*self.wi)*self.cellArea,self.ldd)
		self.totQ= pcr.scalar(0)
		self.dtotStor= pcr.scalar(0)
		#-constants for the energy balance
		# tt:       threshold temperature for snowmelt
		# rho_w:    density of water [kg/m3]
		# lv:       latent heat of vaporization [J/kg]
		# lf:       latent heat of fusion [J/kg]
		# cp:       specific heat of water [J/kg/degC]
		# hw:       heat transfer coefficient for water [W/m2/degC]
		# hi:       heat transfer coefficient for ice [W/m2/degC]
		# aw:       albedo of water [-]
		# ai:       albedo of snow and ice [-]
		self.tt= pcr.scalar(273.15)
		self.rho_w= pcr.scalar(1000)
		self.lv= pcr.scalar(2.5e6)
		self.lf= pcr.scalar(3.34e5)
		self.cp= pcr.scalar(4190)
		self.hw= pcr.scalar(20)
		self.hi= pcr.scalar(8.0)
		self.aw= pcr.scalar(0.15)
		self.ai= pcr.scalar(0.50)
	
	def courantCondition(self,storQ,disQ):
		#-returns the duration of the subloop in terms of nr
		# iterations and duration in seconds relative to the 
		# overall timestep
		limTime= pcr.ifthen(pcr.pcrnot(self.lakeMask) & (disQ > 1),\
			storQ/disQ)
		limTime= pcr.ifthen(limTime<self.timeSec/self.nrIterDef,limTime)
		corStor= pcr.ifthen(limTime>0,disQ)
		corStor= pcr.ifthenelse(pcr.maptotal(corStor)>0,\
			corStor/pcr.max(1,pcr.maptotal(corStor)),1)
		limTime= pcr.maptotal(limTime*corStor)
		deltaTime, valid= pcr.cellvalue(limTime,1)
		if deltaTime <> 0:
			deltaTime= deltaTime
		else:
			deltaTime= self.timeSec/self.nrIterDef
		deltaTime= deltaTime/self.nrIterBuf
		nrIter= max(self.nrIterDef,int(self.timeSec/deltaTime+1))
		while (float(self.timeSec)/nrIter) % 1 <> 0:
			nrIter+= 1
		nrIter= nrIter
		deltaTime= self.timeSec/nrIter
		return nrIter,deltaTime
					
	def fluxStorChk(self,storFlux,storState,absoluteFlux= False):
		#-returns the correction factor to reduce the flux -loss, negative-
		# to a state that can be maintained with the current storage
		if absoluteFlux:
			corStor= pcr.ifthenelse(storFlux>0,pcr.min(1,storState/storFlux),1)
		else:
			corStor= pcr.ifthenelse(storFlux<0,\
				-pcr.min(-storFlux,storState)/storFlux,1)
			corStor= pcr.max(0,corStor)
		return corStor
								
	def momentumEQKW(self,storState,manN,ni):
		#-returns the characteristics of the momentum equation
		# for the kinematic wave given storage and channel characteristics
		# dependent on the presence of ice and corresponding manning's n
		a= storState/self.channelLength
		p= 2*a/self.channelWidth+(2-ni)*self.channelWidth
		alpha= (manN*p**(2.0/3.0)*self.gradChannel**-0.5)**self.betaQ
		return a,p,alpha
									
	def dynamic(self):
		#-dynamic section
		#-evaluate vertical changes to obtain new storage
		# for channels and lakes
		# then calculate the new discharge
		# and evaluate the lateral changes within the current sub-timestep
		#-evaluation of the current date: return current month required for
		print 'processing %s' % self.currentDate.date(),
		#-reading meteo files from CRU dataset of first day of the month
		if self.currentDate.day == 1:
			#-initialization of monthly totals
			# sN:            number of days in month
			# sxQ:           monthly sum of daily discharge
			# sx2Q           monthly sum of squares, daily discharge
			# sxTw:          monthly sum of daily water temperature
			# sx2Tw:         monthly sum of daily water temperature
			# sxdT:          monthly sum of daily deviation between water and air temperature
			# sx2dT:         monthly sum of daily deviation between water and air temperature
			self.sN= 0
			self.sxQ= pcr.scalar(0)
			self.sx2Q= pcr.scalar(0)
			self.sxTw= pcr.scalar(0)
			self.sx2Tw= pcr.scalar(0)
			self.sxdT= pcr.scalar(0)
			self.sx2dT= pcr.scalar(0)
		#-initializing sum of daily discharge and average water temperature and height
		QC_daily= pcr.scalar(0)
		tw_daily= pcr.scalar(0)
		wi_daily= pcr.scalar(0)
		watHeight_daily= pcr.scalar(0)
		#-reading in fluxes over land and water area for current time step
		# note that the different compontents of runoff and water evaporation
		# are read in to calculate their contribution to the surface water
		# energy balance and to return the total runoff components
		# specific runoff and evaporation in [m/d], incoming shortwave radiation (W/m2)
		ta= self.readmap(taFileName)
		vapourPressure= self.readmap(relHumFileName)*0.611*pcr.exp((17.3*ta)/(237.3+ta))
		ta+= 273.15
		rsw= self.readmap(radswFileName)
		prp=  self.readmap(prpFileName)
		EWat= self.readmap(EWatFileName)
		Q1= self.readmap(Q1FileName)
		Q2= self.readmap(Q2FileName)
		Q3= self.readmap(Q3FileName)
		try:
			potentialAbstraction= pcr.readmap(pcrm.generateNameT(totdFileName,self.currentTimeStep()))
			self.lastValidTimeStep= self.currentTimeStep()
		except:
			potentialAbstraction= pcr.readmap(pcrm.generateNameT(totdFileName,self.lastValidTimeStep))		
		landQ= Q1+Q2+Q3
		landT= pcr.cover(Q1/landQ*pcr.max(self.tt+0.1,ta-self.deltaTPrec)+\
			Q2/landQ*pcr.max(self.tt+0.1,ta)+\
			Q3/landQ*pcr.max(self.tt+5.0,self.avgT),ta)
		#-atmospheric emssivity
		self.eAt= pcr.min(1.,1.72*(vapourPressure/ta)**(1./7.))
		#-Definition of subloop
		#-explicit scheme has to satisfy Courant condition
		nrIter, deltaTime= self.courantCondition(self.channelStor,self.QC)
		print '\tevaluating %02d substeps of %4d sec each' % (nrIter,deltaTime)
		#-Subloop for routing and energy scheme
		for nrICur in range(0,nrIter):
			#-timer
			self.timer+= 1
			#-fraction of land surface in each cell given current extent of
			# lake and channel areas (fixed)
			watFrac= self.channelFrac+self.lakeFrac
			landFrac= 1-watFrac
			landQCont= pcr.max(0,landFrac/watFrac*landQ)
			#-energy balance, all totals in [MJ]
			# totStorLoc: 1D storage used for energy scheme [m]
			# totEW:      energy storage in surface water per m2 surface area
			totStorLoc= pcr.max(0.25,self.totStor/(watFrac*self.cellArea))
			totEW= self.convEnergy*totStorLoc*self.tw*self.cp*self.rho_w
			actualDemand= pcr.max(0.,pcr.min(potentialAbstraction/watFrac,\
				0.75*self.totStor/(watFrac*self.cellArea)))
			#-surface water energy fluxes [W/m2]
			# within the current time step
			#-ice formation evaluated prior to routing to account for loss
			# in water height, vertical change in energy evaluated,
			# warming capped to increase to air temperature
			# noIce:    boolean variable indicating the absence of ice,
			#           false when ice is present or when the flux to the
			#           ice layer is negative, indicating growth
			# SHI:       surface energy flux (heat transfer phi) of ice (+: melt)
			# SHW:      heat transfer to surface water
			# SHR:      heat transfer due to short and longwave radiation
			# SHA:      advected energy due to rain or snow
			# SHQ:      advected energy due to lateral inflow
			# SHL:      latent heat flux, based on actual open water evaporation
			#           to be evaluated when actual evap is known
			shi= self.hi*(ta-self.tt)
			shw= self.hi*(self.tt-self.tw)
			noIce= pcr.ifthenelse(self.wi > 0,pcr.boolean(0),\
				pcr.ifthenelse(((shi-shw) < 0) & (ta < self.tt),\
				pcr.boolean(0),pcr.boolean(1)))
			shw= pcr.ifthenelse(noIce,self.hw*(ta-self.tw),shw)
			shr= (1-pcr.ifthenelse(noIce,self.aw,self.ai))*rsw
			shr= shr-self.sigma*(pcr.ifthenelse(noIce,\
				self.tw,self.tt)**4-self.eAt*ta**4)
			sha= prp*pcr.max(self.tt+0.1,ta-self.deltaTPrec)*self.cp*self.rho_w/self.timeSec
			shq= landQCont*landT*self.cp*self.rho_w/self.timeSec
			shq-= actualDemand*self.tw*self.cp*self.rho_w/self.timeSec
			#-ice formation
			# DSHI:     net flux for ice layer [W/m2]
			# wi:       thickness of ice cover [m]
			# wh:       available water height
			# dwi:      change in thickness per day, melt negative
			#dshi= pcr.ifthenelse(noIce,0,shi-shw+sha+shr)
			dshi= pcr.ifthenelse(noIce,0,shi-shw+shr)
			dwi= -dshi*self.timeSec/(self.rho_w*self.lf)
			dwi= pcr.max(-self.wi,dwi)
			dwi= pcr.min(dwi,pcr.max(0,self.maxIceThickness-self.wi))
			#-returning direct gain over water surface
			#watQ= pcr.ifthenelse(noIce,prp-EWat,0)
			#EWat= pcr.ifthenelse(noIce,EWat,0)
			watQ= pcr.ifthenelse(ta >= self.tt,prp-EWat,0)
			EWat= pcr.ifthenelse(ta >= self.tt,EWat,0)
			#-returning vertical gains/losses [m3] over lakes and channels
			# given their corresponding area
			dwi_melt= pcr.max(0,-dwi)
			channeldStor= self.channelFrac*(watQ+landQCont-actualDemand+dwi_melt)*self.cellArea/nrIter
			lakedStor= self.lakeFrac*(watQ+landQCont-actualDemand+dwi_melt)*self.cellArea/nrIter
			#-total lake fluxes and available storage over total lake area [m3]
			# note that only positive active lake storage -lakeStor- is available
			# for routing and partakes in evaporation, contrary to other versions
			lakedStorTot= pcr.areatotal(lakedStor,self.lakeID)
			lakeStorTot= pcr.areatotal(self.lakeStor,self.lakeID)
			#-lake discharge is calculated using the rectangular
			# weir formula and discharge - if sustained- added to the 
			# downstream channel reaches
			#-CLake is a conductance parameter that has to become smalle than unity
			# in case river ice is present
			CLake= 1.0
			QLake= pcr.ifthenelse(self.lakeOutlet,1.7*CLake*\
				pcr.max(0,1.0e-6*lakeStorTot/self.lakeArea)**1.5*self.channelWidth,0)
			#-correction on lake discharge and lateral inflow
			# note that both local and total vertical fluxes over the lake
			# surface have to be corrected
			corStor= self.fluxStorChk(lakedStorTot,lakeStorTot)
			lakedStorTot= corStor*lakedStorTot
			lakedStor= corStor*lakedStor
			EWat= pcr.ifthenelse(self.lakeMask,\
				corStor*EWat,EWat);
			actStorQ= pcr.max(0,lakeStorTot+lakedStorTot)/deltaTime
			QLake= pcr.ifthenelse(self.lakeOutlet,\
				pcr.min(QLake,actStorQ),0)
			#-channel discharge is calculated using the kinematic wave equation
			# note that contrary to other solutions, lake discharge
			# is not added as lateral inflow to the channels
			#-check vertical fluxes for available storage
			corStor= self.fluxStorChk(channeldStor,self.channelStor)
			EWat= pcr.ifthenelse(pcr.pcrnot(self.lakeMask),\
				corStor*EWat,EWat);
			channeldStor= corStor*channeldStor
			#-net cumulative input for mass balance check [m3]
			self.dtotStor= self.dtotStor+pcr.catchmenttotal(channeldStor+lakedStor,self.ldd)
			#-change in water storage due to vertical change only
			# used to limit heating and cooling of surface water
			dtotStorLoc= pcr.ifthenelse(self.lakeMask,\
				lakedStorTot*self.lakeStor/pcr.max(1.e-6,lakeStorTot),\
				channeldStor)/(watFrac*self.cellArea)
			#-latent heat flux due to evapotranspiration [W/m2]
			# and advected energy due to ice melt included here
			# to account for correction in water storage
			shl= -EWat*self.rho_w*self.lv/self.timeSec
			sha= sha+dwi_melt*self.tt*self.cp*self.rho_w/self.timeSec
			#-kinematic wave
			manIce= pcr.max(self.manN,\
				0.0493*pcr.max(0.01,self.channelStor/(self.channelFrac*self.cellArea))**\
				(-0.23)*self.wi**0.57)
			manC= (0.5*(self.manN**1.5+manIce**1.5))**(2./3.)
			wetA, wetP, alphaQ= self.momentumEQKW(self.channelStor,manC,pcr.scalar(noIce))
			q= channeldStor/(self.channelLength*deltaTime)
			#oldQC= pcr.max(1e-12,pcr.cover(self.QC,0))
			oldQC= pcr.ifthenelse(alphaQ > 0,(wetA/alphaQ)**(1/self.betaQ),0)
			self.QC= pcr.kinematic(self.channelLDD,oldQC,q,alphaQ,\
				self.betaQ,1,deltaTime,self.channelLength)
			#-correction of discharge on the basis of available storage,
			# updated with local change - channels and lakes
			actStorQ=  pcr.max(0,self.channelStor+channeldStor)/deltaTime  
			dchannelQ= 0.5*(oldQC+self.QC)
			dchannelQ= pcr.min(dchannelQ,actStorQ)
			#-updated change in water storage due to lateral changes,
			# total for lakes, and fractions of routed storage, including new updates
			channelTransFrac= dchannelQ*deltaTime/pcr.max(1.e-6,self.channelStor+channeldStor)
			lakeTransFrac= pcr.areatotal(QLake*deltaTime,\
				self.lakeID)/pcr.max(1.e-6,lakeStorTot+lakedStorTot)
			channelTransFrac= pcr.ifthenelse(pcr.pcrnot(self.lakeMask),\
				pcr.min(1.,pcr.max(0.,channelTransFrac)),0.)
			lakeTransFrac= pcr.ifthenelse(self.lakeMask,\
				pcr.min(1.,pcr.max(0.,lakeTransFrac)),0.)
			#-total change in storage updated with lateral flow, including lakes
			dlatQ= (pcr.upstream(self.ldd,dchannelQ+QLake)-(dchannelQ+QLake))*deltaTime
			channeldStor= channeldStor+pcr.ifthenelse(pcr.pcrnot(self.lakeMask),dlatQ,0)
			lakedStorTot= lakedStorTot+\
				pcr.areatotal(pcr.ifthenelse(self.lakeMask,dlatQ,0),self.lakeID)
			#-evaluation of energy balance, all totals in [MJ/m2]
			# totEW:     energy storage in surface water
			# totEWC:    energy required to heat or cool the
			#            present surface water by one degree
			# dtotEWC:   likewise, but for additional vertical change in storage
			#            positive only
			# dtotEWLoc: local change in energy storage due to vertical fluxes
			#            of sensible, radiative and latent heat
			# dtotEWAdv: total advected energy
			# dtotEWLat: lateral energy transfer, resolved after vertical
			#            balance is solved
			#-in case of heating, the local change is the minimum of the vertical
			# change and the additional energy required to raise the water temperature
			# to the air temperature
			totEWC= self.convEnergy*totStorLoc*self.cp*self.rho_w
			dtotEWC= self.convEnergy*dtotStorLoc*self.cp*self.rho_w
			dtotEWLoc= self.convEnergy*(shw+pcr.scalar(noIce)*(shr+shl))*deltaTime
			dtotEWAdv= self.convEnergy*(shq+pcr.scalar(noIce)*sha)*deltaTime
			dtotEWLoc= pcr.min(dtotEWLoc,\
				pcr.max(0,totEWC*ta-totEW)+pcr.ifthenelse(dtotStorLoc > 0,\
				pcr.max(0,dtotEWC*ta-dtotEWAdv),0))
			dtotEWLoc= pcr.ifthenelse(self.tw > ta,\
				pcr.min(0,dtotEWLoc),dtotEWLoc)
			dtotEWLoc= pcr.max(dtotEWLoc,\
				pcr.min(0,(totEWC+dtotEWC)*pcr.max(ta,self.tt+.1)-(totEW+dtotEWAdv)))
			#-change in energy storage and resulting temperature
			totEW= pcr.max(0,totEW+dtotEWLoc+dtotEWAdv)
			self.tw= pcr.ifthenelse(self.lakeMask,pcr.areatotal(totEW*watFrac*self.cellArea,\
				self.lakeID)/pcr.areatotal((totStorLoc+dtotStorLoc)*watFrac*self.cellArea,\
				self.lakeID),totEW/(totStorLoc+dtotStorLoc))/(self.convEnergy*self.cp*self.rho_w)
			#-new energy storage and routing
			dtotStorLoc= dtotStorLoc*watFrac*self.cellArea
			totEW= self.convEnergy*(self.totStor+dtotStorLoc)*self.tw*self.cp*self.rho_w
			dtotEWLat= pcr.ifthenelse(self.lakeMask,\
				lakeTransFrac*pcr.areatotal(totEW,self.lakeID),\
				channelTransFrac*totEW)
			totEW= totEW+pcr.upstream(self.ldd,dtotEWLat)-dtotEWLat
			#-discharges and energy fluxes updated
			#-update storage, water height, discharge
			# water temperature and ice thickness,
			# note that lake storage is not allowed to become negative
			# contrary to other versions
			self.channelStor= pcr.max(0,self.channelStor+channeldStor)
			lakeStorTot= pcr.max(0,lakeStorTot+lakedStorTot)
			watHeight= pcr.ifthenelse(self.lakeMask,\
				1.0e-6*lakeStorTot/self.lakeArea,\
				self.channelStor/(self.channelFrac*self.cellArea))
			self.lakeStor= pcr.ifthenelse(self.lakeMask,\
				self.lakeFrac*watHeight*self.cellArea,0)
			self.channelStor= pcr.ifthenelse(self.lakeMask,\
				0,self.channelFrac*watHeight*self.cellArea)
			self.totStor= self.channelStor+self.lakeStor
			self.tw= pcr.ifthenelse(watHeight > 0.25,\
				pcr.ifthenelse(self.lakeMask,pcr.areatotal(totEW,self.lakeID)/\
				pcr.areatotal(self.totStor,self.lakeID),totEW/self.totStor)/\
				(self.convEnergy*self.cp*self.rho_w),\
				pcr.ifthenelse(self.lakeMask,\
				pcr.areatotal(pcr.max(1.,self.lakeStor)*ta,self.lakeID)/\
				pcr.areatotal(pcr.max(1.,self.lakeStor),self.lakeID),ta))
			self.tw= pcr.ifthenelse(self.tw < self.tt+0.1,self.tt+0.1,self.tw)
			#-correction of ice formation for available water height
			# note ice formation can never exhaust water depth
			dwi= pcr.min(dwi,watHeight)
			watHeight= pcr.max(0,watHeight-pcr.max(0,dwi)/nrIter)
			self.lakeStor= pcr.ifthenelse(self.lakeMask,\
				self.lakeFrac*watHeight*self.cellArea,0)
			self.channelStor= pcr.ifthenelse(self.lakeMask,\
				0,self.channelFrac*watHeight*self.cellArea)
			self.totStor= self.channelStor+self.lakeStor
			self.wi= pcr.max(0,self.wi+(dwi+pcr.ifthenelse(ta >= self.tt,0,prp))/nrIter)
			self.wi= pcr.ifthenelse((self.wi <= 0.001) & (dwi < 0),0,self.wi)
			self.wi= pcr.ifthenelse(self.lakeMask,pcr.areatotal(watFrac*\
				self.cellArea*self.wi,self.lakeID)/pcr.areatotal(watFrac*self.cellArea,\
				self.lakeID),self.wi)
			tw_daily= tw_daily+self.tw/nrIter
			wi_daily= wi_daily+self.wi/nrIter
			watHeight_daily= watHeight_daily+watHeight/nrIter
			QC_daily= QC_daily+pcr.ifthenelse(self.lakeMask,pcr.areatotal(QLake,self.lakeID),\
				dchannelQ)*deltaTime
		#-loop completed
		#-budget check
		#-cumulative discharge [m3] for mass balance check
		self.totQ= self.totQ+QC_daily
		#-update accumulated daily discharge from m3 to m3/s
		QC_daily= QC_daily/self.timeSec
		self.report(QC_daily,qcFileName)
		self.report(watHeight_daily,whFileName)
		self.report(tw_daily,twFileName)
		self.report(wi_daily,wiFileName)
		#-on the last day, report budget and new initial files
		if self.currentDate == self.endDate:
			#-total storage upstream of each grid point
			upstreamStorage= pcr.catchmenttotal(self.totStor+\
				pcr.ifthenelse(self.lakeMask,self.lakeFrac*self.wi,\
				self.channelFrac*self.wi)*self.cellArea,self.ldd)
			turnOver= self.totStorIni+self.dtotStor
			massBalanceError= pcr.ifthen(self.massBalEval,\
				(turnOver-self.totQ)-upstreamStorage)
			relmassBalanceError= 1-massBalanceError/pcr.max(0.1,turnOver)
			#-return relative and absolute water balance error
			# per cell and over total domain
			print '\trun completed'
			pcr.report(massBalanceError,massBalanceErrorFileName)
			pcr.report(relmassBalanceError,relmassBalanceErrorFileName)
			totMassBalanceError= pcr.maptotal(pcr.ifthenelse(self.basinOutlet,\
				massBalanceError,0))
			totrelMassBalanceError= 1+totMassBalanceError/\
				pcr.maptotal(pcr.ifthenelse(self.basinOutlet,turnOver,0))
			print '\ttotal global mass balance error [km3]: %8.3g' %\
				pcr.cellvalue(totMassBalanceError,1)[0]
			print '\trelative global mass balance error [-]: %5.3f' %\
				pcr.cellvalue(totrelMassBalanceError,1)[0]
			#-storing initial files
			pcr.report(self.QC,iniQCFileName)
			pcr.report(self.channelStor,iniChannelStorFileName)
			pcr.report(self.lakeStor,iniLakeStorFileName)
			pcr.report(self.tw,iniTWFileName)
			pcr.report(self.wi,iniWIFileName)
		#-update monthly statistics
		self.sN+= 1
		self.sxQ= self.sxQ+QC_daily
		self.sx2Q= self.sx2Q+QC_daily**2
		self.sxTw= self.sxTw+self.tw
		self.sx2Tw= self.sx2Tw+self.tw**2
		self.sxdT= self.sxdT+(self.tw-ta)
		self.sx2dT= self.sx2dT+(self.tw-ta)**2
		#-at end of month, next day == 1, compute statistics and report
		if (self.currentDate+datetime.timedelta(1)).day == 1:
			#-compute means and standard deviations and report
			pcr.report(self.sxQ/self.sN,pcrm.generateNameT(qAvgFileName,\
				self.currentDate.month))
			pcr.report(pcr.sqrt(self.sN*self.sx2Q-self.sxQ**2)/self.sN,\
				pcrm.generateNameT(qSDFileName,self.currentDate.month))
			pcr.report(self.sxTw/self.sN,pcrm.generateNameT(twAvgFileName,\
				self.currentDate.month))
			pcr.report(pcr.sqrt(self.sN*self.sx2Tw-self.sxTw**2)/self.sN,\
				pcrm.generateNameT(twSDFileName,self.currentDate.month))
			pcr.report(self.sxdT/self.sN,pcrm.generateNameT(dtAvgFileName,\
				self.currentDate.month))
			pcr.report(pcr.sqrt(self.sN*self.sx2dT-self.sxdT**2)/self.sN,\
				pcrm.generateNameT(dtSDFileName,self.currentDate.month))
		#-update date
		self.currentDate= self.currentDate+datetime.timedelta(1)
		#end of model script
