#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import shutil
import random

import numpy
from numpy import linalg
import pickle

from pcraster import*
from pcraster.framework import *

def dumpfile(name, var, num):
  path1 = os.path.join(num, 'stateVar',name)
  file_object1 = open(path1, 'w')
  pickle.dump(var, file_object1)
  file_object1.close()
  
def loadfile(name, num):
  path1 = os.path.join(num, 'stateVar', name)
  filehandler1 = open(path1, 'r')
  var = pickle.load(filehandler1)
  filehandler1.close() 
  return(var)

## \brief Framework for particle filter runs
class EnsKalmanFilterFramework(frameworkBase.FrameworkBase):
  ## \brief Constructor
  def __init__(self, userModel):
    frameworkBase.FrameworkBase.__init__(self)
    self._d_model = userModel
    #self._testRequirements()
    self._d_totalTimesteps = self._userModel().nrTimeSteps()
    self._d_trackCloned = {}
    print "de goede"

    # adding framework specific attributes and methods
    self._addAttributeToClass("_d_filterPeriod", 0)
    self._addAttributeToClass("_d_inFilterPeriod", False)
    self._addAttributeToClass("_d_filterTimesteps", [])
    self._addAttributeToClass("_d_inResume", False)
    self._addAttributeToClass("_d_inUpdateWeight", False)
    self._resetSampleWeights()

    self._addMethodToClass(self.getStateVector)
    self._addMethodToClass(self._runPremcloop)
    self._addMethodToClass(self._runPostmcloop)

    self._addMethodToClass(self.readmap)
    self._addMethodToClass(self.readDeterministic)
    self._addMethodToClass(self.setMeasurementOperator)
    self._addMethodToClass(self.setObservedMatrices)
    self._addMethodToClass(self.setCovarianceAdjust)
    self._addMethodToClass(self.giveLenghts)

    # \todo !!!test if filter timesteps are in interval of model timesteps...
    self.sizeStateVector = 0
    self._initialiseObservedDir()

  def setObservedMatrices(self, observations, covariance):
    assert type(observations) == numpy.ndarray
    assert type(covariance) == numpy.ndarray
    filtermoment = self._userModel().currentTimeStep()

    fileName = os.path.join("observedState",'obs%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(observations, file)
    file.close()

    fileName = os.path.join("observedState",'cov%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(covariance, file)
    file.close()


  ## \brief Setting the measurement operator for an update moment
  #
  # If this is not used the identity matrix will be used
  def setMeasurementOperator(self, matrix):
    assert type(matrix) == numpy.ndarray

    filtermoment = self._userModel().currentTimeStep()
    fileName = os.path.join("observedState",'h%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(matrix, file)
    file.close()
    
  def setCovarianceAdjust(self, matrix):
    assert type(matrix) == numpy.ndarray

    filtermoment = self._userModel().currentTimeStep()
    fileName = os.path.join("observedState",'pead%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(matrix, file)
    file.close()
    
  def giveLenghts(self, lenQ, numcels):
    filtermoment = self._userModel().currentTimeStep()

    fileName = os.path.join("observedState",'lenq%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(lenQ, file)
    file.close()    

    fileName = os.path.join("observedState",'numcels%s.tmp' % (filtermoment))
    file = open(fileName, 'wb')
    pickle.dump(numcels, file)
    file.close()    

  def _testRequirements(self):
    print type(self._d_model)
    #\todo test to dynamic framework model
    if not isinstance(self._d_model, mcFramework.MonteCarloFramework):
      self.showError("Model must be instance of MonteCarloFramework.")
      sys.exit()

    if not hasattr(self._d_model, 'run'):
      self.showError("No 'run' section defined.")
      sys.exit()

    if not hasattr(self._userModel(), 'setState'):
      self.showError("No 'setState' function defined.")
      sys.exit()


    if not hasattr(self._userModel(), 'resume'):
      msg = "Cannot run particle filter framework: Implement 'resume' method"
      raise frameworkBase.FrameworkError(msg)


  def _particleWeights(self):
    return self._userModel()._d_particleWeights

  def _userModel(self):
    return self._d_model._userModel()

  def _initialiseObservedDir(self):
    varName = "observedState"

    if not os.path.isdir(varName):
      # Create sample directory.
      os.mkdir(varName)
    else :
      #if not os.path.isdir(varName):
      #  # Remove existing file with name of sample directory.
      shutil.rmtree(varName)
      os.mkdir(varName)





  ## \brief Creates the subdirectories for state variables
  # \todo test if mc dirs are there...
  def _initialiseStateDir(self):
    varName = "stateVector"

    if not os.path.isdir(varName):
      # Create sample directory.
      os.mkdir(varName)
    else :
      #if not os.path.isdir(varName):
      #  # Remove existing file with name of sample directory.
      shutil.rmtree(varName)
      os.mkdir(varName)


  ## \brief Creates the subdirectories for state variables
  # \todo test if mc dirs are there...
  def _initialiseSampleDirectories(self):
    sample = self._userModel()._firstSampleNumber()
    while sample <= self._userModel()._lastSampleNumber():
      cwd = os.getcwd()

      dirname = "%d" % (sample)
      varName = "stateVar"
      os.chdir(dirname)

      if not os.path.isdir(varName):
        # Create sample directory.
        os.mkdir(varName)
      else :
        #if not os.path.isdir(varName):
        #  # Remove existing file with name of sample directory.
        os.remove(varName)
        os.mkdir(varName)

      os.chdir(cwd)
      assert os.path.exists(os.path.join(dirname,"stateVar")) and os.path.isdir(os.path.join(dirname,"stateVar"))
      sample += 1

  ## \brief Setting the filter moments
  def setFilterTimesteps(self, filterTimesteps):
    assert type(filterTimesteps) == list or type(filterTimesteps) == numpy.ndarray
    #assert type(filterTimesteps) == list
    # \todo assert some more
    for filtertimestep in filterTimesteps:
      assert filtertimestep < self._userModel().nrTimeSteps()
    self._userModel()._d_filterTimesteps = filterTimesteps

  ## \brief Returns a list of filter moments
  def filterTimesteps(self):
    return self._userModel()._d_filterTimesteps

  ## \brief Re-implemented from ShellScript.
  #
  # Runs the user model in the filter mode.
  def run(self):
    if(hasattr(self._userModel(), 'run')):
      self._userModel().run()
    else:
      self._atStartOfScript()
      self._initialiseStateDir()
      self._initialiseSampleDirectories()

      lastPeriod = len(self._userModel()._d_filterTimesteps)

      if lastPeriod == 0:
        self.showError("No filter timesteps specified")
        sys.exit()



      # set the proposal/initial weight distribution by user
      if hasattr(self._userModel(), 'setInitialParticleWeights'):
        self._userModel()._d_particleWeights = self._userModel().setInitialParticleWeights()

        # check initial weights
        assert type(self._particleWeights()) == list
        assert len(self._particleWeights()) == self._userModel().nrSamples()

        for i in range(0, len(self._particleWeights())):
          assert type(self._particleWeights()[i]) == float

      # run the premc loop
      self._userModel()._runPremcloop()

      # looping over the filter periods
      for currentPeriod in range(0, len(self._userModel()._d_filterTimesteps) + 1):

        # \todo replace with a better solution...
        sumW = sum(self._particleWeights())
        assert abs(sumW - 1.0) < 0.00001

        self._runMonteCarlo(currentPeriod, lastPeriod)



        if not currentPeriod == lastPeriod:
          # retrieve the state vectors for each sample
          for sample in range(1, self._userModel().nrSamples() + 1):
            self._userModel()._setCurrentSample(sample)
            self._userModel()._d_inUpdateWeight = True
            stateVector = self._userModel().setState()
            self._userModel()._d_inUpdateWeight = False
            assert type(stateVector) == numpy.ndarray
            fileName = os.path.join("stateVector",'ensMember%s.tmp' %(sample))
            file = open(fileName,'wb')
            pickle.dump(stateVector, file)
            file.close()


          # for current update moment
          self._getObservedValues()
          self._kalmanFilter()


          currentPeriod += 1
          self._userModel()._d_filterPeriod += 1

    self._userModel()._setFirstTimeStep(1)
    self._userModel()._runPostmcloop()
    return 0

  def _getObservedValues(self):
    self._userModel().setObservations()

  def _kalmanFilter(self):
    # following equations 44-52 from Geir Evensen's paper
    # 'The Ensemble Kalman Filter: theoretical formulation
    # and practical implemetation'
    #
    # n size of state vector (sizeStateVector)
    # m nr of observations (sizeObservedVector)
    # N nr of ensemble members
    #
    # A matrix with model states
    # H matrix 'measurement operator'
    # D matrix with observations


    fileName = os.path.join("stateVector",'ensMember%s.tmp' %(str(1)))
    file = open(fileName,'rb')
    vec = pickle.load(file)
    sizeStateVector = len(vec)
    file.close()
    # length of the observed vector \todo do we know that?
    fileName = os.path.join("observedState","obs%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    file = open(fileName,'rb')
    vec = pickle.load(file)
    sizeObservedVector = len(vec)
    file.close()

    nrEnsembleMembers =  self._userModel().nrSamples()


    # create A
    A = numpy.zeros((sizeStateVector, nrEnsembleMembers), dtype=float)

    # \todo is there a better way to construct a matrix from vecors?
    for sample in range(1, self._userModel().nrSamples() + 1):
      fileName = os.path.join("stateVector",'ensMember%s.tmp' %(sample))
      file = open(fileName,'rb')
      vec = pickle.load(file)
      file.close()
      for i in range(0, sizeStateVector):
        A[i,sample-1] = vec[i]


    # obtain H specified by user
    fileName = os.path.join("observedState","h%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    if os.path.exists(fileName):
      file = open(fileName,'rb')
      H = pickle.load(file)
      file.close()
    else:
      # or use the identiy matrix
      H = numpy.eye(sizeObservedVector, sizeStateVector, dtype=float)
      
    assert H.shape == (sizeObservedVector, sizeStateVector), "Shape of provided matrix H %s does not match (%s, %s)" %(H.shape, sizeObservedVector, sizeStateVector)

    # obtain Pe adjustments specified by user      
    fileName = os.path.join("observedState","pead%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    if os.path.exists(fileName):
      file = open(fileName,'rb')
      PeAd = pickle.load(file)
      file.close()
    else:
      # or use the identiy matrix
      PeAd = numpy.ones((sizeStateVector, sizeObservedVector), dtype=float)
      
    fileName = os.path.join("observedState","lenq%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    if os.path.exists(fileName):
      file = open(fileName,'rb')
      lenQ = pickle.load(file)
      file.close()
      
    fileName = os.path.join("observedState","numcels%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    if os.path.exists(fileName):
      file = open(fileName,'rb')
      numcels = pickle.load(file)
      file.close()      
    
    assert PeAd.shape == (sizeStateVector, sizeObservedVector), "Shape of provided matrix PeAd %s does not match (%s, %s)" %(H.shape, sizeStateVector, sizeObservedVector)

    # obtain D
    fileName = os.path.join("observedState","obs%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    file = open(fileName, 'rb')
    D = pickle.load(file)
    file.close()

    assert D.shape == (sizeObservedVector, nrEnsembleMembers), "Shape of provided matrix D %s does not match (%s, %s)" %(D.shape, sizeObservedVector, nrEnsembleMembers)

    # obtain error covariance matrix
    fileName = os.path.join("observedState","cov%s.tmp" %(self._userModel()._d_filterTimesteps[self._userModel()._d_filterPeriod]))
    file = open(fileName, 'rb')
    Re = pickle.load(file)
    file.close()

    assert Re.shape == (sizeObservedVector, sizeObservedVector), "Shape of provided matrix Re %s does not match (%s, %s)" %(Re.shape, sizeObservedVector, sizeObservedVector)

    # calculate Pe
    Abar = numpy.dot(A,numpy.array( [[1.0/nrEnsembleMembers] * nrEnsembleMembers ] * nrEnsembleMembers, dtype=float))
    Ad = A - Abar
    del Abar
    #print "Abar"
    #print time.asctime( time.localtime(time.time()) )
    dim = H.shape[0]
    tAd = numpy.transpose(Ad)
    Pe =  1.0/(nrEnsembleMembers - 1) * numpy.dot(Ad,tAd[:,0:dim])
    Pe = Pe * PeAd
    #out = open("update.txt", "w")
    #row = Pe.shape[0]
    #col = Pe.shape[1]
    #for i in range(row):
      #for j in range(col-1):
	#out.write(str(Pe[i,j])+"\t")
      #out.write(str(Pe[i,col-1])+"\n")
    #out.close()
    #print "doc writen"
	
    del Ad
    #print "Ad"
    #print time.asctime( time.localtime(time.time()) )

    # calculate the new A matrix
    DmAH = D - numpy.dot(H,A)
    del D
    #print "D"
    #print time.asctime( time.localtime(time.time()) )

    PeHt = Pe[:,0:dim] #numpy.dot(Pe,numpy.transpose(H))
    del Pe
    #print "Pe"
    #print time.asctime( time.localtime(time.time()) )

    HPeHt = numpy.dot(H, PeHt)
    HPeHtpRe = HPeHt + Re
    del Re
    del HPeHt
    #print "Re"
    #print time.asctime( time.localtime(time.time()) )


    INV = linalg.pinv(HPeHtpRe)
    del HPeHtpRe
    #print "Inv gelukt"
    #print time.asctime( time.localtime(time.time()) )


    INVDmAH = numpy.dot(INV, DmAH)
    del INV
    del DmAH
    #print "Gain"
    #print time.asctime( time.localtime(time.time()) )

    A = A + numpy.dot(PeHt, INVDmAH)
    del PeHt
    del INVDmAH
    print "Update klaar"
    #print time.asctime( time.localtime(time.time()) )


    for sample in range(1, self._userModel().nrSamples() + 1):
      fileName = os.path.join("stateVector",'a%s.tmp' %(sample))
      file = open(fileName,'wb')
      index = sample - 1
      vec = A[:,index]

      pickle.dump(vec, file)
      file.close()

  ## \brief Returns the updated variables
  def getStateVector(self, sampleNumber):
    fileName = os.path.join("stateVector",'a%s.tmp' %(sampleNumber))
    file = open(fileName,'rb')
    vec = pickle.load(file)
    file.close()
    return vec



  def _normaliseWeights(self, weights):
    assert weights
    sumWeights = sum(weights)
    norm = [0.0] * len(weights)
    for i in range(0, len(weights)):
      norm[i] =  weights[i] / sumWeights

    return norm


  def _resetSampleWeights(self):
    assert self._userModel().nrSamples() > 0
    self._userModel()._d_particleWeights = [1.0 / self._userModel().nrSamples()] * self._userModel().nrSamples()


  def _cumulativeWeights(self, weights):
    cumulative = [0.0] * self._userModel().nrSamples()
    value = 0.0
    for i in range(len(weights)):
      value += weights[i]
      cumulative[i] = value
    return cumulative



  def _startEndOfPeriod(self, currentPeriod, lastPeriod):
    # determine start end end timestep of current period
    if currentPeriod == 0:
      startTimestep = 1
      endTimestep = self._userModel()._d_filterTimesteps[currentPeriod]
    elif currentPeriod == lastPeriod:
      startTimestep = self._userModel()._d_filterTimesteps[currentPeriod -1] + 1
      endTimestep = self._d_totalTimesteps
    else:
      startTimestep = self._userModel()._d_filterTimesteps[currentPeriod - 1] + 1
      endTimestep = self._userModel()._d_filterTimesteps[currentPeriod]

    assert startTimestep <= endTimestep
    return startTimestep, endTimestep


  def _executePrePostMc(self, currentPeriod, lastPeriod):
    if currentPeriod == 0:
      # execute premc
      premc = True
      postmc = False
    elif currentPeriod == lastPeriod:
      # execute postmc
      premc = False
      postmc = True
    else:
      # without pre/postmc
      premc = False
      postmc = False
    # \todo assert something
    return premc, postmc

  def _runMonteCarlo(self, currentPeriod, lastPeriod):
    #  get user model and (re)set start and end time
    startTimestep, endTimestep = self._startEndOfPeriod(currentPeriod, lastPeriod)

    self._userModel()._setNrTimeSteps(endTimestep)
    self._userModel()._setFirstTimeStep(startTimestep)
    self._userModel()._setCurrentTimeStep(endTimestep)

    # run the model in mc mode for current filter period
    self._incrementIndentLevel()
    self._atStartOfFilterPeriod(currentPeriod)
    self._d_model.run(False, False)
    self._atEndOfFilterPeriod()
    self._decrementIndentLevel()






  ## \brief reading sample data from disk
  # returns the map of the current time step from the current sample directory
  def readmap(self, name):
    return self._readmapNew(name)


  ## \brief reading deterministic data from disk
  # returns the map of the current time step from the current working directory
  def readDeterministic(self, name):
    if self._userModel()._inPremc() or self._userModel()._inPostmc() or self._userModel()._inInitial():
      newName = name + ".map"
    else:
      newName = generateNameT(name, self._userModel().currentTimeStep())

    import PCRaster
    return PCRaster.readmap(newName)
