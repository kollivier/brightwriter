import string, os
import utils

def TextToXMLChar(mytext):
	"""
	Function: validate.TextToXMLChar(mytext)
	Last Updated: 9/24/02
	Description: Validates text and converts special characters to their XML character equivalents.
	"""
	mytext = string.replace(mytext, u"&", "&amp;")
	#mytext = string.replace(mytext, u"\"", "&quot;")
	mytext = string.replace(mytext, u"<", "&lt;")
	mytext = string.replace(mytext, u">", "&gt;")
	return mytext

def XMLCharToText(mytext):
	"""
	Function: validate.XMLCharToText(mytext)
	Last Updated: 9/24/02
	Description: Validates XML character text and converts XML special characters to their text equivalent.
	"""
	mytext = string.replace(mytext, "&amp;", u"&")
	mytext = string.replace(mytext, "&quot;", u"\"")
	mytext = string.replace(mytext, "&lt;", u"<")
	mytext = string.replace(mytext, "&gt;", u">")
	return mytext

def XMLAttrToText(mytext):
	"""
	Function: validate.XMLAttrToText(mytext)
	Last Updated: 9/24/02
	Description: Validates XML attribute text and converts special characters to their text equivalents
	"""
	mytext = string.replace(mytext, "&amp;", u"&")
	mytext = string.replace(mytext, "&quot;", u'"')
	mytext = string.replace(mytext, "&lt;", u"<")
	mytext = string.replace(mytext, "&gt;", u">")
	return mytext

def TextToXMLAttr(mytext):
	"""
	Function: validate.TextToXMLAttr(mytext)
	Last Updated: 9/24/02
	Description: Validates text and converts special characters to their XML attribute equivalents
	"""
	mytext = string.replace(mytext, u"&", "&amp;")
	mytext = string.replace(mytext, u'"', "&quot;")
	mytext = string.replace(mytext, u"<", "&lt;")
	mytext = string.replace(mytext, u">", "&gt;")
	return mytext

def TextToHTMLChar(mytext):
	mytext = TextToXMLChar(mytext)
	mytext = string.replace(mytext, u"©", "&copy;")
	#mytext = string.replace(mytext, u"¨", "&reg;")
	#mytext = string.replace(mytext, u"ª", "&8482;")
	mytext = string.replace(mytext, u"£", "&pound;")
	#mytext = string.replace(mytext, u"´", "&yen;")
	#mytext = string.replace(mytext, u"Û", "&8364;")
	#mytext = string.replace(mytext, u"Ñ", "&8212;")
	mytext = string.replace(mytext, u"Ò", "&8220;")
	mytext = string.replace(mytext, u"Ó", "&8221;")
	mytext = string.replace(mytext, u"\"", "&quot;")
	#mytext = string.replace(mytext, u"\'", "\\'")
	return mytext

def MakeFileName2(mytext):
	"""
	Function: validate.MakeFileName2(mydir, mytext)
	Last Updated: 10/21/02
	Description: Returns a filename valid on supported operating systems. Also checks for existing files and renames if necessary.
    Replacement for MakeFileName which oddly is designed only for .ecp files...
	"""

	mytext = utils.createSafeFilename(mytext)
	mytext = string.replace(mytext, " ", "_")
	return mytext