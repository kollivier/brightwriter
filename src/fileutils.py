from __future__ import print_function
#files.py - misc file functions needed by conman

#Author - Kevin Ollivier

#Date - 5/8/02

import mimetypes
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

MIMETYPE_SUBDIRS = {
    'audio': 'Audio',
    'image': 'Graphics',
    'video': 'Video',
    'text': 'File',
    'default': 'File'
}

def get_project_file_location(filename):
    type, _encoding = mimetypes.guess_type(filename)
    subdir = MIMETYPE_SUBDIRS['default']
    if type:
        primary_type = type.split('/')[0]
        subdir = MIMETYPE_SUBDIRS.get(primary_type, MIMETYPE_SUBDIRS['default'])

    return os.path.join(settings.ProjectDir, subdir, os.path.basename(filename))

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
                        print("Could not make directory: " + myoutdir)

                if os.path.isdir(myoutdir):
                    CopyFiles(os.path.join(indir,item) ,myoutdir, 1, callback)

def copy_file_if_changed(src_file, dest_file):
    # Don't copy files unless we need to, that way FTP sync won't
    # copy over files that haven't really changed just because the timestamp
    # changed.
    if os.path.exists(dest_file):
        if os.path.getmtime(dest_file) >= os.path.getmtime(src_file):
            if os.path.getsize(dest_file) == os.path.getsize(src_file):
                return False
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    shutil.copy(src_file, dest_file)
    return True

def CopyFile(filename, indir, outdir):
    if indir == outdir:
        return False
    infile = os.path.join(indir, filename)
    outfile = os.path.join(outdir, filename)

    return copy_file_if_changed(infile, outfile)

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
            myfilename = myname[:-2] + repr(counter) + myext
        else:
            myfilename = myname[:-1] + repr(counter) + myext
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
