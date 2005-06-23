import string, os

def TextToXMLChar(mytext):
	"""
	Function: validate.TextToXMLChar(mytext)
	Last Updated: 9/24/02
	Description: Validates text and converts special characters to their XML character equivalents.
	"""
	mytext = string.replace(mytext, "&", "&amp;")
	#mytext = string.replace(mytext, "\"", "&quot;")
	mytext = string.replace(mytext, "<", "&lt;")
	mytext = string.replace(mytext, ">", "&gt;")
	return mytext

def XMLCharToText(mytext):
	"""
	Function: validate.XMLCharToText(mytext)
	Last Updated: 9/24/02
	Description: Validates XML character text and converts XML special characters to their text equivalent.
	"""
	mytext = string.replace(mytext, "&amp;", "&")
	mytext = string.replace(mytext, "&quot;", "\"")
	mytext = string.replace(mytext, "&lt;", "<")
	mytext = string.replace(mytext, "&gt;", ">")
	return mytext

def XMLAttrToText(mytext):
	"""
	Function: validate.XMLAttrToText(mytext)
	Last Updated: 9/24/02
	Description: Validates XML attribute text and converts special characters to their text equivalents
	"""
	mytext = string.replace(mytext, "&amp;", "&")
	mytext = string.replace(mytext, "&quot;", '"')
	mytext = string.replace(mytext, "&lt;", "<")
	mytext = string.replace(mytext, "&gt;", ">")
	return mytext

def TextToXMLAttr(mytext):
	"""
	Function: validate.TextToXMLAttr(mytext)
	Last Updated: 9/24/02
	Description: Validates text and converts special characters to their XML attribute equivalents
	"""
	mytext = string.replace(mytext, "&", "&amp;")
	mytext = string.replace(mytext, '"', "&quot;")
	mytext = string.replace(mytext, "<", "&lt;")
	mytext = string.replace(mytext, ">", "&gt;")
	return mytext

def TextToHTMLChar(mytext):
	mytext = TextToXMLChar(mytext)
	mytext = string.replace(mytext, "©", "&copy;")
	#mytext = string.replace(mytext, "¨", "&reg;")
	#mytext = string.replace(mytext, "ª", "&8482;")
	mytext = string.replace(mytext, "£", "&pound;")
	#mytext = string.replace(mytext, "´", "&yen;")
	#mytext = string.replace(mytext, "Û", "&8364;")
	#mytext = string.replace(mytext, "Ñ", "&8212;")
	mytext = string.replace(mytext, "Ò", "&8220;")
	mytext = string.replace(mytext, "Ó", "&8221;")
	mytext = string.replace(mytext, "\"", "&quot;")
	#mytext = string.replace(mytext, "\'", "\\'")
	return mytext

def MakeFileName(mydir, mytext):
	"""
	Function: validate.MakeFileName(mydir, mytext)
	Last Updated: 9/24/02
	Description: Returns a filename valid on supported operating systems. Also checks for existing files and renames if necessary.
	"""

	mytext = string.replace(mytext, "\\", "")
	mytext = string.replace(mytext, "/", "")
	mytext = string.replace(mytext, ":", "")
	mytext = string.replace(mytext, "*", "")
	mytext = string.replace(mytext, "?", "")
	mytext = string.replace(mytext, "\"", "")
	mytext = string.replace(mytext, "<", "")
	mytext = string.replace(mytext, ">", "")
	mytext = string.replace(mytext, "|", "")
	myfilename = mytext + ".ecp"
	counter = 2			
	while os.path.exists(os.path.join(mydir, myfilename)):
		#newnode.content.metadata.name = "New Page " + `counter`
		myfilename = mytext + " " + `counter` + ".ecp"
		counter = counter + 1
	return myfilename

def MakeFileName2(mytext):
	"""
	Function: validate.MakeFileName2(mydir, mytext)
	Last Updated: 10/21/02
	Description: Returns a filename valid on supported operating systems. Also checks for existing files and renames if necessary.
    Replacement for MakeFileName which oddly is designed only for .ecp files...
	"""

	mytext = string.replace(mytext, "\\", "")
	mytext = string.replace(mytext, "/", "")
	mytext = string.replace(mytext, ":", "")
	mytext = string.replace(mytext, "*", "")
	mytext = string.replace(mytext, "?", "")
	mytext = string.replace(mytext, "\"", "")
	mytext = string.replace(mytext, "<", "")
	mytext = string.replace(mytext, ">", "")
	mytext = string.replace(mytext, "|", "")
	mytext = string.replace(mytext, " ", "_")
	return mytext