# conman.py - open source content management tool
# Designer: Kevin Ollivier
# Organization: Tulane University
# License: EClass.Builder Open Source License
import string
import os
import sys
#import HTMLPublish
import xml_settings
from validate import *
USE_MINIDOM=0
try:
	from xml.dom.ext.reader.Sax import FromXmlFile
except:
	USE_MINIDOM=1
#from xml import xpath
if USE_MINIDOM:
	from xml.dom import minidom

class ConMan:
	"""
	Class: conman.ConMan()
	Last updated: 9/24/02
	Description: The ConMan class defines a content manager for an IMS Compliant Content Package. More information on the IMS Content Packaging format can be found at: http://www.imsproject.org. Nodes are defined as a data structure containing both metadata on a content file and a definition of the content's structure in the package.

	Attributes: 
	- id: the UUID identifier for the content package, compliant with the IETF UUID specification.
	- pubid: EClass specific - this is an 8-character, Greenstone-compliant ID name specified by the user
	- content: a ContentList() object containing all the content nodes
	- namespace: The namespace for the package. IMS suggests using the "URN:IMS-PLIRID-V0:" namespace, which is used by default 
	- orgid: the UUID identifier for the Organization (table of contents)
	- nodes: a list of nodes in the package (NOTE: This list can also contain links to other packages)
	- language: Language of the package, by default English
	- filename: Complete path and filename for the "imsmanifest.xml" content package file
	- name: Name for this content package
	- description: Description of this content package
	- keywords: Keywords for this content package
	- directory: Complete path to the "imsmanifest.xml" content package file
	- CurrentNode: The currently selected node in the package

	Methods:
	- AddChild(id, contentid): Adds a new node as a child of self.CurrentNode. Sets self.CurrentNode to the newly created node
	- AddSibling(id, contentid): Adds a new node after self.CurrentNode. Sets self.CurrentNode to the newly created node
	- RemoveNode(id): Removes a node from the list, but does not remove the content it references (may be referenced by other nodes)
	- NewPub(name, language): Creates a new content package with specified name and language
	- PrintNodes(nodes, indent): Prints a textual representation of the nodes passed in, indenting the items by a number of spaces specified by indent.  	- LoadFromXML(filename): Loads an imsmanifest.xml content package
	- SaveAsXML(filename): Saves an imsmanifest.xml content package to disk, uses self.filename as filename if none specified
	- PublishAsHTML(parent, joustdir, gsdlcollection): Publishes content package to HTML. parent is the window to send status messages to, joustdir is the directory of the joust files, and gsdlcollection is the gsdl pub ID

	"""
	def __init__(self):
		#self.users = {} - for future use, multi-user system
		self.encoding = "ISO-8859-1"
		self.id = ""
		self.pubid = ""
		self.content = ContentList()
		self.namespace = "URN:IMS-PLIRID-V0:"
		self.orgid = ""
		self.nodes = []
		self.authors = []
		self.language = "English"
		self.filename = ""
		self.name = ""
		self.description = ""
		self.keywords = ""
		self.directory = ""
		self.CurrentNode = None  
		self.settings = xml_settings.XMLSettings()

	def __str__(self):
		mytext = self.PrintNodes(self.nodes, 0)
		#print mytext
		return mytext

	def __setattr__(self, name, value):
		if not name == "encoding" and isinstance(value, str) or isinstance(value, unicode):
			self.__dict__[name] = value.encode(self.encoding, 'replace')
		else:
			self.__dict__[name] = value

	def AddChild(self, id, contentid):
		#check to see if an item with this id exists, and if so, use it
		mycontent = self.content.GetItem(contentid, self.language)
		if mycontent == None:
			mycontent = self.content.AddItem(id, self.language)
		self.CurrentNode = self.CurrentNode.AddChild(id, mycontent, self.directory)
		return self.CurrentNode 

	def AddSibling(self, id, contentid):
		mycontent = self.content.GetItem(contentid, self.language)
		if mycontent == None:
			mycontent = self.content.AddItem(id, contentid, self.language)
		self.CurrentNode = self.CurrentNode.AddSibling(mycontent, self.directory)
		return self.CurrentNode 

	def RemoveNode(self, id):
		#leave content - it may be referenced by multiple nodes 
		self.CurrentNode.children.remove(id)

	def NewPub(self, name, lang, directory=''):
		self.directory = directory
		mycontent = self.content.AddItem(GetUUID(), self.language)
		mycontent.name = name
		mynode = ConNode(GetUUID(), mycontent, None)
		mynode.dir = directory
		self.CurrentNode = mynode
		self.name = name 
		self.nodes.append(mynode)
		return mynode

	def PrintNodes(self, nodes, indent):
		mystring = ""
		for node in nodes:
			for number in range(indent):
				mystring = mystring + " "
			myitem = node.content
			if myitem == None:
				pass
			mystring = mystring + node.id + " (resourceid:" + myitem.id + ") " + "\n"
			if len(node.children) > 0:
				mystring = mystring + self.PrintNodes(node.children, indent + 2)
		return mystring

	def LoadFromXML(self, filename):
		self.filename = filename
		self.directory = os.path.split(filename)[0]
		if os.path.exists(os.path.join(self.directory, "settings.xml")):
			self.settings.LoadFromXML(os.path.join(self.directory, "settings.xml"))
		self.content = ContentList()
		self.updatedids = {}
		self.nodes = []
		try: 
			if USE_MINIDOM:
				doc = minidom.parse(open(filename))
			else:
				doc = FromXmlFile(filename)
		except:
			return "The EClass project file cannot be loaded. The error message is: " + `sys.exc_value.args`

		manifest = doc.getElementsByTagName("manifest")[0]
		if manifest.attributes:
			for i in range(0, len(manifest.attributes)):
				attr = manifest.attributes.item(i)
				if attr.name == "identifier" and string.find(attr.value, self.namespace) != -1:
					self.id = string.replace(attr.value, self.namespace, "")
					self.id = string.replace(self.id, "-", "")

			if self.id == "":
				self.id = GetUUID()
					
		metadata = doc.getElementsByTagName("metadata")[0]
		if metadata.childNodes:
			if metadata.getElementsByTagName("PublicationID"):
				if metadata.getElementsByTagName("PublicationID")[0].childNodes:
					self.pubid = metadata.getElementsByTagName("PublicationID")[0].childNodes[0].nodeValue
					#print self.pubid
			else:
				self.pubid = ""
			imsmetadata = doc.getElementsByTagName("imsmd:General")
			self._GetMetadata(metadata)
		resources = doc.getElementsByTagName("resource")
		self._GetResources(resources)
		toc = doc.getElementsByTagName("tableofcontents")[0]
		if toc.attributes:
			for i in range(0, len(toc.attributes)):
				attr = toc.attributes.item(i)
				if attr.name == "identifier" and string.find(attr.value, self.namespace) != -1:
					self.orgid = string.replace(attr.value, self.namespace, "")
					self.orgid = string.replace(self.orgid, "-", "")

			if self.orgid == "":
				self.orgid = GetUUID()
		items = doc.getElementsByTagName("item")[0]
		self._GetNodes(items, None)
		self.CurrentNode = self.nodes[0]
		return ""
	
	def _GetResources(self, resources):
		for resource in resources:
			if resource.attributes:
				myid = ""
				myurl = ""
				for i in range(0, len(resource.attributes)):
					#print len(resource.attributes)
					attr = resource.attributes.item(i)
					if attr.name == "identifier":
						myid = string.replace(attr.value, self.namespace, "")
						myid = string.replace(myid, "-", "")
						if len(myid) < 32: #Created before IMS identifiers used
							self.updatedids[myid] = GetUUID()
							myid = self.updatedids[myid]
					elif attr.name == "href":
						myurl = XMLAttrToText(attr.value)

				myres = self.content.AddItem(myid, self.language)
				myres.filename = myurl
	
	def _GetNodes(self, root, parent):
		id = ""
		contentid = ""
		name = ""
		keywords = ""
		description = ""
		template = ""
		public = "false"
		mycontent = None
		if root.attributes:
			for i in range(0, len(root.attributes)):
				attr = root.attributes.item(i)
				if attr.name == "identifier":
					id = XMLAttrToText(attr.value)
					id = string.replace(id, self.namespace, "")
					id = string.replace(id, "-", "")
					if len(id) < 32: #Not a UUID, used previous ID system
						id = GetUUID()
				elif attr.name == "identifierref":
					contentid = XMLAttrToText(attr.value)
					contentid = string.replace(contentid, self.namespace, "")
					contentid = string.replace(contentid, "-", "")
				elif attr.name == "title":
					name = XMLAttrToText(attr.value)
				elif attr.name == "description":
					description = XMLAttrToText(attr.value)
				elif attr.name == "keywords":
					keywords = XMLAttrToText(attr.value)
				elif attr.name == "template":
					template = XMLAttrToText(attr.value)
				elif attr.name == "public":
					public = XMLAttrToText(attr.value) 

			#Content should already be loaded, so try to get the item first      		
			if self.updatedids.has_key(contentid):
				mycontent = self.content.GetItem(self.updatedids[contentid], self.language)
				#mycontent.id = self.updatedids[contentid]
			else:
				mycontent = self.content.GetItem(contentid, self.language) 

			if mycontent == None:
				mycontent = self.content.AddItem(contentid, self.language)

			mycontent.name = name
			mycontent.keywords = keywords
			mycontent.description = description
			mycontent.template = template
			mycontent.public = public
			
			#Test to make sure the first element isn't added as a child
			if parent:
				mynode = parent.AddChild(id, mycontent, self.directory)
				if not string.find(mycontent.filename, "imsmanifest.xml") == -1:
					mypub = ConMan()
					mypub.LoadFromXML(mycontent.filename)
					mynode.pub = mypub
				self.CurrentNode = mynode 
			else:        				
				mynode = ConNode(id, mycontent, None)
				mynode.dir = self.directory
				#print "My node id = " + mynode.id
				self.nodes = []
				self.nodes.append(mynode)
				self.CurrentNode = mynode

			for node in root.childNodes:
				self._GetNodes(node, mynode)

	def _GetMetadata(self, root):
		if root.childNodes:
			if root.getElementsByTagName("imsmd:Title")[0].childNodes:
				self.name = XMLCharToText(root.getElementsByTagName("imsmd:Title")[0].childNodes[0].nodeValue)
			else:
				self.name = ""

			if root.getElementsByTagName("imsmd:Description")[0].childNodes:
				self.description = XMLCharToText(root.getElementsByTagName("imsmd:Description")[0].childNodes[0].nodeValue)
			else:
				self.description = ""

			if root.getElementsByTagName("imsmd:Keywords")[0].childNodes:
				self.keywords = XMLCharToText(root.getElementsByTagName("imsmd:Keywords")[0].childNodes[0].nodeValue)
			else:
				self.keywords = ""
		
			#if root.getElementsByTagName("contribute"):
			#	print "We have contribute elements..."
			#	for contrib in root.getElementsByTagName("contribute"):
			#		ctx = xpath.Context.Context(contrib, 1, 1)
			#		isAuthor = xpath.Evaluate("/contribute/role/value/langstring/text()", context=ctx)
			#		print "Result is " + `isAuthor`
			#		if isAuthor:
			#			vcard = xpath.Evaluate("centity/vcard/text()", contrib)
			#			print vcard.nodeValue

	def SaveAsXML(self, filename, encoding="ISO-8859-1"):
		if filename == "":
			filename = self.filename
		else:
			self.filename = filename
			self.directory = os.path.split(filename)[0]
		
		myxml = """<?xml version="1.0" encoding="%s"?>
<manifest identifier="%s" xmlns:imsmd="http://www.imsproject.org">
	<metadata>%s</metadata>
	<organizations default="%s">
		<tableofcontents identifier="%s" title="%s">
		%s
		</tableofcontents>
	</organizations>
	<resources>%s
	</resources>
</manifest>
""" % (encoding, self.namespace + self.id, self._MetadataAsXML(), self.namespace + self.orgid, self.namespace + self.orgid, TextToXMLAttr(self.name), self._TOCAsXML(self.nodes[0]), self._ResourcesAsXML())		
		try:	
			self.settings.SaveAsXML(os.path.join(self.directory, "settings.xml"))
		except:
			message = "There was an error saving the file " + os.path.join(self.directory, "settings.xml") + ". Please check to make sure you have write access to this file and try saving again."
			print message
			raise IOError, message

		try:
			myfile = open(filename, "w")
			myfile.write(myxml)
			myfile.close()
		except:
			message = "There was an error saving the file" + filename + ". Please check to make sure you have write access to this file and try saving again."
			print message
			raise IOError, message

	def _MetadataAsXML(self):
		mymetadata = """
		<PublicationID>%s</PublicationID>
		<imsmd:General>
			<imsmd:Title>%s</imsmd:Title>
			<imsmd:Description>%s</imsmd:Description>
			<imsmd:Keywords>%s</imsmd:Keywords>
		</imsmd:General>		
		""" % (self.pubid, TextToXMLChar(self.name), TextToXMLChar(self.description), TextToXMLChar(self.keywords))
		return mymetadata

	def _TOCAsXML(self, root):
		mytoc = """<item identifier="%s" identifierref="%s" title="%s" description="%s" keywords="%s" template="%s" public="%s" """ % (TextToXMLAttr(self.namespace + root.id), TextToXMLAttr(self.namespace + root.content.id), TextToXMLAttr(root.content.name), TextToXMLAttr(root.content.description), TextToXMLAttr(root.content.keywords), TextToXMLAttr(root.content.template), TextToXMLAttr(root.content.public))
		if len(root.children) > 0:
			mytoc = mytoc + ">"
			for child in root.children:
				if child.pub:
					child.pub.SaveAsXML(child.content.filename)
				mytoc = mytoc +	self._TOCAsXML(child)
			mytoc = mytoc + "</item>"
		else:
			mytoc = mytoc + "/>"
		return mytoc

	def _ResourcesAsXML(self):
		myres = ""
		for item in self.content:				
			myres = myres + """<resource identifier="%s" href="%s"/>\n""" % (self.namespace + item.id, TextToXMLAttr(item.filename))
		return myres

	def PublishAsHTML(self, parent, joustdir, gsdlcollection='', useswishe=0):
		htmlpub	= HTMLPublish.conmanHTMLPublisher()
		return htmlpub.Publish(parent, joustdir, gsdlcollection, useswishe)

class ConNode:
	"""
	Class: conman.ConNode()
	Last Updated: 9/24/02
	Description: This class manages the structure/hierarchy/organizations for a node in the system
	
	Attributes:
	- id: unique id identifying the item
	- content: A link to the actual content for the current node
	- parent: a reference to the ConNode which has this node listed as a childnode
	- children: a reference to the childnodes of the current node
	- pub: a reference to the content package of another learning module, used for "linking in" other content packages

	Methods:
	- AddChild(id): adds a child node of the current node, and returns the new node
	- back: returns the previous node in the hierarchy
	- next: returns the next node in the hierarchy
	- AddSibling(id): adds a node after the current node, and returns the new node
	"""

	def __init__(self, id, content, parent):
		self.id = id
		#contentid variable makes it possible to have several nodes pointing to the same resource - NYI
		self.content = content
		self.parent = parent
		self.pub = None
		self.children = []
		self.dir = ""

	def back(self):
		back = None
		if self.parent and self in self.parent.children:
			myindex = self.parent.children.index(self)
			if myindex != 0:
				children = self.parent.children
				if len(children[myindex-1].children) == 0:
					back = self.parent.children[myindex - 1]
				else:
					child = children[myindex-1]
					while not len(child.children) == 0: 
						#if there are child trees, you want the very last child node
						child = child.children[len(child.children)-1]
					back = child
			else:
				back = self.parent

		return back
		
	def next(self):		
		next = None
		if self.children:
			next = self.children[0]				
		elif self.parent and self in self.parent.children:
			myindex = self.parent.children.index(self)
			if not (myindex + 1) >= len(self.parent.children): #get next child
				next = self.parent.children[myindex + 1]
			elif self.parent.parent:
				parent = self.parent.parent
				child = self.parent
				#look for the first parent who has children after this node's parents, if any
				while (len(parent.children) - 1) <= parent.children.index(child):
					#no nodes after the parent, move up another level
					if parent.parent:
						child = parent
						parent = parent.parent
					else:
						return None #this is very last child

				#finally found a parent with children after the parent node
				myindex = parent.children.index(child)
				#print "myindex = ", myindex
				next = parent.children[myindex + 1]
				#return self.parent.next()		
	
		return next
	
	def AddSibling(self, id, contentid, dir):
		if self.parent:
			return self.parent.AddChild(id, contentid, dir)

	def AddChild(self, id, content, dir):
		if id == "":
			id = GetUUID()
		mynode = ConNode(id, content, self)
		mynode.dir = dir
		self.children.append(mynode)
		return mynode

class Content:
	"""
	Class: conman.Content()
	Last Updated: 9/24/02
	Description: This class contains information about a specific content resource in the content package, including its metadata, access permissions, and content (in the form of an external file, represented by filename)

	Attributes:
	- id: a unique UUID string identifying the content
	- name: title for the content
	- keywords: simple, comma separated text list of words and phrases which identify the content
	- description: simple text content summarizing the content of filename
	- permissions: a dictionary specifying each user, and their access priviledges
	  i.e. {'Bob': 'author', 'Jane': 'manager'} FOR FUTURE USE - NOT YET IMPLEMENTED
	- public: a text string indicating whether or not the material is approved for public viewing
	- filename: name of file (path is determined by content type)
	- language: text representing the language of the content, i.e. "English"
	- template: name of the template to apply to content when converting to HTML

	Methods:
	NONE
	"""
	def __init__(self, id, lang):
		self.encoding = "ISO-8859-1"
		#print self.encoding
		self.id = id
		self.language = lang
		self.name = ""
		self.keywords = ""
		self.description = ""
		self.permissions = ""
		self.template = ""
		self.public = "true"
		self.filename = ""

	def __setattr__(self, name, value):
		if not name == "encoding" and isinstance(value, str) or isinstance(value, unicode):
			self.__dict__[name] = value.encode(self.encoding, 'replace')
		else:
			self.__dict__[name] = value
		
		
class ContentList:
	"""
	Class: conman.ContentList()
	Last Updated: 9/24/02
	Description: A collection class for storing all the content items and enabling searches, etc. This class behaves as a standard Python 'list' type.

	Attributes: 
	- content: list of conman.Content() resources

	Methods:
	- GetItem(id, lang): Returns an item given with the proper id and language, or None if failed
	- AddItem(id, lang): Returns a new item with the given id and language, or None if failed
	- RemoveItem(id, lang) Removes an item with the given id and language, returns true if successful, false if failed 
	"""

	def __init__(self):
		self.content = []

	def __getitem__(self, key):
		return self.content[key]

	def __len__(self):
		return len(self.content)
		
	def GetItem(self, id, lang="English"):
		myitem = None
		for item in self.content:
			if item.id == id and item.language == lang:
				myitem = item		
		return myitem

	def AddItem(self, id, lang):
		myitem = None
		if id == "":
			id = GetUUID()
		myitem = Content(id, lang)
		self.content.append(myitem)
		return myitem
		
	def RemoveItem(self, id, lang):
		item = GetItem(id, lang)
		try:
			self.content.remove(item)
			return true
		except:
			return false

def GetUUID():
	"""
	Function: conman.GetUUID()
	Last Updated: 9/24/02
	Description: Generates a UUID using platform specific tools (the built-in GUID generation tools on Windows, and the uuidgen command line utility on Linux/Mac OS X.
	"""
	id = ""
	if sys.platform == "win32" or sys.platform == "nt":
		import pythoncom
		id = pythoncom.CreateGuid()
		id = str(id)
		id = string.replace(id, "'", "")
		id = string.replace(id, "{", "")
		id = string.replace(id, "}", "")
		id = string.replace(id, "-", "")
	else:
		result = os.popen("uuidgen", "r")
		id = result.read()
		id = string.replace(id, "-", "")
		result.close()
	return id

if __name__ == "__main__":
	mypub = ConMan()
	mypub.LoadFromXML("C:\\My Documents\\conman\\test.xml")
	print str(mypub)
	#mypub = ConMan()
	#mypub.NewPub("myhome", "English")
	#mypub.AddChild("Node1", "content1")
	#mypub.AddSibling("MyNewNode", "content2")
	#mypub.AddSibling("myOtherNode", "content3")
	#mypub.AddChild("OtherNodeChild", "content4")
	#str(mypub)
