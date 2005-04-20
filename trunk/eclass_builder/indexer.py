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

indexLog = utils.LogFile("indexing_log.txt")

class SearchEngine:
	def __init__(self, parent, indexdir, folder=""):
		self.parent = parent
		self.indexdir = indexdir
		self.folder = folder #for indexing non-EClass docs
		self.writer = None
		self.publisher = None
		self.numFiles = 0
		self.dialog = None
		self.filecount = 0
		self.keepgoing = True

		#get a tally of all the files being indexed
		for (dir, subdirs, files) in os.walk(os.path.join(settings.CurrentDir, "pub"), False):
			self.numFiles = self.numFiles + len(files)
				
		for (dir, subdirs, files) in os.walk(os.path.join(settings.CurrentDir, "File"),False):
			self.numFiles = self.numFiles + len(files)

		#self.dialog = dialogs.ProgressMonitor(_("Updating Index..."), self.numFiles, _("Preparing to update Index...") + "                             ")

	def IndexDoc(self, node):
		if not self.keepgoing:
			return
		doc = PyLucene.Document()
		self.statustext = _("Indexing page ") + node.content.metadata.name
		self.publisher = None
		ext = os.path.splitext(node.content.filename)[1][1:]
		for plugin in settings.plugins:
			if ext in plugin["Extension"]:
				exec("import plugins." + plugin["Name"])
				self.publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
		if self.dialog:
			wxYield()
			self.keepgoing = self.dialog.Update(self.filecount, self.statustext)
			#self.dialog.sendUpdate(self.filecount, self.statustext)
			#self.cancel = wxCallAfter(self.dialog.Update, self.filecount, statustext)
		self.filecount = self.filecount + 1
		doc.add(PyLucene.Field("title", node.content.metadata.name, True, True, True))
		filename = node.content.filename
		if self.publisher:
			filename = "pub/" + self.publisher.GetFilename(node.content.filename)
		import urllib
		filename = string.replace(filename, "\\", "/")

		print "Filename: " + filename
		doc.add(PyLucene.Field("url", filename, True, True, True))
		doc.add(PyLucene.Field("description", node.content.metadata.description, True, True, True))
		doc.add(PyLucene.Field("keywords", node.content.metadata.keywords, True, True, True))

		#add the author to the index
		author = node.content.metadata.lifecycle.getAuthor()
		if author:
			doc.add(PyLucene.Field("author", author.entity.fname.value, True, True, True))
			doc.add(PyLucene.Field("date", author.date, True, True, True))

		org = node.content.metadata.lifecycle.getOrganization()
		if org:
			doc.add(PyLucene.Field("organization", author.entity.fname.value, True, True, True))

		mytext = ""
		try: 
			#unfortunately, sometimes conversion is hit or miss. Worst case, index the doc with
			#no text.
			mytext = self.GetTextToIndex(node)
		except:
			pass

		if mytext == "":
			global indexLog
			indexLog.write("No text indexed for file: " + filename)

		doc.add(PyLucene.Field("contents", mytext, True, True, True))

		if self.writer:
			self.writer.addDocument(doc)

		for child in node.children:
			self.IndexDoc(child)

	def IndexFolder(self, dir):
		for afile in glob.glob(os.path.join(dir, "*")):
			if not self.keepgoing:
				return 
			fullname = os.path.join(dir, afile)
			if os.path.isdir(fullname):
				self.IndexFolder(fullname)
			elif os.path.isfile(fullname):
				doc = PyLucene.Document()
				filename = string.replace(fullname, self.folder, "File")
				filename = string.replace(filename, "\\", "/")
				print "Filename: " + filename
				doc.add(PyLucene.Field("title", unicode(os.path.basename(fullname)), True, True, True))
				doc.add(PyLucene.Field.UnIndexed("url", unicode(filename)))
				self.statustext = _("Indexing File: \n") + filename
				if self.dialog:
					wxYield()
					self.keepgoing = self.dialog.Update(self.filecount, self.statustext)
				#	self.cancel = wxCallAfter(self.dialog.Update, self.filecount, statustext)
				self.filecount = self.filecount + 1
				mytext = ""
				try: 
					#unfortunately, sometimes conversion is hit or miss. Worst case, index the doc with
					#no text.
					mytext = self.GetTextFromFile(fullname)
				except:
					pass

				doc.add(PyLucene.Field.UnStored("contents", mytext))
				if self.writer:
					self.writer.addDocument(doc)

	def IndexFiles(self, rootnode, dialog=None):s
		store = PyLucene.FSDirectory.getDirectory(self.indexdir, True)
		self.writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), True)
		self.dialog = dialog

		#this will index the root node and all child nodes
		try:
			if self.folder != "":
				self.IndexFolder(self.folder)
			self.IndexDoc(rootnode)
		except:
			import traceback
			print traceback.print_exc()

		self.writer.optimize()
		self.writer.close()

	def GetTextFromFile(self, filename=""):
		"""
		Here we convert the contents to text for indexing by Lucene.
		"""
		data = ""

		if filename == "":
			return ""

		ext = string.lower(os.path.splitext(filename)[1][1:])
		myconverter = None

		returnDataFormat = "html"
		if ext in ["htm", "html"]:
			data = open(filename, "rb").read()
		else:					
			try:
				myconverter = converter.DocConverter(self.parent)
				thefilename, returnDataFormat = myconverter.ConvertFile(filename, "unicodeTxt", settings.options["PreferredConverter"])
				if thefilename == "":
					return ""
				myfile = open(thefilename, "rb")
				data = myfile.read()
				myfile.close()

				if os.path.exists(thefilename):
					os.remove(thefilename)
			except:
				import traceback
				print traceback.print_exc()
				if os.path.exists(thefilename):
					os.remove(thefilename)
				return "", ""

		if returnDataFormat == "html":
			convert = TextConverter()
			convert.feed(data)
			convert.close()
			encoding = "iso-8859-1"
			if convert.encoding != "":
				print "Encoding is: " + convert.encoding
				encoding = convert.encoding
			text = convert.text

			try: 
				text = convert.text.decode(encoding)
			except:
				text = convert.text.decode(locale.getdefaultlocale()[1])
		elif returnDataFormat == "unicodeTxt":
			text = unicode(data)
		else:
			text = unicode(data)

		return text


	def GetTextToIndex(self, node):
		"""
		Here we get the file for indexing and pass it into GetTextFromFile.
		"""
		filename = ""
		data = ""
		if self.publisher:
			if 1:
				self.publisher.Publish(self.parent, node, node.dir)
				filename = node.content.filename
				if self.publisher:
					filename = self.publisher.GetFilename(node.content.filename)
			#except:
			#	import traceback
			#	print traceback.print_exc()
			#	return ""
		else:					
			filename = os.path.join(node.dir, node.content.filename)

		return self.GetTextFromFile(filename)

	def SearchFiles(self, query):
		return []

	def IsInstalled(self):
		return false

class TextConverter(HTMLParser):
    def __init__(self):
        self.text = ""
        HTMLParser.__init__(self)
        self.heading_text = ""
        self.subheading_text = ""
        self.title = ""
        self.currentTag = ""
        self.encoding = ""

    def handle_starttag(self, tag, attrs):
        tagname = string.lower(tag)
        if tagname in ["title", "h1", "h2", "h3", "h4"]:
            self.currentTag = tagname

		#We can get encoding one of two ways, either from an encoding meta tag
		#or from a Content-Type meta tag
        isContentTypeTag = False
        if tagname == "meta":
            for attr in attrs:
                if string.lower(attr[0]) == "http-equiv" and string.lower(attr[1]) == "content-type":
                    isContentTypeTag = True

                if isContentTypeTag == True and string.lower(attr[0]) == "content":
                    values = string.split(attr[1], ";")
                    for value in values:
                        myvalue = string.lower(value)
                        if myvalue.find("charset") != -1:
                            self.encoding = string.split(myvalue, "=")[1]
							
                if string.lower(attr[0]) == "charset":
                    self.encoding = attr[1]
			
			#see encodings/aliases.py - all aliases use underscores where
			#typically a dash is supposed to be.
            self.encoding = string.replace(self.encoding, "-", "_")

    def handle_endtag(self, tag):
        tagname = string.lower(tag)
        if tagname == self.currentTag:
            self.currentTag = ""

	def handle_comment(self, data):
		pass 

    def handle_data(self, data):
        if self.currentTag == "title":
            self.title = data
        elif self.currentTag in ["h1", "h2"]:
            self.heading_text = self.heading_text + " " + data
            #in case the page has no title
            if self.title == "":
                self.title = data
        elif self.currentTag in ["h3", "h4"]:
            self.subheading_text = self.subheading_text + " " + data
        else:
            self.text = self.text + " " + data