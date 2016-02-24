import logging
import mimetypes
import os
import shutil
import tempfile
import uuid
import zipfile

import ncx
import opf

import utils.zip as ziputils
import xmlobjects
import xmlutils

mimetypes.init()
counter = 0


def addIMSItemsToEPubRecursive(imspackage, imsitems, ncxparent, opf):
    import ims.utils
    global counter

    for item in imsitems:
        navpoint = ncx.NCXNavPoint()
        navpoint.label.ncxText.text = item.title.text

        counter += 1
        navpoint.attrs['playOrder'] = str(counter)

        refitem = ims.utils.getIMSResourceForIMSItem(imspackage, item)
        if refitem:
            itemid = xmlutils.createXMLUUID()  # refitem.attrs['identifier']
            navpoint.attrs['id'] = itemid

            opfitemref = xmlobjects.Tag("itemref")
            opfitemref.attrs['idref'] = itemid
            opf.spine.itemrefs.append(opfitemref)

            if len(refitem.files) > 0:
                for afile in refitem.files:
                    fileid = xmlutils.createXMLUUID()
                    filename = afile.attrs['href']
                    if filename == refitem.attrs['href']:
                        fileid = itemid
                    mime_type = mimetypes.guess_type(filename)[0]
                    if mime_type == 'text/html':
                        mime_type = 'application/xhtml+xml'
                    navpoint.content.attrs['src'] = filename
                    opfitem = xmlobjects.Tag("item")
                    opfitem.attrs['href'] = filename
                    opfitem.attrs['media-type'] = mime_type
                    opfitem.attrs['id'] = fileid
                    opf.manifest.items.append(opfitem)
        
        if len(item.items) > 0:
            addIMSItemsToEPubRecursive(imspackage, item.items, navpoint, opf)
        
        ncxparent.navPoints.append(navpoint)
        
class Container(xmlobjects.RootTag):
    def __init__(self, name="container"):
        xmlobjects.RootTag.__init__(self, name)
        
        self.filename = "container.xml"
        self.attrs['xmlns'] = 'urn:oasis:names:tc:opendocument:xmlns:container'
        self.attrs['version'] = '1.0'
        self.rootfiles = xmlobjects.Container("rootfiles", "rootfile", xmlobjects.Tag)
        
        self.children = [self.rootfiles]

class EPubPackage:
    def __init__(self, name=""):
        self.name = name
        self.mimetype = "application/epub+zip"
        self.rootfiles = []
        self.ncx = None # ncx.NCX()
        self.opf = opf.OPFPackage()
        self.container = Container()
        
        
    def imsToEPub(self, imspackage, language="en"):        
        self.ncx = ncx.NCX()
        global counter
        counter = 0
        
        title = imspackage.metadata.lom.general.title
        if len(title.keys()) > 0:
            firstitem = title.keys()[0]
            self.name = title[firstitem]
            self.opf.metadata.title.text = self.name
            
        # TODO: fix EClass support for multiple language packages...
        self.opf.metadata.language.text = language
            
        addIMSItemsToEPubRecursive(imspackage, imspackage.organizations[0].items, self.ncx, self.opf)
        nav_uid = xmlobjects.Tag('ncx:meta')
        nav_uid.attrs['name'] = 'dtb:uid'
        nav_uid.attrs['content'] = str(uuid.uuid4())
        self.ncx.head.metatags.append(nav_uid)
        self.ncx.docTitle.ncxText.text = imspackage.organizations[0].items[0].title.text
        
        
        # add the TOC item
        
        tocitem = xmlobjects.Tag("item")
        tocitem.attrs['id'] = 'ncxtoc'
        tocitem.attrs['media-type'] = 'application/x-dtbncx+xml'
        tocitem.attrs['href'] = os.path.basename(self.ncx.filename)
        self.opf.manifest.items.append(tocitem)
        
        self.opf.spine.attrs['toc'] = 'ncxtoc'
        
        # create Container rootfile reference
        rootfile = xmlobjects.Tag("rootfile")
        rootfile.attrs['full-path'] = 'OEPBS/' + os.path.basename(self.opf.filename)
        rootfile.attrs['media-type'] = 'application/oebps-package+xml'
        self.container.rootfiles.append(rootfile)
    
    def createEPubPackage(self, filesdir, filename):
        zip = zipfile.ZipFile(filename, 'w')
        
        zip.writestr("mimetype", self.mimetype)
        
        opfBasename = os.path.basename(self.opf.filename)
        assert opfBasename != ""
        
        ncxBasename = None
        if self.ncx:
            ncxBasename = os.path.basename(self.ncx.filename)
            assert ncxBasename 
        
        opfFile = tempfile.mkstemp()[1]
        try:
            self.opf.saveAsXML(opfFile)
            zip.write(opfFile, os.path.join("OEPBS", opfBasename))
        finally:
            os.remove(opfFile)
        
        ncxFile = tempfile.mkstemp()[1]
        try:
            self.ncx.saveAsXML(ncxFile)
            zip.write(ncxFile, os.path.join("OEPBS", ncxBasename))
        finally:
            os.remove(ncxFile)

        containerFile = tempfile.mkstemp()[1]
        containerBasename = os.path.basename(self.container.filename)
        try:
            self.container.saveAsXML(containerFile)
            zip.write(containerFile, os.path.join("META-INF", containerBasename))
        finally:
            os.remove(containerFile)
        
        ziputils.dirToZipFile("", zip, filesdir, zipDir="OEPBS")
    
import unittest

class EPubTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()
        rootdir = os.path.abspath(__file__)
        if not os.path.isdir(rootdir):
            rootdir = os.path.dirname(rootdir)

        self.testdir = os.path.join(rootdir, "..", "testFiles", "cpv1p1p4cp","exmpldocs", "Full_Metadata")
        # os.path.join(rootdir, "..", "testFiles", "cpv1p1p4cp")
        self.epub = EPubPackage()
        
    def tearDown(self):
        shutil.rmtree(self.tempdir)
        
    def testIMSConversion(self):
        import ims.contentpackage
        imspackage = ims.contentpackage.ContentPackage()
        imspackage.loadFromXML(os.path.join(self.testdir, "imsmanifest.xml"))
        
        self.epub.imsToEPub(imspackage)
        
        self.assertEquals(self.epub.name, "IMS Content Packaging Sample - Full Metadata")
        
        
def getTestSuite():
    return unittest.makeSuite(EPubTests)

if __name__ == '__main__':
    unittest.main()
