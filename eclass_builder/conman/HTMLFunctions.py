#########################################
# Module: HTMLFunctions.py
# Description: Helper functions for HTML
# conversion
# Author: Kevin Ollivier
##########################################

import re
import file_functions as files
import string
import os
import sys

class ImportFiles:
	def __init__(self):
		self.sourcedir = ""
		self.currentdir = ""
		self.dependentFiles = []

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
	
	def CopyLink(self, match):
		link = match.group(1)
		if not string.find(string.lower(link), "http://") == -1 or not string.find(string.lower(link), "ftp://") == -1 or not string.find(string.lower(link), "mailto:") == -1 or not string.find(string.lower(link), "javascript:") == -1:
			#print "Exiting..."
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
			if not string.find(string.lower(link), "file://") == -1:
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
					mytuple = urllib.urlretrieve(link, os.path.join(destdir, filename))
					if mytuple[0] == os.path.join(destdir, filename):
						result = 1
					else: 
						result = 0
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
	html = myhtml.readline()
	while not html == "":
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
		bodystart = string.find(html, "<BODY")
		if bodystart == -1:
			bodystart = string.find(html, "<body")

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
			bodyend = string.find(html, "</BODY>")

			if bodyend == -1:
				bodyend = string.find(html, "</body>")
				
			#if both <BODY> and </BODY> are on same line, grab it all
			if not bodystart == -1 and not bodyend == -1:
				text = text + html[bodystart+1:bodyend-1]
				bodystart = -1
				bodyend = -1
				inbody = 0
			elif not bodyend == -1:
				if bodyend == 0:
					bodyend = 1 #a hack because -1 means everything
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