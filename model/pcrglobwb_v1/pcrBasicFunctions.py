#-contains some basic PCRaster functions associated with PCR-GLOBWB
import  os, shutil
import pcraster as pcr
from pcraster.framework import generateNameT

def stackAverage(path,Root,StackStart,StackEnd):
	#calculates the average from a stack of maps, missing maps are skipped
	#Initialization
	MV= pcr.scalar(-999)
	NCount= pcr.scalar(0)
	SumStack= pcr.scalar(0)
	for StackNumber in range(StackStart,StackEnd):
		try:
			InMap= pcr.readmap(generateNameT(os.path.join(path,Root),StackNumber))
		except:
			InMap= MV;
		InMap= pcr.cover(InMap,MV)
		SumStack= SumStack+InMap
		NCount= NCount+pcr.ifthenelse(InMap <> MV,pcr.scalar(1),pcr.scalar(0))
	AvgStack= pcr.ifthenelse(NCount>0,SumStack/NCount,MV)
	return AvgStack

def createOutputDirs(DirList):
	#creates empty output directories
	for DirOut in DirList:
		if os.path.exists(DirOut):
			for Root, Dirs, Files in os.walk(DirOut):
				for File in Files:
					FileName= os.path.join(Root,File)
					try:
						os.remove(FileName)
					except:
						pass
		else:
			os.mkdir(DirOut)
	
def generateIniFiles(pathRes,YearDays,iniFiles= []):
	#this procedure does not take any arguments other than the input path and the number of days in
	#the year; it copies files reported at the last day of the year to the new input
	#files with specified extension
	SFX= 'ini'
	#setting last daily output to new initial conditions
	fileList= []
	for FileNameIn in os.listdir(pathRes):
		fileRoot, fileExt= os.path.splitext(FileNameIn)
		if fileExt == ('.%03d' % YearDays):
			if len(iniFiles) > 0:
				if fileRoot in iniFiles:
					fileList.append(FileNameIn)
			else:
				fileList.append(FileNameIn)
	for FileNameIn in fileList:
		FileNameOut= os.path.join(pathRes,FileNameIn.replace('-','_'))
		FileNameOut= FileNameOut.replace('%03d' % YearDays ,SFX)
		FileNameIn= os.path.join(pathRes,FileNameIn)
		try:
			#copying input files
			shutil.copy(FileNameIn,FileNameOut)
		except:
			print 'file ', FileNameIn,' not found'
			pass

def copyIniFiles(pathIn,pathOut,IniExtList= [],SpecMapList= [],recur= 0):
	#copy files from in to out on the basis of the provided extension list; if empty all is copied
	#creating file inventory
	for Root, Dirs, Files in os.walk(pathIn):
		#Dstpath created if absent
		Dir= Root.find('/')+1
		if Dir > 0 and recur:
			DstPath= Root[Dir:len(Root)]
			DstPath= os.path.join(pathOut,DstPath)
		else:
			DstPath= pathOut
		#checking whether destination directory exist, if not it is created
		if not os.path.exists(DstPath):
			os.mkdir(DstPath)
		for File in Files:
			#check if File is a valid inital file
			if len(IniExtList) >0:
				CopyFile= False
			else:
				CopyFile=  True
			for ncnt in range(0,len(IniExtList)):
				Ext= File[-3:]
				if Ext == IniExtList[ncnt]:
					CopyFile=  True
			if CopyFile:
				SrcName = os.path.join(Root,File)
				DstName = os.path.join(DstPath,File)
				try:
					shutil.copy(SrcName,DstName)
					print '\tcopying %s => %s' %(SrcName,DstName)
				except:
					pass
		for File in SpecMapList:
			SrcName = os.path.join(pathIn,File)
			DstName = os.path.join(pathOut,File)
			try:
				shutil.copy(SrcName,DstName)
				print '\tcopying %s => %s' %(SrcName,DstName)
			except:
				pass
