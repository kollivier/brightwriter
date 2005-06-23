#HTMLPublish.py - HTML Publishing utility
import sys
import os
import pre as re
import string
from wxPython.wx import *
import file_functions as files

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

class conmanHTMLPublisher:
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

	def __init__(self):
		self.pub = None
		self.parent = None
		self.progress = None
		self.counter = 1
		self.cancelled = false
		self.dir = ""
		self.templates = {}
		self.appdir = ""
		self.joustdir = ""

	def Publish(self, parent, joustdir, gsdlcollection='', useswishe=false):
		self.parent = parent
		if isinstance(parent, wxFrame):
			self.progress = wxProgressDialog(myDictionary["110"], myDictionary["111"], parent.wxTree.GetCount() + 1, None, wxPD_APP_MODAL | wxPD_AUTO_HIDE | wxPD_CAN_ABORT)
		#print parent.wxTree.GetCount()

		self.pub = parent.pub
		self.dir = parent.CurrentDir
		self.counter = 1
		self.appdir = parent.AppDir
		self.useswishe= useswishe
		self.joustdir = joustdir
		#print pub + " dir = ," + dir
		self.templates = parent.templates

		#self.CreateJoustTOC()
		try:
			self.CopyJoust(gsdlcollection)
			self.CreateTOCPage()
			self.PublishPages(self.pub.nodes[0])
		except:
			self.progress.Destroy()
			raise
			
		if self.progress:
			self.progress.Destroy()

		return not self.cancelled
	
	def CopyJoust(self, gsdlcollection):
		files.CopyFiles(os.path.join(self.appdir, "Joust"), self.dir, 1)
		self.CreateJoustTOC(gsdlcollection)

	def CreateJoustTOC(self, gsdlcollection):
		filename = self._GetFilename(self.pub.nodes[0].content.filename)

		text = """level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename, string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""))
		text = text + self.AddJoustItems(self.pub.nodes[0], 1)
		if self.useswishe:
			searchscript = "../cgi-bin/search"
			if wxPlatform == '__WXMSW__':
				searchscript = searchscript + ".exe"
			text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", searchscript, "Search")
		elif gsdlcollection != "":
			text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", "../gsdl?site=127.0.0.1&a=p&p=about&c=" + gsdlcollection + "&ct=0", "Search")
		file = open(os.path.join(self.joustdir,"index.htm"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "index.htm"), "w")
		data = string.replace(data, "<!-- INSERT INDEX PAGE HERE -->", filename)
		data = string.replace(data, "<!-- INSERT CLASS TITLE HERE -->", self.pub.nodes[0].content.metadata.name)
		data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
		file.write(data)
		file.close()

	def AddJoustItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = self._GetFilename(root.content.filename) 

			if not root.content.public == "false":
				if len(root.children) > 0:
					nodeType = "Book"
				else:
					nodeType = "Document"
				text = text + """level%sID = theMenu.addChild(level%sID,"%s", "%s", "%s", "%s");\n""" % (level + 1, level, nodeType, string.replace(root.content.metadata.name, "\"", "\\\""), filename, string.replace(root.content.metadata.name, "\"", "\\\""))

				if len(root.children) > 0:
					text = text + self.AddJoustItems(root, level + 1)
			else:
				print "Item " + root.content.metadata.name + " is marked private and was not published."
		return text

	def CreateTOCPage(self):
		file = open(os.path.join(self.dir, "pub", "toc.htm"), "w")
		file.write("<HTML><HEAD><TITLE>Table of Contents</TITLE></HEAD><BODY>" + self._TOCAsHTML(self.pub.nodes[0], 0) + "</BODY></HTML>")
		file.close()

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
		return filename


	def _TOCAsHTML(self, root, indent):
		toc = ""
		if string.find(root.content.filename, "imsmanifest.xml") != -1:
			root = root.pub.nodes[0]
		for x in range(0, indent):
			toc = toc + "&nbsp;"
		if len(root.children) > 0:
			toc = toc + """<img src="../Graphics/menu/win/chapter.gif">"""
		else:
			toc = toc + """<img src="../Graphics/menu/win/page.gif">"""
		filename = self._GetFilename(root.content.filename)

		toc = toc + """<FONT face="Arial" size="2"><A href="%s"> %s</A></FONT><BR>""" %(filename, root.content.metadata.name)
		if len(root.children) > 0:
			for child in root.children:
				toc = toc + self._TOCAsHTML(child, indent + 4)
		return toc

	def PublishPages(self, node):
		page = ""
		if self.cancelled:
			return
		keepgoing = self.progress.Update(self.counter, myDictionary["112"] + node.content.metadata.name)
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

		#print "Node filename = ", node.content.filename
		#print "String find = ", `string.find(node.content.filename, ".htm")`
		if node.content.public == "true" and string.find(node.content.filename, ".htm") != -1:
			#print "publishing page..."
			try:
				myhtml = open(os.path.join(self.dir, "Text", node.content.filename), "r")
				page = myhtml.read()
				myhtml.close()
			except IOError:
				print "Could not open file " + os.path.join(self.dir, "Text", node.content.filename)

			if node.content.template != "None":
				try:
					text = self._GetBody(StringIO(page))
					page = self._CreateHTMLShell(node.content.metadata.name, node.content.description, node.content.keywords, node.content.filename, text, self.templates.get(node.content.template))
					file = open(os.path.join(self.dir, "pub", node.content.filename), "w")
					file.write(page)
					file.close()
				except: 
					print "Could not save file ", os.path.join(self.dir, "pub", node.content.filename)

		else: 
			extension = string.split(node.content.filename, ".")[-1]
			publisher = None
			for plugin in myplugins:
				if extension in plugin["Extension"]:
					publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
			if publisher: 
				try:
					filename = publisher.Publish(self.parent, node, self.dir)
				except:
					print "Could not publish page " + os.path.join(self.dir, "pub", node.content.filename)
					import traceback
					print "Traceback is:\n" 
					traceback.print_exc()

		if len(node.children) > 0:
			for child in node.children:
				self.PublishPages(child)

	def _GetBody(self, myhtml):
		inbody = 0
		inscript = 0
		bodystart = 0
		bodyend = 0
		text = ""
		uppercase = 1
		html = myhtml.readline()
		while not html == "":
			bodystart = string.find(html, "<BODY")
			if bodystart == -1:
				uppercase = 0
				bodystart = string.find(html, "<body")
			if not bodystart == -1:
				bodystart = string.find(html, ">", bodystart)        		

			if not string.find(html, "<SCRIPT") == -1 or not string.find(html, "<script") == -1:
				inscript = 1
				inbody = 0
				bodystart = -1

			if not string.find(html, "</SCRIPT>") == -1 or not string.find(html, "</script>") == -1:
				inscript = 0

			if (not bodystart == -1 or inbody) and inscript == 0:
        			inbody = 1
				if uppercase == 1:
					bodyend = string.find(html, "</BODY>")

				elif uppercase == 0:
					bodyend = string.find(html, "</body>")

				if not bodystart == -1 and not bodyend == -1:
					text = text + html[bodystart+1:bodyend-1]
					bodystart = -1
					bodyend = -1
					inbody = 0
				elif not bodyend == -1:
					inbody = 0
					text = text + html[0:bodyend-1] 
					bodyend = -1
				elif not bodystart == -1:
					text = text + html[bodystart+1:-1] 
					bodystart = -1
				elif inbody == 1:
					text = text + html 
			html = myhtml.readline()
		return text

	def _CreateHTMLShell(self, name, description, keywords, filename, content, template):
		if template == "" or template == None:
			template = "default.tpl"

		print template

		temp = open(os.path.join(self.parent.AppDir, "templates", template), "r")
		html = temp.read()
		temp.close()
		html = string.replace(html, "--[name]--", name)
		html = string.replace(html, "--[description]--", description)
		html = string.replace(html, "--[keywords]--", keywords)
		html = string.replace(html, "--[URL]--", filename)
		html = string.replace(html, "--[content]--", content)
		html = string.replace(html, "--[credit]--", "")
		return html

	def _CreateHTMLFrame(self, title, startpage):
		html = """<HTML>
<HEAD>
<TITLE>%s</TITLE>
<frameset cols="260,*">
<frame name="contents" target="main" src="toc.htm">
<frame name="main" src="%s">
<noframes>
<BODY>
Your browser does not support frames. Please click <a href="%s">here</a> to start the course.
</BODY>
</noframes>
</HTML>
""" % (title, startpage, startpage)
		try:	
			file = open(os.path.join(self.dir, "frame.htm"), "w")  
			file.write(html)
			file.close()
		except:
			print "Could not create the HTML frame", os.path.join(self.dir, "frame.htm")