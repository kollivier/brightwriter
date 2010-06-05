import os
import sys
import xml.dom.minidom

from xmlobjects import *

class DCTag(Tag):
    def __init__(self, name):
        Tag.__init__(self, name)
        self.attrs["xmlns:dc"] = "http://purl.org/dc/elements/1.1/"

class OPFMetadata(Tag):
    def __init__(self, name="metadata"):
        Tag.__init__(self, name)
        
        self.identifier = DCTag("dc:identifier")
        self.identifier.attrs['id'] = 'bookid'
        self.title = DCTag("dc:title")
        self.rights = DCTag("dc:rights")
        self.publisher = DCTag("dc:publisher")
        self.subject = DCTag("dc:subject")
        self.date = DCTag("dc:date")
        self.description = DCTag("dc:description")
        self.creator = DCTag("dc:creator")
        self.language = DCTag("dc:language")
        
        self.children = [self.identifier, self.title, self.rights, self.publisher,
            self.subject, self.date, self.description, self.creator, self.language]

class OPFManifest(Tag):
    def __init__(self, name="manifest"):
        Tag.__init__(self, name)
        
        self.items = TagList("item", tagClass=Tag)
        
        self.children = [self.items]
        
class OPFSpine(Tag):
    def __init__(self, name="spine"):
        Tag.__init__(self, name)
        
        self.itemrefs = TagList("itemref", tagClass=Tag)
        
        self.children = [self.itemrefs]
    
class OPFPackage(RootTag):
    def __init__(self, name="package"):
        RootTag.__init__(self, name)
        
        self.attrs['xmlns']= 'http://www.idpf.org/2007/opf'
        self.attrs['version'] = '2.0'
        self.attrs['unique-identifier'] = 'bookid'
        
        self.metadata = OPFMetadata()
        self.manifest = OPFManifest()
        self.spine = OPFSpine()
        self.filename = "content.opf"
        
        self.children = [self.metadata, self.manifest, self.spine]
        
        
