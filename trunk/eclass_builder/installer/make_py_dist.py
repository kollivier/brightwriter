#  Copyright (C) 2004 Kevin Ollivier
#  Licensing terms are in the license/license.txt file.

import sys, os, string, shutil, glob, modulefinder, re
import wxversion
flavor = "ansi"
wx_version = "2.8"
if len(sys.argv) > 1:
    if sys.argv[1] == "--unicode":
        flavor = "unicode"

wxversion.select(wx_version + "-" + flavor)

#rename the installer appropriately.
myfile = open("eclass-builder.nsi", "r")
data = myfile.read()
myfile.close()

#create a python version string
py_version = sys.version[0:3]
py_version = string.replace(py_version, ".", "")

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

port = "msw"
if os.name == "nt": 
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell", "win32com.client"]:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
elif sys.platform == "darwin":
    port = "mac"
else:
    port = "gtk"

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "..", "src"))
modfinder = modulefinder.ModuleFinder(excludes=["Tkinter"])
modulefinder.ReplacePackage("xml", "_xmlplus")
modfinder.add_module("site")
modfinder.add_module("wxaddons.wxblox")

scripts = [os.path.join("..", "eclass_builder.py"), os.path.join("..", "editor.py"), os.path.join("..", "converter.py")]
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

encodingsdir = os.path.join(sys.prefix, "lib", "encodings")
deps = deps + glob.glob(os.path.join(encodingsdir, "*.*"))
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
#wxpth_file = os.path.join(sys.prefix, "lib", "site-packages", "wx.pth")
#if os.path.exists(wxpth_file):
#    deps.append(wxpth_file)
myfile = open(os.path.join(mpdir, "lib", "site-packages", "wx.pth"), "w")
myfile.write("wx-" + wx_version + "-" + port + "-" + flavor)
myfile.close()

if os.name == "nt":
    deps.append(os.path.join(sys.prefix, "python.exe"))
    deps.append(os.path.join(sys.prefix, "w9xpopen.exe"))
    import win32api
    sysdir = win32api.GetSystemDirectory()
    #if the below file exists, then the dependency checking will copy it over
    #if not, we need to check the Windows system dir for it
    py_dll_name = "python%s.dll" % (py_version)
    msvc_dlls = glob.glob(os.path.join(sys.prefix, "msvc*"))
    for dll in msvc_dlls:
        shutil.copyfile(dll, os.path.join(mpdir, os.path.basename(dll)))

    if not os.path.exists(os.path.join(sys.prefix, py_dll_name)):
        syspython = os.path.join(sysdir, py_dll_name)
        if os.path.exists(syspython):
            shutil.copyfile(syspython, os.path.join(mpdir, py_dll_name))
    else: 
        shutil.copyfile(os.path.join(sys.prefix, py_dll_name), os.path.join(mpdir, py_dll_name))

    pywindlls = ["PyWinTypes" + py_version + ".dll", "PythonCOM" + py_version + ".dll"]
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

#let's test for dumpbin.exe first
if sys.platform == "win32":
    stream = os.popen("dumpbin.exe")
    data = stream.read()
    stream.close()
    text = string.strip(data)
    if text == "":
        print "FATAL ERROR: Cannot generate dependency lists. Is dumpbin.exe on your path?"
        sys.exit(1)

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
