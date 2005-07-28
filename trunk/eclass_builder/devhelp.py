import string, sys, os
import settings
import xml.dom.minidom
from xmlutils import *
import plugins

class DevHelpPage:
	def __init__(self, title="", link=""):
		self.title = title
		self.link = link
		self.children = []

	def asXML(self, doc):
		newNode = newXMLNode(doc, "sub", attrs={"name":self.title, "link":self.link})
		for child in self.children:
			newNode.appendChild(child.asXML(doc))
		return newNode

class DevHelpFile:
	def __init__(self):
		self.title = ""
		self.link = ""
		self.functions = []
		self.pages = []
		
	def SaveAsXML(self, filename):
		doc = xml.dom.minidom.Document()
		print "Title = " + self.title + ", Link = " + self.link
		rootNode = newXMLNode(doc, "book", attrs={"title": self.title, "link":self.link})
		chaptersNode = newXMLNode(doc, "chapters")
		for page in self.pages:
			chaptersNode.appendChild(page.asXML(doc))
		rootNode.appendChild(chaptersNode)
		doc.appendChild(rootNode)
		data = doc.toprettyxml("\t")
		myfile = open(filename, "w")
		myfile.write(data)
		myfile.close()

class DevHelpConverter:
	def __init__(self, pub):
		self.pub = pub
		self.devHelpFile = DevHelpFile()
		self.devHelpFile.title = self.pub.name
		self.devHelpFile.link = "index.htm"

	def ExportDevHelpFile(self, filename):
		#create a DevHelp file for the EClass...
		self._ExportPages(self.pub.nodes[0].children)
		self.devHelpFile.SaveAsXML(filename)

	def _ExportPages(self, root, dhParent=None):
		for nodes in root:
			filename = nodes.content.filename

			plugin = plugins.GetPluginForExtension(os.path.splitext(filename)[1][1:])
			if plugin:
				pub = plugin.HTMLPublisher()
				filename = "pub/" + pub.GetFilename(filename)
			
			newSub = DevHelpPage(nodes.content.metadata.name, filename)
			
			if len(nodes.children) > 0:
				self._ExportPages(nodes.children, newSub)

			if dhParent != None:
				dhParent.children.append(newSub)
			else:
				self.devHelpFile.pages.append(newSub)	
	