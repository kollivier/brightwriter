from xmlutils import *

import appdata
import ims
import ims.contentpackage
import os
import settings
import sys

from externals.BeautifulSoup import BeautifulSoup

from core import *

import eclass
import file
import html
import quiz

pluginList = []

metaTags = ["name", "description", "keywords", "credit", "author", "url"]


def LoadPlugins():
    global pluginList

    pluginList.extend([eclass, file, html, quiz])

    # for item in os.listdir(os.path.join(settings.AppDir, "plugins")):
    #     if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
    #         plugin = string.replace(item, ".py", "")
    #         exec("import plugins." + plugin)
    #         exec("pluginList.append(plugins." + plugin + ")")


def GetPluginForFilename(filename):
    fileext = os.path.splitext(filename)[1][1:]
    return GetPluginForExtension(fileext)


def GetPluginForExtension(fileext):
    global pluginList
    for plugin in pluginList:
        if fileext in plugin.plugin_info["Extension"]:
            return plugin

    # As a default, return the file plugin
    for plugin in pluginList:
        if plugin.plugin_info["Name"] == "file":
            return plugin

    return None


def GetPlugin(name):
    global pluginList
    for plugin in pluginList:
        if plugin.plugin_info["Name"] == name or plugin.plugin_info["FullName"] == name:
            return plugin

    return None


def GetExtensionsForPlugin(name):
    plugin = self.GetPlugin(name)
    if plugin:
        return plugin.plugin_info["Extension"]

    return []


def GetPublisherForFilename(filename):
    publisher = None
    plugin = GetPluginForFilename(filename)
    if plugin:
        publisher = plugin.HTMLPublisher()
    
    return publisher

import unittest


class PluginTests(unittest.TestCase):
    def setUp(self):
        rootdir = os.path.abspath(os.path.join(sys.path[0], ".."))
        settings.AppDir = rootdir
        LoadPlugins()

        self.testdir = os.path.join(rootdir, "testFiles", "eclassTest", "TestEClass")
        print self.testdir
        appdata.currentPackage = self.cp = ims.contentpackage.ContentPackage()
        self.cp.loadFromXML(os.path.join(self.testdir, "imsmanifest.xml"))

        settings.ProjectDir = self.testdir
        settings.ProjectSettings["Theme"] = "Default (frames)"

    def tearDown(self):
        self.cp = None

    def testPublish(self):

        imsitem = self.cp.organizations[0].items[0]
        filename = ""
        import ims.utils
        resource = ims.utils.getIMSResourceForIMSItem(self.cp, imsitem)
        if resource:
            filename = resource.getFilename()

        self.assert_(os.path.exists(os.path.join(self.testdir, filename)))
        publisher = GetPublisherForFilename(filename)
        self.assert_(publisher)
        publisher.Publish(None, imsitem, dir=self.testdir)
        pub_filename = publisher.GetFileLink(filename)

        pub_path = os.path.join(self.testdir, pub_filename)
        self.assert_(os.path.exists(pub_path))
        print pub_path
        soup = BeautifulSoup(open(pub_path).read())

        html = """<p>Hello world!
<p>Test
"""
        self.assertEquals(soup.find("meta", attrs={"http-equiv":"description"})['content'], "A Description")
        self.assertEquals(soup.find("meta", attrs={"http-equiv":"keywords"})['content'], "keyword1, keyword2")
        self.assertEquals(soup.body, html)


def getTestSuite():
    return unittest.makeSuite(IndexingTests)

if __name__ == '__main__':
    sys.path.append(os.path.abspath(".."))
    import i18n
    i18n.installEClassGettext()

    unittest.main()
