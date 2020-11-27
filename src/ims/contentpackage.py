#!/usr/bin/python
# -*- coding: utf8 -*-
# contentpackage.py
# Designer: Kevin Ollivier
# Organization: Tulane University
# License: BrightWriter Open Source License

from __future__ import print_function
import string, os, sys
from xmlobjects import *

class LangStringTag(Tag):
    def __init__(self, name=None, attrs={}, ns=None, maxlength=-1):
        Tag.__init__(self, name, attrs=attrs, ns=ns, maxlength=maxlength)
        # this is a dict of {lang: langstring} entries.
        self.strings = {}
        self.children = []

    def __getitem__(self, key):
        return self.strings[key]
        
    def getKeyOrEmptyString(self, key):
        """
        Helper method to reduce the need to check if the key exists before
        retrieving it.
        """
        
        basekey = key.split("-")[0]
        # for languages, en == en-US, but en-US != en (necessarily), so
        # we should check if the base language key exists if the specific
        # dialect/subset we're looking for is not found.
        if key in self.strings:
            return self.strings[key]
        else:
            if basekey in self.strings:
                return self.strings[basekey]
            else:
                return ""
        
        
    def __setitem__(self, key, value):
        self._isDirty = True
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
                self.strings[language] = text.strip()
            
        if strictMode and not self.validate():
            raise ValueError
        
    def asXML(self, doc, strictMode=False):
        node = None
        
        if strictMode and not self.validate():
            raise ValueError
            
        if len(self.strings) > 0:
            node = newXMLNode(doc, self.name, self.text, self.attrs, self.namespace)
            for lang in self.strings:
                if self.strings[lang].strip() != "":
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

class Language(Tag):
    def __init__(self, language=""):
        Tag.__init__(self, "imsmd:language")
        self.text = language

class CEntity(Tag):
    def __init__(self):
        Tag.__init__(self, "imsmd:centity")
        self.vcard = Tag("imsmd:vcard", maxlength=1000)
        
        self.children = [self.vcard]

class Contributor(Tag):
    def __init__(self, name="imsmd:contribute"):
        Tag.__init__(self, name)
        self.role = VocabularyTag("imsmd:role", 
                        vocab=["Author", "Publisher", "Unknown", "Initiator", "Terminator",
                            "Validator", "Editor", "Graphical Designer", "Technical Implementer",
                            "Content Provider", "Technical Validator", "Educational Validator",
                            "Script Writer", "Instructional Designer"]
                            )
        self.centity = CEntity()
        self.date = DateTimeTag("imsmd:date")
        
        self.children = [self.role, self.centity, self.date]
        

class Format(Tag):
    def __init__(self, name="imsmd:format", format=""):
        Tag.__init__(self, name, text=format, maxlength=500)


class Requirement(Tag):
    def __init__(self, name="imsmd:requirement"):
        Tag.__init__(self, name)
        self.type = VocabularyTag("imsmd:type", vocab=["Operating System", "Browser"])
        self.browser_vocab = ["Any", "Netscape Communicator", "Microsoft Internet Explorer", "Other"]
        self.os_vocab = ["PC-DOS", "MS-Windows", "MacOS", "Unix", "Multi-OS", "Other", "None"]
        
        # We need to override default validation, so don't explicitly specify 
        # the vocab here - depends on type value
        self.name = VocabularyTag("imsmd:name", vocab=[])

        self.minimumversion = Tag("imsmd:minimumversion", maxlength=30)
        self.maximumversion = Tag("imsmd:maximumversion", maxlength=30)

        self.children = [self.type, self.name, self.minimumversion, self.maximumversion]

    def validate(self):
        if not self.type.validate() or not self.minimumversion.validate() or not self.maximumversion.validate():
            return False
            
        if self.type.value.text == "Operating System":
            if not self.name.value.text in self.os_vocab:
                return False
                
        if self.type.value.text == "Browser":
            if not self.name.value.text in self.browser_vocab:
                return False
                
        return True

class CatalogEntry(Tag):
    def __init__(self, name="imsmd:catalogentry"):
        Tag.__init__(self, name)
        self.catalog = Tag("imsmd:catalog")
        self.entry = LangStringTag("imsmd:entry")
        
        self.children = [self.catalog, self.entry]


class General(Tag):
    def __init__(self, name="imsmd:general"):
        Tag.__init__(self, name)
        self.identifier = Tag("imsmd:identifier")
        self.title = LangStringTag("imsmd:title", maxlength=1000)
        self.description = LangStringTag("imsmd:description", maxlength=2000)
        self.keyword = LangStringTag("imsmd:keyword", maxlength=1000)
        self.languages = TagList("imsmd:language", tagClass=Language)
        self.catalogentries = TagList("imsmd:catalogentry", tagClass=CatalogEntry)
        self.coverage = LangStringTag("imsmd:coverage", maxlength=1000)
        self.structure = VocabularyTag("imsmd:structure", vocab=["Collection", "Mixed", "Linear", "Hierarchical", "Networked", "Branched", "Parceled", "Atomic"])
        self.aggregationlevel = VocabularyTag("imsmd:aggregationlevel", vocab=["1", "2", "3", "4"])
        
        self.children = [self.identifier, self.title, self.description, self.keyword, self.languages, self.catalogentries, self.coverage, self.structure, self.aggregationlevel]

class Lifecycle(Tag):
    def __init__(self, name="imsmd:lifecycle"):
        Tag.__init__(self, name)
        self.version=LangStringTag("imsmd:version", maxlength=50)
        self.status=VocabularyTag("imsmd:status", vocab=["Draft", "Final", "Revised", "Unavailable"])
        self.contributors=TagList("imsmd:contribute", tagClass=Contributor)
        
        self.children = [self.version, self.status, self.contributors]


class Metametadata(Tag):
    def __init__(self, name="imsmd:metametadata"):
        Tag.__init__(self, name)
        self.identifier = Tag("imsmd:identifier")
        self.catalogentries = TagList("imsmd:catalogentry", tagClass=CatalogEntry)
        self.contributors = TagList("imsmd:contribute", tagClass=Contributor)
        self.date = DateTimeTag("imsmd:date")
        self.metadataschemes = TagList("imsmd:metadatascheme", tagClass=Tag)
        self.language = Tag("imsmd:language")
        
        self.children = [self.identifier, self.catalogentries, self.contributors, self.date, self.metadataschemes, self.language]

class Technical(Tag):
    def __init__(self, name="imsmd:technical"):
        Tag.__init__(self, name)
        self.formats = TagList("imsmd:format", tagClass=Tag)
        self.size = Tag("imsmd:size", maxlength=30)
        self.locations = TagList("imsmd:location", tagClass=Tag)
        self.requirements = TagList("imsmd:requirement", tagClass=Requirement)
        self.installationremarks = LangStringTag("imsmd:installationremarks", maxlength=1000)
        self.otherplatformrequirements = LangStringTag("imsmd:otherplatformrequirements", maxlength=1000)
        self.duration = DateTimeTag("imsmd:duration")
        
        self.children = [self.formats, self.size, self.locations, self.requirements, self.installationremarks, self.otherplatformrequirements, self.duration]

class Educational(Tag):
    def __init__(self, name="imsmd:educational"):
        Tag.__init__(self, name)
        self.interactivitytype = VocabularyTag("imsmd:interactivitytype", vocab=["Active", "Expositive", "Mixed", "Unidentified"])
        self.learningresourcetypes = TagList("imsmd:learningresourcetype", tagClass=VocabularyTag, vocab=["Exercise", "Simulation", "Questionnaire", "Diagram", "Figure", "Graph", "Index", "Slide", "Table", "Narrative Text", "Exam", "Experiment", "ProblemStatement", "SelfAssesment"])
        self.interactivitylevel = VocabularyTag("imsmd:interactivitylevel", vocab=["very low", "low", "medium", "high", "very high"])
        self.semanticdensity = VocabularyTag("imsmd:semanticdensity", vocab=["very low", "low", "medium", "high", "very high"])
        self.intendedenduserroles = TagList("imsmd:intendedenduserrole", tagClass=VocabularyTag, vocab=["Teacher", "Author", "Learner", "Manager"])
        self.contexts = TagList("imsmd:context", tagClass=VocabularyTag, vocab=["Primary Education", "Secondary Education", "Higher Education", "University First Cycle", "University Second Cycle", "University Postgrade", "Technical School First Cycle", "Technical School Second Cycle", "Professional Formation", "Continuous Formation", "Vocational Training"])
        self.typicalageranges = TagList("imsmd:typicalagerange", tagClass=LangStringTag, maxlength=1000)
        self.difficulty = VocabularyTag("imsmd:difficulty", vocab=["very easy", "easy", "medium", "difficult", "very difficult"])
        self.typicallearningtime = DateTimeTag("imsmd:typicallearningtime")
        self.description = LangStringTag("imsmd:description", maxlength=1000)
        self.languages = TagList("imsmd:language", tagClass=Language)

        self.children = [self.interactivitytype, self.learningresourcetypes, self.interactivitylevel, 
                            self.semanticdensity, self.intendedenduserroles, self.contexts, 
                            self.typicalageranges, self.difficulty, self.typicallearningtime,
                            self.description, self.languages]
                            
class Rights(Tag):
    def __init__(self, name="imsmd:rights"):
        Tag.__init__(self, name)
        self.cost = VocabularyTag("imsmd:cost", vocab=["yes", "no"])
        self.copyrightandotherrestrictions = VocabularyTag("imsmd:copyrightandotherrestrictions", vocab=["yes", "no"])
        self.description = LangStringTag("imsmd:description", maxlength=1000)
        
        self.children = [self.cost, self.copyrightandotherrestrictions, self.description]

class LOMetadata(Tag):
    def __init__(self, name="imsmd:lom"):
        Tag.__init__(self, name)
        
        self.general = General()
        self.lifecycle = Lifecycle()
        self.metametadata = Metametadata()
        self.technical = Technical()
        self.educational = Educational()
        self.rights = Rights()
        # TODO: Add relation, annotation and classification support
        
        self.children = [self.general, self.lifecycle, self.metametadata, self.technical, self.educational, self.rights]

class Metadata(Tag):
    def __init__(self, name="metadata"):
        Tag.__init__(self, name)
        self.schema=Tag("schema")
        self.schemaversion=Tag("schemaversion")
        
        self.lom = LOMetadata()
        
        self.children = [self.schema, self.schemaversion, self.lom]
        
class Item(Tag):
    def __init__(self, name="item"):
        Tag.__init__(self, name)
        self.title = Tag("title")
        self.items = TagList("item", tagClass=Item)
        self.metadata = Metadata()
        
        self.children = [self.title, self.items, self.metadata]
        
class File(Tag):
    def __init__(self, name="file"):
        Tag.__init__(self, name)
        
        self.metadata = Metadata()
        
        self.children = [self.metadata]

class Organization(Item):
    def __init__(self, name="organization"):
        Item.__init__(self, name)
        
class Resource(Tag):
    def __init__(self, name="resource"):
        Tag.__init__(self, name)
        
        self.metadata = Metadata()
        self.files = TagList("file", tagClass=File)
        self.dependencies = TagList("dependency", tagClass=Tag)
        
        # default for when it is not set by the tag explicitly
        self.attrs["adlcp:scormtype"] = "asset"
        
        self.children = [self.metadata, self.files, self.dependencies]
        
    def getFilename(self):
        if "href" in self.attrs:
            return self.attrs["href"]
            
        elif len(self.files) > 0:
            return self.files[0].attrs["href"]
            
    def setFilename(self, filename):
        # Make sure we don't have any Windows slashes in file references.
        url_filename = filename.replace("\\", "/")
        self.attrs["href"] = url_filename
        
        hasFile = False
        
        for afile in self.files:
            if afile.attrs["href"] == url_filename:
                hasFile = True
                
        # According to the IMS standard, the resource's href must also
        # be listed as a file reference.
        if not hasFile:
            imsfile = File()
            imsfile.attrs["href"] = url_filename
            self.files.append(imsfile)
        
class Organizations(Container):
    def __init__(self, name="organizations"):
        Container.__init__(self, name, "organization", Organization)
        
class Resources(Container):
    def __init__(self, name="resources"):
        Container.__init__(self, name, "resource", Resource)
        
class ContentPackage(RootTag):
    def __init__(self, name="manifest"):
        RootTag.__init__(self, name)
        self.metadata = Metadata()
        self.organizations = Organizations()
        self.resources = Resources()
        self.filename = None
        
        self.attrs["xmlns"] = "http://www.imsglobal.org/xsd/imscp_v1p1"
        self.attrs["xmlns:imsmd"] = "http://www.imsglobal.org/xsd/imsmd_v1p2"
        self.attrs["xmlns:adlcp"] = "http://www.adlnet.org/xsd/adlcp_v1p3"
        self.attrs["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        self.attrs["xsi:schemaLocation"] = "http://www.imsglobal.org/xsd/imscp_v1p1 http://www.imsglobal.org/xsd/imscp_v1p1.xsd http://www.imsglobal.org/xsd/imsmd_v1p2 http://www.imsglobal.org/xsd/imsmd_v1p2.xsd "
        self.attrs["version"] = "IMS CP 1.1.4"
        
        self.children = [self.metadata, self.organizations, self.resources]
        
        self.clearDirtyBit()
        
    def saveAsXML(self, filename=None, strictMode=False):        
        if len(self.organizations) > 0:
            self.organizations.attrs["default"] = self.organizations[0].attrs["identifier"]
        
        return RootTag.saveAsXML(self, filename, strictMode)

    def getDanglingResources(self):
        needed_resources = []
        missing_resources = []
        
        def getResourceRefsRecursive(item):
            resource_refs = []
            if "identifierref" in item.attrs:
                resource_refs.append(item.attrs["identifierref"])
                for anitem in item.items:
                    resource_refs.extend(getResourceRefsRecursive(anitem))
                    
            return resource_refs
        
        for org in self.organizations:
            for item in org.items:
                needed_resources.extend(getResourceRefsRecursive(item))
                
        for resource in self.resources:
            if "identifier" in resource.attrs and not resource.attrs["identifier"] in needed_resources:
                missing_resources.append(resource)

        return missing_resources

import unittest

class IMSContentPackageTests(unittest.TestCase):

    def setUp(self):
        self.cp = ContentPackage()
        thisdir = os.path.dirname(__file__)
        self.metadataFilename = os.path.join(thisdir, "..", "testFiles", "cpv1p1p4cp","exmpldocs", "Full_Metadata", "imsmanifest.xml")
    
    def tearDown(self):
        self.cp = None
        #if os.path.exists("./imsmanifest.xml"):
        #    os.remove("./imsmanifest.xml")
        
    def testReadingIMSFullMetadataSampleCpv1p1p4cp(self):
        thisdir = os.path.dirname(__file__)
        filename = self.metadataFilename
        if not os.path.exists(filename):
            print("Filename not found. Have you downloaded and installed the IMS Content Packaging examples?")
            return
            
        self.cp.loadFromXML(filename)
        
        # test general metadata
        self.assertEquals(self.cp.metadata.lom.general.title["en-US"], "IMS Content Packaging Sample - Full Metadata")
        
        self.assertEquals(self.cp.metadata.lom.general.catalogentries[0].catalog.text, "ISBN")
        self.assertEquals(self.cp.metadata.lom.general.catalogentries[0].entry["x-none"], "0-534-26702-5")
        
        self.assertEquals(self.cp.metadata.lom.general.languages[0].text, "en_US")
        self.assertEquals(self.cp.metadata.lom.general.description["en-US"], "A sample content packaging record")
        self.assertEquals(self.cp.metadata.lom.general.description["fr"], "Un programme...")
        self.assertEquals(self.cp.metadata.lom.general.keyword["en"], "content interchange")
        
        self.assertEquals(self.cp.metadata.lom.general.coverage["en"], "Sample code")
        
        self.assertEquals(self.cp.metadata.lom.general.structure.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.general.structure.value["x-none"], "Hierarchical")
        
        self.assertEquals(self.cp.metadata.lom.general.aggregationlevel.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.general.aggregationlevel.value["x-none"], "2")
        
        # test lifecycle metadata
        self.assertEquals(self.cp.metadata.lom.lifecycle.version["en"], "1.0")
        
        self.assertEquals(self.cp.metadata.lom.lifecycle.status.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.lifecycle.status.value["x-none"], "Final")
        
        self.assertEquals(len(self.cp.metadata.lom.lifecycle.contributors), 2)
        
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[0].role.source["en"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[0].role.value["en"], "Author")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[0].centity.vcard.text, "BEGIN:vCard FN:Chris Moffatt N:Moffatt END:vCard")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[0].date.datetime.text, "2000-01-01")
        
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[1].role.source["en"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[1].role.value["en"], "Publisher")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[1].centity.vcard.text, "BEGIN:vCard ORG:IMS Global Learning Corporation END:vCard")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[1].date.datetime.text, "2000-01-01")
        self.assertEquals(self.cp.metadata.lom.lifecycle.contributors[1].date.description["en-US"], "20th Century")
        
        # test metametadata metadata
        self.assertEquals(self.cp.metadata.lom.metametadata.catalogentries[0].catalog.text, "IMS-Test")
        self.assertEquals(self.cp.metadata.lom.metametadata.catalogentries[0].entry["x-none"], "1999.000003")

        self.assertEquals(self.cp.metadata.lom.metametadata.catalogentries[1].catalog.text, "ABC123")
        self.assertEquals(self.cp.metadata.lom.metametadata.catalogentries[1].entry["en-US"], "123A")
        
        self.assertEquals(self.cp.metadata.lom.metametadata.contributors[0].role.source["en"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.metametadata.contributors[0].role.value["en"], "Author")
        self.assertEquals(self.cp.metadata.lom.metametadata.contributors[0].centity.vcard.text, "BEGIN:vCard FN:Chris Moffatt N:Moffatt END:vCard")
        self.assertEquals(self.cp.metadata.lom.metametadata.contributors[0].date.datetime.text, "1999-08-05")
        
        self.assertEquals(self.cp.metadata.lom.metametadata.metadataschemes[0].text, "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.metametadata.language.text, "en_US")
        
        # test technical metadata
        self.assertEquals(self.cp.metadata.lom.technical.formats[0].text, "XMLL 1.0")
        self.assertEquals(self.cp.metadata.lom.technical.size.text, "70306")
        self.assertEquals(self.cp.metadata.lom.technical.locations[0].attrs["type"], "URI")
        self.assertEquals(self.cp.metadata.lom.technical.locations[0].text, "http://www.imsglobal.org/content")
        
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].type.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].type.value["x-none"], "Binding")
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].name.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].name.value["x-none"], "XML")
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].minimumversion.text, "1.0")
        self.assertEquals(self.cp.metadata.lom.technical.requirements[0].maximumversion.text, "5.2")
        
        self.assertEquals(self.cp.metadata.lom.technical.installationremarks["en"], "Download")
        self.assertEquals(self.cp.metadata.lom.technical.otherplatformrequirements["en"], "Requires web browser for rendering")
        self.assertEquals(self.cp.metadata.lom.technical.duration.datetime.text, None)
        
        # test educational metadata
        self.assertEquals(self.cp.metadata.lom.educational.learningresourcetypes[0].source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.educational.learningresourcetypes[0].value["x-none"], "Exercise")
        self.assertEquals(self.cp.metadata.lom.educational.interactivitylevel.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.educational.interactivitylevel.value["x-none"], "very low")

        self.assertEquals(self.cp.metadata.lom.educational.semanticdensity.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.educational.semanticdensity.value["x-none"], "low")
        
        self.assertEquals(self.cp.metadata.lom.educational.intendedenduserroles[0].source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.educational.intendedenduserroles[0].value["x-none"], "Learner")
        
        self.assertEquals(self.cp.metadata.lom.educational.contexts[0].source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.educational.contexts[0].value["x-none"], "Vocational Training")
        
        self.assertEquals(self.cp.metadata.lom.educational.typicalageranges[0]["x-none"], "18-99")
        self.assertEquals(self.cp.metadata.lom.educational.description["en"], "Sample code")
        self.assertEquals(self.cp.metadata.lom.educational.languages[0].text, "en_US")
        
        # test rights metadata
        self.assertEquals(self.cp.metadata.lom.rights.cost.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.rights.cost.value["x-none"], "no")
        
        self.assertEquals(self.cp.metadata.lom.rights.copyrightandotherrestrictions.source["x-none"], "LOMv1.0")
        self.assertEquals(self.cp.metadata.lom.rights.copyrightandotherrestrictions.value["x-none"], "no")
        
        self.assertEquals(self.cp.organizations[0].attrs["identifier"], "TOC1")
        self.assertEquals(self.cp.organizations[0].attrs["structure"], "hierarchical")
        self.assertEquals(self.cp.organizations[0].title.text, "default")
        
        self.assertEquals(self.cp.organizations[0].items[0].attrs["identifier"], "ITEM1")
        self.assertEquals(self.cp.organizations[0].items[0].attrs["identifierref"], "RESOURCE1")
        self.assertEquals(self.cp.organizations[0].items[0].title.text, "Lesson 1")
        
        self.assertEquals(self.cp.organizations[0].items[0].items[0].attrs["identifier"], "ITEM2")
        self.assertEquals(self.cp.organizations[0].items[0].items[0].attrs["identifierref"], "RESOURCE2")
        self.assertEquals(self.cp.organizations[0].items[0].items[0].title.text, "Introduction 1")
        
        self.assertEquals(self.cp.resources[0].attrs["identifier"], "RESOURCE1")
        self.assertEquals(self.cp.resources[0].attrs["type"], "webcontent")
        self.assertEquals(self.cp.resources[0].attrs["href"], "lesson1.htm")
        self.assertEquals(self.cp.resources[0].files[0].attrs["href"], "lesson1.htm")
        
    def testGeneralMetadata(self):
        self.cp.metadata.lom.general.title["en-US"] = "Hello World!"
        self.cp.metadata.lom.general.description["en-US"] = "This is a description."
        self.cp.metadata.lom.general.keyword["en-US"] = "hello, world, description"
        self.cp.metadata.lom.general.languages.append(Language("en-US"))
        self.cp.metadata.lom.general.languages.append(Language("jp"))
        
        entry = CatalogEntry()
        entry.catalog.text = "ISBN"
        entry.entry["en-US"] = "10101010101"
        self.cp.metadata.lom.general.catalogentries.append(entry)
        
        self.cp.saveAsXML("./imsmanifest.xml")
        
        self.assert_(os.path.exists("./imsmanifest.xml"))
        data = open("./imsmanifest.xml").read()
        self.assert_(data.find("Hello World!") != -1)
        self.assert_(data.find("This is a description.") != -1)
        self.assert_(data.find("hello, world, description") != -1)
        self.assert_(data.find("jp") != -1)
        self.assert_(data.find("ISBN") != -1)
        self.assert_(data.find("10101010101") != -1)
        
    def testLifecycleMetadata(self):
        self.cp.metadata.lom.lifecycle.version["en-US"] = "1.0"
        self.cp.metadata.lom.lifecycle.status.value["en-US"] = "Draft"
        
        contributor = Contributor()
        contributor.role.value["en-US"] = "Author"
        contributor.centity.vcard.text = "BEGIN:vCard ORG:Tulane University END:vCard"
        contributor.date.text = "2007-07-18"
        
        self.cp.metadata.lom.lifecycle.contributors.append(contributor)

        self.cp.saveAsXML("./imsmanifest.xml")
        
        self.assert_(os.path.exists("./imsmanifest.xml"))
        data = open("./imsmanifest.xml").read()
        
        self.assert_(data.find("1.0") != -1)
        self.assert_(data.find("Draft") != -1)
        self.assert_(data.find("Author") != -1)
        self.assert_(data.find("BEGIN:vCard ORG:Tulane University END:vCard") != -1)
        self.assert_(data.find("2007-07-18") != -1)
        
    def testMultiLingual(self):
        self.cp.metadata.lom.general.title["jp"] = u"今日は世界"
        self.cp.saveAsXML("./imsmanifest.xml")
        
        self.assert_(os.path.exists("./imsmanifest.xml"))
        data = open("./imsmanifest.xml").read().decode("utf-8")
        self.assert_(data.find(u"今日は世界") != -1)
        
    def testEscpaeChars(self):
        self.cp.metadata.lom.general.title["en-US"] = "\"Milk\" & cookies > apples < bananas"
        self.cp.saveAsXML("./imsmanifest.xml")
        
        self.assert_(os.path.exists("./imsmanifest.xml"))
        data = open("./imsmanifest.xml").read().decode("utf-8")
        self.assert_(data.find(u"&quot;Milk&quot; &amp; cookies &gt; apples &lt; bananas") != -1)
        
    def testDirtyBit(self):
        self.assert_(not self.cp.isDirty())
        
        filename = self.metadataFilename
        if not os.path.exists(filename):
            print("Filename not found. Have you downloaded and installed the IMS Content Packaging examples?")
            return
            
        self.cp.loadFromXML(filename)
        self.assert_(not self.cp.isDirty())
        
        # Tag test
        self.cp.metadata.lom.technical.formats[0].text = "Hello"
        self.assert_(self.cp.isDirty())
        self.cp.clearDirtyBit()
        self.assert_(not self.cp.isDirty())
        
        # LangString test
        self.cp.metadata.lom.lifecycle.version["en-US"] = "1.0"
        self.assert_(self.cp.isDirty())
        self.cp.clearDirtyBit()
        self.assert_(not self.cp.isDirty())
        
        # Container test
        org = Organization()
        self.cp.organizations.append(org)
        self.assert_(self.cp.isDirty())
        self.cp.clearDirtyBit()
        self.assert_(not self.cp.isDirty())
        
        contributor = Contributor()        
        self.cp.metadata.lom.lifecycle.contributors.append(contributor)
        self.assert_(self.cp.isDirty())
        self.cp.clearDirtyBit()
        self.assert_(not self.cp.isDirty())
        
    def testStrictMode(self):
        error = False
        overmax = self.cp.metadata.lom.general.title.maxlength + 1
        self.cp.metadata.lom.general.title["en-US"] = "s" * overmax
        
        try:
            self.cp.saveAsXML("./imsmanifest.xml", strictMode=True)
        except ValueError:
            error = True
        self.assert_(error)
        
        self.cp.saveAsXML("./imsmanifest.xml")
        self.assert_(os.path.exists("./imsmanifest.xml"))

        error = False
        undermax = self.cp.metadata.lom.general.title.maxlength
        self.cp.metadata.lom.general.title["en-US"] = "s" * undermax
        
        try:
            self.cp.saveAsXML("./imsmanifest.xml", strictMode=True)
        except ValueError:
            error = True
        self.assert_(not error)
        
        error = False
        self.cp.metadata.lom.lifecycle.status.value["en-US"] = "Not Ready Yet"
        
        try:
            self.cp.saveAsXML("./imsmanifest.xml", strictMode=True)
        except ValueError:
            error = True
            
        self.assert_(error)
        
def getTestSuite():
    return unittest.makeSuite(IMSContentPackageTests)

if __name__ == '__main__':
    unittest.main()
