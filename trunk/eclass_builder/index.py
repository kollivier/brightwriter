#####################################
# indexer.py - controls the indexing and searching
# of Lucene indexes
#####################################
import string, os, StringIO, formatter, locale, glob
import PyLucene
import converter
from HTMLParser import HTMLParser, HTMLParseError
import locale
import settings
import utils
import stat
import ConfigParser
import errors

indexLog = utils.LogFile(os.path.join(settings.ProjectDir, "indexing_log.txt"))

docFormats = ["htm", "html", "doc", "rtf", "ppt", "xls", "txt", "pdf"]
textFormats = ["htm", "html", "txt", "h", "c", "cpp", "cxx", "py", "php", "pl", "rb"]
class Index:
    def __init__(self, parent, indexdir, rootFolder=""):
        self.parent = parent
        self.indexdir = indexdir
        self.folder = rootFolder
        self.reader = None
        self.files = []
        self.keepgoing = True
        self.ignoreTypes = []
        
        
        if not os.path.exists(self.indexdir):
            os.makedirs(self.indexdir)
        
        config = ConfigParser.ConfigParser()
        config.read([os.path.join(settings.ProjectDir, "index_settings.cfg")])
        if config.has_option("Settings", "IgnoreFileTypes"):
            ignoreTypes = config.get("Settings", "IgnoreFileTypes")
            if ignoreTypes != "":
                self.ignoreTypes = ignoreTypes.replace(" ", "").lower().split(",")
        
    def indexExists(self):
        return os.path.isfile(os.path.join(self.indexdir, "segments"))
        
    def getRelativePath(self, filename):
        retval = filename.replace(self.folder, "")
        if retval[0] == os.sep or retval[0] == "/":
            retval = retval[1:]
            
        return retval
        
    def getAbsolutePath(self, filename):
        return os.path.join(self.folder, filename)
        
    def addFile(self, filename, metadata):
        # first, check to see if we're in the index.
        ext = os.path.splitext(filename)[1][1:]
        if not ext.lower() in self.ignoreTypes:
            doc = PyLucene.Document()
            doc.add(PyLucene.Field("url", self.getRelativePath(filename), PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
            for field in metadata:
                doc.add(PyLucene.Field(field, metadata[field], PyLucene.Field.Store.YES, PyLucene.Field.Index.TOKENIZED))
            
            # get document text
            mytext = ""
            fullpath = os.path.join(self.folder, filename)

            if ext.lower() in docFormats + textFormats:
                try: 
                    #unfortunately, sometimes conversion is hit or miss. Worst case, index the doc with
                    #no text.
                    mytext = self.GetTextFromFile(fullpath)
                except:
                    import traceback
                    indexLog.write(`traceback.print_exc()`)#pass
                    
                if mytext == "":
                    print "No text indexed for file: " + filename
                    indexLog.write("No text indexed for file: " + filename)
            try:
                props = os.stat(fullpath)
                doc.add(PyLucene.Field("last_modified", `props[stat.ST_MTIME]`, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
                doc.add(PyLucene.Field("filesize", `props[stat.ST_SIZE]`, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
            except:
                import traceback
                print `traceback.print_exc()`
            doc.add(PyLucene.Field("contents", mytext, PyLucene.Field.Store.NO, PyLucene.Field.Index.TOKENIZED))
            newIndex = not self.indexExists()
            store = PyLucene.FSDirectory.getDirectory(self.indexdir, False)
            writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), newIndex)
            writer.addDocument(doc)
            writer.optimize()
            writer.close()
            
    def findDoc(self, filename):
        result = (-1, None)
        if self.indexExists():
            searcher = PyLucene.IndexSearcher(self.indexdir)
            analyzer = PyLucene.StandardAnalyzer()
            query = PyLucene.TermQuery(PyLucene.Term("url", '"%s"' % filename))
            hits = searcher.search(query)
            if hits.length() > 0:
                result = (hits.id(0), hits.doc(0))
            searcher.close()
                
        return result
        
    def getDocMetadata(self, doc):
        metadata = {}
        for field in doc.fields():
            metadata[field.name()] = field.stringValue()
        return metadata
    
    def getFileInfo(self, filename):
        doc = self.findDoc(filename)[1]
        if doc:
            return (filename, self.getDocMetadata(doc))
        
        return (None, None)
    
    def updateFile(self, filename, metadata):
        myfilename, filedata = self.getFileInfo(filename)
        needsUpdate = True #always true if file doesn't exist
        if filedata and filedata.has_key('filesize'):
            needsUpdate = False # file exists, use metadata to determine update.
            try:
                fullpath=os.path.join(self.folder, filename)
                props = os.stat(fullpath)
                
                if filedata.has_key("last_modified") and `props[stat.ST_MTIME]` != filedata["last_modified"]:
                    needsUpdate = True
                if `props[stat.ST_SIZE]` != filedata["filesize"]:
                    needsUpdate = True
            except:
                import traceback
                print `traceback.print_exc()`
            
        if needsUpdate:
            self.removeFile(filename)
            self.addFile(filename, metadata)
        
    def removeFile(self, filename):
        id, doc = self.findDoc(filename)
        if id != -1:
            reader = PyLucene.IndexReader.open(self.indexdir)
            #for num in range(0, reader.numDocs()-1):
                #print "url: %s, filename: %s" % (reader.document(num).get('url'), filename)
            if reader: #$ reader.document(num).get('url') == filename:
                reader.deleteDocument(id)
                #reader.commit()
                reader.close()

    def search(self, field, search_term):
        results = []
        if self.indexExists():
            searcher = PyLucene.IndexSearcher(self.indexdir)
            analyzer = PyLucene.StandardAnalyzer()
            query = PyLucene.QueryParser(field, analyzer).parse(search_term)
            hits = searcher.search(query)
            if hits.length() > 0:
                for fileNum in range(0, hits.length()-1):
                    results.append(self.getDocMetadata(hits.doc(fileNum)))

        return results
        
    def getIndexInfo(self):
        info = {}
        if self.indexExists:
            reader = PyLucene.IndexReader.open(self.indexdir)
            info["NumDocs"] = reader.numDocs()
            termList = []
            terms = reader.terms()
            moreTerms = True
            while moreTerms:
                termList.append(terms.term())
                moreTerms = terms.next()
            
            info["Terms"] = termList
            
        return info

    def GetTextFromFile(self, filename=""):
        """
        Here we convert the contents to text for indexing by Lucene.
        """
        data = ""
        global indexLog
        if filename == "":
            indexLog.write('GetTextFromFile: No filename!')
            return ""

        ext = string.lower(os.path.splitext(filename)[1][1:])
        myconverter = None

        returnDataFormat = "text"
        if ext in ["htm", "html"]:
            returnDataFormat = "html"
            
        if ext in textFormats:
            data = open(filename, "rb").read()
        else:                   
            try:
                prefConverter = ""
                if "PreferredConverter" in settings.AppSettings.keys():
                    prefConverter = settings.AppSettings["PreferredConverter"]
                    
                myconverter = converter.DocConverter(self.parent)
                thefilename, returnDataFormat = myconverter.ConvertFile(filename, "unicodeTxt", prefConverter)
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
                try:
                    text = convert.text.decode(locale.getdefaultlocale()[1])
                except: 
                    text = convert.text

        elif returnDataFormat == "unicodeTxt":
            text = unicode(data)
        else:
            text = unicode(data)

        return text


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