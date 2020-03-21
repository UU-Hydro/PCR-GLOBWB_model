import os, sys, shutil

print 'input path, input str, output path, output str'

inputPath= sys.argv[1]
inputStr= sys.argv[2]
outputPath= sys.argv[3]
outputStr= sys.argv[4]

if not os.path.exists(outputPath):
	sys.exit('%s does not exist')
	
for fileName in os.listdir(inputPath):
	if inputStr in fileName:
		inputFileName= os.path.join(inputPath,fileName)
		outputFileName= os.path.join(outputPath,fileName.replace(inputStr,outputStr))
		print inputFileName,
		try:
			shutil.copy(inputFileName,outputFileName)
			print 'copied'
		except:
			print 'could not be moved'
	
