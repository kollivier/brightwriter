#####################################
# indexer.py - controls the indexing and searching
# of Lucene indexes
#####################################
import string, os, StringIO, formatter, locale
import PyLucene
import converter
from HTMLParser import HTMLParser, HTMLParseError

class SearchEngine:
	def __init__(self, parent, indexdir):
		self.parent = parent
		self.indexdir = indexdir
		self.writer = None
		self.publisher = None

		if not os.path.exists(indexdir):
			os.mkdir(indexdir)

	def IndexDoc(self, node):
		doc = PyLucene.Document()
		statustext = "Indexing page " + node.content.metadata.name
		self.publisher = None
		ext = os.path.splitext(node.content.filename)[1][1:]
		for plugin in self.parent.parent.myplugins:
			if ext in plugin["Extension"]:
				exec("import plugins." + plugin["Name"])
				self.publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
		if self.parent.txtProgress:
			self.parent.txtProgress.WriteText(statustext + "\n")
		doc.add(PyLucene.Field("title", node.content.metadata.name, True, True, True))
		filename = node.content.filename
		if self.publisher:
			filename = "pub/" + self.publisher.GetFilename(node.content.filename)
		import urllib
		filename = string.replace(filename, "\\", "/")
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

		doc.add(PyLucene.Field("contents", mytext, True, True, True))

		#print "Adding " + node.content.metadata.name + " to index."
		if self.writer:
			self.writer.addDocument(doc)

		for child in node.children:
			self.IndexDoc(child)

	def IndexFiles(self, rootnode):
		store = PyLucene.FSDirectory.getDirectory(self.indexdir, True)
		self.writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), True)
		
		#this will index the root node and all child nodes
		try:
			self.IndexDoc(rootnode)
		except:
			import traceback
			print traceback.print_exc()
		print "Hello world!"
		self.writer.optimize()
		self.writer.close()

	def GetTextToIndex(self, node):
		"""
		Here we convert the contents to text for indexing by Lucene.
		"""
		filename = ""
		data = ""
		if self.publisher:
			try:
				self.publisher.Publish(self.parent.parent, node, node.dir)
				filename = node.content.filename
				if self.publisher:
					filename = self.publisher.GetFilename(node.content.filename)
				data = open(os.path.join(node.dir, "pub", filename), "rb").read()
			except:
				import traceback
				print traceback.print_exc()
				return ""
		else:					
			try:
				myconverter = converter.DocConverter(self.parent)
				thefilename = myconverter.ConvertFile(os.path.join(node.dir, node.content.filename), "html")
				myfile = open(thefilename, "rb")
				data = myfile.read()
				myfile.close()
			except:
				print "There was an error here."
				import traceback
				print traceback.print_exc()
				#if os.path.exists(thefilename):
				#	os.remove(thefilename)
				return ""

		convert = TextConverter()
		convert.feed(data)
		convert.close()
		encoding = "iso-8859-1"
		if convert.encoding != "":
			encoding = convert.encoding
		text = convert.text

		try: 
			text = convert.text.decode(encoding)
		except:
			text = convert.text.decode(locale.getdefaultlocale()[1])
		return text

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

        if tagname == "meta":
            for attr in attrs:
                if string.lower(attr[0]) == "charset":
                    self.encoding = attr[1]

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