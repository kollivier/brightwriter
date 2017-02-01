#!/usr/bin/python

from distutils.core import setup

import logging
logging.basicConfig()
import os
import sys

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

import constants
import settings
import version

import pewtools.codesign

try:
    from local_settings import *
except:
    pass

myplist = dict(
    CFBundleIdentifier='com.kosoftworks.brightwriter',
    CFBundleDisplayName="BrightWriter",
    CFBundleVersion=version.asString()
    )
 
rootdir = "./"

py2app_options = dict(
    iconfile=rootdir + "icons/brightwriter.icns", 
    argv_emulation=True,
    plist=myplist,
    optimize=2,
    strip=False,
    packages=["wx", "cefpython3"],
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

dll_excludes_win = ["combase.dll", "crypt32.dll", "dhcpcsvc.dll", "msvcp90.dll", "mpr.dll", "oleacc.dll", "powrprof.dll", "psapi.dll", "setupapi.dll", "userenv.dll",  "usp10.dll", "wtsapi32.dll"]
dll_excludes_win.extend(["iertutil.dll", "iphlpapi.dll", "nsi.dll", "urlmon.dll", "Secur32.dll", "webio.dll","wininet.dll", "winhttp.dll", "winnsi.dll"])


py2exe_options = {"skip_archive":True, "dll_excludes": dll_excludes_win, "packages": ['wx.lib.pubsub']}

subdirs = ['3rdparty/mediaplayer-5.3', '3rdparty/src/flash_mp3_player', '3rdparty/' + platform, 'about', 'autorun', 'convert', 
                '3rdparty/bin', 'docs/en/web', 'externals', 'greenstone', "gui/html", 'icons', 'locale', 'license',
                'mmedia', 'plugins', 'themes', 'web']

source_files = []

for subdir in subdirs:
    source_files.extend(allFilesRecursive(rootdir + subdir))

import cefpython3
cefp = os.path.dirname(cefpython3.__file__)

if sys.platform.startswith("win"):
    source_files.extend([('', ['%s/icudt.dll' % cefp,
          '%s/cef.pak' % cefp,
          '%s/cefclient.exe' % cefp,
          '%s/d3dcompiler_43.dll' % cefp,
          '%s/d3dcompiler_46.dll' % cefp,
          '%s/devtools_resources.pak' % cefp,
          '%s/ffmpegsumo.dll' % cefp,
          '%s/libEGL.dll' % cefp,
          '%s/libGLESv2.dll' % cefp,
          '%s/subprocess.exe' % cefp]),
        ('locales', ['%s/locales/en-US.pak' % cefp]),
        ]
    )

setup(
    name=settings.app_name,
    app=[rootdir + 'main.py'],
    windows=[{"script": rootdir + 'main.py', "icon_resources": [(1, rootdir + "icons/brightwriter.ico")]}],
    data_files=source_files,
    options=dict(py2exe=py2exe_options, py2app=py2app_options),
)

if sys.platform.startswith("darwin"):
    if 'osx_identity' in globals():
        to_sign = []
        output_path = os.path.abspath("dist/BrightWriter.app")
        os.remove(os.path.join(output_path, "Contents", "Frameworks", "subprocess"))
        to_sign.extend(glob.glob(os.path.join(output_path, "Contents", "Frameworks", "*.framework")))
        to_sign.extend(glob.glob(os.path.join(output_path, "Contents", "Frameworks", "*.dylib")))
        to_sign.extend(glob.glob(os.path.join(output_path, "Contents", "Frameworks", "*.so")))
        to_sign.extend(glob.glob(os.path.join(output_path, "Contents", "Resources", "lib", "python2.7", "cefpython3", "*.dylib")))
        to_sign.extend(glob.glob(os.path.join(output_path, "Contents", "Resources", "lib", "python2.7", "cefpython3", "*.so")))
        exes = ["Python"]
        for exe in exes:
            to_sign.append(os.path.join(output_path, 'Contents', 'MacOS', exe))

        # sign the main bundle last
        to_sign.append(output_path)
        for path in to_sign:
            pewtools.codesign.osx_code_sign_file(path, osx_identity)

    else:
        logging.warning("Not code-signing build, for local use only.")

    dmg_name = "%s %s.dmg" % (settings.app_name, version.asString())
    dmg_name = dmg_name.replace(" ", "-")
    deploy_dir = "deploy5"
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)

    deploy_path = os.path.join(deploy_dir, dmg_name)
    if os.path.exists(deploy_path):
        os.remove(deploy_path)
    cmd = "hdiutil create -srcfolder dist -volname \"%s\" -imagekey zlib-level=9 \"%s\"" % (settings.app_name, deploy_path)
    os.system(cmd)
