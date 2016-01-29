#!/usr/bin/python

from distutils.core import setup

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "htmleditor"))

platform = None
if sys.platform.startswith("win"):
    import py2exe
    sys.argv.append("py2exe")
    platform = "win32"
elif sys.platform.startswith("darwin"):
    import py2app
    sys.argv.append("py2app")
    platform = "mac"
import glob

import settings
import version

myplist = dict(
    CFBundleIdentifier='net.eclass.eclass_builder',
    CFBundleDisplayName="EClass.Builder",
    CFBundleVersion=version.asString()
    )
 
rootdir = "./"

py2app_options = dict(
    iconfile=rootdir + "icons/eclass_builder.icns", 
    argv_emulation=True,
    plist=myplist,
    optimize=2,
    strip=False,
    packages=["wx"],
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

subdirs = ['3rdparty/mediaplayer-5.3', '3rdparty/src/flash_mp3_player', '3rdparty/' + platform, 'about', 'autorun', 'convert', 
                '3rdparty/bin', 'docs/en/web', 'externals', 'greenstone', 'icons', 'locale', 'license',
                'mmedia', 'plugins', 'themes', 'web']

source_files = []

for subdir in subdirs:
    source_files.extend(allFilesRecursive(rootdir + subdir))

setup(
    name=settings.app_name,
    app=[rootdir + 'eclass_builder.py'],
    windows=[{"script": rootdir + 'eclass_builder.py', "icon_resources": [(1, rootdir + "icons/eclass_builder.ico")]}],
    data_files=source_files,
    options=dict(py2exe=py2exe_options, py2app=py2app_options),
)

if sys.platform.startswith("darwin"):
    dmg_name = "%s %s.dmg" % (settings.app_name, version.asString())
    deploy_dir = "deploy"
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)

    deploy_path = os.path.join(deploy_dir, dmg_name)
    if os.path.exists(deploy_path):
        os.remove(deploy_path)
    cmd = "hdiutil create -srcfolder dist -volname \"%s\" -imagekey zlib-level=9 \"%s\"" % (settings.app_name, deploy_path)
    os.system(cmd)
