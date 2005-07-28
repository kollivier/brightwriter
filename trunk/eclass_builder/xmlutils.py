
def newXMLNode(doc, name, text="", attrs={}):
	node = doc.createElement(name)
	if not text == "":
		node.appendChild(doc.createTextNode(text))
	for attr in attrs.keys():
		if attrs[attr] != "":
			node.setAttribute(attr, attrs[attr])

	return node