from builtins import range
from builtins import object
import sys, os
import xml.dom.minidom
import utils

metadata_ns = ["dc", "dls"]


class ExtraMetadataFields(object):
    def __init__(self, filename):
        self.filename = filename
        self.fields = []
        self.LoadData()
        
    def SaveData(self):
        md_file = open(self.filename, "w")
        for field in self.fields:
            md_file.write(field + "\n")
        md_file.close()
        
    def LoadData(self):
        if os.path.exists(self.filename):
            md_file = open(self.filename, "r")
            line = md_file.readline()
            while line != "":
                self.fields.append(line.strip())
            md_file.close()

class FileMetadata(object):
    def __init__(self):
        self.metadata = {}
        
    def addMetadata(self, field, value, append=False):
        global metadata_ns
        
        for ns in metadata_ns:
            fullns = ns + "."
            length = len(fullns)
            if field[0:length] == fullns:
                field = field[length:]
            
        if append and field in self.metadata:
            self.metadata[field].append(value)
        else:
            self.metadata[field] = [value]

def readGSMetadata(filename):
    doc = xml.dom.minidom.parse(utils.openFile(filename))
    files = doc.getElementsByTagName("FileSet")
    
    metadata = {}
    
    def getNodeValue(node):
        if node and len(node.childNodes) > 0:
            return node.childNodes[0].nodeValue
        else:
            return ""
            
    
    for afile in files:
        filetags = afile.getElementsByTagName("FileName")
        if len(filetags) > 0:
        
            # greenstone <FileName> tags actually keep escape codes in them
            # for some reason
            filename = getNodeValue(filetags[0]).replace("\\\\", "/")
            filename = filename.replace("\\", "")
            #print "filename = %s" % filename
            
            file_metadata = FileMetadata()
            metadata_fields = afile.getElementsByTagName("Metadata")
            
            for field in metadata_fields:
                append = False
                name = ""
                for i in range(0, len(field.attributes)):
                    attr = field.attributes.item(i)
                    if attr.name == "mode":
                        append = (attr.value.lower() == "accumulate")
                        
                    if attr.name == "name":
                        name = attr.value
                        
                if name != "":
                    value = getNodeValue(field)
                    file_metadata.addMetadata(name, value, append)
                    
        if filename != "":
            metadata[filename] = file_metadata
            
    return metadata
   
   
import unittest

class MetadataTests(unittest.TestCase):
    def testreadGSMetadata(self):
        rootdir = os.path.abspath(sys.argv[0])
        if not os.path.isdir(rootdir):
            rootdir = os.path.dirname(rootdir)
        
        filename = os.path.join(rootdir, "testFiles", "libraryTest", "metadata_test", "metadata.xml")
        file_metadata = readGSMetadata(filename)
        self.assertEqual(file_metadata["brief_semanal_121903.pdf"].metadata["Title"], ["Informe Semanal, 19 diciembre de 2003  "])
        self.assertEqual(file_metadata["CDCZimbabweReport[3].pdf"].metadata["Country"], ["Zimbabwe"])

def getTestSuite():
    return unittest.makeSuite(MetadataTests)