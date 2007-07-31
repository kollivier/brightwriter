import string, os, sys
import types 

USE_MINIDOM=0
try:
    from xml.dom.ext.reader.Sax import FromXmlFile
except:
    USE_MINIDOM=1
#from xml import xpath
if USE_MINIDOM:
    from xml.dom import minidom


def newXMLNode(doc, name, text=None, attrs={}, ns=None):
    if ns:
        node = doc.createElementNS(ns, name)
    else:
        node = doc.createElement(name)
    
    if text:
        node.appendChild(doc.createTextNode(text))
    
    for attr in attrs.keys():
        if attrs[attr] != "":
            node.setAttribute(attr, attrs[attr])

    return node
    

class Tag:
    def __init__(self, name="", text=None, attrs={}, children=[], ns=None, maxlength=-1):
        self.namespace = ns
        self.name = name
        self.text = text
        self.attrs = attrs
        self.maxlength = maxlength
        self.children = children
        # If a tag isn't required to be in the output, let's only create it 
        # if it has attributes, a value, or children set.
        self.required = False
        
    def validate(self):
        for child in self.children:
            childNodes = [child]
            if isinstance(child, TagList):
                childNodes = child
                
            for anode in childNodes:
                if not anode.validate():
                    return False

        return True
        
    def fromXML(self, node, strictMode=False):
        if node.attributes:
            for (name, value) in node.attributes.items():            
                self.attrs[name] = value
        
        self.namespace = node.namespaceURI
        
        for childNode in node.childNodes:
            if childNode.nodeType == childNode.TEXT_NODE:
                self.text = childNode.nodeValue
            elif childNode.nodeType == childNode.ELEMENT_NODE:
                for child in self.children:
                    if childNode.nodeName == child.name:
                        child.fromXML(childNode, strictMode)
                        break
        
        if strictMode and not self.validate():
            raise ValueError
    def asString(self):
        attrs=""
        for attr in self.attrs:
            attrs += " %s=\"%s\"" % (attr, self.attrs[attr])
            
        childrenText = ""
        for child in self.children:
            childNodes = [child]
            if isinstance(child, TagList):
                childNodes = child
                
            for anode in childNodes:
                childrenText = "\n" + anode.asString()
        
        text = "<%s%s>%s</%s>\n" % (self.name, attrs, self.text + childrenText, self.name)
        
        return text 
        
    def asXML(self, doc, strictMode=False):
        if strictMode and not self.validate():
            raise ValueError
            
        hasValidChild = False
        node = newXMLNode(doc, self.name, self.text, self.attrs, self.namespace)
        for child in self.children:
            childNodes = [child]
            if isinstance(child, TagList):
                childNodes = child
                
            for anode in childNodes:
                childNode = anode.asXML(doc, strictMode)
                if childNode:
                    hasValidChild = True
                    node.appendChild(childNode)
                
        if hasValidChild or self.required or self.text or self.attrs != {}:
            return node
            
        return None

class TagList:
    def __init__(self, name="", tagClass=None, **kwargs):
        self.name = name
        self.tagClass = tagClass
        self.tags = []
        self.args = kwargs
    
    def append(self, item):
        self.tags.append(item)
        
    def extend(self, item):
        self.tags.extend(item)
        
    def sort(self, *args, **kwargs):
        self.tags.sort(*args, **kwargs)
        
    def reverse(self):
        self.tags.reverse()
        
    def index(self, *args, **kwargs):
        self.tags.reverse(*args, **kwargs)
        
    def insert(self, *args, **kwargs):
        self.tags.insert(*args, **kwargs)
        
    def count(self, *args, **kwargs):
        self.tags.count(*args, **kwargs)
        
    def remove(self, *args, **kwargs):
        self.tags.remove(*args, **kwargs)
        
    def pop(self, *args, **kwargs):
        self.tags.pop(*args, **kwargs)
        
    def __iter__(self):
        return iter(self.tags)
        
    def __len__(self):
        return len(self.tags)
        
    def __contains__(self, item):
        return item in self.tags
        
    def __getitem__(self, key):
        return self.tags[key]
        
    def __setitem__(self, key, value):
        self.tags[key] = value
        
    def __delitem__(self, key):
        del self.tags[key]
        
    def fromXML(self, node, strictMode=False):
        newTag = self.tagClass(self.name, **self.args)
        newTag.fromXML(node, strictMode)
        self.append(newTag)
        
        
class LangStringTag(Tag):
    def __init__(self, name=None, attrs={}, ns=None, maxlength=-1):
        Tag.__init__(self, name, attrs=attrs, ns=ns, maxlength=maxlength)
        # this is a dict of {lang: langstring} entries.
        self.strings = {}
        self.children = []

    def __getitem__(self, key):
        return self.strings[key]
        
    def __setitem__(self, key, value):
        self.strings[key] = value
        
    def __delitem__(self, key):
        del self.strings[key]
        
    def keys(self):
        return self.strings.keys()
        
    def validate(self):
        for key in self.strings:
            if self.maxlength != -1 and len(self.strings[key]) > self.maxlength:
                return False
            
        return True
        
    def fromXML(self, node, strictMode=False):
        strings = node.getElementsByTagName("imsmd:langstring")
        
        for astring in strings:
            language="x-none"
            text=None
            if astring.attributes:
                for (name, value) in astring.attributes.items():
                    if name=="xml:lang":
                        language=value
                    else:
                        self.attrs[name] = value
            
            self.namespace = node.namespaceURI
            
            for childNode in astring.childNodes:
                if childNode.nodeType == childNode.TEXT_NODE:
                    text = childNode.nodeValue
            
            if text:
                self.strings[language] = text
            
        if strictMode and not self.validate():
            raise ValueError
        
    def asXML(self, doc, strictMode=False):
        node = None
        
        if strictMode and not self.validate():
            raise ValueError
            
        if len(self.strings) > 0:
            node = newXMLNode(doc, self.name, self.text, self.attrs, self.namespace)
            for lang in self.strings:
                node.appendChild(newXMLNode(doc, "imsmd:langstring", self.strings[lang], 
                            {"xml:lang": lang}))
        return node

        
class VocabularyTag(Tag):
    def __init__(self, name=None, text=None, attrs={}, ns=None, vocab=[]):
        Tag.__init__(self, name, None, attrs, ns)
        self.vocab = vocab
        self.source = LangStringTag("imsmd:source")
        self.value = LangStringTag("imsmd:value")
        
        self.children = [self.source, self.value]
        
    def validate(self):
        for lang in self.value.keys():
            if not self.value[lang] in self.vocab:
                return False
            
        return True
        
        
class VCardTag(Tag):
    def __init__(self, name=None, attrs={}, ns=None, maxlength=-1):
        Tag.__init__(self, name, attrs=attrs, ns=ns, maxlength=maxlength)
        self.vcard = Tag("imsmd:vcard", maxlength=1000)
        self.children = [self.vcard]


class DateTimeTag(Tag):
    def __init__(self, name=None, attrs={}, ns=None, maxlength=-1):
        Tag.__init__(self, name, attrs=attrs, ns=ns, maxlength=maxlength)
        self.datetime = Tag("imsmd:datetime", maxlength=200)
        self.description = LangStringTag("imsmd:description", maxlength=1000)
        
        self.children = [self.datetime, self.description]
