from __future__ import print_function
import string, sys, os
import plugins
import settings
import ims
import ims.utils
import appdata
import conman

plugin_info = { "Name":"file", 
                "FullName":"File", 
                "Directory":"File", 
                "Extension":["*"], 
                "Mime Type": "",
                "IMS Type": "webcontent",
                "Requires":"",
                "CanCreateNew":False}


class HTMLPublisher(plugins.BaseHTMLPublisher):

    def GetData(self):
        return None
        
    def Publish(self, parent=None, node=None, dir=None):
        return


class EditorDialog:
    def __init__(self, parent, item):
        self.item = item
        self.parent = parent

    def ShowModal(self):
        import guiutils
        filename = None
        if isinstance(self.item, conman.conman.ConNode):
            filename = self.item.content.filename
            
        elif isinstance(self.item, ims.contentpackage.Item):
            resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.item)
            if resource:
                filename = resource.getFilename()
            
        myFilename = os.path.join(settings.ProjectDir, filename)
        result = False

        print(myFilename)
        if os.path.exists(myFilename):
            print("File exists!")
            result = guiutils.sendCommandToApplication(myFilename, "open")

        if not result:
            result = PagePropertiesDialog(parent, parent.CurrentItem, parent.CurrentItem.content, os.path.join(parent.ProjectDir, "Text")).ShowModal()

        return result