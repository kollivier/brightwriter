import csv
import string, os, sys
from validate import *
from HTMLFunctions import *

class PluginList:
	def __init__(self):
		self.plugins = []
		self.filename = ""

	def Load(self, filename=""):
		"""Load plugin list from a CSV file."""
		if not filename == "" and os.path.exists(filename):
			self.filename = filename
		if not self.filename == "":
			try:
				myfile = open(filename)
				input = csv.reader(myfile)
				for row in input:
					reqlist = string.replace(row[4], "[", "")
					reqlist = string.replace(reqlist, "]", "")
					reqlist = string.split(reqlist, ",")
					myplugin = Plugin(row[0], row[1], row[2], row[3], reqlist)
					self.plugins.append(myplugin)
				input = None
				if myfile:
					myfile.close()
			except:
				import traceback
				traceback.print_exc()

	def Save(self, filename=""):
		if not filename == "":
			self.filename = filename
		if not self.filename == "":
			try:
				myfile = open(filename, "w")
				output = csv.writer(myfile)
				output.writerows(self.plugins)
				output = None
				if myfile:
					myfile.close()
			except:
				import traceback
				traceback.print_exc()  

class Plugin:
	def __init__(self, modname, fullname, ext, mimetype, requires):
		self.modulename = modname
		self.fullname = fullname
		self.extension = ext
		self.mimetype = mimetype
		self.requires = requires

#a base publisher to be overridden by plugins 
class BaseHTMLPublisher:
	"""
	Class: conman.plugins.BaseHTMLPublisher()
	Last Updated: 11/25/03
	Description: This class creates an HTML version of the currently open EClass Page.

	Attributes:
	- parent: parent wxWindow which called the function
	- node: the ConNode containing information on the current page
	- dir: The root directory of the currently open project
	- templates: a list of templates available to the publisher
	- mypage: the EClassPage being published
	"""

	def __init__(self, parent=None, node=None, dir=None):
		self.encoding = "ISO-8859-1"
		self.parent = parent
		self.node = node
		self.dir = dir
		self.templates = None
		self.mypage = None
		self.rename = None #should we rename long files if found?
		self.data = {} #data dictionary used to hold template variables
		#self.language, self.encoding = locale.getdefaultlocale()			

	def GetCreditString(self):
		if self.node:
	  		creditstring = string.replace(self.node.content.metadata.rights.description, "\r\n", "<br>")#mac
	  		creditstring = string.replace(creditstring, "\n", "<br>")#win
	  		creditstring = string.replace(creditstring, "\r", "<br>")#unix
	  		creditstring = creditstring + "<h5 align=\'center\'>[ <a href=\'javascript:window.close()\'>" + _("Close") + "</a> ]</h5>"
	  		creditstring = string.replace(creditstring, "'", "\\'")
	  		creditText = """[ <b><a href="javascript:openCredit('newWin','%s')">%s</a></b> ]""" % (TextToHTMLChar(creditstring), _("Credit"))
	  		thisauthor = ""
	  		for contrib in self.node.content.metadata.lifecycle.contributors:
	  			if contrib.role == "Author":
	  				thisauthor = contrib.entity.fname.value
	  		creditText = "<h5>" + thisauthor + " " + creditText + "</h5>"
			return creditText
			
	def Publish(self, parent=None, node=None, dir=None):
		"""
		This function prepares the Page to be converted by putting variables into self.data
		and then calling ApplyTemplate to insert the data into the template.

		In many cases, the GetData function (and possibly the GetFilename function) will be 
		all that needs to be overridden in the plugin. 
		"""
		self.parent = parent
		self.node = node
		self.dir = dir
		self.data['name'] = TextToHTMLChar(node.content.name)
		self.data['description'] = TextToXMLAttr(node.content.description)
		self.data['keywords'] = TextToXMLAttr(node.content.keywords)
		self.data['URL'] = "pub/" + self.GetFilename(node.content.filename)
		self.data['credit'] = self.GetCreditString()
		filename = os.path.join(self.dir, "Text", node.content.filename)
		filename = self.GetFilename(node.content.filename)
		self.GetLinks()
		self.GetData()
		templatefile = os.path.join(self.parent.AppDir, "themes", self.parent.currentTheme[0], "default.tpl")
		myhtml = self.ApplyTemplate(templatefile, self.data)
		try:		
			myfile = open(os.path.join(self.dir, "pub", os.path.basename(filename)), "w")
			myfile.write(myhtml)
			myfile.close()
		except: 
			message = "There was an error writing the file", filename + " to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file."
			print `message`
			raise IOError, message
			return false
		return myhtml

	def GetLinks(self):
		"""
		Retrieve the back and next links for the page.
		"""
		backnode = self.node.back()
		#since we're publishing, we only want public nodes
		while backnode != None and backnode.content.public != "true":
			backnode = backnode.back()
		backlink = ""
		if backnode != None:
			backlink = self.GetFilename(backnode.content.filename)
			self.data['backlink'] = "<a href=\"" + backlink + "\">Back </a>"
		else:
			self.data['backlink'] = ""
		nextnode = self.node.next()
		while nextnode != None and nextnode.content.public != "true":
			nextnode = nextnode.next()
		if nextnode != None:
			nextlink = self.GetFilename(nextnode.content.filename)
			self.data['nextlink'] = "<a href=\"" + nextlink + "\">Next </a>"
		else:
			self.data['nextlink'] = ""

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

		#filename = string.replace(filename, ".html", "")
		filename = os.path.splitext(filename)[0] #filename = string.replace(filename, ".htm", "")
		filename = os.path.basename(filename)
		filename = filename[:28]
		filename = filename + ".htm"
		filename = string.replace(filename, " ", "_")
		return "../pub/" + filename

	def _CreateHTMLPage(self, mypage, filename):
		pass #overridden in child classes

	def ApplyTemplate(self, template="default.tpl", data={}):
		if template == "default.tpl":
			#get the template file from the current theme
			template = os.path.join(self.parent.AppDir,  "themes", self.parent.currentTheme[0], template)
		temp = open(template, "r")
		html = temp.read()
		temp.close()
		ext = os.path.splitext(template)[1]
		if ext == ".tpl":
			for key in data.keys():
				html = string.replace(html, "--[" + key + "]--", data[key])
		elif ext == ".tal": #SimpleTAL support
			pass #for now.... =)
		return html