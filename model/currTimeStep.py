#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Edwin H. Sutanudjaja, Rens van Beek, Niko Wanders, Yoshihide Wada, 
# Joyce H. C. Bosmans, Niels Drost, Ruud J. van der Ent, Inge E. M. de Graaf, Jannis M. Hoch, 
# Kor de Jong, Derek Karssenberg, Patricia López López, Stefanie Peßenteiner, Oliver Schmitz, 
# Menno W. Straatsma, Ekkamol Vannametee, Dominik Wisser, and Marc F. P. Bierkens
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
logger = logging.getLogger(__name__)

import time
import datetime

class ModelTime(object):

    def __init__(self):
        object.__init__(self)
        self._spinUpStatus = False
    
  
    #FIXME: use __init__
    def getStartEndTimeSteps(self,strStartTime,strEndTime,showNumberOfTimeSteps=True):
        # get startTime, endTime, nrOfTimeSteps 
        sd = str(strStartTime).split('-')
        self._startTime = datetime.date(int(sd[0]), int(sd[1]), int(sd[2]))
        ed = str(strEndTime).split('-')
        self._endTime = datetime.date(int(ed[0]), int(ed[1]), int(ed[2]))
        self._nrOfTimeSteps = 1 + (self.endTime - self.startTime).days
        self._spinUpStatus = False
        if showNumberOfTimeSteps == True: logger.info("number of time steps: "+str(self._nrOfTimeSteps))
        self._monthIdx = 0 # monthly indexes since the simulation starts
        self._annuaIdx = 0 #  yearly indexes since the simulation starts

    #FIXME: use __init__
    def getStartEndTimeStepsForSpinUp(self,strStartTime,noSpinUp,maxSpinUps):
        # get startTime, endTime, nrOfTimeSteps for SpinUps
        sd = str(strStartTime).split('-')
        self._startTime = datetime.date(int(sd[0]), int(sd[1]), int(sd[2]))

        # ~ # using one year
        # ~ self._endTime = datetime.date(int(sd[0])+1, int(sd[1]), int(sd[2])) -\
                       # ~ datetime.timedelta(days=1)
        
        # always use the last day of a year: 31 December of the starting year
        self._endTime = datetime.date(int(sd[0]), int(12), int(31))
        
        self._nrOfTimeSteps = 1 + (self.endTime - self.startTime).days
        self._spinUpStatus = True
        self._noSpinUp   = noSpinUp
        self._maxSpinUps = maxSpinUps
        self._monthIdx = 0 # monthly indexes since the simulation starts
        self._annuaIdx = 0 #  yearly indexes since the simulation starts


    def setStartTime(self, date):
        self._startTime = date
        self._nrOfTimeSteps = 1 + (self.endTime - self.startTime).days

    def setEndTime(self, date):
        self._endTime = date
        self._nrOfTimeSteps = 1 + (self.endTime - self.startTime).days

    @property
    def spinUpStatus(self):
        return self._spinUpStatus

    @property    
    def startTime(self):
        return self._startTime
    
    @property    
    def endTime(self):
        return self._endTime

    @property    
    def currTime(self):
        return self._currTime

    @property    
    def day(self):
        return self._currTime.day

    @property    
    def doy(self):
        return self._currTime.timetuple().tm_yday

    @property    
    def month(self):
        return self._currTime.month
    
    @property    
    def year(self):
        return self._currTime.year

    @property    
    def timeStepPCR(self):
        return self._timeStepPCR
    
    @property    
    def monthIdx(self):
        return self._monthIdx
    
    @property    
    def annuaIdx(self):
        return self._annuaIdx
    
    @property    
    def nrOfTimeSteps(self):
        return self._nrOfTimeSteps
    
    @property
    def fulldate(self):
        return self._fulldate

    def update(self,timeStepPCR):
        self._timeStepPCR = timeStepPCR
        self._currTime = self._startTime + datetime.timedelta(days=1 * (timeStepPCR - 1))
        
        #~ self._fulldate = str(self.currTime.strftime('%Y-%m-%d'))     # This does not work for the date before 1900
        self._fulldate = '%04i-%02i-%02i' %(self._currTime.year, self._currTime.month, self._currTime.day)
        #~ print(self._fulldate)
        
        if self.spinUpStatus == True : 
            logger.info("Spin-Up "+str(self._noSpinUp)+" of "+str(self._maxSpinUps))

        # The following contains hours, minutes, seconds, etc. 
        self._currTimeFull = datetime.datetime(self.year,self.month,self.day)
        
        # check if a certain day is the last day of the month
        if self.isLastDayOfMonth():
            self._monthIdx = self._monthIdx + 1

        # check if a certain day is the last day of the year
        if self.isLastDayOfYear():
            self._annuaIdx = self._annuaIdx + 1
            
    def isFirstTimestep(self):
        return self.timeStepPCR == 1

    def isFirstDayOfMonth(self):
        return self.day == 1
    
    def isFirstDayOfYear(self):
        return self.doy== 1
    
    def isLastDayOfMonth(self):
        tomorrow = self.currTime + datetime.timedelta(days=1)
        
        #tomorrow is the first day of the month
        return tomorrow.day == 1
    
    def isLastDayOfYear(self):
        tomorrow = self.currTime + datetime.timedelta(days=1)
        
        #tomorrow is the first day of the year
        return tomorrow.timetuple().tm_yday == 1

    def isLastTimeStep(self):
        return self._currTime == self._endTime

    def yesterday(self):
        yesterday = self.currTime - datetime.timedelta(days=1)
        return str(yesterday.strftime('%Y-%m-%d'))

    #FIXME: use isLastDayOfMonth
    @property
    def endMonth(self):
        return self.isLastDayOfMonth()

    #FIXME: use isLastDayOfYear
    @property
    def endYear(self):
        return self.isLastDayOfYear()
    
    def __str__(self):
        #~ print self._currTime
        return str(self._currTime)
