import string, sys, os
import ims.contentpackage
import constants
import version
import unittest
import shutil
import plugins

def createEClass(dirname):
    # create the EClass folders
    os.mkdir(dirname)
    for dir in constants.eclassdirs:
        subdir = os.path.join(dirname, dir)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
            
    return EClass(os.path.join(dirname, "imsmanifest.xml"))

def getEClassPageForIMSResource(imsresource):
    # for EClass pages, the source page is listed as a dependency of the generated
    # HTML page. This is so that tools that do not understand the EClass Page format
    # can read EClass-created IMS content packages.
    filename = None
    for file in imsresource.files:
        if "href" in file.attrs and os.path.splitext(file.attrs["href"])[1] == ".ecp":
            filename = file.attrs["href"]
    
    return filename
    
def setEClassPageForIMSResource(imsresource, filename):
    # for EClass pages, the source page is listed as a dependency of the generated
    # HTML page. This is so that tools that do not understand the EClass Page format
    # can read EClass-created IMS content packages.
    plugin = plugins.GetPluginForFilename(filename)
    publisher = plugin.HTMLPublisher()
    filelink = publisher.GetFileLink(filename)
            
    imsresource.attrs["href"] = filelink
            
    imsfile = ims.contentpackage.File()
    imsfile.attrs["href"] = filelink
    imsresource.files.append(imsfile)
    
    # According to the IMS standard, the resource's href must also
    # be listed as a file reference.
    
    imsfile = ims.contentpackage.File()
    imsfile.attrs["href"] = filename
    imsresource.files.append(imsfile)

class EClass:
    """ 
    The purpose of this class is to handle issues specific to EClass
    that do not necessarily fall under IMSCP functionality. Such as
    creating and managing .ecp files, while still making the output
    100% IMSCP-compatibile.    
    """
    def __init__(self, filename):
        self.filename = filename
        self.imscp = ims.contentpackage.ContentPackage()
        if os.path.exists(self.filename):
            self.imscp.loadFromXML(self.filename)
            
        generator = ims.contentpackage.Contributor()
        generator.role.source["x-none"] = "LOMv1.0"
        generator.role.value["x-none"] = "Creator"
        generator.centity.vcard="BEGIN:vCard FN:EClass Builder v%s END:vCard" % version.asString()
        
        self.imscp.metadata.lom.metametadata.contributors.append(generator)
            
    def saveAsIMSCP(self, filename=None):
        self.imscp.saveAsXML(self.filename)


class EClassTests(unittest.TestCase):
    def testCreateEClass(self):
        import tempfile
        tempdir = tempfile.mkdtemp()
        eclassdir = os.path.join(tempdir, "testEClass")
        createEClass(eclassdir)
        
        for adir in constants.eclassdirs:
            self.assert_(os.path.exists(os.path.join(eclassdir, adir)))
            
        shutil.rmtree(tempdir)

        
def getTestSuite():
    return unittest.makeSuite(EClassTests)

if __name__ == '__main__':
    unittest.main()