
import sys, os, shutil
import utils
import unittest
import conman
import plugins
import ims
import ims.contentpackage
import eclassutils
import settings

if not os.path.exists(settings.AppDir):
    rootdir = os.path.abspath(sys.path[0])
    # os.path.dirname will chop the last dir if the path is to a directory
    if not os.path.isdir(rootdir):
        rootdir = os.path.dirname(rootdir)
        
    settings.AppDir = rootdir

class EClassIMSConverter:
    def __init__(self, filename):
        self.filename=filename
        self.id_namespace = u"URN:IMS-PLIRID-V0:"
        
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
        plugins.LoadPlugins()
        eclasspub = conman.ConMan()
        eclasspub.LoadFromXML(self.filename)
        
        imspackage = ims.contentpackage.ContentPackage()
        imspackage.filename = self.filename
        imspackage.metadata.lom.general.title[language] = eclasspub.name
        if not eclasspub.description == "":
            imspackage.metadata.lom.general.description[language] = eclasspub.description
        if not eclasspub.keywords == "":
            imspackage.metadata.lom.general.keyword[language] = eclasspub.keywords
        
        imspackage.organizations.append(ims.contentpackage.Organization())
        imspackage.organizations[0].attrs["identifier"] = self.id_namespace + eclasspub.orgid
        newitems = self._convertEClassNodes(eclasspub.nodes, language)
        for item in newitems:
            imspackage.organizations[0].items.append(item)
            
        newresources = self._convertEClassResources(eclasspub.content, language)
        for res in newresources:
            imspackage.resources.append(res)
        
        return imspackage
        
    def _convertEClassMetadata(self, node, imsnode, language):
        if not node.metadata.description == "":
            imsnode.metadata.lom.general.description[language] = node.metadata.description
        if not node.metadata.keywords == "":
            imsnode.metadata.lom.general.keyword[language] = node.metadata.keywords
        
        if not node.metadata.lifecycle.version == "":
            imsnode.metadata.lom.lifecycle.version[language] = node.metadata.lifecycle.version
        
        if not node.metadata.lifecycle.status == "": 
            imsnode.metadata.lom.lifecycle.status.source["x-none"] = "LOMv1.0" 
            imsnode.metadata.lom.lifecycle.status.value[language] = node.metadata.lifecycle.status
        
        for contrib in node.metadata.lifecycle.contributors:
            newcontrib = ims.contentpackage.Contributor()
            newcontrib.role.source["x-none"] = "LOMv1.0"
            newcontrib.role.value[language] = contrib.role
            newcontrib.date.datetime.text = contrib.date
            newcontrib.centity.vcard.text = contrib.entity.asString()
            imsnode.metadata.lom.lifecycle.contributors.append(newcontrib)
            
        if not node.metadata.rights.description == "":
            imsnode.metadata.lom.rights.description[language] = node.metadata.rights.description            
            
    def _convertEClassResources(self, resources, language):
        imsresources = []
        for resource in resources:
            imsresource = ims.contentpackage.Resource()
            imsresource.attrs["type"] = resource.type
            imsresource.attrs["identifier"] = self.id_namespace + resource.id
            self._convertEClassMetadata(resource, imsresource, language)
            
            # Since only EClass can read The EClass Page (ecp) format, 
            # The main file reference should be the html file it produces
            # EClass will check if there's an EClass page and use that if so.
            if os.path.splitext(resource.filename)[1] == ".ecp":
                eclassutils.setEClassPageForIMSResource(imsresource, resource.filename)
            else:
                imsresource.setFilename(resource.filename)
            
            imsresources.append(imsresource)
            
        return imsresources
    
    def _convertEClassNodes(self, nodes, language):
        imsItems = []
        for node in nodes:
            #print "newitem name is " + node.content.metadata.name
            newitem = ims.contentpackage.Item()
            newitem.attrs["identifier"] = self.id_namespace + node.id
            newitem.attrs["identifierref"] = self.id_namespace + node.content.id
            newitem.title.text = node.content.metadata.name
            
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
        
        lang="en-US"
        imspackage = converter.ConvertToIMSContentPackage(lang)
        self.assertEqual(imspackage.metadata.lom.general.title[lang], "12 Steps of Instructional Design")
        self.assertEqual(imspackage.organizations[0].items[0].title.text, "12 Steps of Instructional Design")
        #imspackage.saveAsXML(os.path.expanduser("~/imsmanifest.xml"))
        
    def testConvertEClassMetadata(self):
        filename = os.path.join(self.filesRootDir, "Metadata", "imsmanifest.xml")
        converter = EClassIMSConverter(filename)
        self.assert_(converter.IsEClass())
        
        lang="en-US"
        imspackage = converter.ConvertToIMSContentPackage(lang)
        #elf.assertEqual(imspackage.metadata.lom.general.title[lang], "12 Steps of Instructional Design")
        #self.assertEqual(imspackage.organizations[0].items[0].title.text, "12 Steps of Instructional Design")
        imspackage.saveAsXML(os.path.expanduser("~/imsmanifest.xml"))
        

def getTestSuite():
    return unittest.makeSuite(EClassIMSConverterTests)

if __name__ == '__main__':
    localedir = os.path.join(rootdir, 'locale')
    import gettext
    gettext.install('eclass', localedir)
    lang_dict = {
			"en": gettext.translation('eclass', localedir, languages=['en']), 
			"es": gettext.translation('eclass', localedir, languages=['es']),
			"fr": gettext.translation('eclass', localedir, languages=['fr'])
			}
			
    unittest.main()