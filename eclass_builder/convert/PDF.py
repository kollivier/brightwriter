import sys, copy
import os
import re
import StringIO
#import pre as re
import string
import types
from wxPython.wx import *
import conman.file_functions as files
from conman.HTMLFunctions import *
from conman.validate import *
import settings
import tempfile
import shutil
import utils

myDictionary={}
#import plugins.eclass as eclass
myplugins = []
rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
	rootdir = os.path.dirname(rootdir)
sys.path.append(rootdir)
for item in os.listdir(os.path.join(rootdir, "plugins")):
	if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
		plugin = string.replace(item, ".py", "")
		exec("import plugins." + plugin)
		exec("myplugins.append(plugins." + plugin + ".plugin_info)") 
from StringIO import StringIO

themename = "PDF"
Elements = []
myDictionary = {}

def initial(the_dictionary):
	myDictionary=the_dictionary

class PDFPublisher:
	"""
	Class: BaseTheme.BasePDFPublisher
	Last Updated: 9/24/02  
	Description: This class creates an PDF version of the IMS Content Package viewable in all Javascript-enabled browsers.

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
		self.dir = settings.CurrentDir
		#if sys.platform != "win32":
		#	self.dir = string.replace(self.dir, " ", "\\ ")
		Title = self.pub.nodes[0].content.metadata.name
		self.counter = 1
		self.appdir = parent.AppDir
		self.ThirdPartyDir = parent.ThirdPartyDir
		self.themedir = os.path.join(self.appdir, "themes", themename)
		#self.templates = parent.templates
		self.cancelled = false
		self.progress = None
		self.pdffile = ""
		self.pdfdir = ""
		self.tempdir = tempfile.mkdtemp()
		self.files = []

	def Publish(self):
		self.pdfdir = self.dir
		#if wxPlatform == "__WXMSW__":
		#	import win32api
		#	self.pdfdir = win32api.GetShortPathName(self.pdfdir.encode(utils.getCurrentEncoding(), "replace"))
		try:
			#if not os.path.exists(os.path.join(self.pdfdir, "temp")):
			#	os.mkdir(os.path.join(self.pdfdir, "temp"))
			if isinstance(self.parent, wxFrame):
				self.progress = wxProgressDialog("Publishing PDF", "Publishing PDF", self.parent.wxTree.GetCount() + 1, None, wxPD_APP_MODAL | wxPD_AUTO_HIDE | wxPD_CAN_ABORT)
			#self.CopySupportFiles()
			#self.CreateTOC()
			self.counter = 1
			self.PublishPages(self.pub.nodes[0])
		except:
			if self.progress:
				self.progress.Destroy()
			raise
		
		#self.myfile.close()
		self.pdffile = os.path.join(self.pdfdir, MakeFileName2(self.pub.nodes[0].content.metadata.name + ".pdf"))
		bookfile = "#HTMLDOC\n"
		pdffile = self.pdffile
		if sys.platform == "win32":
			pdffile = string.replace(self.pdffile, "\\", "/")
		bookfile = bookfile + "-f \"" + pdffile + "\" -t pdf --no-toc --no-links --compression=9 --jpeg=90 --verbose\n" 
		for afile in self.files:
			#if wxPlatform == "__WXMSW__":
				#import win32api
			#	local_filename = file.encode(utils.getCurrentEncoding(), "replace")
			#	if os.path.exists(local_filename):
					#file = win32api.GetShortPathName(local_filename)
			#		file = string.replace(file, "\\", "/")
			#	else:
			#		file = ""
			if afile != "" and os.path.exists(afile):
				bookfile = bookfile + afile + "\n"

		bookpath = os.path.join(self.tempdir, "eclass.book")
		book = utils.openFile(bookpath, "w")
		book.write(bookfile)
		book.close()
		
		if sys.platform == "win32":
			htmldoc = os.path.join(self.ThirdPartyDir, "htmldoc", "htmldoc")
		else:
			htmldoc = os.path.join(self.ThirdPartyDir, "htmldoc", "bin", "htmldoc")

		try:
			os.system(htmldoc + " --batch " + bookpath)
		except:
			if isinstance(self.parent, wxFrame):
				wxMessageBox(_("Could not publish PDF File."))
	
		if self.progress:
			self.progress.Destroy()
		
		#if os.path.exists(self.tempdir):
		#	shutil.rmtree(self.tempdir)

		return not self.cancelled

	def CreateTOC(self):
		pass

	def AddTOCItems(self, nodes, level):
		pass				

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

	def PublishPages(self, node):
		page = ""
		if self.cancelled:
			return
		keepgoing = True #assuming no dialog to cancel, this must always be the case
		if self.progress:
			keepgoing = self.progress.Update(self.counter, _("Updating ") + node.content.metadata.name)
		if not keepgoing:
			result = wxMessageDialog(self.parent, _("Are you sure you want to cancel publishing this EClass?"), _("Cancel Publishing?"), wxYES_NO).ShowModal()
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
					publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher(self.parent, node, self.dir)")
			if publisher: 
				try:
					filename = publisher.GetFilename(node.content.filename)
					publisher.data['name'] = TextToHTMLChar(node.content.metadata.name)
					publisher.GetData()
					templatefile = os.path.join(self.parent.AppDir, "convert", "PDF.tpl")
					publisher.data['charset'] = publisher.GetConverterEncoding()
			
					myhtml = publisher.ApplyTemplate(templatefile, publisher.data)
					
					myhtml = publisher.EncodeHTMLToCharset(myhtml, publisher.data['charset'])
					
					#myhtml = publisher.Publish(self.parent, node, self.dir)
					#myhtml = GetBody(StringIO(myhtml))
					#print "in PDF plugin, myhtml = " + myhtml[:100]
					if not myhtml == "":
						myfile = utils.openFile(os.path.join(self.tempdir, filename), "w")
						myfile.write(myhtml)
						myfile.close()
						self.files.append(os.path.join(self.tempdir, filename))
				except:
					#print "Could not publish page " + os.path.join(self.dir, "pub", node.content.filename)
					import traceback
					print "Traceback is:\n" 
					traceback.print_exc()
        	
		if len(node.children) > 0:
        		for child in node.children:
        			self.PublishPages(child)
