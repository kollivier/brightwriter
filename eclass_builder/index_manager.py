import sys, os
import ConfigParser

import index
import utils
import shutil
import settings

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

class IndexManager:
    def __init__(self):
        self.indexes = ConfigParser.ConfigParser()
        self.indexFile = "indexes.cfg"
        self.indexes.read(self.indexFile)
        self.indexesDir = settings.AppDir
        
    def addIndex(self, name, contentDir):
        if not self.indexes.has_section(name):
            self.indexes.add_section(name)
            self.indexes.set(name, "content_directory", contentDir)
            
            indexdir = os.path.join(self.indexesDir, "indexes")
            if not os.path.exists(indexdir):
                os.makedirs(indexdir)
            
            thisindexdir = os.path.join(indexdir, utils.createSafeFilename(name))
            if not os.path.exists(thisindexdir):
                os.makedirs(thisindexdir)
            self.setIndexProp(name, "index_directory", thisindexdir)
            self.saveChanges()
        
        else:
            raise IndexExistsError(name)
            
    def getIndex(self, name):
        if self.indexes.has_section(name):
            folder = self.getIndexProp(name, "content_directory")
            indexdir = self.getIndexProp(name, "index_directory")
    
            lucenedir = os.path.join(indexdir, "index.lucene")
            indexer = index.Index(lucenedir, folder)
            return indexer
        else:
            raise IndexNotFoundError(name)
    
    def getIndexProp(self, name, prop):
        if self.indexes.has_option(name, prop):
            return self.indexes.get(name, prop)
        else:
            return ""
    
    def setIndexProp(self, name, prop, value):
        self.indexes.set(name, prop, value)
        
    def saveChanges(self):
        self.indexes.write(open(self.indexFile, "w"))
        
    def removeIndex(self, name, deleteIndexFiles=True):
        if self.indexes.has_section(name):
            indexdir = self.getIndexProp(name, "index_directory")
            if deleteIndexFiles:
                shutil.rmtree(indexdir)
            self.indexes.remove_section(name)
            
        else:
            raise IndexNotFoundError(name)