from __future__ import print_function
#####################################
# indexer.py - controls the indexing and searching
# of Lucene indexes
#####################################
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os, io, formatter, locale, glob
import PyLucene
import converter
from html.parser import HTMLParser, HTMLParseError
import locale
import settings
import utils
import index
import plugins
import fileutils

class SearchEngine(object):
	def __init__(self, parent, indexdir, folder, callback = None):
		self.parent = parent
		
		self.index = index.Index(indexdir, folder)
		self.callback = callback
		self.folder = folder
		self.keepgoing = True
		self.filecount = 0

		#get a tally of all the files being indexed
		self.numFiles = self.parent.pub.GetNodeCount()
				
		self.numFiles += fileutils.getNumFiles( self.folder )

	def IndexDoc(self, node):
		if not self.keepgoing:
			return

		self.statustext = _("Indexing page ") + node.content.metadata.name
		filename = node.content.filename
		self.publisher = plugins.GetPluginForFilename(filename).HTMLPublisher()
		if self.callback:
			self.callback.fileProgress(self.filecount, self.statustext)

		self.filecount = self.filecount + 1
		metadata = {}
		metadata["title"] = node.content.metadata.name
		
		if self.publisher:
			filename = self.publisher.GetFileLink(node.content.filename)
		import urllib.request, urllib.parse, urllib.error
		filename = filename.replace("\\", "/")

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
		
		for child in node.children:
			self.IndexDoc(child)

	def IndexFolder(self, dirname):
		for afile in os.listdir(dirname):
			if not self.keepgoing:
				return 
			fullname = os.path.join(dirname, afile)
			if os.path.isdir(fullname):
				self.IndexFolder(fullname)
			elif os.path.isfile(fullname):
				filename = fullname.replace(self.folder + os.sep, "")
				filename = filename.replace("\\", "/")
				metadata = {}
				metadata["title"] = str(os.path.basename(fullname))
				metadata["url"] = str(filename)
				
				self.statustext = _("Indexing File: \n") + filename
				if self.callback:
					self.callback.fileProgress(self.filecount, self.statustext)

				self.filecount = self.filecount + 1
				self.index.updateFile(filename, metadata)

	def IndexFiles(self, rootnode):

		#this will index the root node and all child nodes
		try:
			if self.folder != "":
				self.IndexFolder(self.folder)
			self.IndexDoc(rootnode)
		except:
			import traceback
			print(traceback.print_exc())
