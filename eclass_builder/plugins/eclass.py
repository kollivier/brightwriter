from wxPython.wx import *
import string
import os
#import conman.conman as conman
import conman
import locale
import re
from conman.validate import *
from conman import plugins
from conman.HTMLFunctions import *
from conman.HTMLTemplates import *
from StringIO import StringIO

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

#-------------------------- PLUGIN REGISTRATION ---------------------
# This info is used so that EClass can be dynamically be added into
# EClass.Builder's plugin registry.
plugin_info = {	"Name":"eclass", 
				"FullName":"EClass Page", 
				"Directory":"EClass", 
				"Extension":["ecp"], 
				"Mime Type": "",
				"Requires":"", 
				"CanCreateNew":True}

#-------------------------- DATA CLASSES ----------------------------

EVT_RESULT_ID = wxNewId()

def EVT_RESULT(win, func):
	win.Connect(-1, -1, EVT_RESULT_ID, func)

def CreateNewFile(name, filename):
	try:
		file = EClassPage()
		file.name = name
		file.SaveAsXML(filename)
		return True
	except:
		return False
		
class EClassPage:
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
		self.encoding = "ISO-8859-1"
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

	def __setattr__(self, name, value):
		if not name == "encoding" and isinstance(value, str) or isinstance(value, unicode):
			self.__dict__[name] = value.encode(self.encoding, 'replace')
		else:
			self.__dict__[name] = value

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
				doc = minidom.parse(open(filename))
			else:	
				doc = FromXmlFile(filename)
			self.LoadDoc(doc)
		except:
			print traceback.print_exc()
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
						print "Could not load hotword page for", myterm.name
				else:
					myterm.page = None
	
				self.terms.append(myterm)
			#	
		#	mythread = HotwordLoader(self)
		#	mythread.run(terms)

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
			return "The EClass page file cannot be loaded from disk. The error message is: " + `sys.exc_value.args`

		if len(doc.getElementsByTagName("Terms")) > 0:
			terms = []
			node = doc.getElementsByTagName("Terms")[0]
			for child in node.childNodes:
				if (child.nodeType == node.ELEMENT_NODE and child.tagName == "Term"):
					terms.append(child)
				
			#mythread = HotwordLoader(self)
			#mythread.run(terms)

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

#			if root.getElementsByTagName("Codigo_pub"):
#				self.codigo_pub = XMLCharToText(root.getElementsByTagName("Codigo_pub")[0].childNodes[0].nodeValue)
#			else:
#				self.codigo_pub = ""
				
#			if root.getElementsByTagName("Fecha_pub"):
#				self.fecha_pub = XMLCharToText(root.getElementsByTagName("Fecha_pub")[0].childNodes[0].nodeValue)
#			else:
#				self.fecha_pub = ""

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
			myxml = """<?xml version="1.0" encoding="%s"?>%s""" % (encoding, self.WriteDoc())
		except:
			message = "There was an error updating the file " + filename + ". Please check to make sure you did not enter any invalid characters (i.e. Russian, Chinese/Japanese, Arabic) and try updating again."
			print message
			raise IOError, message
		try:
			myfile = open(filename, "w")
			myfile.write(myxml)
			myfile.close()
		except:
			message = "There was an error writing the file " + filename + " to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file."
			print `message`
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
			myobj = myobj + "<Objective>" + TextToXMLChar(obj).encode(self.encoding, 'replace') + "</Objective>"
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

class HotwordLoader(Thread):
	"""
	Class: eclass.HotwordLoader(Thread)
	Last Updated: 9/24/02
	Description: This class loads hotwords in a thread, to ensure GUI processing can continue. This class is not currently used and needs further testing.

	Attributes:
	- parent: the parent wxWindow to send status messages to and receive input from
	- cancelload: boolean specifying whether or not to abort the process

	Methods:
	- run(terms): Given a list of terms in XML format, loads them into the hotword data structures
	- cancel(): sets the cancelload variable to signal processing to stop
	"""
	def __init__(self, parent):
		Thread.__init__(self)
		self.parent = parent
		self.cancelload = 0

	def run(self, terms):
		self.parent.hotwordsloaded = 0
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
				#print "now value is: " + myterm.url
				else:
					myterm.url = ""
			else:
				myterm.url = ""

			if term.getElementsByTagName("Page"):
				myterm.LoadPage(term.getElementsByTagName("Page")[0])
			else:
				myterm.page = None

			self.parent.terms.append(myterm)
			
			if self.cancelload:
				return #exit immediately
			if self.parent.window != None:
				print "Loaded hotword " + myterm.name
				wxPostEvent(self.parent.window,ResultEvent(myterm.name, self.parent.terms.index(myterm)))

	def cancel(self):
		self.cancelload = 1

class ResultEvent(wxPyEvent):
	def __init__(self, hwname, hwid):
		wxPyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)
		self.hwname = hwname
		self.hwid = hwid
	
class EClassMedia:
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
		self.encoding = "ISO-8859-1"
		self.image = ""
		self.audio = ""
		self.audioautostart = False
		self.video = ""
		self.videoautostart = False
		self.introduction = ""
		self.text = ""
		self.powerpoint = ""
		self.name = ""

	def __setattr__(self, name, value):
		if not name == "encoding" and isinstance(value, str) or isinstance(value, unicode):
			self.__dict__[name] = value.encode(self.encoding, 'replace')
		else:
			self.__dict__[name] = value

class EClassTerm:
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
		self.encoding = "ISO-8859-1"
		self.name = ""
		self.type = ""
		self.url = ""
		self.page = None

	def __setattr__(self, name, value):
		if not name == "encoding" and isinstance(value, str) or isinstance(value, unicode):
			self.__dict__[name] = value.encode(self.encoding, 'replace')
		else:
			self.__dict__[name] = value
	
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
		print filename
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
				html = self._CreateEClassPage(term.page, myfilename, True)
			elif term.type == "URL":
				myfilename = term.url
				basename = os.path.basename(myfilename)
				myname, myext = os.path.splitext(basename)
				#print "myname = " + myfilename + "\nlength of myname is: " + `len(myname)` + "len of myext is: " + `len(myext)` + "\n"
				if len(basename) > 31:
					if self.parent.pub.settings["ShortenFilenames"] == "":
						message = _("EClass has detected filenames containing more than 31 characters in the EClass Page '%(pagename)s. This could cause compatibility problems with older browsers and operating systems. Would you like EClass to automatically rename these files?") % {"pagename":mypage.name}
						mydialog = wxMessageDialog(self.parent, message, _("Rename file?"), wxYES_NO)
						if mydialog.ShowModal() == wxID_YES:
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
			if 1: #string.find(os.path.split(string.lower(mypage.media.text))[1], "htm") != -1:
				myfile = open(os.path.join(self.dir, "Text", mypage.media.text), 'r')
			else: 
				#It might be a Word/RTF document, try to convert...
				convert = True
				myfilename = os.path.join(self.dir, "Text", mypage.media.text)
				if wxPlatform == "__WXMSW__":
					import win32api
					myfilename = win32api.GetShortPathName(myfilename)
				if 1:
					#openofficedir = self.parent.settings["OpenOffice"]
					#if openofficedir != "" and os.path.exists(os.path.join(openofficedir, "program", "uno.py")):
						#programdir = os.path.join(openofficedir, "program")
						#sys.path.append(programdir)
						#os.environ['PATH'] = os.environ['PATH'] + ";" + programdir
					import converter
						
					myconverter = converter.DocConverter(self.parent)
					thefilename = myconverter.ConvertFile(myfilename, "html")
					if thefilename == "":
						wxMessageBox("Unable to convert file " + mypage.media.text)
					myfile = open(thefilename, 'r')
				else:
					import traceback
					print traceback.print_exc()
					myhtml = ""
				
			if myfile:
				myhtml = GetBody(myfile)
				myfile.close()

			if convert:
				myhtml = ImportFiles().ImportLinks(myhtml, os.path.join(os.getcwd(), "temp"), self.dir)
		else:
			myhtml = ""
		objtext = ""
		myhtml = self._InsertTerms(myhtml, termlist)
		
		if len(mypage.objectives) > 0:
			objtext = "<hr><h2>" + _("Objectives") + "</h2><ul>"
			for obj in mypage.objectives:
				objtext = objtext + "<li>" + TextToXMLChar(obj) + "</li>"
			objtext = objtext + "</ul><hr>"

		try:
			myhtml = self._AddMedia(mypage) + objtext + myhtml
			
		except UnicodeError:
			raise

		try: 
			importer = ImportFiles
			myhtml2 = importer.ImportLinks(myhtml, os.path.join(self.dir, "Text"), self.dir)
			myhtml = myhtml2
		except:
			pass

		if not ishotword:
			self.data['content'] = myhtml
			creditstring = ""
			if len(mypage.credit) > 0:
				mypage.credit = string.replace(mypage.credit, "\r\n", "<br>")#mac
				mypage.credit = string.replace(mypage.credit, "\n", "<br>")#win
				mypage.credit = string.replace(mypage.credit, "\r", "<br>")#unix
				mypage.credit = mypage.credit + "<h5 align=\'center\'>[ <a href=\'javascript:window.close()\'>" + _("Close") + "</a> ]</h5>"
				mypage.credit = string.replace(mypage.credit, "'", "\\'")
				creditstring = """[ <b><a href="javascript:openCredit('newWin','%(credit)s')">%(credittext)s</a></b> ]""" % {"credit":TextToHTMLChar(mypage.credit), "credittext":_("Credit")}	
			self.data['credit'] = "<h5>" + mypage.author + " " + creditstring + "</h5>"
		else: #ugly hack for now...
			if self.node.content.template == None or self.node.content.template == "None":
				self.node.content.template = "Default"

			try:
				myhtml = self._CreateHTMLShell(mypage, self.node, myhtml, ishotword)
			except UnicodeError:
				raise

			try:		
				myfile = open(os.path.join(self.dir, "pub",filename), "w")
				myfile.write(myhtml)
				myfile.close()
			except: 
				message = _("There was an error writing the file '%(filename)s' to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file.") % {"filename":filename}
				print `message`
				raise IOError, message
				return False	
		return myhtml

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
 
		if len(mypage.media.image) > 0 and os.path.exists(os.path.join(self.dir, "Graphics", mypage.media.image)):
			imageHTML = "<IMG src='../Graphics/%s'>" % (mypage.media.image)
		
		if len(mypage.media.video) > 0 and os.path.exists(os.path.join(self.dir, "Video", mypage.media.video)):
			template = ""
			if string.find(string.lower(mypage.media.video), ".mpg") != -1 or string.find(string.lower(mypage.media.video), ".mpeg") != -1:
				template = wmTemp
				mimetype = "video/x-ms-asf-plugin" 
			if string.find(string.lower(mypage.media.video), ".wmv") != -1:
				template = wmTemp
				mimetype = "video/x-ms-asf" 
			elif string.find(string.lower(mypage.media.video), ".avi") != -1:
				template = wmTemp
				mimetype = "application/x-mplayer2"
			elif string.find(string.lower(mypage.media.video), ".asf") != -1:
				template = wmTemp
				mimetype = "video/x-ms-asf"
			elif string.find(string.lower(mypage.media.video), ".rm") != -1 or string.find(string.lower(mypage.media.video), ".ram") != -1:
				template = rmVideoTemp
				mimetype = "application/vnd.rn-realmedia"
			elif string.find(string.lower(mypage.media.video), ".mov") != -1:
				template = qtTemp
				mimetype = "video/quicktime"
			elif string.find(string.lower(mypage.media.video), ".swf") != -1:
				template = flashTemp
				mimetype = "application/x-shockwave-flash"

			videoHTML = string.replace(template, "_filename_", "../Video/" + mypage.media.video)
			autostart = "False"
			if mypage.media.videoautostart == True:
				autostart = "True"
			videoHTML = string.replace(videoHTML, "_autostart_", autostart)
			videoHTML = string.replace(videoHTML, "_mimetype_", mimetype)

		if len(mypage.media.audio) > 0 and os.path.exists(os.path.join(self.dir, "Audio", mypage.media.audio)):
			template = ""
			if string.find(string.lower(mypage.media.audio), ".wma") != -1:
				template = wmTemp
				mimetype = "audio/x-ms-asf" 
			elif string.find(string.lower(mypage.media.audio), ".wav") != -1:
				template = wmTemp
				mimetype = "audio/wav"
			elif string.find(string.lower(mypage.media.audio), ".mp3") != -1:
				template = wmTemp
				mimetype = "audio/mp3"
			elif string.find(string.lower(mypage.media.audio), ".asf") != -1:
				template = wmTemp
				mimetype = "audio/x-ms-asf"
			elif string.find(string.lower(mypage.media.audio), ".rm") != -1 or string.find(string.lower(mypage.media.audio), ".ram") != -1:
				template = rmAudioTemp
				mimetype = "application/vnd.rn-realmedia"
			elif string.find(string.lower(mypage.media.audio), ".mov") != -1:
				template = qtTemp
				mimetype = "video/quicktime"

			audioHTML = string.replace(template, "_filename_", "../Audio/" + mypage.media.audio)
			autostart = "False"
			if mypage.media.audioautostart == True:
				autostart = "True"
			audioHTML = string.replace(audioHTML, "_autostart_", autostart)
			audioHTML = string.replace(audioHTML, "_mimetype_", mimetype)

		if len(mypage.media.powerpoint) > 0 and os.path.exists(os.path.join(self.dir, "Present", mypage.media.powerpoint)):
			presentHTML = """<a href="../Present/%(pres)s" target="_blank">%(viewpres)s</a>""" % {"pres":mypage.media.powerpoint, "viewpres":_("View Presentation")}
	
		if len(imageHTML) > 0 and len(videoHTML) > 0:
			HTML = HTML + """<CENTER>
<table border="0" cellpadding="2" cellspacing="4">
<td align="center" valign="top">%s</td>
<td align="center" valign="top">%s</td>
</table></CENTER>
""" % (imageHTML, videoHTML)
		elif len(mypage.media.image) > 0 or len(mypage.media.video) > 0:
			if len(mypage.media.image) > 0:
				vidimage = imageHTML
			else:
				vidimage = videoHTML

			HTML = HTML + """<p align="center">%s</p>""" % (vidimage)

		if len(mypage.media.audio) > 0:
			HTML = HTML + "<br>%s" % (audioHTML)

		if len(mypage.media.powerpoint) > 0:
			HTML = HTML + "<br><h3 align=\"center\">%s</h3>" % (presentHTML)
		
		return HTML

	def _CreateHTMLShell(self, mypage, node, content, ishotword=False):
		template = "default.tpl"
		temp = open(os.path.join(self.parent.AppDir, "themes", self.parent.currentTheme[0], template), "r")

		html = unicode(temp.read(), 'iso8859-1', 'replace')
		temp.close()
		#print "in create html shell, my name = " + mypage.name
		html = string.replace(html, "--[name]--", TextToHTMLChar(mypage.name))
		html = string.replace(html, "--[description]--", TextToXMLAttr(node.content.description))
		html = string.replace(html, "--[keywords]--", TextToXMLAttr(node.content.keywords))
		html = string.replace(html, "--[URL]--", "pub/" + self.GetFilename(node.content.filename))
		html = string.replace(html, "--[content]--", content)

		if not ishotword:
			backnode = node.back()
			#since we're publishing, we only want public nodes
			while backnode != None and backnode.content.public != "True":
				backnode = backnode.back()
			backlink = ""
			if backnode != None:
				backlink = self.GetFilename(backnode.content.filename)
				
				html = string.replace(str(html), "--[backlink]--", "<a href=\"" + backlink + "\">" + _("Back") + " </a>")
			else:
				html = string.replace(str(html), "--[backlink]--", "")

			nextnode = node.next()
			while nextnode != None and nextnode.content.public != "True":
				nextnode = nextnode.next()

			if nextnode != None:
				nextlink = self.GetFilename(nextnode.content.filename)
				html = string.replace(str(html), "--[nextlink]--", "<a href=\"" + nextlink + "\">" + _("Next") + " </a>")
			else:
				html = string.replace(str(html), "--[nextlink]--", "")
		else:
			html = string.replace(str(html), "--[backlink]--", "<a href=\"javascript:window.close()\">" + _("Close") + "</a>")
			html = string.replace(str(html), "--[nextlink]--", "")
		
		creditstring = ""
		if len(mypage.credit) > 0:
			mypage.credit = string.replace(mypage.credit, "\r\n", "<br>")#mac
			mypage.credit = string.replace(mypage.credit, "\n", "<br>")#win
			mypage.credit = string.replace(mypage.credit, "\r", "<br>")#unix
			mypage.credit = mypage.credit + "<h5 align=\'center\'>[ <a href=\'javascript:window.close()\'>" + _("Close") + "</a> ]</h5>"
			mypage.credit = string.replace(mypage.credit, "'", "\\'")
			creditstring = """[ <b><a href="javascript:openCredit('newWin','%s')">%s</a></b> ]""" % (TextToHTMLChar(mypage.credit), _("Credit"))	
		html = string.replace(str(html), "--[credit]--", "<h5>" + mypage.author + " " + creditstring + "</h5>")
		return html

class PDFPublisher:
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

	def _CreateEClassPage(self, mypage, filename, ishotword=False):
		myhtml = ""
		if len(mypage.media.text) > 0 and os.path.exists(os.path.join(self.dir, "Text", mypage.media.text)):
			myfile = None
			convert = False
			if string.find(os.path.split(mypage.media.text)[1], "htm") != -1:
				myfile = open(os.path.join(self.dir, "Text", mypage.media.text), 'r')
			else: #try to convert...
				convert = True
				myfilename = os.path.join(self.dir, "Text", mypage.media.text)
				if wxPlatform == "__WXMSW__":
					import win32api
					myfilename = win32api.GetShortPathName(myfilename)
				try:
					openofficedir = self.parent.settings["OpenOffice"]
					if openofficedir != "" and os.path.exists(os.path.join(openofficedir, "program", "uno.py")):
						programdir = os.path.join(openofficedir, "program")
						sys.path.append(programdir)
						os.environ['PATH'] = os.environ['PATH'] + ";" + programdir
						import converter
						
						myconverter = converter.DocConverter(self.parent)
						thefilename = myconverter.ConvertFile(myfilename, "html")
						if thefilename == "":
							wxMessageBox(_("Unable to convert file %(filename)s") % {"filename":mypage.media.text})
						myfile = open(thefilename, 'r')
				except:
					import traceback
					print traceback.print_exc()
					myhtml = ""
				
			if myfile:
				myhtml = GetBody(myfile)
				myfile.close()
		else:
			myhtml = ""
		objtext = ""
		
		if len(mypage.objectives) > 0:
			objtext = "<hr><h2>" + _("Objectives") + "</h2><ul>"
			for obj in mypage.objectives:
				objtext = objtext + "<li>" + TextToXMLChar(obj) + "</li>"
			objtext = objtext + "</ul><hr>"

		try:
			myhtml = self._AddMedia(mypage) + objtext + myhtml
			
		except UnicodeError:
			raise

		return myhtml



		return True
#-------------------------- EDITOR INTERFACE ----------------------------------------

class wxSelectBox:
	"""
	Class: eclass.wxSelectBox
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

	def __init__(self, parent, title, filename, type, x, y, length=120):
		self.parent = parent
		self.filename = filename
		self.type = type
		self.title = title
		self.dir = self.parent.mainform.CurrentDir
		self.selecteddir = ""
		icnFolder = wxBitmap(os.path.join(self.parent.mainform.AppDir, "icons", "Open.gif"), wxBITMAP_TYPE_GIF)
		self.label = wxStaticText(parent, -1, title, wxPoint(x, y+4))
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.textbox = wxTextCtrl(parent, -1, filename, wxPoint(x+70, y), wxSize(length,-1))
		self.selectbtn = wxBitmapButton(parent, -1, icnFolder, wxPoint(x+length+72, y+2), wxSize(20, 18))

		EVT_BUTTON(self.selectbtn, self.selectbtn.GetId(), self.selectbtnClicked)
		EVT_TEXT(self.textbox, self.textbox.GetId(), self.textboxChanged)

	def selectbtnClicked(self, event):
		hyperlink = False
		if self.type == "Graphics":
			filter = _("Image Files") + "(*.jpg,*.gif,*.bmp,*.png)|*.jpg;*.jpeg;*.gif;*.bmp;*.png"
		elif self.type == "Video":
			filter = _("Video Files") + "(*.avi,*.mov,*.mpg,*.asf,*.wmv,*.rm, *.ram, *.swf)|*.avi;*.mov;*.mpg;*.mpeg;*.asf;*.wmv;*.rm;*.ram;*.swf"
		elif self.type == "Audio":
			filter = _("Audio Files") + "(*.wav,*.aif,*.mp3,*.asf,*.wma,*.rm,*.ram)|*.wav;*.aif;*.mp3;*.asf;*.wma;*.rm;*.ram"
		elif self.type == "Text":
			filter = _("Document Files") + "(*.htm,*.html)|*.htm;*.html"
		elif self.type == "Present":
			filter = _("Presentation Files") + "(*.ppt,*.htm,*.html,*.swf)|*.ppt;*.htm;*.html;*.swf"
		else:
			hyperlink = True
			self.type = "File"
			filter = _("All Files") + "(*.*)|*.*"

		f = wxFileDialog(self.parent, _("Select a file"), os.path.join(self.parent.CurrentDir, self.type), "", filter, wxOPEN)
		if f.ShowModal() == wxID_OK:
			self.selecteddir = f.GetDirectory()

			if string.find(f.GetPath(), os.path.join(self.parent.mainform.CurrentDir, self.type)) == -1:
				destdir = os.path.join(self.parent.mainform.CurrentDir,self.type)
				self.CopyFile(f.GetPath(), f.GetFilename(), destdir)
									
			if hyperlink:
				result = False
				if len(f.GetFilename()) > 31 and self.parent.mainform.pub.settings["ShortenFilenames"] == "":
					message = _("This filename contains more than 31 characters. This could cause compatibility problems with older browsers and operating systems. Would you like EClass to automatically rename the file?")
					dialog = wxMessageDialog(self.parent, message, _("Rename File?"), wxYES_NO)			
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
					os.rename(os.path.join(self.dir, "File", oldfilename), os.path.join(self.dir, "File", myfilename))
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
			file = open(path, "rb")
			data = file.read()
			if not string.find(filename, ".htm") == -1:
				importer = ImportFiles()
				data = importer.ImportLinks(data, self.selecteddir, self.parent.mainform.CurrentDir)
			file.close()
		except IOError:
			error = True
			message =  _("Could not read file '%(filename)s from disk. Please check that the file exists in the location specified and that you have permission to open/view the file.") % {"filename":path} 
			print message
			if showgui:
				wxMessageDialog(self.parent, message, _("File Read Error"), wxOK).ShowModal()
				
		if not error:
			if not os.path.exists(destdir):
				os.mkdir(destdir)
			try:
				self.parent.mainform.SetStatusText(_("Pasting %(filename)s...") % {"filename":os.path.join(destdir, filename)})
				out = open(os.path.join(destdir, filename), "wb")
				out.write(data)
				out.close()
			except IOError:
				message = _("EClass.Builder could not write the file '%(filename)s' to disk. Please check that '%(directory)s' exists and you have permissions to write to this folder, and that a read-only version of the file does not exist in this folder.") % {"filename":os.path.join(destdir, filename),"directory":destdir}
				print message
				if showgui:
					wxMessageDialog(self, message, _("File Write Error."), wxOK).ShowModal()
		self.parent.mainform.SetStatusText("")

	def textboxChanged(self, event):
		self.filename = self.textbox.GetValue()
		#print self.filename

class EClassObjectiveEditorDialog(wxDialog):
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
		wxDialog.__init__ (self, parent, -1, _("Objective Editor"),
						 wxDefaultPosition,
						   wxSize(200,150),
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.txtObj = wxTextCtrl(self, -1, parent.CurrentObj, wxPoint(10, 5), wxSize(180, 80), wxTE_MULTILINE)
		self.btnOK = wxButton(self,wxID_OK,_("OK"),wxPoint(30, 100),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.txtObj.SetFocus()
		self.txtObj.SetSelection(0, -1)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"),wxPoint(110, 100),wxSize(76,24))
		
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.txtObj, 1, wxEXPAND)

		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add((100, 25), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonsizer, 0)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)

		self.ShowModal()

	def btnOKClicked(self, event):
		if len(self.txtObj.GetValue()):	
			self.parent.CurrentObj = self.txtObj.GetValue().encode(self.parent.mainform.encoding, 'replace')
			self.EndModal(wxID_OK)
		else:
			wxMessageDialog(self, _("Please enter some text for your objective, or click Cancel to quit."), _("Empty Objective"), wxICON_INFORMATION | wxOK).ShowModal() 

class EClassHyperlinkEditorDialog(wxDialog):
	"""
	Class: eclass.EClassHyperlinkEditorDialog(wxDialog)
	Last Updated: 9/24/002
	Description: Dialog for editing hyperlink hotwords.

	Attributes:
	- parent: the parent window which called the dialog
	- term: the hotword to be edited
	- txtName: textbox to edit hotword name
	- selectFile: wxSelectBox to choose the file to link to
	- btnOK: OK button
	
	Methods:
	-btnOKClicked: Updates hotword information and closes dialog
	"""

	def __init__(self, parent, term):
		wxDialog.__init__ (self, parent, -1, _("Hyperlink Editor"),
						 wxDefaultPosition,
						   wxSize(300,120),
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25

		self.parent = parent
		self.mainform = parent.mainform
		self.CurrentDir = parent.CurrentDir
		self.term = term
		self.lblName = wxStaticText(self, -1, _("Name"), wxPoint(10, 5))
		self.txtName = wxTextCtrl(self, -1, term.name, wxPoint(80, 5), wxSize(180, -1))
		self.selectFile = wxSelectBox(self, _("Link Address"), term.url, _("Link"), 10, 30, 180)
		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(130, 60),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.txtName.SetFocus()
		self.txtName.SetSelection(0, -1)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))
		
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.filesizer = wxFlexGridSizer(0, 3, 4, 4)
		self.filesizer.Add(self.lblName, 0, wxALIGN_LEFT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.filesizer.Add(self.txtName, 0, wxALIGN_CENTER|wxALL, 4)
		self.filesizer.Add((10, 25), 0)
		self.filesizer.Add(self.selectFile.label, 0, wxALIGN_LEFT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.filesizer.Add(self.selectFile.textbox, 0, wxALIGN_CENTER|wxALL, 4)
		self.filesizer.Add(self.selectFile.selectbtn, 0, wxALIGN_CENTER|wxALL, 4)
		self.mysizer.Add(self.filesizer)
		
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add((100, height), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonsizer, 0, wxEXPAND)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)

		self.ShowModal()

	def btnOKClicked(self, event):
		self.term.name = self.txtName.GetValue()
		self.term.url = self.selectFile.textbox.GetValue()
		self.EndModal(wxID_OK)

#--------------------------- E-Class Page Editor Class ------------------------------------
class EditorDialog (wxDialog):
	"""
	Class: EditorDialog
	Last Updated: 10/21/02
	Description: This dialog lets users edit the selected EClassPage. 

	Attributes:
	- item: the ConNode selected on the main EClass editor, or an EClassPage
	- parent: the parent window that called this dialog
	- mainform: the main window of the application - needed to update status messages
	- CurrentDir: the root directory of the currently selected node
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
		if wxPlatform == "__WXMAC__":
			height = 25
		busy = wxBusyCursor()
		self.item = item
		self.parent = parent
		# We need to have a pointer to the main frame to get global settings
		if isinstance(parent, wxFrame):
			self.mainform = parent
		else:
			self.mainform = parent.mainform
		self.CurrentObj = None
		loaded = True 

		#check if ConNode or if EClassPage
		if isinstance(item, conman.conman.ConNode):
			self.CurrentDir = item.dir 
			self.filename = item.content.filename
			self.page = EClassPage(self)
			if len(self.filename) > 0:
				
				if not os.path.exists(os.path.join(self.CurrentDir, "EClass", os.path.basename(self.filename))):
					self.page.SaveAsXML(os.path.join(self.CurrentDir, "EClass", os.path.basename(self.filename)))

				try:
					self.page.LoadPage(os.path.join(self.CurrentDir, "EClass", os.path.basename(self.filename)))
					item.content.filename = self.filename
				except RuntimeError, e:
					wxMessageDialog(parent, _("There was an error loading the EClass page '%(page)s'. The error reported by the system is: %(error)s") % {"page":os.path.join(parent.CurrentDir, "EClass", self.filename), "error":str(e)}, _("Error loading page"), wxOK).ShowModal()
					print e
					del busy
					return
			else:
				myfilename = MakeFileName(os.path.join(self.parent.CurrentDir, "EClass"), self.page.name)
				self.filename = item.content.filename = myfilename
				try:
					self.page.SaveAsXML(os.path.join(self.parent.CurrentDir, "EClass", myfilename))
				except IOError, e:
					wxMessageDialog(self, _("There was an error saving the EClass page '%(page)s'. The error message returned by the system is: %(error)s") % {"page":os.path.join(self.parent.CurrentDir, "EClass", myfilename), "error":str(e)}, _("File Write Error"), wxOK)

			self.page.name = item.content.metadata.name
		else:
			self.CurrentDir = self.parent.CurrentDir
			self.page = item.page
		
		wxDialog.__init__ (self, parent, -1, _("EClass Page Editor"),
						 wxPoint(100, 100),
						   wxDefaultSize,
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)

		#mytuple = self.parent.GetPositionTuple()
		#self.MoveXY(mytuple[0] + 30, mytuple[1] + 30)
		self.lblTitle = wxStaticText(self, -1, _("Name"), wxPoint(10, 5))
		self.lblAuthor = wxStaticText(self, -1, _("Author:          "),wxPoint(10,5 + height))
		self.lblCredit = wxStaticText(self, -1, _("Credit"), wxPoint(10, 5 + (height*2)))
		
		self.txtTitle = wxTextCtrl(self, -1, self.page.name, wxPoint(80, 5), wxSize(280, -1))
		self.txtAuthor = wxTextCtrl(self, -1, self.page.author, wxPoint(80, 25), wxSize(280, -1))
		self.txtCredit = wxTextCtrl(self, -1, self.page.credit, wxDefaultPosition, wxSize(280, height*3), wxTE_MULTILINE)

		#Left Input Labels
		self.selectImage = wxSelectBox(self, _("Image:"), self.page.media.image, _("Graphics"), 10, 100, 160)
		self.selectVideo = wxSelectBox(self, _("Video:"), self.page.media.video, _("Video"), 10, 100 + height, 160)
		self.chkVideoAutostart = wxCheckBox(self, -1, _("Play on load"), wxPoint(80, 100 + (height*2)))
		if self.page.media.videoautostart == True:
			self.chkVideoAutostart.SetValue(True)
		self.selectAudio = wxSelectBox(self, _("Audio:"), self.page.media.audio, _("Audio"), 10, 100 + (height*2), 160)
		self.chkAudioAutostart = wxCheckBox(self, -1, _("Play on load"), wxPoint(460, 50 + (height*2) + 1))
		if self.page.media.audioautostart == True:
			self.chkAudioAutostart.SetValue(True)

		#self.selectIntroduction = wxSelectBox(self, "Intro", self.page.media.introduction, "Text", 240, 100, 160)
		self.selectText = wxSelectBox(self, _("Web Page:"), self.page.media.text, "Text", 240, 100, 160)
		self.btnEditText = wxButton(self,-1,_("Edit"))
		self.btnNewFile = wxButton(self,-1,_("New"))
		self.selectPowerPoint = wxSelectBox(self, _("Presentation:"), self.page.media.powerpoint, "Present", 240, 100 + (height*2), 160)
		
		self.lblHotwords = wxStaticText(self, -1, _("Hotwords"), wxPoint(10, 100 + (height*5)))

		self.lstTerms = wxListBox(self, -1, wxPoint(10, 115 + (height*5)), wxSize(200, 100))
		self.LoadTerms()

		self.btnAddTerm = wxButton(self,-1,_("Add"),wxPoint(15, 215 + (height*5)),wxDefaultSize)
		self.btnEditTerm = wxButton(self,-1,_("Edit"),wxPoint(80, 215 + (height*5)),wxDefaultSize)
		self.btnRemoveTerm = wxButton(self,-1,_("Remove"),wxPoint(145, 215 + (height*5)),wxDefaultSize)

		self.lblObjectives = wxStaticText(self, -1, _("Objectives"), wxPoint(240, 100 + (height*5)))

		self.lstObjectives = wxListBox(self, -1, wxPoint(240, 115 + (height*5)), wxSize(200, 100))
		self.LoadObjectives()

		self.btnAddObjective = wxButton(self,-1,_("Add"),wxPoint(245, 215 + (height*5)),wxDefaultSize)
		self.btnEditObjective = wxButton(self,-1,_("Edit"),wxPoint(310, 215 + (height*5)),wxDefaultSize)
		self.btnRemoveObjective = wxButton(self,-1,_("Remove"),wxPoint(375, 215 + (height*5)),wxDefaultSize)

		self.btnOK = wxButton(self,wxID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.txtTitle.SetSelection(0, -1)
		self.txtTitle.SetFocus()
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))

		bordersize = 2
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.topgridsizer = wxFlexGridSizer(0, 3, 4, 4)
		self.topgridsizer.Add(self.lblTitle, 0, wxALL|wxALIGN_LEFT|wxALIGN_TOP, bordersize)
		self.topgridsizer.Add(self.txtTitle, 0, wxALL|wxALIGN_CENTER, bordersize)
		self.topgridsizer.Add((1, height), 1, wxEXPAND)

		self.topgridsizer.Add(self.lblAuthor, 0, wxALL|wxALIGN_LEFT|wxALIGN_TOP, bordersize)
		self.topgridsizer.Add(self.txtAuthor, 0, wxALL|wxALIGN_CENTER, bordersize)
		self.topgridsizer.Add((1, height), 1, wxEXPAND)
		#self.mysizer.Add(self.row3sizer, 1, wxEXPAND)

		#self.row4sizer = wxBoxSizer(wxHORIZONTAL)
		self.topgridsizer.Add(self.lblCredit, 0, wxALL|wxALIGN_LEFT|wxALIGN_TOP, bordersize)
		self.topgridsizer.Add(self.txtCredit, 0, wxALL|wxALIGN_CENTER, bordersize)
		self.topgridsizer.Add((1, height), 1, wxEXPAND)
		#self.topgridsizer.AddGrowableRow(2)
		self.mysizer.Add(self.topgridsizer, 0, wxEXPAND|wxLEFT|wxRIGHT, 10)

		self.midgridsizer = wxBoxSizer(wxHORIZONTAL)
		self.leftgridsizer = wxFlexGridSizer(0, 3, bordersize, bordersize)
		self.leftgridsizer.Add(self.selectImage.label, 0, wxALL|wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT, bordersize)
		self.leftgridsizer.Add(self.selectImage.textbox, 0, wxALIGN_CENTER|wxALL, bordersize)
		self.leftgridsizer.Add(self.selectImage.selectbtn, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER, bordersize)
		
		self.rightgridsizer = wxFlexGridSizer(0, 3, bordersize, bordersize)
		self.rightgridsizer.Add(self.selectText.label, 0, wxALL|wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT, bordersize)
		self.rightgridsizer.Add(self.selectText.textbox, 1, wxALIGN_CENTER|wxLEFT, 10)
		self.rightgridsizer.Add(self.selectText.selectbtn, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER, bordersize)
		
		self.leftgridsizer.Add(self.selectVideo.label, 0, wxALL|wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT, bordersize)
		self.leftgridsizer.Add(self.selectVideo.textbox, 1, wxALIGN_CENTER|wxALL, bordersize)
		self.leftgridsizer.Add(self.selectVideo.selectbtn, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER, bordersize)
		
		#new and edit buttons
		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.neweditsizer = wxBoxSizer(wxHORIZONTAL)
		self.neweditsizer.Add(self.btnNewFile, 0, wxALL|wxALIGN_CENTER, 4)
		self.neweditsizer.Add(self.btnEditText, 0, wxALL|wxALIGN_CENTER, 4)
		self.rightgridsizer.Add(self.neweditsizer, 0, wxALL|wxALIGN_CENTER, bordersize)
		self.rightgridsizer.Add((1, 1), 0, wxALL, bordersize)
		
		#autoplay video checkbox
		self.leftgridsizer.Add((1, 1), 0, wxALL, bordersize)
		self.leftgridsizer.Add(self.chkVideoAutostart, 0, wxALL|wxALIGN_TOP|wxALIGN_LEFT, bordersize)
		self.leftgridsizer.Add((1, 1), 0, wxALL, bordersize)

		self.rightgridsizer.Add(self.selectPowerPoint.label, 0, wxALL|wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT, bordersize)
		self.rightgridsizer.Add(self.selectPowerPoint.textbox, 1, wxALL|wxALIGN_CENTER|wxALL, bordersize)
		self.rightgridsizer.Add(self.selectPowerPoint.selectbtn, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER, bordersize)	

		self.leftgridsizer.Add(self.selectAudio.label, 0, wxALL|wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT, bordersize)
		self.leftgridsizer.Add(self.selectAudio.textbox, 0, wxALL|wxALIGN_CENTER, bordersize)
		self.leftgridsizer.Add(self.selectAudio.selectbtn, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER, bordersize)	

		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)

		self.leftgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.leftgridsizer.Add(self.chkAudioAutostart, 0, wxALL|wxALIGN_LEFT|wxALIGN_TOP, bordersize)
		self.leftgridsizer.Add((1, height), 0, wxALL, bordersize)

		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.rightgridsizer.Add((1, height), 0, wxALL, bordersize)
		self.midgridsizer.Add(self.leftgridsizer, 1, wxEXPAND|wxALIGN_CENTER)
		self.midgridsizer.Add(self.rightgridsizer, 1, wxEXPAND|wxALIGN_CENTER)
		self.mysizer.Add(self.midgridsizer, 0, wxEXPAND|wxLEFT|wxRIGHT, 10)

		self.bottomsizer = wxFlexGridSizer(0, 2, bordersize, bordersize)
		self.bottomsizer.Add(self.lblHotwords, 1, wxALL|wxEXPAND|wxALIGN_LEFT, bordersize)
		self.bottomsizer.Add(self.lblObjectives, 1, wxALL|wxEXPAND|wxALIGN_LEFT, bordersize)

		self.bottomsizer.Add(self.lstTerms, 1, wxRIGHT|wxLEFT|wxEXPAND, 8)
		self.bottomsizer.Add(self.lstObjectives, 1, wxLEFT|wxRIGHT|wxEXPAND, 8)

		self.termbuttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.termbuttonsizer.Add(self.btnAddTerm, 0, wxALL|wxALIGN_CENTER, 8)
		self.termbuttonsizer.Add(self.btnEditTerm, 0, wxALL|wxALIGN_CENTER, 8)
		self.termbuttonsizer.Add(self.btnRemoveTerm, 0, wxALL|wxALIGN_CENTER, 8)
		self.bottomsizer.Add(self.termbuttonsizer,1, wxEXPAND|wxALL|wxALIGN_CENTER,bordersize)

		self.objbuttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.objbuttonsizer.Add(self.btnAddObjective, 0, wxALL|wxALIGN_CENTER, 8)
		self.objbuttonsizer.Add(self.btnEditObjective, 0, wxALL|wxALIGN_CENTER, 8)
		self.objbuttonsizer.Add(self.btnRemoveObjective, 0, wxALL|wxALIGN_CENTER, 8)	
		self.bottomsizer.Add(self.objbuttonsizer, 1, wxEXPAND|wxALL|wxALIGN_CENTER, bordersize)
		self.bottomsizer.AddGrowableRow(0)
		self.bottomsizer.AddGrowableRow(1)
		self.mysizer.Add(self.bottomsizer, 0, wxEXPAND|wxALIGN_CENTER|wxLEFT|wxRIGHT, 10)

		self.okcancelsizer = wxBoxSizer(wxHORIZONTAL)
		self.okcancelsizer.Add((100, height), 1, wxEXPAND)
		self.okcancelsizer.Add(self.btnOK, 0, wxALL, 4)
		self.okcancelsizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.okcancelsizer, 0, wxEXPAND|wxRIGHT|wxLEFT, 10)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()


		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnNewFile, self.btnNewFile.GetId(), self.btnNewFileClicked)
		EVT_BUTTON(self.btnEditText, self.btnEditText.GetId(), self.btnEditTextClicked)
		EVT_BUTTON(self.btnEditTerm, self.btnEditTerm.GetId(), self.btnEditTermClicked)
		EVT_BUTTON(self.btnEditObjective, self.btnEditObjective.GetId(), self.btnEditObjectiveClicked)
		EVT_BUTTON(self.btnRemoveTerm, self.btnRemoveTerm.GetId(), self.btnRemoveTermClicked)
		EVT_BUTTON(self.btnRemoveObjective, self.btnRemoveObjective.GetId(), self.btnRemoveObjectiveClicked)
		EVT_BUTTON(self.btnAddTerm, self.btnAddTerm.GetId(), self.btnAddTermClicked)
		EVT_BUTTON(self.btnAddObjective, self.btnAddObjective.GetId(), self.btnAddObjectiveClicked)
		#EVT_KEY_UP(self, self.checkKey)
		EVT_LISTBOX_DCLICK(self.lstTerms, self.lstTerms.GetId(), self.btnEditTermClicked)
		EVT_LISTBOX_DCLICK(self.lstObjectives, self.lstObjectives.GetId(), self.btnEditObjectiveClicked)
		#EVT_RESULT(self, self.NewHotwordLoaded)

		del busy

	#def Load(self):
	#	self.ShowModal()
	#	self.page.LoadHotwords()

	#def NewHotwordLoaded(self, event):
	#	print "New Hotword Loaded called on " + event.hwname
	#	self.lstTerms.Append(event.hwname, self.page.terms[event.hwid])

	def checkKey(self, event):
		if event.keyCode == wxRETURN:
			self.btnOKClicked(event)		

	def btnEditTextClicked(self, event):
		if wxPlatform == '__WXMAC__':	
			try:
				from OSATools import AppModels
				dreamweaver = AppModels.AppleScriptApp("Dreamweaver MX")
				opencommand = 'set myPath to POSIX file "' + os.path.join(self.CurrentDir, "Text", self.selectText.filename) + '"'
				result = dreamweaver.tellBlock(['activate',opencommand, 'open file myPath'])
			except:
				pass
			return

		if self.mainform.settings["HTMLEditor"] == "":
			wxMessageDialog(self, _("To edit the page, E-Class needs to know what HTML Editor you would like to use. To specify a HTML Editor, select 'Preferences' from the 'Options' menu."), _("Cannot Edit Page"), wxOK).ShowModal()
		else:
			if not os.path.exists(os.path.join(self.CurrentDir, "Text", self.selectText.filename)):
				dialog = wxMessageDialog(self, _("The text file '%(filename)s' does not exist. Would you like EClass to create it for you?") % {"filename":self.selectText.filename}, _("File not found"), wxYES_NO)
				if dialog.ShowModal() == wxID_YES:
					self.CreateHTMLFile(os.path.join(self.CurrentDir, "Text", self.selectText.filename))
				else:
					return
			if wxPlatform == "__WXMSW__":
				import win32api
				editor = "\"" + self.mainform.settings["HTMLEditor"] + "\""
				if not string.find(string.lower(editor), "mozilla") == -1:
					editor = editor + " -edit" 
				win32api.WinExec(editor + " \"" + os.path.join(self.CurrentDir, "Text", self.selectText.filename) + "\"")
				
				#path = win32api.GetShortPathName(os.path.join(self.CurrentDir, "Text", self.selectText.filename))
				#editor = win32api.GetShortPathName(self.mainform.settings["HTMLEditor"])
				#if not string.find(string.lower(editor), "mozilla") == -1:
				#	editor = editor + " -edit" 
				#print editor + " " + path
				#os.system(editor + " " + path)
				#os.spawnv(1, self.mainform.settings["HTMLEditor"], [os.path.split(self.mainform.settings["HTMLEditor"])[1], "\"" + os.path.join(self.CurrentDir, "Text", self.selectText.filename) + "\""])
			else:
				editor = self.mainform.settings["HTMLEditor"] 
				if wxPlatform == "__WXMAC__":
					editor = "open -a '" + editor + "'"
				path = editor + " '" + os.path.join(self.CurrentDir, "Text", self.selectText.filename) + "'"
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
			file = open(filename, "w")
			file.write(html)
			file.close()
		except IOError: 
			wxMessageDialog(self, _("Unable to create the file '%(filename)s'. Please make sure that this is a valid filename and try again.") % {"filename":filename}, _("File write error"), wxOK)

	def btnNewFileClicked(self, event):
		savefile = False

		f = wxFileDialog(self, _("New HTML Page"), os.path.join(self.CurrentDir, "Text"), "", _("HTML Files") + " (*.html)|*.html", wxSAVE)
		if f.ShowModal() == wxID_OK:
			filename = f.GetPath()
			if os.path.exists(filename):
				msg = wxMessageDialog(self, _("A file with this name already exists. Would you like to overwrite it?"), _("Overwrite File?"), wxYES_NO)
				answer = msg.ShowModal()
				if answer == wxID_YES:
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
		if result == wxID_OK:
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
		result = wxMessageDialog(self, _("Are you sure you want to delete the term '%(term)s'?") % {"term":myterm.name}, _("Delete Term?"), wxYES_NO).ShowModal()  
		if result == wxID_YES:
			self.page.terms.remove(myterm)
			self.LoadTerms()

	def btnRemoveObjectiveClicked(self,event):	
		index = self.page.objectives.index(self.lstObjectives.GetStringSelection())
		obj = self.page.objectives[index]
		result = wxMessageDialog(self, _("Are you sure you want to delete the objective '%(objective)s'?") % {"objective":obj}, _("Delete Objective?"), wxYES_NO).ShowModal()  
		if result == wxID_YES:
			self.page.objectives.remove(obj)
			self.LoadObjectives()

	def btnOKClicked(self,event):
		busy = wxBusyCursor()
		self.page.name = self.txtTitle.GetValue()
		if isinstance(self.item, conman.conman.ConNode):
			self.item.content.name = self.page.name
		else:
			self.item.name = self.page.name

		self.page.author = self.txtAuthor.GetValue()
		self.page.credit = self.txtCredit.GetValue()
		self.page.media.image = self.selectImage.filename
		self.page.media.video = self.selectVideo.filename
		self.page.media.videoautostart = self.chkVideoAutostart.GetValue()
		self.page.media.audio = self.selectAudio.filename
		self.page.media.audioautostart = self.chkAudioAutostart.GetValue()		
		#self.page.media.Introduction = self.selectIntroduction.filename
		self.page.media.text = self.selectText.filename
		self.page.media.powerpoint = self.selectPowerPoint.filename
		
		missingfiles = []
		filenames = []
		if len(self.page.media.image) > 0:
			filenames.append(os.path.join(self.CurrentDir, "Graphics", self.page.media.image))
		if len(self.page.media.video) > 0:
			filenames.append(os.path.join(self.CurrentDir, "Video", self.page.media.video))
		if len(self.page.media.audio) > 0:
			filenames.append(os.path.join(self.CurrentDir, "Audio", self.page.media.audio))
		if len(self.page.media.text) > 0:
			filenames.append(os.path.join(self.CurrentDir, "Text", self.page.media.text))
		if len(self.page.media.powerpoint) > 0:
			filenames.append(os.path.join(self.CurrentDir, "Present", self.page.media.powerpoint))

		for file in filenames:
			if not os.path.exists(file):
				missingfiles.append(file)

		if len(missingfiles) > 0:
			filelist = ""
			for file in missingfiles:
				filelist = filelist + file + "\n"

			message = _("The following files could not be found:\n\n %(filelist)s \n\nWould you still like to save and exit this page?") % {"filelist":filelist}
			result = wxMessageDialog(self, message, _("Missing files"), wxYES_NO).ShowModal()
			if result == wxID_NO:
				return

		if isinstance(self.item, conman.conman.ConNode):
			if len(self.filename) > 0:
				try:
					self.page.SaveAsXML(os.path.join(self.parent.CurrentDir, "EClass", os.path.basename(self.filename)),self.mainform.encoding)
				except IOError, e:
					wxMessageDialog(self, str(e), _("File Write Error"), wxOK).ShowModal()
					return
			else:
				myfilename = MakeFileName(os.path.join(self.parent.CurrentDir, "EClass"), self.page.name)
				self.item.content.filename = myfilename
				try: 
					self.page.SaveAsXML(os.path.join(self.parent.CurrentDir, "EClass", myfilename),self.mainform.encoding)
				except IOError, e:
					wxMessageDialog(self, str(e), _("File Write Error"), wxOK).ShowModal()
					return

			eclassPub = HTMLPublisher()
			try:
				#filename = eclassPub.Publish(self.parent, self.parent.CurrentItem, self.parent.CurrentDir)
				#self.parent.Preview(filename)
				del busy
			except Exception, ex:
				del busy
				print "Error publishing page. Error message is: \n%s" % (traceback.print_exc())
				wxMessageDialog(self, _("There was an error publishing the EClass Page to HTML. Please check to make sure you have sufficient disk space, have write permission to the 'pub' directory, and that the page does not contain any foreign characters."), _("Publishing Error")).ShowModal()
			
		self.EndModal(wxID_OK)

class NewTermDialog(wxDialog):
	"""
	Class: eclass.NewTermDialog(wxDialog)
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
		wxDialog.__init__ (self, parent, -1, _("Create New Hotword"),
						 wxDefaultPosition,
						   wxDefaultSize, 
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)

		self.parent = parent
		self.lblName = wxStaticText(self, -1, _("Name")) #wxPoint(10, 10))
		self.lblType = wxStaticText(self, -1, _("Type"))#,wxPoint(10,30))

		choices = [_("EClass Page"), _("Link to File")]
		self.txtName = wxTextCtrl(self, -1, "", wxPoint(40, 10), wxSize(160, -1))
		self.cmbType = wxChoice(self, -1, wxPoint(40, 30), wxSize(160, -1), choices)
		self.cmbType.SetSelection(1)
		self.btnOK = wxButton(self,wxID_OK,_("OK"),wxDefaultPosition,wxDefaultSize)
		self.btnOK.SetDefault()
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"),wxDefaultPosition,wxDefaultSize)
	
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.flexsizer = wxFlexGridSizer(0, 2, 4, 4)
		self.flexsizer.Add(self.lblName, 0, wxALIGN_LEFT|wxALL, 4)
		self.flexsizer.Add(self.txtName, 0, wxALIGN_LEFT|wxALL, 4)
		self.flexsizer.Add(self.lblType, 0, wxALIGN_LEFT|wxALL, 4)
		self.flexsizer.Add(self.cmbType, 0, wxALIGN_LEFT|wxALL, 4)
		self.mysizer.Add(self.flexsizer, 0, wxLEFT|wxRIGHT, 10)
		
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add((10, 25), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALIGN_LEFT|wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALIGN_LEFT|wxALL, 4)
		self.mysizer.Add(self.buttonsizer, 0, wxLEFT|wxRIGHT|wxEXPAND, 10)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		
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
			self.EndModal(wxID_OK)
			self.parent.AddTerm(myterm)
		else:
			wxMessageDialog(self, _("Please enter a name for your hotword, or click Cancel to exit without creating a hotword."), _("Please enter a name"), wxOK).ShowModal()  

def strict(char):
	print "Unicode Error on character: " + chr(char)

if __name__ == "__main__":
	pass
