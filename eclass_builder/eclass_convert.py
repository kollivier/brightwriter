
import sys, os, shutil
import utils
import unittest
import conman
import ims
import ims.contentpackage

class EClassIMSConverter:
    def __init__(self, filename):
        self.filename=filename
        
    def IsEClass(self):
        myfile = utils.openFile(self.filename)
        data = myfile.read()
        myfile.close()
        
        return data.find("<PublicationID>") != -1
        
    def BackupEClass(self, backupfile):
        eclasspub = conman.ConMan()
        eclasspub.LoadFromXML(self.filename)
        eclasspub.ExportToZIP(backupfile)
        
    def ConvertToIMSContentPackage(self, language="en-US"):
        eclasspub = conman.ConMan()
        eclasspub.LoadFromXML(self.filename)
        print eclasspub.name
        
        imspackage = ims.contentpackage.ContentPackage()
        imspackage.metadata.lom.general.title[language] = eclasspub.name
        if not eclasspub.description == "":
            imspackage.metadata.lom.general.description[language] = eclasspub.description
        if not eclasspub.keywords == "":
            imspackage.metadata.lom.general.keyword[language] = eclasspub.keywords
        
        imspackage.organizations.append(ims.contentpackage.Organization())
        newitems = self._convertEClassNodes(eclasspub.nodes, language)
        for item in newitems:
            imspackage.organizations[0].items.append(item)
            
        newresources = self._convertEClassResources(eclasspub.content)
        for res in newresources:
            imspackage.resources.append(res)
        
        print "Num items = " + `len(imspackage.organizations[0].items)`
        
        return imspackage
        
    def _convertEClassMetadata(self, node, imsnode, language):
        if not node.content.metadata.description == "":
            imsnode.metadata.lom.general.description[language] = node.content.metadata.description
        if not node.content.metadata.keywords == "":
            imsnode.metadata.lom.general.keyword[language] = node.content.metadata.keywords
        
        if not node.content.metadata.lifecycle.version == "":
            imsnode.metadata.lom.lifecycle.version[language] = node.content.metadata.lifecycle.version
        
        if not node.content.metadata.lifecycle.status == "": 
            imsnode.metadata.lom.lifecycle.status.source["x-none"] = "LOMv1.0" 
            imsnode.metadata.lom.lifecycle.status.value[language] = node.content.metadata.lifecycle.status
        
        for contrib in node.content.metadata.lifecycle.contributors:
            newcontrib = ims.contentpackage.Contributor()
            newcontrib.role.source["x-none"] = "LOMv1.0"
            newcontrib.role.value[language] = contrib.role
            newcontrib.date.datetime.text = contrib.date
            newcontrib.centity.vcard = contrib.entity.asString()
            
    def _convertEClassResources(self, resources):
        imsresources = []
        for resource in resources:
            imsresource = ims.contentpackage.Resource()
            imsresource.attrs["type"] = resource.type
            imsresource.attrs["href"] = resource.filename
            imsresource.attrs["identifier"] = resource.id
            
            # According to the IMS standard, the resource's href must also
            # be listed as a file reference.
            imsfile = ims.contentpackage.File()
            imsfile.attrs["href"] = resource.filename
            imsresource.files.append(imsfile)
            
            imsresources.append(imsresource)
            
        return imsresources
    
    def _convertEClassNodes(self, nodes, language):
        imsItems = []
        for node in nodes:
            #print "newitem name is " + node.content.metadata.name
            newitem = ims.contentpackage.Item()
            newitem.attrs["identifier"] = node.id
            newitem.attrs["identifierref"] = node.content.id
            newitem.title.text = node.content.metadata.name
            self._convertEClassMetadata(node, newitem, language)
            
            if len(node.children) > 0:
                newchildren = self._convertEClassNodes(node.children, language)
                for child in newchildren:
                    newitem.items.append(child)
        
            imsItems.append(newitem)
        
        return imsItems
        
class EClassIMSConverterTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()
        rootdir = os.path.abspath(sys.path[0])
        if not os.path.isdir(rootdir):
            rootdir = os.path.dirname(rootdir)
        self.filesRootDir = os.path.join(rootdir, "testFiles", "eclassTest")
    
    def tearDown(self):
        shutil.rmtree(self.tempdir)
        
    def testConvertEClass(self):
        filename = os.path.join(self.filesRootDir, "12steps", "imsmanifest.xml")
        converter = EClassIMSConverter(filename)
        self.assert_(converter.IsEClass())
        zipfile = os.path.join(self.tempdir, "12steps.zip")
        converter.BackupEClass(zipfile)
        self.assert_(os.path.exists(zipfile))
        
        imspackage = converter.ConvertToIMSContentPackage()
        imspackage.saveAsXML(os.path.expanduser("~/imsmanifest.xml"))
        
        

def getTestSuite():
    return unittest.makeSuite(EClassIMSConverterTests)

if __name__ == '__main__':
    unittest.main()