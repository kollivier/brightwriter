from BaseTheme import *
themename = "Default (frames)"

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)

	def CreateTOC(self):
		filename = self._GetFilename(self.pub.nodes[0].content.filename)

		text = """level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename, string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""))
		text = text + self.AddJoustItems(self.pub.nodes[0], 1)
		if self.pub.settings["SearchEnabled"] != "" and int(self.pub.settings["SearchEnabled"]):
			if self.pub.settings["SearchProgram"] == "Swish-e":
				searchscript = "../cgi-bin/search.py"
				text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", searchscript, "Search")
			elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
				text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", "../gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0", "Search")
		file = open(os.path.join(self.themedir,"frame.tpl"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "index.htm"), "w")
		data = string.replace(data, "<!-- INSERT INDEX PAGE HERE -->", "pub/" + os.path.basename(filename))
		data = string.replace(data, "<!-- INSERT CLASS TITLE HERE -->", self.pub.nodes[0].content.metadata.name)
		data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
		file.write(data)
		file.close()

	def _GetFilename(self, filename):
		extension = string.split(filename, ".")[-1]
		publisher = None
		for plugin in myplugins:
			if extension in plugin["Extension"]:
				publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
		if publisher: 
			try:
				filename = "pub/" + publisher.GetFilename(filename)
			except: 
				pass
		else:
			filename = string.replace(filename, "\\", "/")
		return filename

	def GetContentsPage(self):
		if os.path.exists(os.path.join(self.themedir,"frame.tpl")):
			return "index.htm"

	def AddJoustItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = self._GetFilename(root.content.filename) 

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