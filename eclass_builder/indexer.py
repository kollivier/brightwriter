#####################################
# indexer.py - controls the indexing and searching
# of Lucene indexes
#####################################
import string, os, StringIO, formatter, locale, glob
import PyLucene
import converter
from HTMLParser import HTMLParser, HTMLParseError
from wxPython.wx import *
import locale
import settings
import utils
import index
import plugins
import fileutils

import errors

indexLog = errors.appErrorLog #utils.LogFile("indexing_log.txt")

class SearchEngine:
	def __init__(self, parent, indexdir, folder):
		self.parent = parent
		
		self.index = index.Index(self.parent, indexdir, folder)
		self.folder = folder
		self.keepgoing = True
		self.filecount = 0

		#get a tally of all the files being indexed
		self.numFiles = self.parent.pub.GetNodeCount()
				
		for (dir, subdirs, files) in os.walk(os.path.join(settings.CurrentDir, "File"),False):
			self.numFiles = self.numFiles + len(files)

		#self.dialog = dialogs.ProgressMonitor(_("Updating Index..."), self.numFiles, _("Preparing to update Index...") + "                             ")

	def IndexDoc(self, node):
		if not self.keepgoing:
			return

		self.statustext = _("Indexing page ") + node.content.metadata.name
		print self.statustext
		filename = node.content.filename
		self.publisher = plugins.GetPluginForFilename(filename).HTMLPublisher()
		if self.dialog:
			wxYield()
			self.keepgoing = self.dialog.Update(self.filecount, self.statustext)
			#self.dialog.sendUpdate(self.filecount, self.statustext)
			#self.cancel = wxCallAfter(self.dialog.Update, self.filecount, statustext)
		self.filecount = self.filecount + 1
		metadata = {}
		metadata["title"] = node.content.metadata.name
		
		if self.publisher:
			filename = "pub/" + self.publisher.GetFilename(node.content.filename)
		import urllib
		filename = string.replace(filename, "\\", "/")

		metadata["url"] = filename
		metadata["description"] = node.content.metadata.description
		metadata["keywords"] = node.content.metadata.keywords

		#add the author to the index
		author = node.content.metadata.lifecycle.getAuthor()
		if author:
			metadata["author"] = author.entity.fname.value
			metadata["date"] = author.date

		org = node.content.metadata.lifecycle.getOrganization()
		if org:
			metadata["organization"] = author.entity.fname.value
			
		self.index.updateFile(filename, metadata)

	def IndexFolder(self, dir):
		for afile in glob.glob(os.path.join(dir, "*")):
			if not self.keepgoing:
				return 
			fullname = os.path.join(dir, afile)
			if os.path.isdir(fullname):
				self.IndexFolder(fullname)
			elif os.path.isfile(fullname):
				filename = string.replace(fullname, self.folder + os.sep, "")
				filename = string.replace(filename, "\\", "/")
				metadata = {}
				metadata["title"] = unicode(os.path.basename(fullname))
				metadata["url"] = unicode(filename)
				
				self.statustext = _("Indexing File: \n") + filename
				print self.statustext
				if self.dialog:
					wxYield()
					self.keepgoing = self.dialog.Update(self.filecount, self.statustext)
				#	self.cancel = wxCallAfter(self.dialog.Update, self.filecount, statustext)
				self.filecount = self.filecount + 1
				self.index.updateFile(filename, metadata)

	def IndexFiles(self, rootnode, dialog=None):
		self.dialog = dialog

		#this will index the root node and all child nodes
		try:
			if self.folder != "":
				self.IndexFolder(self.folder)
			self.IndexDoc(rootnode)
		except:
			import traceback
			print traceback.print_exc()