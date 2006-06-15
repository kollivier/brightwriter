#files.py - misc file functions needed by conman

#Author - Kevin Ollivier

#Date - 5/8/02
import sys
import os
import utils

def CopyFiles(indir, outdir, recurse=0):
	if not os.path.exists(outdir):
		os.makedirs(outdir)
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
		file = utils.openFile(os.path.join(indir, filename), "rb")
		data = file.read()
		file.close()
	except IOError:
		print "Error reading file: " + os.path.join(indir, filename)
		return False

	try:
		out = utils.openFile(os.path.join(outdir, filename), "wb")
		out.write(data)
		out.close()
	except:
		print "Error writing file: " + os.path.join(outdir, filename)
		return False

	return True

def DeleteFiles(pattern):
	import glob
	for afile in glob.glob(pattern):
		if os.path.exists(afile):
			os.remove(afile)

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
	

def MakeFileName2(mytext):
    """
    Function: MakeFileName2(mydir, mytext)
    Last Updated: 10/21/02
    Description: Returns a filename valid on supported operating systems. Also checks for existing files and renames if necessary.
    Replacement for MakeFileName which oddly is designed only for .ecp files...
    """

    mytext = utils.createSafeFilename(mytext)
    mytext = mytext.replace(" ", "_")
    return mytext