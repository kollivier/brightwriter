#########################################
# Module: HTMLFunctions.py
# Description: Helper functions for HTML
# conversion
# Author: Kevin Ollivier
##########################################

import re
import file_functions as files
import string, os, sys
from HTMLParser import HTMLParser
import utils

# I'd LIKE to do things this way, but there's some problem that's causing 
# files to have non-standard HTML in them that I can't seem to figure out.
# even OpenOffice has created HTML files that choke the parser...
class HTMLImporter:
	def __init__(self, filename="", sourcedir="", currentdir="", data=""):
		self.sourcedir = sourcedir
		self.currentdir = currentdir
		self.dependentFiles = []
		self.title = ""
		self.metadata = {}
		self.encoding = ""
		self.data = data
		try:
			if filename != "":
				myfile = open(filename, "r")
				self.data = myfile.read()
				myfile.close()

			parser = LinkParser()
			parser.feed(self.data)
			parser.close()

			self.title = parser.title
			self.metadata = parser.metadata
			self.encoding = parser.encoding
			self.dependentFiles = parser.replaceLinks

		except:
			import traceback
			print traceback.print_exc()
			pass

	def GetDocInfo(self):
		return (self.title, self.encoding, self.metadata, self.dependentFiles)

	def CopyAndReplaceLinks(self):
		formatdict = {"Graphics":".jpg;.jpeg;.gif;.bmp;.png", "Video":".avi;.mov;.mpg;.mpeg;.asf;.wmv;.rm;", "Audio":".wav;.aif;.mp3;.asf;.wma;.rm;"}
		for mylink in self.dependentFiles[:]:
			import urllib
			link = mylink
			link = string.replace(link, '"', '') #remove any surrounding quotes
			link = urllib.unquote(link)

			if string.find(string.lower(link), "file://") == -1:
				#link is relative to path
				if not os.sep == "/":
					link = string.replace(link, "/", os.sep)
			
				#TODO: Re-evaluate this logic... Why did I do it this way?
				checklink = os.path.join(self.currentdir, "Text", link)
			
				if os.path.isfile(checklink):
					break

				link = os.path.join(self.sourcedir, link)
			
			index = 0
			index = string.rfind(link, os.sep)
			if index == -1:
				index = string.rfind(link, "/")

			filename = link[index+1:]
			filedir = link[:index]
			#print filename
			subdir = ""
			for key in formatdict.keys():
				formatlist = string.splitfields(formatdict[key], ";")
				for format in formatlist:
					if not string.find(filename, format) == -1:
						subdir = key
						break
			if subdir == "":
				subdir = "File"
			destdir = os.path.join(self.currentdir,subdir)
			#print destdir
			result = 0
			if string.find(string.lower(link), "file://") != -1:
				try:
					mytuple = urllib.urlretrieve(link, os.path.join(destdir, filename))
					if mytuple[0] == os.path.join(destdir, filename):
						result = 1
					else: 
						result = 0
				except:
					pass
			else:
				result = files.CopyFile(filename, filedir, destdir)
			
			if result:
				newlink = "../" + subdir + "/" + filename
				self.data = string.replace(self.data, mylink, newlink)
				self.dependentFiles.remove(mylink)
				self.dependentFiles.append(newlink)
			else:
				print "Couldn't copy file from html document: " + filename
		return self.data

class ImportFiles:
	def __init__(self, filename=""):
		self.sourcedir = ""
		self.currentdir = ""
		self.dependentFiles = []
		self.filename = ""

	def ImportLinks(self, myhtml, mysourcedir, mycurrentdir):
		"""
		Detects any relative links (including hyperlinks and images) and copies the linked file into the EClass project folder.
		"""
		self.sourcedir = mysourcedir
		#print "self.sourcedir = " + self.sourcedir
		self.currentdir = mycurrentdir
		imagelinks = re.compile("src\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
		myhtml = imagelinks.sub(self.CopyLink,myhtml)
		weblinks = re.compile("href\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
		myhtml = weblinks.sub(self.CopyLink, myhtml)
		return myhtml

	def CopyLinks(self, match):
		link = match.group(1)
		if not string.find(string.lower(link), "http://") == -1 or not string.find(string.lower(link), "ftp://") == -1 or not string.find(string.lower(link), "mailto:") == -1 or not string.find(string.lower(link), "javascript:") == -1:
			return match.group()
		else:
			formatdict = {"Graphics":".jpg;.jpeg;.gif;.bmp;.png", "Video":".avi;.mov;.mpg;.mpeg;.asf;.wmv;.rm;", "Audio":".wav;.aif;.mp3;.asf;.wma;.rm;"}
			import urllib
			#originallink = link
			link = string.replace(link, '"', '') #remove any surrounding quotes
			link = urllib.unquote(link)

			#print "Link = " + link
			if string.find(string.lower(link), "file://") == -1:
				#link is relative to path
				if not os.sep == "/":
					link = string.replace(link, "/", os.sep)
			
				checklink = os.path.join(self.currentdir, "Text", link)
			
				if os.path.isfile(checklink):
					return match.group()

				link = os.path.join(self.sourcedir, link)
			
			index = 0
			index = string.rfind(link, os.sep)
			#if index == -1 and sys.platform[:6] == "darwin":
			#	index = string.rfind(link, ":")
			if index == -1:
				index = string.rfind(link, "/")

			filename = link[index+1:]
			filedir = link[:index]
			#print filename
			subdir = ""
			for key in formatdict.keys():
				formatlist = string.splitfields(formatdict[key], ";")
				for format in formatlist:
					if not string.find(filename, format) == -1:
						subdir = key
						break
			if subdir == "":
				subdir = "File"
			destdir = os.path.join(self.currentdir,subdir)
			#print destdir
			result = 0
			if string.find(string.lower(link), "file://") != -1:
				if os.name == "posix" and sys.platform[:6] == "darwin":
					result = 0
				else:
					try:
						mytuple = urllib.urlretrieve(link, os.path.join(destdir, filename))
						if mytuple[0] == os.path.join(destdir, filename):
							result = 1
						else: 
							result = 0
					except:
						pass
			else:
				result = files.CopyFile(filename, filedir, destdir)
			
			if result:
				type = string.split(match.group(), "=")[0]
				endlink =  type + "=\"../" + subdir + "/" + filename + "\""
				#print "file copied. New link is: " + endlink
				return endlink
			else:
				print "Couldn't copy file from html document: " + filename
				return match.group() #couldn't copy file so don't change the link
	
	def CopyLink(self, match):
		link = match.group(1)
		if not string.find(string.lower(link), "http://") == -1 or not string.find(string.lower(link), "ftp://") == -1 or not string.find(string.lower(link), "mailto:") == -1 or not string.find(string.lower(link), "javascript:") == -1:
			return match.group()
		else:
			formatdict = {"Graphics":".jpg;.jpeg;.gif;.bmp;.png", "Video":".avi;.mov;.mpg;.mpeg;.asf;.wmv;.rm;", "Audio":".wav;.aif;.mp3;.asf;.wma;.rm;"}
			import urllib
			#originallink = link
			link = string.replace(link, '"', '') #remove any surrounding quotes
			link = urllib.unquote(link)

			#print "Link = " + link
			if not string.find(string.lower(link), "file://") == -1:
				pass
				#absolute link
				#link = string.replace(link, "file://", "")
				#if not os.path.isfile(link) and sys.platform[:6] == "darwin":
				#	link = string.replace(link, "/", ":") 
			else:
				#link is relative to path
				if not os.sep == "/":
					link = string.replace(link, "/", os.sep)
			
				checklink = os.path.join(self.currentdir, "Text", link)
			
				if os.path.isfile(checklink):
					return match.group()

				link = os.path.join(self.sourcedir, link)
			
			index = 0
			index = string.rfind(link, os.sep)
			#if index == -1 and sys.platform[:6] == "darwin":
			#	index = string.rfind(link, ":")
			if index == -1:
				index = string.rfind(link, "/")

			filename = link[index+1:]
			filedir = link[:index]
			#print filename
			subdir = ""
			for key in formatdict.keys():
				formatlist = string.splitfields(formatdict[key], ";")
				for format in formatlist:
					if not string.find(filename, format) == -1:
						subdir = key
						break
			if subdir == "":
				subdir = "File"
			destdir = os.path.join(self.currentdir,subdir)
			#print destdir
			result = 0
			if string.find(string.lower(link), "file://") != -1:
				#try:
				if os.name == "posix" and sys.platform[:6] == "darwin":
					#not yet supported
					#import urlparse
					#print "path = " + link
					#import mac
					#print mac.getbootvol()
					#filedir = string.replace(filedir, "file://", "")
					#if filedir[0] == "/":
					#	filedir = filedir[1:] + ":" + filename
					#filedir = string.replace(filedir, "/", ":")
					#myurl = urlparse.urlparse(link)
					#f os.path.isfile(filedir):
					#	print "file exists = " + filedir + ", destdir = " + destdir
					#else:
					#	print "file doesn't exist = " + filedir
					#print "path = " + myurl[0] + " " + myurl[1]
					#result = files.CopyFile(filename, filedir, destdir)
					result = 0
				else:
					try:
						mytuple = urllib.urlretrieve(link, os.path.join(destdir, filename))
						if mytuple[0] == os.path.join(destdir, filename):
							result = 1
						else: 
							result = 0
					except:
						pass
			else:
				result = files.CopyFile(filename, filedir, destdir)
			
			if result:
				type = string.split(match.group(), "=")[0]
				endlink =  type + "=\"../" + subdir + "/" + filename + "\""
				#print "file copied. New link is: " + endlink
				return endlink
			else:
				print "Couldn't copy file from html document: " + filename
				return match.group() #couldn't copy file so don't change the link

	def GetDependentFiles(self, myhtml):
		imagelinks = re.compile("src\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
		imagelinks.sub(self.FindDependencies,myhtml)
		weblinks = re.compile("href\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
		weblinks.sub(self.FindDependencies, myhtml)
		return self.dependentFiles

	def FindDependencies(self, match):
		link = match.group(1)
		if not string.find(string.lower(link), "http://") == -1 or not string.find(string.lower(link), "ftp://") == -1 or not string.find(string.lower(link), "mailto:") == -1 or not string.find(string.lower(link), "javascript:") == -1:
			#print "Exiting..."
			return 
		else:
			formatdict = {"Graphics":".jpg;.jpeg;.gif;.bmp;.png", "Video":".avi;.mov;.mpg;.mpeg;.asf;.wmv;.rm;", "Audio":".wav;.aif;.mp3;.asf;.wma;.rm;"}
			import urllib
			#originallink = link
			link = string.replace(link, '"', '') #remove any surrounding quotes
			link = urllib.unquote(link)

			#print "Link = " + link
			if not string.find(string.lower(link), "file://") == -1:
				pass
				#absolute link
				#link = string.replace(link, "file://", "")
				#if not os.path.isfile(link) and sys.platform[:6] == "darwin":
				#	link = string.replace(link, "/", ":") 
			else:
				#link is relative to path
				self.dependentFiles.append(link)
				
def GetEncoding(myhtml):
	"""Checks for document HTML encoding and returns it if found."""
	import re
	match = re.search("""<meta\s+http-equiv="Content-Type"\s+content="text/html;\s*charset=([^\"]*)">""", myhtml, re.IGNORECASE)
	if match:
		return match.group(1).lower() #python encodings always in lowercase
	else:
		return None

def GetBody(myhtml):
	"""
	Function: _GetBody(self, myhtml)
	Last Updated: 9/24/02
	Description: Internal function to get the data in between the <BODY></BODY> tags.

	Arguments:
	- myhtml: a string containing the HTML page

	Return values:
	Returns the data between the <BODY></BODY> tags of the HTML page
			"""
	inbody = 0
	inscript = 0
	bodystart = 0
	bodyend = 0
	text = ""
	uppercase = 1
	encoding = None
	html = myhtml.readline()
	while not html == "":
		if not encoding and string.find(html.lower(), "<meta"):
			encoding = GetEncoding(html)
		#if we're inside a script, mark it so that we can test if body tag is inside the script
		scriptstart = string.find(html, "<SCRIPT")
		if scriptstart == -1:
			scriptstart = string.find(html, "<script")

		if not string.find(html, "</SCRIPT>") == -1 or not string.find(html, "</script>") == -1:
			inscript = 0

		#if we've found a script BEFORE the start of the body tag, and then found a body tag
		#it would be part of the script
		#that's why we check the script status first
		if not scriptstart == -1 and inbody == 0:
			inscript = 1

		#check for start of body in upper and lowercase
		bodystart = string.find(string.lower(html), "<body")

		#if body is found, mark the end of it
		if not bodystart == -1:
			bodystart = string.find(html, ">", bodystart)

		#if we've found both a body tag and a script tag, find which one comes first
		#if script is first, this isn't the "real" body tag
		if bodystart != -1 and scriptstart != -1:
			if bodystart > scriptstart:
				inscript = 1

		#if we are not in a script, and we've found the body tag, capture the text
		if inscript == 0 and (not bodystart == -1 or inbody):
			inbody = 1
			bodyend = string.find(string.lower(html), "</body>")
				
			#if both <BODY> and </BODY> are on same line, grab it all
			if not bodystart == -1 and not bodyend == -1:
				text = text + html[bodystart+1:bodyend]
				bodystart = -1
				bodyend = -1
				inbody = 0
			elif not bodyend == -1:
				#if bodyend == 0:
				#	bodyend = 1 #a hack because -1 means everything
				inbody = 0
				text = text + html[0:bodyend] 
				bodyend = -1
			elif not bodystart == -1:
				text = text + html[bodystart+1:-1] 
				bodystart = -1
			elif inbody == 1:
				text = text + html 
		html = myhtml.readline()
	
	if not encoding:
		encoding = utils.getCurrentEncoding()

	if encoding:
		print "Encoding is: " + `encoding`
		try:
			text = text.decode(encoding, "replace") # all import data should be converted to unicode
		except:
			pass # if it fails, just work with the byte string
	return text

#in case one day we can switch to this...
class LinkParser(HTMLParser):
    def __init__(self):
        self.text = ""
        HTMLParser.__init__(self)
        self.title = ""
        self.currentTag = ""
        self.encoding = ""
        self.metadata = {}
        self.replaceLinks = []

    def handle_starttag(self, tag, attrs):
        tagname = string.lower(tag)
        if tagname in ["a", "img"]:
            link = ""
            newlink = ""
            for attr in attrs:
                attrname = string.lower(attr[0])
                if attrname == "href" or attrname == "src":
                    link = attr[1]
                    ignore_link_types = ["http://", "ftp://", "mailto:", "javascript:"]
                    for type in ignore_link_types:
                        link = "" #forget about it, just leave it be
                    if link != "":
                        self.replaceLinks.append(link)

        if tagname == "meta":
            for attr in attrs:
                attrname = string.lower(attr[0])
                if attrname == "charset":
                    self.encoding = attr[1]
                else:
                    self.metadata[attrname] = attr[1]

    def handle_endtag(self, tag):
        tagname = string.lower(tag)
        if tagname == self.currentTag:
            self.currentTag = ""

	def handle_comment(self, data):
		pass 

    def handle_data(self, data):
        if self.currentTag == "title":
            self.title = data
