from __future__ import print_function
#xml_settings.py - script for loading and saving Python app settings as XML. Settings are represented internally as a 
#Python dictionary. Does not currently support dictionaries or lists
#Version: 0.
#Author: Kevin Ollivier
#Date: 4/5/01

from builtins import str
from builtins import range
from builtins import object
USE_MINIDOM=0
try:
    from xml.dom.ext.reader.Sax import FromXmlFile
except:
    USE_MINIDOM=1

if USE_MINIDOM:
    from xml.dom import minidom

import sys

class XMLSettings(object):
    def __init__(self):
        self.settings = {}
        self.filename = ""

    def __getitem__(self, key):
        if key not in self.settings:
            self.settings[key] = "" 
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value

    def __delitem__(self, key):
        del self.settings[key]

    def __getslice__(self, low, high):
        return self.settings[low:high]

    def __setslice__(self, low, high, seq):
        self.settings[low:high] = seq

    def __delslice__(self, low, high):
        del self.settings[low:high]

    def __repr__(self):
        text = ""
        for key in list(self.settings.keys()):
            text = text + key + "=" + str(self.settings[key]) + "\n"
        return text
        
    def keys(self):
        return list(self.settings.keys())

    def Add(self, key, value):
        self.settings[key] = value

    def Remove(self, key):
        del self.settings[key]

    def LoadFromXML(self, filename=None):
        self.settings = {}
        self.filename = filename

        if USE_MINIDOM:
            doc = minidom.parseString(open(filename, 'rb').read().decode('utf-8'))
        else:
            doc = FromXmlFile(filename)

        settings = doc.getElementsByTagName("Setting")
        for item in settings:
            if item.attributes:
                myname = ""
                myvalue = ""
                for i in range(0, len(item.attributes)):
                    attr = item.attributes.item(i)
                    if attr.name == "name":
                        myname = attr.value
                    elif attr.name == "value":
                        myvalue = attr.value
                self.settings[myname] = myvalue

    def SaveAsXML(self, filename=None):
        XML = """<?xml version="1.0" encoding="utf-8"?>\n<Settings>"""
        doc = minidom.Document()
        root = doc.createElement("Settings")

        if filename:
            self.filename = filename

        if not self.filename:
            raise IOError("No filename set for XMLSettings file!")
        
        for key in list(self.settings.keys()):
            setting = doc.createElement("Setting")
            setting.setAttribute("name", key)
            setting.setAttribute("value", self.settings[key])
            root.appendChild(setting)
        
        doc.appendChild(root)
        
        import codecs
        data = doc.toprettyxml("\t", encoding="utf-8")
        myfile = open(self.filename, "wb")
        myfile.write(codecs.BOM_UTF8)
        myfile.write(data)
        myfile.close()
        return True

def Test():
    settings = XMLSettings()
    settings.LoadFromXML("xmltest1.xml")
    print(repr(settings))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-t":
            Test()

