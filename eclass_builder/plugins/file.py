import string, sys, os
import plugins

plugin_info = {	"Name":"file", 
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


class EditorDialog:
	def __init__(self, parent, item):
		self.item = item
		self.parent = parent

	def ShowModal(self):
		import guiutils
		myFilename = os.path.join(settings.ProjectDir, self.item.content.filename)
		result = False

		if os.path.exists(myFilename):
			result = guiutils.sendCommandToApplication(myFilename, "open")

		if not result:
			result = PagePropertiesDialog(parent, parent.CurrentItem, parent.CurrentItem.content, os.path.join(parent.ProjectDir, "Text")).ShowModal()

		return result