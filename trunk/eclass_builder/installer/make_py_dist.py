#
#  This file is part of Documancer (http://documancer.sf.net)
#
#  Copyright (C) 2004 Kevin Ollivier
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#  $Id$
#
#  This script creates the mini python distribution that is shipped
#  with Documancer on Windows.

import sys, os, string, shutil, glob, modulefinder

def makedir(path):
    pathparts = string.split(path, os.sep)
    fullpath = ""
    for part in pathparts:
        fullpath = fullpath + part + os.sep
        if not os.path.exists(fullpath):
            os.mkdir(fullpath)

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", "src"))
modfinder = modulefinder.ModuleFinder(excludes=["Tkinter"])
#modulefinder.ReplacePackage("_xmlplus", "xml")
modfinder.add_module("site")
modfinder.run_script(os.path.join("..", "editor.py"))

deps = []

for item in modfinder.modules.items():
    filename = item[1].__file__
    #print filename
    if filename and string.find(filename, sys.prefix) != -1:
        deps.append(filename)

encodingsdir = os.path.join(sys.prefix, "lib", "encodings", "*")
deps = deps + glob.glob(encodingsdir)
deps = deps + glob.glob(os.path.join(sys.prefix, "*.txt"))
libdir = os.path.join(sys.prefix, "lib")
deps.append(os.path.join(libdir, "site.py"))
deps.append(os.path.join(libdir, "locale.py"))
deps.append(os.path.join(libdir, "codecs.py"))

#these are for indexer.py
deps.append(os.path.join(libdir, "HTMLParser.py"))
deps.append(os.path.join(libdir, "formatter.py"))
deps.append(os.path.join(libdir, "markupbase.py"))

#if we're using wxPython 2.5.3 or above, we need to include wx.pth
wxpth_file = os.path.join(sys.prefix, "lib", "site-packages", "wx.pth")
if os.path.exists(wxpth_file):
    deps.append(wxpth_file)

if os.name == "nt":
    deps.append(os.path.join(sys.prefix, "python.exe"))
    deps.append(os.path.join(sys.prefix, "w9xpopen.exe"))

mpdir = "minipython"

if os.path.exists(mpdir):
    shutil.rmtree(mpdir)

os.mkdir(mpdir)
os.mkdir(os.path.join(mpdir, "lib"))
os.mkdir(os.path.join(mpdir, "lib", "site-packages"))
os.mkdir(os.path.join(mpdir, "lib", "encodings"))
#shutil.copytree(os.path.join(libdir, "xml"), os.path.join(mpdir, "lib", "xml"))

for filename in deps:
    destfilename = string.replace(filename, sys.prefix, mpdir)
    makedir(os.path.dirname(destfilename))
    shutil.copyfile(filename, destfilename)
    if os.path.splitext(filename)[1] == ".pyd":
        stream = os.popen("dumpbin.exe /DEPENDENTS " + filename)
        data = stream.read()
        stream.close()
        
        data = string.split(data, "\n")
        for datum in data:
            if string.find(datum, ".dll") != -1:
                thisfile = string.strip(datum)
                thisdir = os.path.dirname(filename)
                destdir = os.path.dirname(destfilename)
                #if the DLL is not in the extension's directory
                #that means it's on the path somewhere, so it should
                #not be copied in
                if os.path.exists(os.path.join(thisdir, thisfile)):
                    shutil.copyfile(os.path.join(thisdir, thisfile), os.path.join(destdir, thisfile))

print `modfinder.any_missing_maybe()`
