#updateVersion.py
#this should be run whenever the software is rebuilt

import re
import os
import glob
import version
build = version.build

mydir = os.getcwd()
os.chdir("..")
#Write the new build to version.py
myfile = open("version.py", "r")
data = myfile.read()
myfile.close()

myterm = re.compile("(build = )([0-9]*)", re.IGNORECASE|re.DOTALL)
mymatch = myterm.match(data)

data = myterm.sub("\\1" + `build`, data)

myfile = open("version.py", "w")
myfile.write(data)
myfile.close()

reload(version)

#update the installer version number
myfile = open(os.path.join("installer", "eclass-builder.nsi"), "r")
data = myfile.read()
myfile.close()

myterm = re.compile("(!define MUI_VERSION \").*(\")",re.IGNORECASE|re.MULTILINE)
data = myterm.sub("\\1" + version.asString() + "\\2", data)

myfile = myfile = open(os.path.join("installer", "eclass-builder.nsi"), "w")
myfile.write(data)
myfile.close()

#update the version number in the about box
aboutfiles = glob.glob(os.path.join("about","*","*.htm*"))
for file in aboutfiles:
    myfile = open(file, "r")
    data = myfile.read()
    myfile.close()

    myterm = re.compile("(<strong>EClass.Builder )(.*)(<br>)",re.IGNORECASE|re.MULTILINE)
    data = myterm.sub("\\1" + version.asString() + "\\3", data)

    myfile = myfile = open(file, "w")
    myfile.write(data)
    myfile.close()

os.chdir(mydir)