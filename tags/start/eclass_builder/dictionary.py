#!/usr/bin/env python

from conman.validate import *
from xml.dom.ext.reader.Sax import FromXmlFile
import conman.xml_settings as xml_settings
import sys,os

class EClassLabel:
	def __init__(self):
		self.codelabel = ""
		self.stringtext = ""

the_dictionary = {}
filename = ""

class DictionaryManager:
	def __init__(self):
		self.filename=""
		self.the_dictionary={}
		
	def LoadDictionary(self, filename=""):
		if len(filename) > 0:
			self.filename = filename
		doc = FromXmlFile(self.filename)
		self.LoadDoc(doc)
		return self.the_dictionary

	def LoadDoc(self, doc):		
		the_labels=doc.getElementsByTagName("LABEL")
		for the_label in the_labels:
			a_label=EClassLabel()
			the_codelabel=the_label.getElementsByTagName("CODELABEL")[0].childNodes
			the_stringtext=the_label.getElementsByTagName("STRING")[0].childNodes
			if the_codelabel:
				a_label.codelabel=XMLCharToText(the_codelabel[0].nodeValue)
			else:
				the_codelabel="-"
			if the_stringtext:
				a_label.stringtext=XMLCharToText(the_stringtext[0].nodeValue)
			else:
				the_stringtext="-"	
			self.the_dictionary[str(a_label.codelabel)]=str(a_label.stringtext)
