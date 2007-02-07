import sys, os
import ConfigParser

import index
import utils
import shutil
import settings
import tarfile
import tempfile

# constants

INDEX_DIR = "index_directory"
CONTENT_DIR = "content_directory"
tempdir = ""
tarName = ""
extension = ".library"

# Custom error classes
class IndexExistsError(Exception):
    def __init__(self, indexName):
        self.indexName = indexName
    def __str__(self):
        return "Index with name '%s' already exists." % self.indexName
        
class IndexNotFoundError(Exception):
    def __init__(self, indexName):
        self.indexName = indexName
    def __str__(self):
        return "Index named '%s' not found." % self.indexName
        
def walker(archive, dirname, names):
    global tempdir
    global tarName
    
    for name in names:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            
        fullpath = os.path.join(dirname, name)
        if os.path.isfile(fullpath):
            arcpath = fullpath.replace(tempdir, "")
            print "Adding %s to archive" % (arcpath)            
            archive.add(fullpath, arcpath)

class IndexManager:
    def __init__(self, cfgFile=""):
        self.indexes = ConfigParser.ConfigParser()
        self.indexFile = cfgFile
        self.indexes.read(self.indexFile)
        self.indexesDir = os.path.join(os.path.dirname(cfgFile), "indexes")
        
        # Automatically load any projects in the indexes dir, if they have 
        # a contents directory.
        if not os.path.exists(self.indexesDir):
            os.makedirs(self.indexesDir)
        
        for item in os.listdir(self.indexesDir):
            fullpath = os.path.join(self.indexesDir, item)
            contentDir = os.path.join(fullpath, "contents")
            if os.path.isdir(contentDir):
                try:
                    self.addIndex(item, contentDir)
                except:
                    pass
        
    def addIndex(self, name, contentDir):
        if not self.indexes.has_section(name):
            self.indexes.add_section(name)
            self.indexes.set(name, CONTENT_DIR, contentDir)
            
            indexdir = self.indexesDir
            if not os.path.exists(indexdir):
                os.makedirs(indexdir)
            
            thisindexdir = os.path.join(indexdir, utils.createSafeFilename(name))
            if not os.path.exists(thisindexdir):
                os.makedirs(thisindexdir)
            self.setIndexProp(name, INDEX_DIR, thisindexdir)
            self.saveChanges()
        
        else:
            raise IndexExistsError(name)
            
    def getIndexes(self):
        return self.indexes.sections()
            
    def getIndex(self, name):
        if self.indexes.has_section(name):
            folder = self.getIndexProp(name, CONTENT_DIR)
            indexdir = self.getIndexProp(name, INDEX_DIR)
    
            lucenedir = os.path.join(indexdir, "index.lucene")
            indexer = index.Index(lucenedir, folder)
            return indexer
        else:
            raise IndexNotFoundError(name)
    
    def getIndexList(self):
        return self.indexes.sections()
        
    def getIndexProp(self, name, prop):
        if self.indexes.has_option(name, prop):
            return self.indexes.get(name, prop)
        else:
            return ""
    
    def setIndexProp(self, name, prop, value):
        self.indexes.set(name, prop, value)
        
    def saveChanges(self):
        self.indexes.write(open(self.indexFile, "w"))
        
    def exportIndex(self, name, dir="."):
        if self.indexes.has_section(name):
            print "Exporting index properties for %s" % name

            global tempdir
            global tarName
            global extension
            
            tempdir = tempfile.mkdtemp()
            exportConfig = ConfigParser.ConfigParser()
            exportConfig.add_section(name)
            for opt in self.indexes.options(name):
                exportConfig.set(name, opt, self.getIndexProp(name, opt))
                
            exportConfig.set(name, INDEX_DIR, "indexes")
            exportConfig.set(name, CONTENT_DIR, "contents")
                
            exportConfig.write(open(os.path.join(tempdir, "indexes.cfg"), "w"))
            
            print "Copying index files (this may take a while)..."
            import shutil
            shutil.copytree(self.getIndexProp(name, INDEX_DIR), os.path.join(tempdir, INDEX_DIR))
            
            print "Copying content files (this may take a while)..."
            shutil.copytree(self.getIndexProp(name, INDEX_DIR), os.path.join(tempdir, CONTENT_DIR))
            
            tarName = utils.createSafeFilename(name)
            archive = tarfile.open(os.path.join(dir, tarName + extension), "w:bz2")
            os.path.walk(tempdir, walker, archive)
            archive.close()
            
            shutil.rmtree(tempdir)
            
    def importIndex(self, name, archive):
        name = os.path.splitext(os.path.basename(archive))[0]
        print "importing library %s... " % name
        
        
    def removeIndex(self, name, deleteIndexFiles=True):
        if self.indexes.has_section(name):
            indexdir = self.getIndexProp(name, INDEX_DIR)
            if deleteIndexFiles:
                shutil.rmtree(indexdir)
            self.indexes.remove_section(name)
            
        else:
            raise IndexNotFoundError(name)