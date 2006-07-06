from BaseTheme import *
themename = "Default (no frames)"

rootdir = "../"

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)

	def CreateTOC(self):
		filename = rootdir + self._GetFilename(self.pub.nodes[0].content.filename)

		text = """foldersTree = gFld("%s", "%s")\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename)
		text = text + self.AddTOCItems(self.pub.nodes[0], 1)

		searchlink = self.GetSearchPageLink()
		if searchlink != "":
			text = text + """searchID = theMenu.addEntry(-1, "Document", "%s", "%s", "%s");\n""" % ("Search", rootdir + searchlink, "Search")

		file = open(os.path.join(self.themedir,"eclassNodes.js"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "eclassNodes.js"), "w")
		data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
		file.write(data)
		file.close()

		file = open(os.path.join(self.themedir,"index.tpl"), "r")
		data = file.read()
		file.close()
		file = open(os.path.join(self.dir, "index.htm"),"w")
		data = string.replace(data, "<!-- INSERT FIRST PAGE HERE -->", "pub/" + os.path.basename(self._GetFilename(self.pub.nodes[0].content.filename)))
		file.write(data.encode("utf-8"))
		file.close()

	def AddTOCItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = rootdir + self._GetFilename(root.content.filename) 

			if not root.content.public == "false":
				nodeName = "foldersTree"
				if (level > 1):
					nodeName = "level" + `level` + "Node"
				if len(root.children) > 0:
					nodeType = "../Graphics/menu/win/chapter.gif"
				else:
					nodeType = "../Graphics/menu/win/page.gif"
				self.counter = self.counter + 1                            
			
				if len(root.children) > 0:
					text = text + """level%sNode = insFld(%s, gFld("%s", "%s"))\n""" % (level + 1, nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), filename)
					text = text + self.AddTOCItems(root, level + 1)
				else:
					text = text + """insDoc(%s, gLnk('S', "%s", "%s"))\n""" % (nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), filename)
			else:
				print "Item " + root.content.metadata.name + " is marked private and was not published."
		return text