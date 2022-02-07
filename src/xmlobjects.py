from builtins import object
import os
import shutil
import tempfile


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
    
    for attr in list(attrs.keys()):
        if attrs[attr] != "":
            node.setAttribute(attr, attrs[attr])

    return node
    

class Tag(object):
    def __init__(self, name="", text=None, attrs=None, children=None, ns=None, maxlength=-1):
        self.namespace = ns
        self.name = name
        self.text = text
        self.attrs = {}
        if attrs:
            self.attrs = attrs
            
        # isDirty bit exists to make life easy when determining when a project is in need
        # of being saved.
        self._isDirty = False
        
        self.maxlength = maxlength
        
        self.children = []
        if self.children:
            self.children = children
        # If a tag isn't required to be in the output, let's only create it 
        # if it has attributes, a value, or children set.
        self.required = False
    
    def __setattr__(self, name, value):
        if name.find("_") != 0: # make sure changing private vars don't set the bit
            self._isDirty = True
        
        self.__dict__[name] = value
        
    def isDirty(self):
        if self._isDirty:
            return True
            
        for child in self.children:
            if child.isDirty():
                return True
                
        return False
    
    def clearDirtyBit(self):
        """
        Recursively reset the dirty bit on all tags.
        """
        self._isDirty = False
        for child in self.children:
            child.clearDirtyBit()
        
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
            for (name, value) in list(node.attributes.items()):            
                self.attrs[name] = value
        
        self.namespace = node.namespaceURI
        
        for childNode in node.childNodes:
            if childNode.nodeType == childNode.TEXT_NODE:
                self.text = childNode.nodeValue.strip()
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
        #print "Name is: " + self.name
        node = newXMLNode(doc, self.name, self.text, self.attrs, self.namespace)
        for child in self.children:
            #print "in asXml, children are " + `len(self.children)`
            childNodes = [child]
            if isinstance(child, TagList):
                #print "name = %s, len(child) is %s" % (child.name, `len(child)`)
                childNodes = child
                
            for anode in childNodes:
                #print "anode.name = " + anode.name
                childNode = anode.asXML(doc, strictMode)
                if childNode:
                    hasValidChild = True
                    node.appendChild(childNode)
                
        if hasValidChild or self.required or self.text or self.attrs != {}:
            return node
            
        return None

class TagList(object):
    def __init__(self, name="", tagClass=None, **kwargs):
        self.name = name
        self.tagClass = tagClass
        self.tags = []
        self.args = kwargs
    
    def clearDirtyBit(self):
        for tag in self.tags:
            tag.clearDirtyBit()
    
    def isDirty(self):
        for tag in self.tags:
            if tag.isDirty():
                return True
                
        return False
    
    def append(self, item):
        self.tags.append(item)
        
    def extend(self, item):
        self.tags.extend(item)
        
    def sort(self, *args, **kwargs):
        self.tags.sort(*args, **kwargs)
        
    def reverse(self):
        self.tags.reverse()
        
    def index(self, *args, **kwargs):
        return self.tags.index(*args, **kwargs)
        
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
        
class Container(Tag):
    def __init__(self, name, childTagName, childTagClass):
        Tag.__init__(self, name)
        self.childTags = TagList(childTagName, tagClass=childTagClass)
        
        self.children = [self.childTags]
        
    def append(self, item):
        self.childTags.append(item)
        
    def extend(self, item):
        self.childTags.extend(item)
        
    def sort(self, *args, **kwargs):
        self.childTags.sort(*args, **kwargs)
        
    def reverse(self):
        self.childTags.reverse()
        
    def index(self, *args, **kwargs):
        self.childTags.reverse(*args, **kwargs)
        
    def insert(self, *args, **kwargs):
        self.childTags.insert(*args, **kwargs)
        
    def count(self, *args, **kwargs):
        self.childTags.count(*args, **kwargs)
        
    def remove(self, *args, **kwargs):
        self.childTags.remove(*args, **kwargs)
        
    def pop(self, *args, **kwargs):
        self.childTags.pop(*args, **kwargs)
        
    def __iter__(self):
        return iter(self.childTags)
        
    def __len__(self):
        return len(self.childTags)
        
    def __contains__(self, item):
        return item in self.childTags
        
    def __getitem__(self, key):
        return self.childTags[key]
        
    def __setitem__(self, key, value):
        self.childTags[key] = value
        
    def __delitem__(self, key):
        del self.childTags[key]

class RootTag(Tag):
    def __init__(self, name):
        Tag.__init__(self, name)
        self.filename = None
        
    def loadFromXML(self, filename, strictMode=False):
        assert(os.path.exists(filename))
        self.filename = filename
        doc = minidom.parse(filename)
        
        self.fromXML(doc.getElementsByTagName(self.name)[0], strictMode)
        # Obviously a load shouldn't set the publication as needing saved
        self.clearDirtyBit()

    def saveAsXML(self, filename=None, strictMode=False):
        if not filename:
            filename = self.filename
        doc = minidom.Document()
        
        doc.appendChild(self.asXML(doc, strictMode))
        
        import codecs
        data = doc.toprettyxml("\t", encoding="utf-8")
        if data:
            temp_file = None
            try:
                # write to temp file first, so if anything goes wrong during the write
                # process, we don't lose data.
                fd, temp_file = tempfile.mkstemp()
                os.close(fd)
                myfile = open(temp_file, "wb")
                myfile.write(codecs.BOM_UTF8)
                myfile.write(data)
                myfile.close()
                if os.path.exists(temp_file):
                    shutil.copy2(temp_file, filename)
            except IOError:
                # calling code will report the error
                pass
            finally:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
        else:
            return False
        
        if not os.path.exists(filename):
            return False
        
        self.filename = filename
        
        self.clearDirtyBit()
        
        return True
