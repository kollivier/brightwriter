#files.py - misc file functions needed by conman

#Author - Kevin Ollivier

#Date - 5/8/02
import sys
import os	

def CopyFiles(indir, outdir, recurse=0):
	for item in os.listdir(indir):
		if os.path.isfile(os.path.join(indir, item)):
			CopyFile(item, indir, outdir)
		elif os.path.isdir(os.path.join(indir, item)) and recurse:
			myoutdir = os.path.join(outdir, item)
			if not os.path.isdir(myoutdir):
				try:
					if not item == "CVS":
						os.mkdir(myoutdir)
				except: 
					print "Could not make directory: " + myoutdir
			
			if os.path.isdir(myoutdir):
				CopyFiles(os.path.join(indir,item) ,myoutdir, 1)

def CopyFile(filename, indir, outdir): 
	try: 
		file = open(os.path.join(indir, filename), "rb")
		data = file.read()
		file.close()
	except IOError:
		print "Error reading file: " + os.path.join(indir, filename)
		return 0

	try:
		out = open(os.path.join(outdir, filename), "wb")
		out.write(data)
		out.close()
	except:
		print "Error writing file: " + os.path.join(outdir, filename)
		return 0

	return 1

def DeleteFolder(folder):
	if not os.path.exists(folder):
		return False

	files = os.listdir(folder)
	for file in files:
		filename = os.path.join(folder, file)
		if os.path.isfile(filename):
			os.remove(filename)
		elif os.path.isdir(filename):
			DeleteFolder(filename) 

	os.rmdir(folder)