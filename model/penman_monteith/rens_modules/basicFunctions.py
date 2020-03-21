#-file with basic functions
#///start of file with basic functions///

import sys, os, zipfile, zlib
import pcraster as pcr

def testInstance(x,instance,\
    message= 'variable x is not of type specified'):
  #-tests whether variable x is of the type specified
  import sys
  try:
    assert isinstance(x,instance)
  except:
    sys.exit(message)

def returnValDivZero(x,y,y_lim,z_def= 0.):
  #-returns the result of a division that possibly involves a zero
  # denominator; in which case, a default value is substituted:
  # x/y= z in case y > y_lim,
  # x/y= z_def in case y <= y_lim, where y_lim -> 0.
  # z_def is set to zero if not otherwise specified
  return pcr.ifthenelse(y > y_lim,x/pcr.max(y_lim,y),z_def)

def expandList(list_,length,entry= None):
  #-expands a list until it contains the required number of elements
  try:
    testInstance(list_,list)
    while length >= len(list_):
      list_.append(entry)
    return list_
  except:
    print 'list could not be expanded'

def sumList(listLikeType):
  #-sums all entries in a list-like type
  return reduce(lambda x, y: x+y,listLikeType)

def returnPrecision(pcrMap,precisionValue= -6.):
  #-returns the precision of a PCRaster map relative to the log10 base
  # specified by the precisionValue
  return 10.**(precisionValue+pcr.rounddown(pcr.log10(pcrMap)))

def constructListFromDictionary(listConstructor,resultList):
  #-constructs a list of arbitrary form from a dictionary object
  # holding a unique identifier as keyword, and two items identified by
  # the keywords "entry", holding the actual list entry, and "levelInfo"
  # that holds information on the levels and indices as a separate dictionary
  # in which levels are used as keys and indices as values, e.g.,
  # {0: {'entry': 'a', 'levelInfo': {0: 0, 1: 0}}, 1: {'entry': 'b', 'levelInfo': {0: 0, 1: 1}}}
  # which is equivalent with a zero-order list that contains at position 0 the first-order list
  # with the elements a and b: [[a,b]]
  resultList= resultList[:]
  assert isinstance(listConstructor,dict)
  #-iterate over all list entries in the listConstructor object
  for key, listInfo in listConstructor.iteritems():
    entry= listInfo['entry']
    levelInfo= listInfo['levelInfo']
    #-get levels from levelInfo and sort them in ascending order
    levels= levelInfo.keys()
    levels.sort()
    #-create dictionary of list contents and populate
    listContents= dict([(level,[]) for level in levels])
    for level in levels:
      index= levelInfo[level]
      #-populate listContents at lowest level with the sublist at index i
      # otherwise
      if level == 0:
        #-get the contents of resultList at index, else insert the necessary elements as empty lists
        if index >= len(resultList):
          resultList= expandList(resultList,index,[])
        listContents[level]= resultList[:]
      else:
        listContents[level]= listContents[level-1][levelInfo[level-1]][:]
        if index >= len(listContents[level]):
          listContents[level]= expandList(listContents[level],index,[])
      #-at the highest level, insert entry
      if level == max(levels):
        listContents[level][index]= entry
    #-process the levels in reverse order and insert result from higher level into the underlying level
    #-remove highest level first
    level= levels.pop()
    index= levelInfo[level]
    while len(levels) > 0:
      level= levels.pop()
      index= levelInfo[level]
      listContents[level][index]= listContents[level+1]
    resultList[index]= listContents[level][index]
  #-return the updated list
  return resultList

def createListConstructor(s,separators):
  #-returns the listConstructor from a string and list of separators,
  # which is a dictionary object holding a unique identifier as keyword,
  # and two items identified by the keywords "entry", holding the actual list entry,
  # and "levelInfo" that holds information on the levels and indices as a
  # separate dictionary in which levels are used as keys and indices as values, e.g.,
  # {'a': {0: 0, 1: 0}, 'b': {0: 0, 1: 1}}, from a string organized in different levels
  # by the separators that are listed in descending order
  #-listConstructor is intialized as an empty dictionary with a known identifier
  separators= separators[:]
  identifier= 0
  listConstructor= {}
  listConstructor[identifier]= {}
  listConstructor[identifier]['entry']= s
  listConstructor[identifier]['levelInfo']= {}
  level= 0
  #-step through separators and keys in the list constructor
  while len(separators) > 0:
    #-get separator and list of current identifiers, including the maximum value
    # to be used for adding new dictionary entries
    separator= separators.pop()
    IDs= listConstructor.keys()
    maxID= max(IDs)
    #-step through dictionary entries
    for identifier in IDs:
      #-if the entry of the current dictionary entry contains the separator
      # get entry and levelInfo, delete the present entry and process for all
      # subsequent entries of increasing order at the given level
      if separator in listConstructor[identifier]['entry']:
        entry= listConstructor[identifier]['entry']
        levelInfo= listConstructor[identifier]['levelInfo']
        del listConstructor[identifier]
        order= 0
        #-for each element of the split entry, update the identifier and add
        # the info to the new entry of the dictionary
        for newEntry in entry.split(separator):
          maxID+= 1
          listConstructor[maxID]= {}
          listConstructor[maxID]['entry']= newEntry
          listConstructor[maxID]['levelInfo']= levelInfo.copy()
          listConstructor[maxID]['levelInfo'][level]= order
          order+= 1
    #-increment level counter
    level+= 1
  #-return listConstructor object
  return listConstructor

def tanh(x):
  #-returns the hyperbolic tangent of a PCRaster map as (exp(2x)-1)/(exp(2x)+1)
  return (pcr.exp(2*x)-1.)/(pcr.exp(2*x)+1.)

def fractionXY(surface):
  #-returns the fraction of transport in the x- and y-directions
  # given a gradient in a surface
  aspect= pcr.aspect(surface)
  noAspect= pcr.nodirection(pcr.directional(aspect))
  sinAspect= pcr.sin(aspect)
  cosAspect= pcr.cos(aspect)
  fracX= pcr.ifthenelse(noAspect,0.,sinAspect/(pcr.abs(sinAspect)+pcr.abs(cosAspect)))
  fracY= pcr.ifthenelse(noAspect,0.,cosAspect/(pcr.abs(sinAspect)+pcr.abs(cosAspect)))
  return fracX,fracY

def diffuseTransportXY(dMat,fracX,fracY):
  #-evaluates transport in the four cardinal directions with the
  # shift function (1: up, left; -1: right, down), returning the
  # resulting change at each location
  dMatWest=   pcr.max(0,pcr.shift0(-fracX*dMat, 0, 1))
  dMatEast=   pcr.max(0,pcr.shift0( fracX*dMat, 0,-1))
  dMatNorth=  pcr.max(0,pcr.shift0( fracY*dMat, 1, 0))
  dMatSouth=  pcr.max(0,pcr.shift0(-fracY*dMat,-1, 0))
  return -dMat+dMatNorth+dMatEast+dMatSouth+dMatWest

def printCellValue(x,repStr= 'map value',location= 1):
  #-returns the cell value at the location specified
  # it tests whether this is a tuple or not of the format row, column
  try:
    value,valid= pcr.cellvalue(x,location[1],location[0])
    posStr= 'at row column: %d, %d' % (location,[0],location[1])
  except:
    try:
      value,valid= pcr.cellvalue(x,location)
      posStr= 'at cell location: %d' % location
    except:
      value= x
      valid= True
      posStr= 'global float'
  if valid:
    print repStr+(' %f ' % value)+posStr
    return value

def extractArchive(archiveFileName,targetDirectory,patterns):
  #-reads files from a specified archive matching a pattern to the output directory
  # specified
  try:
    archive= zipfile.ZipFile(archiveFileName)
    fileNames= []
    for sourceFileName in archive.namelist():
      for pattern in patterns:
        if pattern in sourceFileName:
          fileNames.append(sourceFileName)
    for sourceFileName in fileNames:
      targetFileName= sourceFileName
      if targetDirectory <> '':
        targetFileName= os.path.join(targetDirectory,targetFileName)
      tempFile= open(targetFileName,'wb')
      tempFile.write(archive.read(sourceFileName ))
      tempFile.close()
    archive.close()
  except:
    sys.exit('%s cannot be processed' % archiveFileName)

def readTSS(tssFileName,columnList= [1], header= 'true'):
  #-reads in TSS and returns list of lists with desired variables
  rawList= []
  resultList= []
  for colCnt in xrange(0,len(columnList)):
    resultList.append(rawList[:])
  lineCnt= 0
  headerLines= 2
  try:
    tssFile= open(tssFileName)
    lineCnt= 0
    try:
        for line in tssFile:
            if header and lineCnt < headerLines:
                if lineCnt == 1: headerLines= headerLines+int(line)
            else:
                rawList= line.split()
                for colCnt in xrange(0,len(columnList)):
                    resultList[colCnt].append(float(rawList[columnList[colCnt]]))
            lineCnt+= 1
    finally:
        tssFile.close()
    return resultList
  except:
    print 'timeseries could not be read'

def extractTimer(timer,ntime):
  #-returns the modulo of a continuous timer over a predefined period length
  extractedTime= timer % ntime
  if extractedTime == 0: extractedTime= ntime
  return extractedTime

class calerosTSS:
  #-definition of the class object handling default timeseries input for the Caleros landscape dynamics model
  # reads in a timeseries and return the entry belonging to a particular timestep

  def __init__(self,tssFileName= '',colNr= 0):
    if tssFileName != '':
      self.tssList= readTSS(tssFileName,colNr)[0]
    else:
      self.tssList= [None]

  def setTSS(self,tssList):
    if isinstance(tssList,list):
      self.tssList= tssList
    else:
      sys.exit('tssList is not specified as a 1-D list')

  def update(self,timer):
    #-updates the timer and extracts and returns the corresponding value from the timeseries
    timer= extractTimer(timer,len(self.tssList))-1
    return self.tssList[timer]
  #/end of the TSS object/
