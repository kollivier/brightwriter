#!/usr/bin/python

from distutils.core import setup

import os
import sys
platform = None
if sys.platform.startswith("win"):
    import py2exe
    sys.argv.append("py2exe")
    platform = "win"
elif sys.platform.startswith("darwin"):
    import py2app
    sys.argv.append("py2app")
    platform = "mac"
import glob
import version

myplist = dict(
    CFBundleIdentifier='net.eclass.eclass_builder',
    CFBundleDisplayName="EClass.Builder",
    CFBundleVersion=version.asString()
    )
 
rootdir = "../"

py2app_options = dict(
    iconfile=rootdir + "icons/eclass_builder.icns", 
    argv_emulation=True,
    plist=myplist,
    optimize=2
)

def allFilesRecursive(dir):
    fileList = []
    print dir
    for root, subFolders, files in os.walk(dir):
        if root.find(".svn") == -1:
            dirfiles = [root.replace(rootdir, ""),[]]
            for file in files:
                path = os.path.join(root,file)
                if path.find(".svn") == -1:
                    dirfiles[1].append(os.path.join(root,file))
            fileList.append(dirfiles)
    return fileList

py2exe_options = dict(skip_archive=True)

subdirs = ['3rdparty/src/flash_flv_player', '3rdparty/src/flash_mp3_player', '3rdparty/' + platform, 'about', 'autorun', 'convert', 
                'docs', 'externals', 'greenstone', 'icons', 'locale', 'license',
                'mmedia', 'plugins', 'themes', 'web']

source_files = []

for subdir in subdirs:
    source_files.extend(allFilesRecursive(rootdir + subdir))

setup(
    name="EClass.Builder",
    app=[rootdir + 'eclass_builder.py'],
    data_files=source_files,
    options=dict(py2exe=py2exe_options, py2app=py2app_options),
)
