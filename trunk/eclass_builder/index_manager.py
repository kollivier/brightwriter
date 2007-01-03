import sys, os
import ConfigParser

import index
import utils
import shutil
import settings

# constants

INDEX_DIR = "index_directory"
CONTENT_DIR = "content_directory"

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
        self.indexesDir = os.path.join(settings.AppDir, "indexes")
        
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
        
    def removeIndex(self, name, deleteIndexFiles=True):
        if self.indexes.has_section(name):
            indexdir = self.getIndexProp(name, INDEX_DIR)
            if deleteIndexFiles:
                shutil.rmtree(indexdir)
            self.indexes.remove_section(name)
            
        else:
            raise IndexNotFoundError(name)