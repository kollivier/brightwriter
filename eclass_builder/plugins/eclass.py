#from wxPython.wx import *
import string
import os
#import conman.conman as conman
import conman
import locale
import re
import plugins
from htmlutils import *
from xmlutils import *
from StringIO import StringIO
import utils
import fileutils
import mmedia
import gui.media_convert
import settings

import wx
import wxaddons.persistence
import wxaddons.sized_controls as sc

USE_MINIDOM=0
try:
	from xml.dom.ext.reader.Sax import FromXmlFile
except: 
	USE_MINIDOM=1

if USE_MINIDOM:
	from xml.dom import minidom

from threading import *
import traceback
import sys

import errors
log = errors.appErrorLog

#-------------------------- PLUGIN REGISTRATION ---------------------
# This info is used so that EClass can be dynamically be added into
# EClass.Builder's plugin registry.
plugin_info = { "Name":"eclass", 
				"FullName":"EClass Page", 
				"Directory":"EClass", 
				"Extension":["ecp"], 
				"Mime Type": "",
				"Requires":"", 
				"CanCreateNew":True}

#-------------------------- DATA CLASSES ----------------------------

EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
	win.Connect(-1, -1, wx.EVT_RESULT_ID, func)

def CreateNewFile(name, filename):
	try:
		file = EClassPage()
		file.name = name
		file.SaveAsXML(filename)
		return True
	except:
		global log
		log.write(_("Could not create new file."))
		return False
		
class EClassPage(plugins.PluginData):
	"""
	Class: eclass.EClassPage()
	Last Updated: 9/24/02
	Description: This class manages the EClass Page data structure.

	Attributes:
	- window: GUI window to send status messages to
	- filename: fully qualified filename, including path, of currently open EClass Page
	- directory: directory in which the currently open EClass Page is located
	- name: name of the currently open EClass Page
	- author: author of the currently open EClass Page
	- credit: credit and copyright info for the currently open EClass Page
	- objectives: list of objectives for the currently open EClass Page
	- media: Media files for the currently open EClass Page
	- terms: list of hotwords for the currently open EClass Page

	Methods:
	- LoadPage(filename)
	- LoadDoc(document)
	- LoadHotwords(doc)
	- SaveAsXML(filename)
	- WriteDoc(document)
	"""

	def __init__(self, window=None):
		plugins.PluginData.__init__(self)
		self.window = window
		self.filename = ""
		self.directory = ""
		self.name = ""
		self.codigo_pub = ""
		self.fecha_pub = ""
		self.title = ""
		self.author = ""
		self.credit = ""
		self.objectives = []
		self.media = EClassMedia()
		self.terms = []

	def LoadPage(self, filename):
		"""
		Function: LoadPage(filename)
		Last Updated: 9/24/02
		Description: Loads an EClass Page file in XML format

		Arguments:
		- filename: fully qualified filename, including directory, of the XML file to load
		
		Return values:
		Returns an empty string if successful, or an error string if failed.

		"""
		self.filename = filename
		self.directory = os.path.split(filename)[0]
		try:
			if USE_MINIDOM:
				doc = minidom.parse(open(filename.encode(utils.getCurrentEncoding())))
			else:	
				doc = FromXmlFile(filename)
			self.LoadDoc(doc)
		except:
			global log
			log.write(_("Could not load EClass Page %(filename)s.") % {"filename":filename})
			raise RuntimeError, `sys.exc_value.args`
		return ""

	def LoadDoc(self, doc):
		"""
		Function: LoadDoc(doc)
		Last Updated: 9/24/02
		Description: Loads the EClass Page from an XML string.

		Arguments: 
		- doc: an XML string containing the EClass Page to load

		Return values:
		None
		"""

		metadata = doc.getElementsByTagName("Metadata")
		self._GetMetadata(metadata[0])
		
		objectives = doc.getElementsByTagName("Objectives")[0].getElementsByTagName("Objective")
		for obj in objectives:
			self.objectives.append(XMLCharToText(obj.childNodes[0].nodeValue))
		
		media = doc.getElementsByTagName("Media")[0]
		self._GetMedia(media)

		if len(doc.getElementsByTagName("Terms")) > 0:
			terms = []
			node = doc.getElementsByTagName("Terms")[0]
			for child in node.childNodes:
				if (child.nodeType == node.ELEMENT_NODE and child.tagName == "Term"):
					terms.append(child)

		for term in terms:
				myterm = EClassTerm()
				if term.getElementsByTagName("Name"):
					myterm.name = XMLCharToText(term.getElementsByTagName("Name")[0].childNodes[0].nodeValue)
				else:
					myterm.name = ""
	
				if term.getElementsByTagName("Type"):
					myterm.type = XMLCharToText(term.getElementsByTagName("Type")[0].childNodes[0].nodeValue)
				else:
					myterm.type = ""
	
				if term.getElementsByTagName("URL"):
					if term.getElementsByTagName("URL")[0].childNodes:
						myterm.url = XMLCharToText(term.getElementsByTagName("URL")[0].childNodes[0].nodeValue)
					else:
						myterm.url = ""
				else:
					myterm.url = ""
	
				if term.getElementsByTagName("Page"):
					try:
						myterm.LoadPage(term.getElementsByTagName("Page")[0])
					except:
						global log
						log.write(_("Could not load hotword page for '%(name)s'.") % {"name":myterm.name})
				else:
					myterm.page = None
	
				self.terms.append(myterm)

	def LoadHotwords(self):
		"""
		Function: LoadHotwords() - NOT CURRENTLY USED
		Last Updated: 9/24/02
		Description: Loads hotwords in a separate thread.

		Arguments: 
		None

		Return values:
		None 
		"""
		try:	
			doc = FromXmlFile(self.filename)
		except:
			message = _("The EClass page file cannot be loaded from disk.")
			global log
			log.write(message)

		if len(doc.getElementsByTagName("Terms")) > 0:
			terms = []
			node = doc.getElementsByTagName("Terms")[0]
			for child in node.childNodes:
				if (child.nodeType == node.ELEMENT_NODE and child.tagName == "Term"):
					terms.append(child)
				

	def _GetMedia(self, root):
		if root.getElementsByTagName("Image")[0].childNodes:
			self.media.image = XMLCharToText(root.getElementsByTagName("Image")[0].childNodes[0].nodeValue)
		else:
			self.media.image = ""

		if root.getElementsByTagName("Video")[0].childNodes:
			self.media.video = XMLCharToText(root.getElementsByTagName("Video")[0].childNodes[0].nodeValue)
		else:
			self.media.video = ""

		if root.getElementsByTagName("VideoAutostart"):
			value = root.getElementsByTagName("VideoAutostart")[0].childNodes[0].nodeValue
			if value == "1":
				self.media.videoautostart = True
			else:
				self.media.videoautostart = False
		else:
			self.media.videoautostart = False

		if root.getElementsByTagName("Audio")[0].childNodes:
			self.media.audio = XMLCharToText(root.getElementsByTagName("Audio")[0].childNodes[0].nodeValue)
		else:
			self.media.audio = ""

		if root.getElementsByTagName("AudioAutostart"):
			value = root.getElementsByTagName("AudioAutostart")[0].childNodes[0].nodeValue
			if value == "1":
				self.media.audioautostart = True
			else:
				self.media.audioautostart = False
		else:
			self.media.audioautostart = False

		if root.getElementsByTagName("Text")[0].childNodes:
			self.media.text = XMLCharToText(root.getElementsByTagName("Text")[0].childNodes[0].nodeValue)
		else:
			self.media.text = ""

		if root.getElementsByTagName("PowerPoint")[0].childNodes:
			self.media.powerpoint = XMLCharToText(root.getElementsByTagName("PowerPoint")[0].childNodes[0].nodeValue)
		else:
			self.media.powerpoint = ""

	def _GetMetadata(self, root):
		if root.childNodes:
			if root.getElementsByTagName("Name")[0].childNodes:
				self.name = XMLCharToText(root.getElementsByTagName("Name")[0].childNodes[0].nodeValue)
			else:
				self.name = ""

			if root.getElementsByTagName("Author")[0].childNodes:
				self.author = XMLCharToText(root.getElementsByTagName("Author")[0].childNodes[0].nodeValue)
			else:
				self.author = ""

			if root.getElementsByTagName("Credit")[0].childNodes:
				self.credit = XMLCharToText(root.getElementsByTagName("Credit")[0].childNodes[0].nodeValue)
			else:
				self.credit = ""
		

	def SaveAsXML(self, filename="", encoding="ISO-8859-1"):
		"""
		Function: SaveAsXML(filename)
		Last Updated: 9/24/02
		Description: Saves the EClass Page to an XML file.

		Arguments:
		- filename: filename, including directory, of the XML file to save - if no value given, defaults to the filename used when loading the page

		Return values:
		Returns an error string if failed, or an empty string if successful.
		"""
		if filename == "":
			filename = self.filename
		else:
			self.filename = filename

		try:
			myxml = """<?xml version="1.0"?>%s""" % (self.WriteDoc())
		except:
			message = _("There was an error updating the file '%(filename)s'. Please check to make sure you did not enter any invalid characters (i.e. Russian, Chinese/Japanese, Arabic) and try updating again.") % {"filename": filename}
			global log
			log.write(message)
			raise IOError, message
		try:
			import types
			if type(myxml) != types.UnicodeType:
				#import locale
				#encoding = locale.getdefaultlocale()[1]
				myxml = unicode(myxml, encoding)
			
			myxml = myxml.encode("utf-8")
			myfile = utils.openFile(filename, "w")
			myfile.write(myxml)
			myfile.close()
		except:
			message = utils.getStdErrorMessage("IOError", {"filename":filename, "type":"write"})
			global log
			log.write(message)
			raise IOError, message

		return ""

	def WriteDoc(self):
		"""
		Function: WriteDoc()
		Last Updated: 9/24/02
		Description: Writes the EClass Page into XML format.

		Arguments:
		None

		Return values:
		None
		"""

		myxml = """
<Page>
	<Metadata>
		%s
	</Metadata>
	<Objectives>
		%s
	</Objectives>
	<Media>
		%s
	</Media>
	<Terms>
		%s
	</Terms>
</Page>
""" % (self._MetadataAsXML(), self._ObjectivesAsXML(), self._MediaAsXML(), self._TermsAsXML())	
		return myxml

	def _MetadataAsXML(self):
		mymetadata = """<Name>%s</Name>
		<Codigo_pub>%s</Codigo_pub>
		<Fecha_pub>%s</Fecha_pub>
		<Author>%s</Author>
		<Credit>%s</Credit>""" % (TextToXMLChar(self.name), TextToXMLChar(self.codigo_pub), TextToXMLChar(self.fecha_pub), TextToXMLChar(self.author), TextToXMLChar(self.credit))
		return mymetadata

	def _ObjectivesAsXML(self):
		myobj = ""
		for obj in self.objectives:
			myobj = myobj + "<Objective>" + TextToXMLChar(obj) + "</Objective>"
		return myobj

	def _MediaAsXML(self):
		mymedia = """<Image>%s</Image>
		<Video>%s</Video>
		<VideoAutostart>%s</VideoAutostart>
		<Audio>%s</Audio>
		<AudioAutostart>%s</AudioAutostart>
		<Text>%s</Text>
		<PowerPoint>%s</PowerPoint>""" % (TextToXMLChar(self.media.image), TextToXMLChar(self.media.video), `self.media.videoautostart`, TextToXMLChar(self.media.audio), `self.media.audioautostart`, TextToXMLChar(self.media.text), TextToXMLChar(self.media.powerpoint))
		return mymedia

	def _TermsAsXML(self):
		myterms = ""
		for term in self.terms:
			if term.type == "URL":
				myvalue = "<URL>" + TextToXMLChar(term.url) + "</URL>"
			elif term.type == "Page":
				myvalue = term.SavePage() 
			myterms = myterms + """<Term>
		<Name>%s</Name>
		<Type>%s</Type>
		%s
		</Term>""" % (TextToXMLChar(term.name), TextToXMLChar(term.type), myvalue)
		return myterms

class ResultEvent(wx.PyEvent):
	def __init__(self, hwname, hwid):
		wx.PyEvent.__init__(self)
		self.SetEventType(wx.EVT_RESULT_ID)
		self.hwname = hwname
		self.hwid = hwid
	
class EClassMedia (plugins.PluginData):
	"""
	Class: eclass.EClassMedia()
	Last Updated: 9/24/02
	Description: This class contains the data structures for the EClass media files.

	Attributes:
	- image: filename
	- audio: filename
	- audioautostart: boolean which determines whether or not to automatically start playing audio
	- video: filename
	- videoautostart: boolean which determines whether or not to automatically start playing video
	- introduction: filename (depreciated)
	- text: filename
	- powerpoint: filename
	"""

	def __init__(self):
		plugins.PluginData.__init__(self)
		self.image = ""
		self.audio = ""
		self.audioautostart = False
		self.video = ""
		self.videoautostart = False
		self.introduction = ""
		self.text = ""
		self.powerpoint = ""
		self.name = ""
		

class EClassTerm(plugins.PluginData):
	"""
	Class: eclass.EClassTerm()
	Last Updated: 9/24/02
	Description: This class contains the methods and attributes for dealing with hotwords.

	Attributes:
	- name: name of the hotword
	- type: hotword type, current possible values are "EClass Page" or "URL"
	- url: if hotword type is "URL", this contains the URL to link to
	- page: if hotword type is "EClass Page", this contains the EClass Page data

	Methods:
	- NewPage(): Creates a new EClass Page
	- LoadPage(doc): Loads an EClass XML document.
	- SavePage(): Converts the EClassPage hotword into XML
	"""
	def __init__(self):
		plugins.PluginData.__init__(self)
		self.name = ""
		self.type = ""
		self.url = ""
		self.page = None
	
	def NewPage(self):
		self.page = EClassPage()
		self.page.name = self.name

	def LoadPage(self, doc):
		self.page = EClassPage()
		self.page.LoadDoc(doc)

	def SavePage(self):
		return self.page.WriteDoc()

#------------------------ PUBLISHER CLASSES -------------------------------------------
class HTMLPublisher(plugins.BaseHTMLPublisher):

	def GetFileLink(self, filename):
		return "pub/" + self.GetFilename(filename)

	def GetFilename(self, filename):
		"""
		Function: GetFilename(filename)
		Last Updated: 9/24/02
		Description: Given the filename of an EClassPage, returns the filename of the converted HTML file.

		Arguments:
		- filename: the filename, without directory, of an EClassPage

		Return values:
		Returns the filename, without directory, of the HTML page generated by HTMLPublisher
		"""

		filename = os.path.splitext(filename)[0] 
		filename = os.path.basename(filename)
		filename = filename[:28]
		filename = filename + ".htm"
		filename = string.replace(filename, " ", "_")
		return filename

	def GetData(self):
		filename = os.path.join(self.dir, self.node.content.filename)
		if not os.path.exists(filename):
			filename = os.path.join(self.dir, "EClass", self.node.content.filename)
		self.mypage = EClassPage()
		self.mypage.LoadPage(filename)
		
		self._CreateEClassPage(self.mypage, filename, False)

	def _CreateEClassPage(self, mypage, filename, ishotword=False):
		counter = 1
		#publish terms first
		termlist = [] #holds term names and published filenames
		for term in mypage.terms:
			myfilename = ""
			if term.type == "Page":
				myfilename = string.replace(os.path.basename(filename), ".ecp", "")
				myfilename = myfilename + "hw" + `counter` + ".htm"
				self.data['backlink'] = "<a href=\"javascript:window.close()\">" + _("Close") + "</a>"
				html = self._CreateEClassPage(term.page, myfilename, True)
			elif term.type == "URL":
				myfilename = term.url
				basename = os.path.basename(myfilename)
				myname, myext = os.path.splitext(basename)
				#print "myname = " + myfilename + "\nlength of myname is: " + `len(myname)` + "len of myext is: " + `len(myext)` + "\n"
				if len(basename) > 31:
					if self.parent.pub.settings["ShortenFilenames"] == "":
						message = _("EClass has detected filenames containing more than 31 characters in the EClass Page '%(pagename)s. This could cause compatibility problems with older browsers and operating systems. Would you like EClass to automatically rename these files?") % {"pagename":mypage.name}
						mydialog = wx.MessageDialog(self.parent, message, _("Rename file?"), wx.YES_NO)
						if mydialog.ShowModal() == wx.ID_YES:
							self.parent.pub.settings["ShortenFilenames"] = "Yes"
						else:
							self.parent.pub.settings["ShortenFilenames"] = "No"
					if self.parent.pub.settings["ShortenFilenames"] == "Yes":
						oldfilename = myfilename
						myname = myname[:31-len(myext)]
						myfilename = myname + myext
						counter = 1
						while os.path.exists(os.path.join(self.dir, "File", myfilename)):
							if counter > 9:
								myfilename = myname[:-2] + `counter` + myext
							else:
								myfilename = myname[:-1] + `counter` + myext
							counter = counter + 1
							#print "new filename is: " + myfilename + "\n"
						os.rename(os.path.join(self.dir, "File", oldfilename), os.path.join(self.dir, "File", myfilename))
						myfilename = "../File/" + myfilename
						term.url = myfilename
						
						#print "new filename length is: " + `len(myfilename)` + "\n"
			termlist.append([term.name, myfilename])
			counter = counter + 1	
		if self.parent.pub.settings["ShortenFilenames"] == "Yes":
			mypage.SaveAsXML()	

		myhtml = ""
		if len(mypage.media.text) > 0 and os.path.exists(os.path.join(self.dir, "Text", mypage.media.text)):
			myfile = None
			convert = False
			if string.find(os.path.splitext(string.lower(mypage.media.text))[1], "htm") != -1:
				myhtml = GetBody(utils.openFile(os.path.join(self.dir, "Text", mypage.media.text), 'rb'))
			else: 
				#It might be a Word/RTF document, try to convert...
				convert = True
				myfilename = os.path.join(self.dir, "Text", mypage.media.text)
				
				myhtml = self._ConvertFile(myfilename)
				if myhtml == "":
					return ""

				myhtml = ImportFiles().ImportLinks(myhtml, os.path.join(os.path.dirname(thefilename)), self.dir)

		else:
			myhtml = ""
		objtext = ""
		myhtml = self._InsertTerms(myhtml, termlist)
		
		if len(mypage.objectives) > 0:
			objtext = "<hr><h2>" + _("Objectives") + "</h2><ul id=\"objectives\">"
			for obj in mypage.objectives:
				objtext = objtext + "<li>" + TextToXMLChar(obj) + "</li>"
			objtext = objtext + "</ul><hr>"

		#try:
		bjtext = utils.makeUnicode(objtext)
		myhtml = self._AddMedia(mypage) + objtext + utils.makeUnicode(myhtml)
			
		#except UnicodeError:
		#	raise

		try: 
			importer = ImportFiles()
			myhtml2 = importer.ImportLinks(myhtml, os.path.join(self.dir, "Text"), self.dir)
			myhtml = myhtml2
		except:
			pass

		if not ishotword:
			self.data['content'] = myhtml
			self.data['credit'] = self.GetCreditString() 
			
		else: #ugly hack for now...
			if self.node.content.template == None or self.node.content.template == "None":
				self.node.content.template = "Default"

			try:
				myhtml = self.ApplyTemplate(data=self.data)
			except UnicodeError:
				raise

			try:		
				myfile = utils.openFile(os.path.join(self.dir, "pub",filename), "w")
				myfile.write(myhtml)
				myfile.close()
			except:
				message = utils.getStdErrorMessage("IOError", {"filename":filename, "type":"write"})
				global log
				log.write(message)
				raise IOError, message
				return False	
		return myhtml
		
	def _ConvertFile(self, filename):
		myfilename = filename
		if wx.Platform == "__WXMSW__":
			import win32api
			myfilename = win32api.GetShortPathName(filename)

		message = _("Unable to convert file %(filename)s") % {"filename": mypage.media.text}
		try:
			import converter
			wx.BeginBusyCursor()
			myconverter = converter.DocConverter(self.parent)
			thefilename = myconverter.ConvertFile(myfilename, "html", "ms_office")[0]
			wx.EndBusyCursor()
			if thefilename == "":
				wx.MessageBox(message)
				return ""
			myhtml = GetBody(utils.openFile(thefilename, "rb"))
		except:
			wx.EndBusyCursor()
			global log
			log.write(message)
			return ""

	def _InsertTerms(self, myhtml, termlist):
		for term in termlist:	
			regexterm = string.replace(term[0], "(", "\(")
			regexterm = TextToXMLChar(regexterm)
			regexterm = string.replace(regexterm, ")", "\)")
			regexterm = string.replace(regexterm, "'", "\'")
			regexterm = string.replace(regexterm, "?", "\?")
			regexterm = string.replace(regexterm, ".", "\.")
			regexterm = string.replace(regexterm, "*", "\*")
			regexterm = string.replace(regexterm, "$", "\$")
			regexterm = string.replace(regexterm, " ", "[\s&nbsp;]+")
			regexterm = string.replace(regexterm, "\"", "&quot;")
			#print "Regex term = " + regexterm
			myterm = re.compile("(<[^>]*>[^<]*)(" + regexterm  +")(.*<[^>]*>)", re.IGNORECASE|re.DOTALL)
			#myterm = re.compile("([^<\w]*)(" + regexterm +")([^<\w]*)", re.IGNORECASE|re.DOTALL)

			mymatch = myterm.match(myhtml)
			#if mymatch:
			#	print "Match: " + mymatch.group(0)
			#else:
			#	print "Match not found."
			myhtml = myterm.sub("\\1<a href=\"" + term[1] + "\" target=_blank>\\2</a>\\3", myhtml)
		return myhtml

	def _AddMedia(self, mypage):
		"""Appends media files specified in the EClassPage to the current HTML page."""
		HTML = ""
	
		template = ""
		mimetype = ""
		imageHTML = ""
		videoHTML = ""
		audioHTML = ""
		presentHTML = ""
 
		if len(mypage.media.image) > 0 and os.path.exists(os.path.join(settings.ProjectDir, "Graphics", mypage.media.image)):
			imageHTML = "<IMG src='../Graphics/%s'>" % (mypage.media.image)
		
		if len(mypage.media.video) > 0 and os.path.exists(os.path.join(settings.ProjectDir, "pub", "Video", mypage.media.video)):
			template = ""
			url = "Video/" + mypage.media.video
			template = mmedia.getHTMLTemplate(os.path.join(settings.ProjectDir, "pub", url), isVideo=True)

			videoHTML = string.replace(template, "_filename_", url)
			autostart = "False"
			if mypage.media.videoautostart == True:
				autostart = "True"
			videoHTML = string.replace(videoHTML, "_autostart_", autostart)

		if len(mypage.media.audio) > 0 and os.path.exists(os.path.join(settings.ProjectDir, "pub", "Audio", mypage.media.audio)):
			template = ""
			url = "Audio/" + mypage.media.audio
			template = mmedia.getHTMLTemplate(os.path.join(settings.ProjectDir, "pub", url), isVideo=False)

			audioHTML = string.replace(template, "_filename_", url)
			autostart = "False"
			if mypage.media.audioautostart == True:
				autostart = "True"
			audioHTML = string.replace(audioHTML, "_autostart_", autostart)

		if len(mypage.media.powerpoint) > 0 and os.path.exists(os.path.join(settings.ProjectDir, "Present", mypage.media.powerpoint)):
			presentHTML = """<a href="../Present/%(pres)s" target="_blank">%(viewpres)s</a>""" % {"pres":mypage.media.powerpoint, "viewpres":_("View Presentation")}
	
		if len(imageHTML) > 0 and len(videoHTML) > 0:
			HTML = HTML + """<CENTER>
<table border="0" cellpadding="2" cellspacing="4">
<td align="center" valign="top"><span id="image">%s</span></td>
<td align="center" valign="top"><span id="video">%s</span></td>
</table></CENTER>
""" % (imageHTML, videoHTML)
		elif len(mypage.media.image) > 0 or len(mypage.media.video) > 0:
			if len(mypage.media.image) > 0:
				vidimage = imageHTML
			else:
				vidimage = videoHTML

			HTML = HTML + """<p align="center">%s</p>""" % (vidimage)

		if len(mypage.media.audio) > 0:
			HTML = HTML + "<br><span id=\"audio\">%s</span>" % (audioHTML)

		if len(mypage.media.powerpoint) > 0:
			HTML = HTML + "<br><h3 align=\"center\"><span id=\"presentation\">%s</span></h3>" % (presentHTML)
		
		return utils.makeUnicode(HTML)

class PDFPublisher(HTMLPublisher):
	def __init__(self, parent, node, dir):
		self.parent = parent
		self.node = node
		self.dir = dir
		filename = os.path.join(self.dir, node.content.filename)
		if not os.path.exists(filename):
			filename = os.path.join(self.dir, "EClass", node.content.filename)
		self.mypage = EClassPage()
		self.mypage.LoadPage(filename)

	def Publish(self):
		filename = self.GetFilename(node.content.filename)
		myhtml = self._CreateEClassPage(self.mypage, filename)
		return myhtml

#-------------------------- EDITOR INTERFACE ----------------------------------------

class SelectBox(sc.SizedPanel):
	"""
	Class: eclass.SelectBox
	Last Updated: 9/24/02
	Description: A customized text box class to integrate file selection capabilities.

	Attributes:
	- parent: the parent window hosting the control
	- filename: points to the file selected by the user
	- type: file types the user is allowed to select (i.e. "Graphics", "Audio")
	- title: label text
	- label: textbox label
	- textbox: the textbox to store the file selected by the user
	- selectbtn: button the user clicks to select a file

	Methods:
	- selectbtnClicked: brings up the file selection dialog when the user clicks the selectbtn
	- textboxChanged: updates the textbox attribute whenever the textbox changes
	"""

	def __init__(self, parent, filename, type):
		sc.SizedPanel.__init__(self, parent, -1)
		self.parent = parent
		self.filename = filename
		self.type = type
		self.selecteddir = ""
		#pane = sc.SizedPanel(parent, -1)
		self.SetSizerType("horizontal")
		self.SetSizerProp("expand", True)
		self.SetSizerProp("proportion", 1)
		
		icnFolder = wx.Bitmap(os.path.join(settings.AppDir, "icons", "Open.gif"), wx.BITMAP_TYPE_GIF)
		self.textbox = wx.TextCtrl(self, -1, filename)
		self.textbox.SetSizerProp("expand", True)
		self.textbox.SetSizerProp("proportion", 1)
		self.selectbtn = wx.BitmapButton(self, -1, icnFolder)

		wx.EVT_BUTTON(self.selectbtn, self.selectbtn.GetId(), self.selectbtnClicked)
		wx.EVT_TEXT(self.textbox, self.textbox.GetId(), self.textboxChanged)

	def selectbtnClicked(self, event):
		hyperlink = False
		if self.type == "Graphics":
			filter = _("Image Files") + "(*.jpg,*.gif,*.bmp,*.png)|*.jpg;*.jpeg;*.gif;*.bmp;*.png"
		elif self.type == "Video":
			filter = _("Video Files") + "(*.avi,*.mov,*.mpg,*.asf,*.wmv,*.rm, *.ram, *.swf)|*.avi;*.mov;*.mpg;*.mpeg;*.asf;*.wmv;*.rm;*.ram;*.swf"
		elif self.type == "Audio":
			filter = _("Audio Files") + "(*.wav,*.aif,*.mp3,*.asf,*.wma,*.rm,*.ram)|*.wav;*.aif;*.mp3;*.asf;*.wma;*.rm;*.ram"
		elif self.type == "Text":
			filter = _("Document Files") + "(*.htm,*.html, *.doc, *.rtf)|*.htm;*.html;*.doc;*.rtf"
		elif self.type == "Present":
			filter = _("Presentation Files") + "(*.ppt,*.htm,*.html,*.swf)|*.ppt;*.htm;*.html;*.swf"
		else:
			hyperlink = True
			self.type = "File"
			filter = _("All Files") + "(*.*)|*.*"

		f = wx.FileDialog(self.parent, _("Select a file"), os.path.join(settings.ProjectDir, self.type), "", filter, wx.OPEN)
		if f.ShowModal() == wx.ID_OK:
			self.selecteddir = f.GetDirectory()
			dir = os.path.join(settings.ProjectDir, self.type)
			if self.type in ["Video", "Audio"]:
				dir = os.path.join(settings.ProjectDir, "pub", self.type)
			
			if string.find(f.GetPath(), dir) == -1:
				self.CopyFile(f.GetPath(), f.GetFilename(), dir)
									
			if hyperlink:
				result = False
				if len(f.GetFilename()) > 31 and self.parent.mainform.pub.settings["ShortenFilenames"] == "":
					message = _("This filename contains more than 31 characters. This could cause compatibility problems with older browsers and operating systems. Would you like EClass to automatically rename the file?")
					dialog = wx.MessageDialog(self.parent, message, _("Rename File?"), wx.YES_NO)			
					if dialog.ShowModal() == wxID_YES:
						result = True
				elif len(f.GetFilename()) > 31 and self.parent.mainform.pub.settings["ShortenFilenames"] == "Yes":
					result = True
				else:
					result = False
					self.filename = "../File/" + f.GetFilename()

				if result:
					self.parent.mainform.pub.settings["ShortenFilenames"] = "Yes"
					oldfilename = f.GetFilename()
					myname, myext = os.path.splitext(oldfilename)
					myname = myname[:31-len(myext)]
					myfilename = myname + myext
					counter = 1
					while os.path.exists(os.path.join(self.dir, "File", myfilename)):
						if counter > 9:
							myfilename = myname[:-2] + `counter` + myext
						else:
							myfilename = myname[:-1] + `counter` + myext
						counter = counter + 1
						#print "new filename is: " + myfilename + "\n"
					os.rename(os.path.join(settings.ProjectDir, "File", oldfilename), os.path.join(settings.ProjectDir, "File", myfilename))
					self.filename = "../File/" + myfilename
			else:
				self.filename = f.GetFilename()
			self.textbox.SetValue(self.filename)
		#print "This is running..."
		f.Destroy()
		selecteddir = ""

	def CopyFile(self, path, filename, destdir, showgui=True):
		self.parent.mainform.SetStatusText(_("Copying File %(filename)s...") % {"filename":filename})
		error = False
		try:
			file = utils.openFile(path, "rb")
			data = file.read()
			if string.lower(os.path.splitext(filename)[1]) in [".html", ".htm"]:
				importer = ImportFiles()
				data = importer.ImportLinks(data, self.selecteddir, settings.ProjectDir)
			file.close()
		except IOError:
			error = True
			global log
			message = utils.getStdErrorMessage("IOError", {"type":"read", "filename":path})
			log.write(message)
			if showgui:
				wx.MessageDialog(self.parent, message, _("File Read Error"), wx.OK).ShowModal()
				
		if not error:
			if not os.path.exists(destdir):
				os.mkdir(destdir)
			try:
				self.parent.mainform.SetStatusText(_("Pasting %(filename)s...") % {"filename":os.path.join(destdir, filename)})
				out = utils.openFile(os.path.join(destdir, filename), "wb")
				out.write(data)
				out.close()
			except IOError:
				message = _("EClass.Builder could not write the file '%(filename)s' to disk. Please check that '%(directory)s' exists and you have permissions to write to this folder, and that a read-only version of the file does not exist in this folder.") % {"filename":os.path.join(destdir, filename),"directory":destdir}
				global log
				log.write(message)
				if showgui:
					wx.MessageDialog(self, message, _("File Write Error."), wx.OK).ShowModal()
		self.parent.mainform.SetStatusText("")

	def textboxChanged(self, event):
		self.filename = self.textbox.GetValue()
		#print self.filename

class EClassObjectiveEditorDialog(sc.SizedDialog):
	"""
	class: eclass.EClassObjectiveEditorDialog(wxDialog)
	Last Updated: 9/24/02
	Description: This dialog presents an interface for editing objectives.

	Attributes:
	- parent: the parent window which called the dialog
	- txtObj: a text box containing the objective
	- btnOK: OK button

	Methods:
	- btnOKClicked: Saves data and closes the dialog
	"""

	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("Objective Editor"),
						 wx.DefaultPosition,
						   wx.Size(200,150),
						   wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		pane = self.GetContentsPane()
		self.txtObj = wx.TextCtrl(pane, -1, parent.CurrentObj, style=wx.TE_MULTILINE)
		self.txtObj.SetSizerProps({"expand":"true", "proportion": 1})
		self.txtObj.SetFocus()
		self.txtObj.SetSelection(0, -1)
		
		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"))

		buttonsizer = wx.StdDialogButtonSizer()
		buttonsizer.AddButton(self.btnOK)
		buttonsizer.AddButton(self.btnCancel)
		buttonsizer.Realize()
		self.SetButtonSizer(buttonsizer)
		
		self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)

		self.ShowModal()

	def btnOKClicked(self, event):
		if len(self.txtObj.GetValue()): 
			self.parent.CurrentObj = self.txtObj.GetValue()
			self.EndModal(wx.ID_OK)
		else:
			wx.MessageDialog(self, _("Please enter some text for your objective, or click Cancel to quit."), _("Empty Objective"), wx.ICON_INFORMATION | wx.OK).ShowModal() 

class EClassHyperlinkEditorDialog(sc.SizedDialog):
	"""
	Class: eclass.EClassHyperlinkEditorDialog(wxDialog)
	Last Updated: 9/24/002
	Description: Dialog for editing hyperlink hotwords.

	Attributes:
	- parent: the parent window which called the dialog
	- term: the hotword to be edited
	- txtName: textbox to edit hotword name
	- selectFile: SelectBox to choose the file to link to
	- btnOK: OK button
	
	Methods:
	-btnOKClicked: Updates hotword information and closes dialog
	"""

	def __init__(self, parent, term):
		sc.SizedDialog.__init__ (self, parent, -1, _("Hyperlink Editor"),
						 wx.DefaultPosition,
						   wx.DefaultSize,
						   wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		self.parent = parent
		self.mainform = parent.mainform
		self.term = term
		
		pane = self.GetContentsPane()
		# make it a grid sizer
		pane.SetSizerType("form")
		
		self.lblName = wx.StaticText(pane, -1, _("Name"))
		self.lblName.SetSizerProps({"halign":"left", "valign":"center"})
		
		self.txtName = wx.TextCtrl(pane, -1, term.name)
		self.txtName.SetSizerProps({"expand":True, "proportion":1,"align":"center"})
		self.txtName.SetFocus()
		self.txtName.SetSelection(0, -1)
		
		#spacer = sc.SizedPanel(pane, -1)
		#spacer.SetSizerProp("expand", "true")
		
		wx.StaticText(pane, -1, _("Link Address")).SetSizerProp("valign", "center")
		self.selectFile = SelectBox(pane, term.url, _("Link"))
		
		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"))
		
		self.buttonsizer = wx.StdDialogButtonSizer()
		self.buttonsizer.AddButton(self.btnOK)
		self.buttonsizer.AddButton(self.btnCancel)
		self.buttonsizer.Realize()
		self.SetButtonSizer(self.buttonsizer)
		
		self.LoadState("HyperlinkEditor")

		self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)

		self.ShowModal()

	def btnOKClicked(self, event):
		self.term.name = self.txtName.GetValue()
		self.term.url = self.selectFile.textbox.GetValue()
		self.SaveState("HyperlinkEditor")
		self.EndModal(wxID_OK)

#--------------------------- E-Class Page Editor Class ------------------------------------
class EditorDialog (sc.SizedDialog):
	"""
	Class: EditorDialog
	Last Updated: 10/21/02
	Description: This dialog lets users edit the selected EClassPage. 

	Attributes:
	- item: the ConNode selected on the main EClass editor, or an EClassPage
	- parent: the parent window that called this dialog
	- mainform: the main window of the application - needed to update status messages
	- ProjectDir: the root directory of the currently selected node
	- CurrentObj: the currently-selected objective

	Methods:
	- btnEditTextClicked: opens a text file in the HTML editing application, if selected
	- btnNewFileClicked: creates a new text file on disk
	- LoadTerms: clears the hotword list and reloads hotwords
	- LoadObjectives: clears the objective list and reloads objectives
	- AddTerm: Adds a hotword to the hotword list, opens the hotword editor, and updates the hotword list
	- btnAddTermClicked: Opens the new hotword dialog
	- btnEditObjectiveClicked: Opens the objective editor and updates the objective list
	- EditTerm: Edits an existing hotword, and updates the hotword list
	- btnRemoveTermClicked: Removes the currently selected hotword
	- btnRemoveObjectiveClicked: Removes the currently selected objective
	- btnOKClicked: Saves page settings, writes page to disk, and closes the dialog
	"""

	def __init__(self, parent, item):
		height = 20
		if wx.Platform == "__WXMAC__":
			height = 25
		busy = wx.BusyCursor()
		self.item = item
		self.parent = parent
		# We need to have a pointer to the main frame to get global settings
		if isinstance(parent, wx.Frame):
			self.mainform = parent
		else:
			self.mainform = parent.mainform
		self.CurrentObj = None
		loaded = True 
		self.isHotword = False 

		#check if ConNode or if EClassPage
		if isinstance(item, conman.conman.ConNode):
			self.filename = item.content.filename
			self.page = EClassPage(self)
			if len(self.filename) > 0:
				
				if not os.path.exists(os.path.join(settings.ProjectDir, "EClass", os.path.basename(self.filename))):
					self.page.SaveAsXML(os.path.join(settings.ProjectDir, "EClass", os.path.basename(self.filename)))

				try:
					self.page.LoadPage(os.path.join(settings.ProjectDir, "EClass", os.path.basename(self.filename)))
					item.content.filename = self.filename
				except RuntimeError, e:
					global log
					message = _("There was an error loading the EClass page '%(page)s'. The error reported by the system is: %(error)s") % {"page":os.path.join(parent.ProjectDir, "EClass", self.filename), "error":str(e)}
					wx.MessageDialog(parent, message, _("Error loading page"), wx.OK).ShowModal()
					log.write(message)
					del busy
					return
			else:
				myfilename = os.path.join(settings.ProjectDir, "EClass", utils.suggestFileName(self.page.name + ".ecp"))
				self.filename = item.content.filename = myfilename
				try:
					self.page.SaveAsXML(os.path.join(settings.ProjectDir, "EClass", myfilename))
				except IOError, e:
					global log
					message = _("There was an error saving the EClass page '%(page)s'. The error message returned by the system is: %(error)s") % {"page":os.path.join(self.parent.ProjectDir, "EClass", myfilename), "error":str(e)}
					log.write(message)
					wx.MessageDialog(self, message, _("File Write Error"), wx.OK)

			self.page.name = item.content.metadata.name
		else:
			settings.ProjectDir = self.parent.ProjectDir
			self.page = item.page
			self.isHotword = True
		
		authorname = ""
		if self.isHotword:
			authorname = self.page.author
		else:
			if self.page.author and not self.item.content.metadata.lifecycle.getAuthor():
				self.item.content.metadata.lifecycle.addContributor(self.page.author, "Author")

			author = self.item.content.metadata.lifecycle.getAuthor()
			if author:
				authorname = author.entity.fname.value
				
		credits = ""
		if self.isHotword:
			credits = self.page.credit
		else:
			if self.page.credit and self.item.content.metadata.rights.description == "":
				self.item.content.metadata.rights.description = self.page.credit

			credits = self.item.content.metadata.rights.description

		
		sc.SizedDialog.__init__ (self, parent, -1, _("EClass Page Editor"),
						 wx.DefaultPosition,
						   wx.DefaultSize,
						   wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
						   
		pane = self.GetContentsPane()

		topPane = sc.SizedPanel(pane, -1)
		topPane.SetSizerType("form")
		topPane.SetSizerProps({"expand":True})
		#topPane.SetSizerProps({"hgrow": 100})
		
		self.lblTitle = wx.StaticText(topPane, -1, _("Name"))
		self.txtTitle = wx.TextCtrl(topPane, -1, self.page.name)
		self.txtTitle.SetSizerProps({"expand":True}) # SetSizerProp("hgrow", 100)
		
		self.lblAuthor = wx.StaticText(topPane, -1, _("Author"))
		self.txtAuthor = wx.TextCtrl(topPane, -1, authorname)
		self.txtAuthor.SetSizerProps({"expand":True}) # SetSizerProp("hgrow", 100)
		
		self.lblCredit = wx.StaticText(topPane, -1, _("Credit"))
		self.txtCredit = wx.TextCtrl(topPane, -1, credits, style=wx.TE_MULTILINE)
		self.txtCredit.SetSize(wx.Size(self.txtCredit.GetSize()[0], 80))
		self.txtCredit.SetSizerProps({"expand":True}) # SetSizerProp("hgrow", 100)

		midPane = sc.SizedPanel(pane, -1)
		midPane.SetSizerType("grid", {"cols": 2})
		midPane.SetSizerProp("expand", True)
		midPane.GetSizer().AddGrowableCol(0)
		midPane.GetSizer().AddGrowableCol(1)
		
		# Left-hand side
		midleftPane = sc.SizedPanel(midPane, -1)
		midleftPane.SetSizerType("form")
		midleftPane.SetSizerProp("expand", True)
		midleftPane.SetSizerProp("proportion", 1)
		
		wx.StaticText(midleftPane, -1, _("Image:")).SetSizerProps({"halign": "right", "valign":"center"})
		self.selectImage = SelectBox(midleftPane, self.page.media.image, _("Graphics"))
		
		wx.StaticText(midleftPane, -1, _("Video:")).SetSizerProps({"halign": "right", "valign":"center"})
		self.selectVideo = SelectBox(midleftPane, self.page.media.video, _("Video"))
		
		sc.SizedPanel(midleftPane, -1) #spacer
		self.chkVideoAutostart = wx.CheckBox(midleftPane, -1, _("Play on load"))
		if wx.Platform == "__WXMAC__":
			self.chkVideoAutostart.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
		#self.chkVideoAutostart.SetSizerProp("all", 0)
		if self.page.media.videoautostart == True:
			self.chkVideoAutostart.SetValue(True)
		
		wx.StaticText(midleftPane, -1, _("Audio:")).SetSizerProps({"halign": "right", "valign":"center"})
		self.selectAudio = SelectBox(midleftPane, self.page.media.audio, _("Audio"))
		sc.SizedPanel(midleftPane, -1) #spacer
		self.chkAudioAutostart = wx.CheckBox(midleftPane, -1, _("Play on load"))
		if wx.Platform == "__WXMAC__":
			self.chkAudioAutostart.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
		if self.page.media.audioautostart == True:
			self.chkAudioAutostart.SetValue(True)

		midrightPane = sc.SizedPanel(midPane, -1)
		midrightPane.SetSizerType("form")
		midrightPane.SetSizerProp("expand", True)
		
		wx.StaticText(midrightPane, -1, _("Text:")).SetSizerProps({"halign": "right", "valign":"center"})
		self.selectText = SelectBox(midrightPane, self.page.media.text, _("Text"))
		sc.SizedPanel(midrightPane, -1)
		btnPane = sc.SizedPanel(midrightPane, -1)
		btnPane.SetSizerType("horizontal")
		self.btnNewFile = wx.Button(btnPane,-1,_("New"))
		if wx.Platform == "__WXMAC__":
			self.btnNewFile.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
		self.btnEditText = wx.Button(btnPane,-1,_("Edit"))
		if wx.Platform == "__WXMAC__":
			self.btnEditText.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

		wx.StaticText(midrightPane, -1, _("Presentation:")).SetSizerProps({"halign": "right", "valign":"center"})
		self.selectPowerPoint = SelectBox(midrightPane, self.page.media.powerpoint, "Present")
		
		bottomPane = sc.SizedPanel(pane, -1)
		bottomPane.SetSizerType("grid", {"cols": 2})
		bottomPane.SetSizerProps({"expand": True, "proportion":1})
		bottomPane.GetSizer().AddGrowableCol(0)
		bottomPane.GetSizer().AddGrowableCol(1)
		bottomPane.GetSizer().AddGrowableRow(1)
		wx.StaticText(bottomPane, -1, _("Hotwords"))
		wx.StaticText(bottomPane, -1, _("Objectives"))

		self.lstTerms = wx.ListBox(bottomPane, -1)
		self.lstTerms.SetSizerProps({"expand": True, "proportion":1})
		self.LoadTerms()

		self.lstObjectives = wx.ListBox(bottomPane, -1)
		self.lstObjectives.SetSizerProps({"expand": True, "proportion":1})
		self.LoadObjectives()
		
		hwBtnPane = sc.SizedPanel(bottomPane, -1)
		hwBtnPane.SetSizerType("horizontal")
		
		self.btnAddTerm = wx.Button(hwBtnPane,-1,_("Add"))
		self.btnEditTerm = wx.Button(hwBtnPane,-1,_("Edit"))
		self.btnRemoveTerm = wx.Button(hwBtnPane,-1,_("Remove"))

		objBtnPane = sc.SizedPanel(bottomPane, -1)
		objBtnPane.SetSizerType("horizontal")
		self.btnAddObjective = wx.Button(objBtnPane,-1,_("Add"))
		self.btnEditObjective = wx.Button(objBtnPane,-1,_("Edit"))
		self.btnRemoveObjective = wx.Button(objBtnPane,-1,_("Remove"))

		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.txtTitle.SetSelection(0, -1)
		self.txtTitle.SetFocus()
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"))

		self.okcancelsizer = wx.StdDialogButtonSizer()
		self.okcancelsizer.AddButton(self.btnOK)
		self.okcancelsizer.AddButton(self.btnCancel)
		self.okcancelsizer.Realize()
		self.SetButtonSizer(self.okcancelsizer)

		self.Fit()
		self.SetMinSize(self.GetSize())
		convertFiles = []
		audioFile = os.path.join(settings.ProjectDir, "pub", "Audio", self.page.media.audio)
		if mmedia.canConvertFile(self.page.media.audio) and not mmedia.wasConverted(audioFile):
			convertFiles.append(self.page.media.audio)
		
		videoFile = os.path.join(settings.ProjectDir, "pub", "Video", self.page.media.video)
		if mmedia.canConvertFile(self.page.media.video) and not mmedia.wasConverted(videoFile):
			convertFiles.append(self.page.media.video)
			
		if mmedia.findFFMpeg() != "" and convertFiles != []:
			dlg = gui.media_convert.ConvertMediaDialog(self, convertFiles)
			if dlg.ShowModal() == wx.ID_OK:
				files = dlg.GetSelectedFiles()
				for afile in files:
					filepath = os.path.join(settings.ProjectDir, "pub", "Video", afile)
					if not os.path.exists(filepath):
						filepath = os.path.join(settings.ProjectDir, "pub", "Audio", afile)
					if os.path.exists(filepath):
						mmedia.convertFile(filepath)

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		wx.EVT_BUTTON(self.btnNewFile, self.btnNewFile.GetId(), self.btnNewFileClicked)
		wx.EVT_BUTTON(self.btnEditText, self.btnEditText.GetId(), self.btnEditTextClicked)
		wx.EVT_BUTTON(self.btnEditTerm, self.btnEditTerm.GetId(), self.btnEditTermClicked)
		wx.EVT_BUTTON(self.btnEditObjective, self.btnEditObjective.GetId(), self.btnEditObjectiveClicked)
		wx.EVT_BUTTON(self.btnRemoveTerm, self.btnRemoveTerm.GetId(), self.btnRemoveTermClicked)
		wx.EVT_BUTTON(self.btnRemoveObjective, self.btnRemoveObjective.GetId(), self.btnRemoveObjectiveClicked)
		wx.EVT_BUTTON(self.btnAddTerm, self.btnAddTerm.GetId(), self.btnAddTermClicked)
		wx.EVT_BUTTON(self.btnAddObjective, self.btnAddObjective.GetId(), self.btnAddObjectiveClicked)
		#wx.EVT_KEY_UP(self, self.checkKey)
		wx.EVT_LISTBOX_DCLICK(self.lstTerms, self.lstTerms.GetId(), self.btnEditTermClicked)
		wx.EVT_LISTBOX_DCLICK(self.lstObjectives, self.lstObjectives.GetId(), self.btnEditObjectiveClicked)
		#wx.EVT_RESULT(self, self.NewHotwordLoaded)

		del busy

	#def Load(self):
	#	self.ShowModal()
	#	self.page.LoadHotwords()

	#def NewHotwordLoaded(self, event):
	#	print "New Hotword Loaded called on " + event.hwname
	#	self.lstTerms.Append(event.hwname, self.page.terms[event.hwid])

	def checkKey(self, event):
		if event.keyCode == wx.RETURN:
			self.btnOKClicked(event)		

	def btnEditTextClicked(self, event):
		if wx.Platform == '__wx.MAC__': 
			try:
				from OSATools import AppModels
				dreamweaver = AppModels.AppleScriptApp("Dreamweaver MX")
				opencommand = 'set myPath to POSIX file "' + os.path.join(settings.ProjectDir, "Text", self.selectText.filename) + '"'
				result = dreamweaver.tellBlock(['activate',opencommand, 'open file myPath'])
			except:
				pass
			return

		if self.mainform.settings["HTMLEditor"] == "":
			wx.MessageDialog(self, _("To edit the page, E-Class needs to know what HTML Editor you would like to use. To specify a HTML Editor, select 'Preferences' from the 'Options' menu."), _("Cannot Edit Page"), wx.OK).ShowModal()
		else:
			if not os.path.exists(os.path.join(settings.ProjectDir, "Text", self.selectText.filename)):
				dialog = wx.MessageDialog(self, _("The text file '%(filename)s' does not exist. Would you like EClass to create it for you?") % {"filename":self.selectText.filename}, _("File not found"), wx.YES_NO)
				if dialog.ShowModal() == wx.ID_YES:
					self.CreateHTMLFile(os.path.join(settings.ProjectDir, "Text", self.selectText.filename))
				else:
					return
			if wx.Platform == "__wx.MSW__":
				import win32api
				editor = "\"" + self.mainform.settings["HTMLEditor"] + "\""
				if not string.find(string.lower(editor), "mozilla") == -1:
					editor = editor + " -edit" 
				win32api.WinExec(editor + " \"" + os.path.join(settings.ProjectDir, "Text", self.selectText.filename) + "\"")
				
				#path = win32api.GetShortPathName(os.path.join(settings.ProjectDir, "Text", self.selectText.filename))
				#editor = win32api.GetShortPathName(self.mainform.settings["HTMLEditor"])
				#if not string.find(string.lower(editor), "mozilla") == -1:
				#	editor = editor + " -edit" 
				#print editor + " " + path
				#os.system(editor + " " + path)
				#os.spawnv(1, self.mainform.settings["HTMLEditor"], [os.path.split(self.mainform.settings["HTMLEditor"])[1], "\"" + os.path.join(settings.ProjectDir, "Text", self.selectText.filename) + "\""])
			else:
				editor = self.mainform.settings["HTMLEditor"] 
				if wx.Platform == "__wx.MAC__":
					editor = "open -a '" + editor + "'"
				path = editor + " '" + os.path.join(settings.ProjectDir, "Text", self.selectText.filename) + "'"
				os.system(path)

	def CreateHTMLFile(self, filename):
		html = """
<HTML>
<HEAD>
</HEAD>
<BODY>
</BODY>
</HTML>"""
		try: 
			file = utils.openFile(filename, "w")
			file.write(html)
			file.close()
		except IOError: 
			global log
			message = _("Unable to create the file '%(filename)s'. Please make sure that this is a valid filename and try again.") % {"filename":filename}
			log.write(message)
			wx.MessageDialog(self, message, _("File write error"), wx.OK)

	def btnNewFileClicked(self, event):
		savefile = False

		f = wx.FileDialog(self, _("New HTML Page"), os.path.join(settings.ProjectDir, "Text"), "", _("HTML Files") + " (*.html)|*.html", wx.SAVE)
		if f.ShowModal() == wx.ID_OK:
			filename = f.GetPath()
			if os.path.exists(filename):
				msg = wx.MessageDialog(self, _("A file with this name already exists. Would you like to overwrite it?"), _("Overwrite File?"), wx.YES_NO)
				answer = msg.ShowModal()
				if answer == wx.ID_YES:
					savefile = True
			else:
				savefile = True

			if savefile:
				try: 
					self.CreateHTMLFile(filename)
					self.selectText.filename = f.GetFilename()
					self.selectText.textbox.SetValue(f.GetFilename())
				except:
					pass
		f.Destroy()

	def LoadTerms(self):
		self.lstTerms.Clear()
		for term in self.page.terms:
			self.lstTerms.Append(term.name, term)

	def LoadObjectives(self):
		self.lstObjectives.Clear()
		for obj in self.page.objectives:
			self.lstObjectives.Append(obj)

	def AddTerm(self, myterm):
		self.lstTerms.Append(myterm.name, myterm)
		self.page.terms.append(myterm)
		self.lstTerms.SetSelection(self.lstTerms.GetCount() - 1)
		self.EditTerm()
		self.LoadTerms()

	def btnAddTermClicked(self,event):
		myterm = NewTermDialog(self)
		myterm.ShowModal()
		myterm.Destroy()

	def btnAddObjectiveClicked(self,event):
		self.CurrentObj = ""
		EClassObjectiveEditorDialog(self)
		if len(self.CurrentObj) > 0:
			self.page.objectives.append(self.CurrentObj)
		self.LoadObjectives()

	def btnEditTermClicked(self,event):
		self.EditTerm()

	def btnEditObjectiveClicked(self,event):
		index = self.page.objectives.index(self.lstObjectives.GetStringSelection())
		self.CurrentObj = self.page.objectives[index]
		result = EClassObjectiveEditorDialog(self).GetReturnCode()
		if result == wx.ID_OK:
			self.page.objectives[index] = self.CurrentObj
			self.LoadObjectives()
		else:
			print "Error: result =", result

	def EditTerm(self):
		myterm = self.lstTerms.GetClientData(self.lstTerms.GetSelection())
		if myterm.type == "URL":
			EClassHyperlinkEditorDialog(self, myterm)
		else:
			dialog = EditorDialog(self, myterm)
			dialog.ShowModal()
		self.LoadTerms()

	def btnRemoveTermClicked(self,event):	
		myterm = self.lstTerms.GetClientData(self.lstTerms.GetSelection())
		result = wx.MessageDialog(self, _("Are you sure you want to delete the term '%(term)s'?") % {"term":myterm.name}, _("Delete Term?"), wx.YES_NO).ShowModal()	 
		if result == wx.ID_YES:
			self.page.terms.remove(myterm)
			self.LoadTerms()

	def btnRemoveObjectiveClicked(self,event):	
		index = self.page.objectives.index(self.lstObjectives.GetStringSelection())
		obj = self.page.objectives[index]
		result = wx.MessageDialog(self, _("Are you sure you want to delete the objective '%(objective)s'?") % {"objective":obj}, _("Delete Objective?"), wx.YES_NO).ShowModal()	 
		if result == wx.ID_YES:
			self.page.objectives.remove(obj)
			self.LoadObjectives()

	def btnOKClicked(self,event):
		busy = wx.BusyCursor()
		self.page.name = self.txtTitle.GetValue()
		if isinstance(self.item, conman.conman.ConNode):
			self.item.content.metadata.name = self.page.name
		else:
			self.item.name = self.page.name

		#self.page.author = self.txtAuthor.GetValue()
		if self.isHotword:
			self.page.author = self.txtAuthor.GetValue()
		else:
			author = self.item.content.metadata.lifecycle.getAuthor()
			if not author:
				self.item.content.metadata.lifecycle.addContributor(self.txtAuthor.GetValue(), "Author")
				author = self.item.content.metadata.lifecycle.getAuthor()
		
			author.entity.fname.value = self.txtAuthor.GetValue()
			if author.entity.filename == "":
				afilename = os.path.join(self.parent.PrefDir, "Contacts", fileutils.MakeFileName2(author.entity.fname.value) + ".vcf")
				author.entity.filename = afilename
			
			author.entity.saveAsFile()

		if self.isHotword:
			self.page.credit = self.txtCredit.GetValue()
		else:
			self.item.content.metadata.rights.description = self.txtCredit.GetValue()
		self.page.media.image = self.selectImage.filename
		self.page.media.video = self.selectVideo.filename
		if self.chkVideoAutostart.IsChecked():
			self.page.media.videoautostart = 1
		else:
			self.page.media.videoautostart = 0

		self.page.media.audio = self.selectAudio.filename
		if self.chkAudioAutostart.IsChecked():
			self.page.media.audioautostart = 1
		else:
			self.page.media.audioautostart = 0		
		#self.page.media.Introduction = self.selectIntroduction.filename
		self.page.media.text = self.selectText.filename
		self.page.media.powerpoint = self.selectPowerPoint.filename
		
		missingfiles = []
		filenames = []
		if len(self.page.media.image) > 0:
			filenames.append(os.path.join(settings.ProjectDir, "Graphics", self.page.media.image))
		if len(self.page.media.video) > 0:
			filenames.append(os.path.join(settings.ProjectDir, "pub", "Video", self.page.media.video))
		if len(self.page.media.audio) > 0:
			filenames.append(os.path.join(settings.ProjectDir, "pub", "Audio", self.page.media.audio))
		if len(self.page.media.text) > 0:
			filenames.append(os.path.join(settings.ProjectDir, "Text", self.page.media.text))
		if len(self.page.media.powerpoint) > 0:
			filenames.append(os.path.join(settings.ProjectDir, "Present", self.page.media.powerpoint))

		for file in filenames:
			if not os.path.exists(file):
				missingfiles.append(file)

		if len(missingfiles) > 0:
			filelist = ""
			for file in missingfiles:
				filelist = filelist + file + "\n"

			message = _("The following files could not be found:\n\n %(filelist)s \n\nWould you still like to save and exit this page?") % {"filelist":filelist}
			result = wx.MessageDialog(self, message, _("Missing files"), wx.YES_NO).ShowModal()
			if result == wx.ID_NO:
				return

		if isinstance(self.item, conman.conman.ConNode):
			if len(self.filename) > 0:
				filename = os.path.join(self.parent.ProjectDir, "EClass", os.path.basename(self.filename))
				try:
					self.page.SaveAsXML(filename,self.mainform.encoding)
				except IOError, e:
					global log
					message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":filename})
					log.write(message)
					wx.MessageDialog(self, message, _("File Write Error"), wx.OK).ShowModal()
					return
			else:
				myfilename = os.path.join(self.parent.ProjectDir, "EClass", utils.suggestFileName(self.page.name + ".ecp"))
				self.item.content.filename = myfilename
				try: 
					self.page.SaveAsXML(os.path.join(self.parent.ProjectDir, "EClass", myfilename),self.mainform.encoding)
				except IOError, e:
					import traceback
					print `traceback.print_exc()`
					wx.MessageDialog(self, str(e), _("File Write Error"), wx.OK).ShowModal()
					return

			eclassPub = HTMLPublisher()
			try:
				#filename = eclassPub.Publish(self.parent, self.parent.CurrentItem, self.parent.ProjectDir)
				#self.parent.Preview(filename)
				del busy
			except Exception, ex:
				del busy
				message = _("There was an error publishing the EClass Page to HTML. Please check to make sure you have sufficient disk space, have write permission to the 'pub' directory, and that the page does not contain any foreign characters.")
				global log
				log.write(message)
				wx.MessageDialog(self, message, _("Publishing Error")).ShowModal()
			
		self.EndModal(wx.ID_OK)

class NewTermDialog(wx.Dialog):
	"""
	Class: eclass.NewTermDialog(wx.Dialog)
	Last Updated: 9/24/02
	Description: This dialog creates a new term using the options specified by the user.
	
	Attributes:
	- parent: the window that called the dialog
	- txtName: textbox for storing hotword name
	- cmbType: combobox for hotword type
	- btnOK: OK button

	Methods:
	- btnOKClicked: Creates the new term, passes control back to the claling window, and closes the dialog
	"""
	def __init__(self, parent):
		wx.Dialog.__init__ (self, parent, -1, _("Create New Hotword"),
						 wx.DefaultPosition,
						   wx.DefaultSize, 
						   wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE)

		self.parent = parent
		self.lblName = wx.StaticText(self, -1, _("Name")) #wx.Point(10, 10))
		self.lblType = wx.StaticText(self, -1, _("Type"))#,wx.Point(10,30))

		choices = [_("EClass Page"), _("Link to File")]
		self.txtName = wx.TextCtrl(self, -1, "", wx.Point(40, 10), wx.Size(160, -1))
		self.cmbType = wx.Choice(self, -1, wx.Point(40, 30), wx.Size(160, -1), choices)
		self.cmbType.SetSelection(1)
		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"),wx.DefaultPosition,wx.DefaultSize)
		self.btnOK.SetDefault()
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"),wx.DefaultPosition,wx.DefaultSize)
	
		self.mysizer = wx.BoxSizer(wx.VERTICAL)
		self.flexsizer = wx.FlexGridSizer(0, 2, 4, 4)
		self.flexsizer.Add(self.lblName, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.flexsizer.Add(self.txtName, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.flexsizer.Add(self.lblType, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.flexsizer.Add(self.cmbType, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.mysizer.Add(self.flexsizer, 0, wx.LEFT|wx.RIGHT, 10)
		
		self.buttonsizer = wx.StdDialogButtonSizer()
		self.buttonsizer.AddButton(self.btnOK)
		self.buttonsizer.AddButton(self.btnCancel)
		self.buttonsizer.Realize()
		self.mysizer.Add(self.buttonsizer, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		
	def btnOKClicked(self, event):
		myterm = EClassTerm()
		if not self.txtName.GetValue() == "":
			myterm.name = self.txtName.GetValue()
			type = self.cmbType.GetStringSelection()
			if type == _("EClass Page"):
				myterm.type = "Page"
				myterm.NewPage()
			else:
				myterm.type = "URL"
			self.EndModal(wx.ID_OK)
			self.parent.AddTerm(myterm)
		else:
			wx.MessageDialog(self, _("Please enter a name for your hotword, or click Cancel to exit without creating a hotword."), _("Please enter a name"), wx.OK).ShowModal()	 

def strict(char):
	print "Unicode Error on character: " + chr(char)

if __name__ == "__main__":
	pass
