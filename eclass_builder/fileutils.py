#files.py - misc file functions needed by conman

#Author - Kevin Ollivier

#Date - 5/8/02
import sys
import os
import utils
import settings
import constants

def getPubDir():
    return os.path.join(settings.ProjectDir, "pub")

def getGraphicsDir():
    return os.path.join(settings.ProjectDir, "Graphics")
    
def getAudioDir():
    return os.path.join(getPubDir(), "Audio")
    
def getVideoDir():
    return os.path.join(getPubDir(), "Video")
    
def getTextDir():
    return os.path.join(settings.ProjectDir, "Text")
    
def getPresentDir():
    return os.path.join(settings.ProjectDir, "Present")
    
def getFileDir():
    return os.path.join(settings.ProjectDir, "File")
    
def getContactsDir():
    return os.path.join(settings.PrefDir, "Contacts")

def CopyFiles(indir, outdir, recurse=0):
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	for item in os.listdir(indir):
		if os.path.isfile(os.path.join(indir, item)):
			CopyFile(item, indir, outdir)
		elif os.path.isdir(os.path.join(indir, item)) and recurse:
			if not item.upper() == "CVS":
				myoutdir = os.path.join(outdir, item)
				if not os.path.isdir(myoutdir):
					try:
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
	
def getShortenedFilename(filename):
    oldfilename = filename
    dirname = os.path.dirname(oldfilename)
    myname, myext = os.path.splitext(oldfilename)
    myname = myname[:31-len(myext)]
    myfilename = myname + myext
    counter = 1
    while os.path.exists(os.path.join(dirname, myfilename)):
        if counter > 9:
            myfilename = myname[:-2] + `counter` + myext
        else:
            myfilename = myname[:-1] + `counter` + myext
        counter = counter + 1
        #print "new filename is: " + myfilename + "\n"
    return os.path.join(dirname, myfilename)

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