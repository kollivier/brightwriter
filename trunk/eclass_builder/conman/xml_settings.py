#xml_settings.py - script for loading and saving Python app settings as XML. Settings are represented internally as a 
#Python dictionary. Does not currently support dictionaries or lists
#Version: 0.
#Author: Kevin Ollivier
#Date: 4/5/01

USE_MINIDOM=0
try:
	from xml.dom.ext.reader.Sax import FromXmlFile
except:
	USE_MINIDOM=1

if USE_MINIDOM:
	from xml.dom import minidom

import sys

class XMLSettings:
	def __init__(self):
		self.settings = {}
		self.filename = ""

	def __getitem__(self, key):
		if not self.settings.has_key(key):
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
		for key in self.settings.keys():
			text = text + key + "=" + str(self.settings[key]) + "\n"
		return text
		
	def keys(self):
		return self.settings.keys()

	def Add(self, key, value):
		self.settings[key] = value

	def Remove(self, key):
		del self.settings[key]

	def LoadFromXML(self, filename):
		self.settings = {}
		self.filename = filename
		if USE_MINIDOM:
			doc = minidom.parse(open(filename))
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

	def SaveAsXML(self, filename):
		XML = """<?xml version="1.0"?>\n<Settings>"""
		for key in self.settings.keys():
			XML = XML + "<Setting name=\"" + str(key) + "\" value=\"" + str(self.settings[key]) + "\"/>\n"
		XML = XML + "</Settings>"
		xmlfile = open(filename, "w")
		xmlfile.write(XML)
		xmlfile.close()
		return None

def Test():
	settings = XMLSettings()
	settings.LoadFromXML("xmltest1.xml")
	print `settings`

if __name__ == "__main__":
	if len(sys.argv) > 1:
		if sys.argv[1] == "-t":
			Test()

