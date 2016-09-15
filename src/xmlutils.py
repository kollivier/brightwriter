import uuid
import sys
import base64 

escapeChars = [ ("&", "&amp;"), ("\"", "&quot;"), ("<", "&lt;"), (">", "&gt;") ] 

# taken from http://www.snee.com/bobdc.blog/2006/12/generating-a-single-globally-u.html
def createXMLUUID():
    b64uid = '00000000'    
    # Keep generating until we have one that starts with a letter. 
    while (b64uid[0:1] < 'A') or \
            (b64uid[0:1] > 'z') or \
            ((b64uid[0:1] > 'Z') and (b64uid[0:1] < 'a')):
        uid = uuid.uuid4()
        b64uid = base64.b64encode(uid.bytes,'-_')
    
    return b64uid[0:22] # lose the "==" that finishes a base64 value

# Validation routines
def TextToXMLChar(mytext):
    """
    Function: TextToXMLChar(mytext)
    Description: Validates text and converts special characters to their XML character equivalents.
    """
    
    if not mytext:
        return ""
        
    global escapeChars
    for char in escapeChars:
        mytext = mytext.replace(char[0], char[1])

    return mytext

def XMLCharToText(mytext):
    """
    Function: XMLCharToText(mytext)
    Description: Validates XML character text and converts XML special characters to their text equivalent.
    """

    if not mytext:
        return ""

    global escapeChars
    for char in escapeChars:
        mytext = mytext.replace(char[1], char[0])

    return mytext

def XMLAttrToText(mytext):
    """
    Function: XMLAttrToText(mytext)
    Description: Validates XML attribute text and converts special characters to their text equivalents
    """
    if not mytext:
        return ""

    return XMLCharToText(mytext)

def TextToXMLAttr(mytext):
    """
    Function: TextToXMLAttr(mytext)
    Description: Validates text and converts special characters to their XML attribute equivalents
    """
    if not mytext:
        return ""

    return TextToXMLChar(mytext)


def newXMLNode(doc, name, text="", attrs={}):
	node = doc.createElement(name)
	if not text == "":
		node.appendChild(doc.createTextNode(text))
	for attr in attrs.keys():
		if attrs[attr] != "":
			node.setAttribute(attr, attrs[attr])

	return node
