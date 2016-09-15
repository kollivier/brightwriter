#updateVersion.py
#this should be run whenever the software is rebuilt

import sys
import re
import os
import glob
import version
version_str = version.asString()

if len(sys.argv) == 2:
    version_str = sys.argv[1]

mydir = os.getcwd()
os.chdir("..")
#Write the new build to version.py
#myfile = open("version.py", "r")
#data = myfile.read()
#myfile.close()

#myterm = re.compile("(build = )([0-9]*)", re.IGNORECASE|re.DOTALL)
#mymatch = myterm.match(data)

#data = mymatch.sub("\\1" + `build`, data)

#myfile = open("version.py", "w")
#myfile.write(data)
#myfile.close()

#reload(version)

#update the installer version number
myfile = open(os.path.join("installer", "eclass-builder.nsi"), "r")
data = myfile.read()
myfile.close()

myterm = re.compile('define MUI_VERSION "[^"]*"',re.IGNORECASE|re.MULTILINE)
data = myterm.sub("define MUI_VERSION \"" + version_str + "\"", data)

myfile = myfile = open(os.path.join("installer", "eclass-builder.nsi"), "w")
myfile.write(data)
myfile.close()

#update the version number in the about box
aboutfiles = glob.glob(os.path.join("about","*","*.htm*"))
for file in aboutfiles:
    myfile = open(file, "r")
    data = myfile.read()
    myfile.close()

    myterm = re.compile("<strong>BrightWriter .*<br>",re.IGNORECASE|re.MULTILINE)
    data = myterm.sub("<strong>BrightWriter " + version_str + "<br>", data)

    myfile = myfile = open(file, "w")
    myfile.write(data)
    myfile.close()

os.chdir(mydir)