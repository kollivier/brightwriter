escapeChars = [ ("&", "&amp;"), ("\"", "&quot;"), ("<", "&lt;"), (">", "&gt;") ] 

# Validation routines

def TextToXMLChar(mytext):
    """
    Function: TextToXMLChar(mytext)
    Description: Validates text and converts special characters to their XML character equivalents.
    """
    global escapeChars
    for char in escapeChars:
        mytext = mytext.replace(char[0], char[1])

    return mytext

def XMLCharToText(mytext):
    """
    Function: XMLCharToText(mytext)
    Description: Validates XML character text and converts XML special characters to their text equivalent.
    """
    global escapeChars
    for char in escapeChars:
        mytext = mytext.replace(char[1], char[0])

    return mytext

def XMLAttrToText(mytext):
    """
    Function: XMLAttrToText(mytext)
    Description: Validates XML attribute text and converts special characters to their text equivalents
    """
    
    return XMLCharToText(mytext)

def TextToXMLAttr(mytext):
    """
    Function: TextToXMLAttr(mytext)
    Description: Validates text and converts special characters to their XML attribute equivalents
    """

    return TextToXMLChar(mytext)


def newXMLNode(doc, name, text="", attrs={}):
	node = doc.createElement(name)
	if not text == "":
		node.appendChild(doc.createTextNode(text))
	for attr in attrs.keys():
		if attrs[attr] != "":
			node.setAttribute(attr, attrs[attr])

	return node