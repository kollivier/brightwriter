#####################################
# indexer.py - controls the indexing and searching
# of Lucene indexes
#####################################
import sys, string, os, StringIO, formatter, locale, glob
import PyLucene
import converter
from HTMLParser import HTMLParser, HTMLParseError
import locale
import settings
import utils
import stat
import ConfigParser
import errors
import types
import shutil
import library.metadata

indexLog = errors.appErrorLog #utils.LogFile(os.path.join(settings.ProjectDir, "indexing_log.txt"))

docFormats = ["htm", "html", "doc", "rtf", "ppt", "xls", "txt", "pdf"]
textFormats = ["htm", "html", "txt", "h", "c", "cpp", "cxx", "py", "php", "pl", "rb"]

ignoreFolders = ["CVS", ".svn"]
# metadata that should not be edited by users
internalMetadata = ["contents", "url", "filesize", "last_modified"]
            
def indexingWalker(indexer, dirname, names):
    
     # skip ignored folders
    for dir in ignoreFolders:
        if dirname.find(dir) != -1:
            return
    
    metadata = {}
    
    # automatically import GSDL metadata
    metadata_filename = os.path.join(dirname, "metadata.xml")
    if os.path.exists(metadata_filename):
        metadata = library.metadata.readGSMetadata(metadata_filename)
        
    for name in names:
        fullpath = os.path.join(dirname, name)
        if os.path.isfile(fullpath) and not fullpath == metadata_filename:
            if indexer.callback:
                indexer.callback.fileIndexingStarted(fullpath)
            
            file_metadata = {}
            metafilename = fullpath.replace(indexer.folder + os.sep, "")
            
            if metafilename in metadata:
                file_metadata = metadata[metafilename].metadata
            
            indexer.addFile(fullpath, file_metadata)

class IndexingCallback:
    def __init__(self, index):
        self.index = index
        self.numFiles = 0
        
    def indexingStarted(self, numFiles):
        self.numFiles = numFiles
        print "Indexing files in %s" % (self.index)
        
    def fileIndexingStarted(self, filename):
        print "%s: Indexing %s" % (self.index, filename)
        
    def indexingComplete(self):
        print "Finished indexing %s" % (self.index)

class Index:
    def __init__(self, indexdir, rootFolder="", log_errors=True):
        self.indexdir = indexdir
        self.folder = rootFolder
        self.reader = None
        self.files = []
        self.keepgoing = True
        self.ignoreTypes = []
        self.ignoreFiles = [".DS_Store"]
        self.filenameIDs = {}
        self.log_errors = log_errors
        self.reader = None
        
        if not os.path.exists(self.indexdir):
            os.makedirs(self.indexdir)
        
        config = ConfigParser.ConfigParser()
        config.read([os.path.join(settings.ProjectDir, "index_settings.cfg")])
        if config.has_option("Settings", "IgnoreFileTypes"):
            ignoreTypes = config.get("Settings", "IgnoreFileTypes")
            if ignoreTypes != "":
                self.ignoreTypes = ignoreTypes.replace(" ", "").lower().split(",")
        
    def __del__(self):
        self.closeIndex()
            
    def indexExists(self):
        return os.path.isfile(os.path.join(self.indexdir, "segments")) or os.path.isfile(os.path.join(self.indexdir, "segments.gen"))
        
    def openWriter(self):
        """
        If a crash occurs while a PyLucene database is open, the lock file may never get
        deleted, even though access to the database ends when the program shuts down.
        
        So, what we are doing here is checking to see whether an old FSLock file is hanging
        around, and if so, delete it. 
        
        TODO: handle concurrent access scenarios, though they are not likely to occur. 
        """
        
        newindex = not self.indexExists()
        try:
            store = PyLucene.FSDirectory.getDirectory(self.indexdir, False)
            self.writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), newindex)
            #writer.close()
        except Exception, e:
            message = e.getJavaException().getMessage()
            lockFile = ""
            lockError = "Lock obtain timed out: SimpleFSLock@"
            if message.find(lockError) != -1:
                lockFile = message.replace(lockError, "")
            #print "lockFile = " + lockFile
            if os.path.exists(lockFile):
                try:
                    os.remove(lockFile)
                    return self.openWriter()
                except:
                    return False
        
    def getRelativePath(self, filename):
        retval = filename.replace(self.folder, "")
        if retval[0] == os.sep or retval[0] == "/":
            retval = retval[1:]
            
        return retval
    
    def indexLibrary(self, callback=None):
        self.callback = callback

        if self.callback:
            self.callback.indexingStarted(0)
        
        currentdir = os.getcwd()
        os.chdir(self.folder)
        
        os.path.walk(self.folder, indexingWalker, self)
        
        os.chdir(currentdir)
        
        if self.callback:
            self.callback.indexingComplete()
        
        self.callback = None        
        
    def reindexLibrary(self, callback=None):
        files = self.getFilesInIndex()
        if callback:
            callback.indexingStarted(len(files))
        
        for afile in files:
            metadata = self.getFileInfo(afile)[1]
            if metadata:
                if callback:
                    callback.fileIndexingStarted(afile)
                
                self.updateFile(self.getAbsolutePath(afile), metadata, force=True)
        
        if callback:
            callback.indexingComplete()
    
    def getAbsolutePath(self, filename):
        return os.path.join(self.folder, filename)
        
    def openIndex(self):
        if self.indexExists() and not self.reader:
            self.reader = PyLucene.IndexReader.open(self.indexdir)
            
    def closeIndex(self):
        if self.reader:
            self.reader.close()
            self.reader = None

    def addFile(self, filename, metadata, indexText=True):
        self.closeIndex() # close it if it's being read from...
        # first, check to see if we're in the index.
        ext = os.path.splitext(filename)[1][1:]
        basename = os.path.basename(filename)
        if not ext.lower() in self.ignoreTypes and basename not in self.ignoreFiles:
            doc = PyLucene.Document()
            url = self.getRelativePath(filename).replace(os.sep, "/")
            doc.add(PyLucene.Field("url", url, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
            for field in metadata:
                if field in ["url", "last_modified", "filesize"]:
                    continue
                values = metadata[field]
                if not type(values) in [types.ListType, types.TupleType]:
                    values = [values]
                if field == "contents":
                    if not indexText:
                        doc.add(PyLucene.Field("contents", values[0], PyLucene.Field.Store.NO, PyLucene.Field.Index.TOKENIZED))
                else:
                    for value in values:
                        doc.add(PyLucene.Field(field.lower(), value, PyLucene.Field.Store.YES, PyLucene.Field.Index.TOKENIZED))
            
            # get document text
            mytext = ""
            fullpath = os.path.join(self.folder, filename)

            if indexText:
                try: 
                    #unfortunately, sometimes conversion is hit or miss. Worst case, index the doc with
                    #no text.
                    if ext.lower() in docFormats + textFormats:
                        mytext = self.GetTextFromFile(fullpath)
                except:
                    import traceback
                    if self.log_errors:
                        indexLog.write(`traceback.print_exc()`)#pass
                    
                if mytext == "":
                    print "No text indexed for file: " + filename
                    if self.log_errors:
                        indexLog.write("No text indexed for file: " + filename)

                doc.add(PyLucene.Field("contents", mytext, PyLucene.Field.Store.NO, PyLucene.Field.Index.TOKENIZED))
                            
            try:
                props = os.stat(fullpath)
                doc.add(PyLucene.Field("last_modified", `props[stat.ST_MTIME]`, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
                doc.add(PyLucene.Field("filesize", `props[stat.ST_SIZE]`, PyLucene.Field.Store.YES, PyLucene.Field.Index.UN_TOKENIZED))
            except:
                import traceback
                print `traceback.print_exc()`

            newIndex = not self.indexExists()
            store = PyLucene.FSDirectory.getDirectory(self.indexdir, False)
            self.openWriter() #PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), newIndex)
            self.writer.addDocument(doc)
            self.writer.optimize()
            self.writer.close()             
            
    def updateFileMetadata(self, filename, metadata):
        """
        This function is used to update metadata, but not re-convert/index text.
        """
        
        if metadata != {}:
            allMetadata = self.getFileInfo(filename)[1]
            
            assert allMetadata
                #print "All metadata is none?"
                #return
            
            for field in metadata:
                if allMetadata.has_key(field):
                    del allMetadata[field]
                
            allMetadata.update(metadata)
            self.removeFile(filename)
            self.addFile(filename, allMetadata, indexText=False)
            
    def findDoc(self, filename):
        result = (-1, None)
        if self.indexExists():
            self.openIndex()
            filename = filename.replace(self.folder + os.sep, "")        
            if self.filenameIDs.has_key(filename):
                id = self.filenameIDs[filename]
                doc = self.reader.document(id)
                return (id, doc)
                
            searcher = PyLucene.IndexSearcher(self.indexdir)
            analyzer = PyLucene.StandardAnalyzer()
            query = PyLucene.TermQuery(PyLucene.Term("url", filename))
            hits = searcher.search(query)
            if hits.length() > 0:
                result = (hits.id(0), hits.doc(0))
            searcher.close()
        return result
        
    def getDocMetadata(self, doc):
        metadata = {}
        for field in doc.fields():
            if not field.name() in metadata:
                metadata[field.name()] = field.stringValue()
            else:
                if isinstance(metadata[field.name()], types.StringTypes):
                    metadata[field.name()] = [metadata[field.name()]]
                metadata[field.name()].append(field.stringValue())
        return metadata
    
    def getFileInfo(self, filename):
        doc = self.findDoc(filename)[1]
        if doc:
            return (filename, self.getDocMetadata(doc))
        
        return (None, None)
    
    def updateFile(self, filename, metadata={}, force=False):
        myfilename, filedata = self.getFileInfo(filename)
        needsUpdate = True #always true if file doesn't exist
        if not force and filedata and filedata.has_key('filesize'):
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
            self.openIndex()
            #for num in range(0, reader.numDocs()-1):
                #print "url: %s, filename: %s" % (reader.document(num).get('url'), filename)
            if self.reader: #$ reader.document(num).get('url') == filename:
                self.reader.deleteDocument(id)
                #reader.close()

    def search(self, field, search_term):
        results = []
        if self.indexExists():
            searcher = PyLucene.IndexSearcher(self.indexdir)
            analyzer = PyLucene.StandardAnalyzer()
            query = PyLucene.QueryParser(field.lower(), analyzer).parse(search_term)
            
            hits = searcher.search(query)
            if hits.length() > 0:
                for fileNum in range(0, hits.length()):
                    results.append(self.getDocMetadata(hits.doc(fileNum)))

        return results
        
    def getFilesInIndex(self):
        files = []
        if self.indexExists():
            self.openIndex() #reader = PyLucene.IndexReader.open(self.indexdir)
            try:
                numDocs = self.reader.numDocs()
                for i in range(0, numDocs):
                    doc = self.reader.document(i)
                    filename = doc.get("url")
                    self.filenameIDs[filename] = i
                    files.append( filename )
            finally:
                pass #    reader.close()
                
        return files
            
    def getIndexInfo(self):
        info = {}
        if self.indexExists():
            self.openIndex() #reader = PyLucene.IndexReader.open(self.indexdir)
            info["NumDocs"] = self.reader.numDocs()
            info["MetadataFields"] = self.reader.getFieldNames(PyLucene.IndexReader.FieldOption.ALL)
            termList = []
            terms = self.reader.terms()
            moreTerms = True
            while moreTerms:
                termList.append(terms.term())
                moreTerms = terms.next()
            
            info["Terms"] = termList 
        return info
        
    def getUniqueFieldValues(self, field, sort="A-Z"):
        sort = sort.replace("-", " TO ")
        results = self.search(field, "%s:[%s]" % (field, sort) )
        
        result_list = []
        for result in results:
            if not type(result[field]) in [types.ListType, types.TupleType]:
                result[field] = [result[field]]
            for subject in result[field]:
                if not subject.strip() in result_list:
                    result_list.append(subject.strip())
                
        result_list.sort()
        return result_list

    def GetTextFromFile(self, filename=""):
        """
        Here we convert the contents to text for indexing by Lucene.
        """
        data = ""
        global indexLog
        if filename == "" and self.log_errors:
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
                    
                myconverter = converter.DocConverter()
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
                #print "Encoding is: " + convert.encoding
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
            


import unittest

class IndexingTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()
        rootdir = os.path.abspath(sys.path[0])
        if not os.path.isdir(rootdir):
            rootdir = os.path.dirname(rootdir)
        settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName())

        self.testdir = os.path.join(rootdir, "testFiles", "libraryTest")
        self.index = Index(self.tempdir, self.testdir, log_errors=False)
        
    def tearDown(self):
        shutil.rmtree(self.tempdir)
        
    def testIndexExists(self):
        filename = os.path.join(self.testdir, "hello.doc")
        self.index.updateFile(filename)
        self.assertEqual(self.index.indexExists(), True)
        
    def testAddDocFile(self):
        filename = os.path.join(self.testdir, "hello.doc")
        self.index.updateFile(filename)
        results = self.index.search("contents", "import")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "hello.doc")
        
    def testAddPDFFile(self):
        filename = os.path.join(self.testdir, "hello.pdf")
        self.index.updateFile(filename)
        results = self.index.search("contents", "appears")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "hello.pdf")
        
    def testIndexLibrary(self):
        self.index.indexLibrary()
        #print `self.index.getFilesInIndex()`
        self.assertEqual(self.index.getIndexInfo()["NumDocs"], 5)
        
    def testAddHtmlFile(self):
        filename = os.path.join(self.testdir, "html_test", "test.html")
        self.index.updateFile(filename)
        results = self.index.search("contents", "Test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "html_test/test.html")
        
    def testAddTextFile(self):
        filename = os.path.join(self.testdir, "text_test", "test.txt")
        self.index.updateFile(filename)
        results = self.index.search("contents", "Text")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "text_test/test.txt")

    def testGetFileInfo(self):
        filename = os.path.join(self.testdir, "text_test", "test.txt")
        self.index.updateFile(filename)
        metadata = self.index.getFileInfo(filename)[1]
        self.assertEqual(len(metadata), 3)
        
    def testUpdateMetadata(self):
        filename = os.path.join(self.testdir, "text_test", "test.txt")
        newMetadata = {"testing": "test_value"}
        self.index.updateFile(filename)
        metadata = self.index.getFileInfo(filename)[1]
        self.assertEqual(len(metadata), 3)
        
        self.index.updateFileMetadata(filename, newMetadata)
        updatedMetadata = self.index.getFileInfo(filename)[1]
        #print "updatedMetadata = " + `updatedMetadata`
        
        self.assert_(updatedMetadata.has_key("testing"))
        self.assertEqual(len(updatedMetadata), len(metadata) + len(newMetadata))
        self.assertEqual(updatedMetadata["testing"], newMetadata["testing"])

        results = self.index.search("testing", newMetadata["testing"])
        self.assertEqual(len(results), 1)
    
    def testSearchSingeFieldValue(self):
        filename = os.path.join(self.testdir, "html_test", "test.html")
        self.index.updateFile(filename, metadata={"Subject": "document"} )
        results = self.index.search("Subject", "document")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "html_test/test.html")

    def testSearchMultipleFieldValues(self):
        filename = os.path.join(self.testdir, "html_test", "test.html")
        self.index.updateFile(filename, metadata={"Subject": ["Test", "HTML", "document"]} )
        results = self.index.search("Subject", "document")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "html_test/test.html")
        
def getTestSuite():
    return unittest.makeSuite(IndexingTests)

if __name__ == '__main__':
    unittest.main()
