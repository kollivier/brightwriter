#!/usr/bin/python

from distutils.core import setup

import glob
import os
import shutil
import sys

sys.path.append("..")
platform = None
if sys.platform.startswith("win"):
    import py2exe
    sys.argv.append("py2exe")
    platform = "win32"
elif sys.platform.startswith("darwin"):
    import py2app
    sys.argv.append("py2app")
    platform = "mac"

myplist = dict(
    CFBundleIdentifier='net.eclass.htmledit',
    CFBundleDisplayName="EClass.HTMLEdit",
    CFBundleVersion="0.1"
    )

py2app_options = dict(
    argv_emulation=True,
    plist=myplist,
    optimize=2
)

py2exe_options = dict(skip_archive=True)

rootdir = os.path.dirname(__file__)
distdir = os.path.join(rootdir, "dist")

if os.path.exists(distdir):
    shutil.rmtree(distdir)

source_files = glob.glob("htmledit/images/*")

setup(
    name="EClass.HTMLEdit",
    app=[rootdir + 'htmleditor.py'],
    windows=[{"script": rootdir + 'htmleditor.py'}],
    data_files=[("htmledit/images", source_files)],
    options=dict(py2exe=py2exe_options, py2app=py2app_options),
)
