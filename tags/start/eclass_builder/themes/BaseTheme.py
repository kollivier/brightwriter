#HTMLPublish.py - HTML Publishing utility
import sys
import os
import re
import StringIO
#import pre as re
import string
from wxPython.wx import *
import conman.file_functions as files
from conman.HTMLFunctions import *

myDictionary={}
#import plugins.eclass as eclass
myplugins = []
rootdir = os.path.join(os.path.abspath(sys.path[0]))
sys.path.append(rootdir)
for item in os.listdir(os.path.join(rootdir, "plugins")):
	if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
		plugin = string.replace(item, ".py", "")
		exec("import plugins." + plugin)
		exec("myplugins.append(plugins." + plugin + ".plugin_info)") 
from StringIO import StringIO

def initial(the_dictionary):
	global myDictionary
	myDictionary=the_dictionary

themename = "Default (frames)"

class BaseHTMLPublisher:
	"""
	Class: HTMLPublish.HTMLPublisher
	Last Updated: 9/24/02  
	Description: This class creates an HTML version of the IMS Content Package viewable in all Javascript-enabled browsers.

	Attributes:
	- pub: the currently open ConMan project
	- parent: the window which initiated this class
	- dir: the root directory of the currently open ConMan project
	- templates: a dictionary of templates used when publishing HTML pages
	- appdir: Path to the EClass.Builder application
	- joustdir: Path to the Joust files directory

	Methods:
	- Publish: Creates the table of contents and publishes each page in the collection to HTML
	- CopyJoust: Copies the Joust navigation files to the published EClass
	- CreateTOCPage: Creates the table of contents for Joust
	- PublishPages: Publishes each node in the ConMan project to HTML 
	"""

	def __init__(self, parent=None):
		self.parent = parent
		self.pub = parent.pub
		self.dir = parent.CurrentDir
		self.counter = 1
		self.appdir = parent.AppDir
		self.themedir = os.path.join(self.appdir, "themes", themename)
		self.cancelled = false

	def Publish(self):
		self.progress = None
		try:
			if isinstance(self.parent, wxFrame):
				self.progress = wxProgressDialog(_("Updating EClass"), _("Preparing to update EClass..."), self.parent.wxTree.GetCount() + 1, None, wxPD_APP_MODAL | wxPD_AUTO_HIDE | wxPD_CAN_ABORT)
			self.CopySupportFiles()
			self.CreateTOC()
			self.counter = 1
			self.PublishPages(self.pub.nodes[0])
		except:
			if self.progress:
				self.progress.Destroy()
			raise
			
		if self.progress:
			self.progress.Destroy()

		return not self.cancelled
	
	def CopySupportFiles(self):
		files.CopyFiles(os.path.join(self.themedir, "Files"), self.dir, 1)

	def CreateTOC(self):
		filename = "../pub/" + self._GetFilename(self.pub.nodes[0].content.filename)
        
		text = """foldersTree = gFld("%s", "%s")\n""" % (string.replace(self.pub.nodes[0].content.name, "\"", "\\\""), filename)
		text = text + self.AddTOCItems(self.pub.nodes[0], 1)
		searchenabled = False
		if self.pub.settings["SearchEnabled"] != "":
			searchenabled = int(self.pub.settings["SearchEnabled"])

		if searchenabled:
			if self.pub.settings["SearchProgram"] == "Swish-e":
				searchscript = "../cgi-bin/search.py"
				text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", searchscript)
			elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
				text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", "../gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0")
		file = open(os.path.join(self.themedir,"eclassNodes.js"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "eclassNodes.js"), "w")
		data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
		file.write(data)
		file.close()

		file = open(os.path.join(self.themedir,"index.tpl"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "index.htm"),"w")
		data = string.replace(data, "<!-- INSERT FIRST PAGE HERE -->", "pub/" + self._GetFilename(self.pub.nodes[0].content.filename))
		file.write(data)
		file.close()

	def AddTOCItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = "../pub/" + self._GetFilename(root.content.filename) 

			if not root.content.public == "false":
				nodeName = "foldersTree"
				if (level > 1):
					nodeName = "level" + `level` + "Node"
				if len(root.children) > 0:
					nodeType = "../Graphics/menu/win/chapter.gif"
				else:
					nodeType = "../Graphics/menu/win/page.gif"
				self.counter = self.counter + 1                            
			
				if len(root.children) > 0:
					text = text + """level%sNode = insFld(%s, gFld("%s", "%s"))\n""" % (level + 1, nodeName, string.replace(root.content.name, "\"", "\\\""), filename)
					text = text + self.AddTOCItems(root, level + 1)
				else:
					text = text + """insDoc(%s, gLnk('S', "%s", "%s"))\n""" % (nodeName, string.replace(root.content.name, "\"", "\\\""), filename)
			else:
				print "Item " + root.content.name + " is marked private and was not published."
        	return text					

	def _GetFilename(self, filename):
		extension = string.split(filename, ".")[-1]
		publisher = None
		for plugin in myplugins:
			if extension in plugin["Extension"]:
				publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
		if publisher: 
			try:
				filename = publisher.GetFilename(filename)
			except: 
				pass
		else:
			filename = "../File/" + filename
		return filename

	def GetContentsPage(self):
		if os.path.exists(os.path.join(self.themedir,"eclassNodes.js")):
			return "eclassNodes.js"

	def PublishPages(self, node):
		page = ""
		if self.cancelled:
			return
		keepgoing = True #assuming no dialog to cancel, this must always be the case
		if self.progress:
			keepgoing = self.progress.Update(self.counter, _("Updating page %(page)s") % {"page":node.content.name})
		if not keepgoing:
			result = wxMessageDialog(self.parent, "Are you sure you want to cancel publishing this EClass?", "Cancel Publishing?", wxYES_NO).ShowModal()
			if result == wxID_NO:
				self.cancelled = false
				self.progress.Resume()
			else:
				self.cancelled = true
				return
		self.counter = self.counter + 1
		if string.find(node.content.filename, "imsmanifest.xml") != -1:
			node = node.pub.nodes[0]

		if 1:
			extension = string.split(node.content.filename, ".")[-1]
			publisher = None
			for plugin in myplugins:
				if extension in plugin["Extension"]:
					publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
			if publisher: 
				try:
					filename = publisher.GetFilename(node.content.filename)
					publisher.Publish(self.parent, node, self.dir)
				except:
					print "Could not publish page " + os.path.join(self.dir, "pub", node.content.filename)
					import traceback
					print "Traceback is:\n" 
					traceback.print_exc()
        	
		if len(node.children) > 0:
        		for child in node.children:
        			self.PublishPages(child)