import string, sys, os
from conman import plugins

plugin_info = {	"Name":"file", 
				"FullName":"File", 
				"Directory":"File", 
				"Extension":["*"], 
				"Mime Type": "",
				"Requires":"",
				"CanCreateNew":False}


class HTMLPublisher(plugins.BaseHTMLPublisher):

	def GetData(self):
		return None

	def GetFilename(self, filename):
		"""
		For the file plugin, we don't convert so filename doesn't change.
		"""

		return filename

class EditorDialog:
	def __init__(self, parent, item):
		self.item = item
		self.parent = parent

	def ShowModal(self):
		import guiutils
		myFilename = os.path.join(settings.CurrentDir, self.item.content.filename)
		result = False

		if os.path.exists(myFilename):
			result = guiutils.sendCommandToApplication(myFilename, "open")

		if not result:
			result = PagePropertiesDialog(parent, parent.CurrentItem, parent.CurrentItem.content, os.path.join(parent.CurrentDir, "Text")).ShowModal()

		return result