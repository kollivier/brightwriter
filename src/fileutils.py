#files.py - misc file functions needed by conman

#Author - Kevin Ollivier

#Date - 5/8/02

import os
import shutil
import sys

import utils
import settings


def getNumFiles(dirname, recurse=True):
    numFiles = 0
    for filename in os.listdir(dirname):
        fullname = os.path.join(dirname, filename)
        if os.path.isfile(fullname):
            numFiles += 1
        elif recurse and os.path.isdir(fullname):
            numFiles += getNumFiles(fullname)
            
    return numFiles
            
def isHidden(filename):
    """
    Determines if a file is marked hidden, or is within a hidden directory.
    """
    for part in filename.split(os.sep):
        if not len(part) == 1 and part.startswith("."):
            return True
    
    return False

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

def CopyFiles(indir, outdir, recurse=0, callback=None):
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	if os.path.basename(indir).startswith('.'):
		return
		
	for item in os.listdir(indir):
		
		if os.path.isfile(os.path.join(indir, item)):
			if callback:
				callback.fileChanged(item)
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
					CopyFiles(os.path.join(indir,item) ,myoutdir, 1, callback)

def CopyFile(filename, indir, outdir):
	if indir == outdir:
		return False
	infile = os.path.join(indir, filename)
	outfile = os.path.join(outdir, filename)
	
	# Don't copy files unless we need to, that way FTP sync won't 
	# copy over files that haven't really changed just because the timestamp 
	# changed.
	if os.path.exists(outfile):
		if os.path.getmtime(outfile) >= os.path.getmtime(infile):
			if os.path.getsize(outfile) == os.path.getsize(infile):
				return False
	shutil.copy(os.path.join(indir, filename), outdir)
	return True

def DeleteFiles(pattern):
	import glob
	for afile in glob.glob(pattern):
		if os.path.exists(afile):
			os.remove(afile)
	
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
