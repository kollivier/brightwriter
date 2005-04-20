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

import sys, os, string, shutil, glob, modulefinder, re
#import wxversion
flavor = "ansi"

#if len(sys.argv) > 1:
#    if sys.argv[1] == "--unicode":
#        flavor = "unicode"

#wxversion.select("2.5-" + flavor)

#rename the installer appropriately.
myfile = open("eclass-builder.nsi", "r")
data = myfile.read()
myfile.close()

myterm = re.compile("(!define UNICODE_STRING \").*(\")",re.IGNORECASE|re.MULTILINE)
unicodeText = ""
if flavor == "unicode":
    unicodeText = "-unicode"

data = myterm.sub("\\1" + unicodeText + "\\2", data)

myfile = myfile = open("eclass-builder.nsi", "w")
myfile.write(data)
myfile.close()

def makedir(path):
    pathparts = string.split(path, os.sep)
    fullpath = ""
    for part in pathparts:
        fullpath = fullpath + part + os.sep
        if not os.path.exists(fullpath):
            os.mkdir(fullpath)

if os.name == "nt": 
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell", "win32com.client"]:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", "src"))
modfinder = modulefinder.ModuleFinder(excludes=["Tkinter"])
#modulefinder.ReplacePackage("_xmlplus", "xml")
modfinder.add_module("site")

scripts = [os.path.join("..", "editor.py"), os.path.join("..", "converter.py")]
deps = []

for script in scripts:
    modfinder.run_script(script)
    for item in modfinder.modules.items():
        filename = item[1].__file__
    #print filename
        if filename and string.find(filename, sys.prefix) != -1:
            deps.append(filename)

mpdir = "minipython"

if os.path.exists(mpdir):
    shutil.rmtree(mpdir)

os.mkdir(mpdir)
os.mkdir(os.path.join(mpdir, "lib"))
os.mkdir(os.path.join(mpdir, "lib", "site-packages"))
os.mkdir(os.path.join(mpdir, "lib", "encodings"))

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
    import win32api
    sysdir = win32api.GetSystemDirectory()
    #if the below file exists, then the dependency checking will copy it over
    #if not, we need to check the Windows system dir for it
    if not os.path.exists(os.path.join(sys.prefix, "python23.dll")):
        syspython = os.path.join(sysdir, "python23.dll")
        if os.path.exists(syspython):
            shutil.copyfile(syspython, os.path.join(mpdir, "python23.dll"))

    pywindlls = ["PyWinTypes23.dll", "PythonCOM23.dll"]
    for dll in pywindlls:
        pywindll = os.path.join(sysdir, dll)
        if os.path.exists(pywindll):
            shutil.copyfile(pywindll, os.path.join(mpdir, dll))

    #we need this to make sure win32 modules are on the path.
    myfile = open(os.path.join(mpdir, "lib", "site-packages", "win32.pth"), "w")
    myfile.write("win32")
    myfile.close()

    myfile = open(os.path.join(mpdir, "lib", "site-packages", "win32lib.pth"), "w")
    myfile.write("win32/lib")
    myfile.close()

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
                filename = os.path.join(os.path.dirname(filename), thisfile)
                destdir = os.path.dirname(destfilename)
                #if the DLL is not in the extension's directory
                #that means it's on the path somewhere, so it should
                #not be copied in
                if os.path.exists(filename):
                    shutil.copyfile(filename, os.path.join(destdir, thisfile))

print `modfinder.any_missing_maybe()`
