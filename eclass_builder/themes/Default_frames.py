from BaseTheme import *
themename = "Default (frames)"
import plugins
import utils

# all file links are relative to the directory specified here
rootdir = ""

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)

	def CreateTOC(self):
		filename = rootdir + utils.GetFileLink(self.pub.nodes[0].content.filename)

		text = u"""level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename, string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""))
		text = text + self.AddJoustItems(self.pub.nodes[0], 1)
		
		searchlink = self.GetSearchPageLink()
		if searchlink != "":
			text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", rootdir + searchlink, "Search")
			
		file = open(os.path.join(self.themedir,"frame.tpl"), "r")
		data = file.read().decode("utf-8")
		file.close()
		file = open(os.path.join(self.dir, "index.htm"), "w")
		data = string.replace(data, "<!-- INSERT INDEX PAGE HERE -->", "pub/" + os.path.basename(filename))
		data = string.replace(data, "<!-- INSERT CLASS TITLE HERE -->", self.pub.nodes[0].content.metadata.name)
		data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
		file.write(data.encode("utf-8"))
		file.close()

	def GetContentsPage(self):
		if os.path.exists(os.path.join(self.themedir,"frame.tpl")):
			return "index.htm"

	def AddJoustItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = rootdir + utils.GetFileLink(root.content.filename) 

			if not root.content.public == "false":
				if len(root.children) > 0:
					nodeType = "Book"
				else:
					nodeType = "Document"
				text = text + """level%sID = theMenu.addChild(level%sID,"%s", "%s", "%s", "%s");\n""" % (level + 1, level, nodeType, string.replace(root.content.metadata.name, "\"", "\\\""), filename, string.replace(root.content.metadata.name, "\"", "\\\""))

				if len(root.children) > 0:
					text = text + self.AddJoustItems(root, level + 1)
			else:
				print "Item " + root.content.metadata.name + " is marked private and was not published."
		return text			