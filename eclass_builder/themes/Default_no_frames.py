from BaseTheme import *
themename = "Default (no frames)"

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)

	def CreateTOC(self):
		filename = "../pub/" + self._GetFilename(self.pub.nodes[0].content.filename)

		text = """foldersTree = gFld("%s", "%s")\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename)
		text = text + self.AddTOCItems(self.pub.nodes[0], 1)
		if self.pub.settings["SearchEnabled"] != "" and int(self.pub.settings["SearchEnabled"]):
			if self.pub.settings["SearchProgram"] == "Swish-e":
				searchscript = "../cgi-bin/search.py"
				text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", searchscript)
			elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
				text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", "/gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0")
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
		data = string.replace(data, "<!-- INSERT FIRST PAGE HERE -->", "pub/" + self._GetFilename(self.pub.nodes[0].content.filename))
		file.write(data)
		file.close()

	def AddTOCItems(self, nodes, level):
		text = ""
		for root in nodes.children:
			filename = ""
			if string.find(root.content.filename, "imsmanifest.xml") != -1:
					root = root.pub.nodes[0]

			filename = "../pub/" + self._GetFilename(root.content.filename) 

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
					text = text + """level%sNode = insFld(%s, gFld("%s", "%s"))\n""" % (level + 1, nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), "../Pub/" + filename)
					text = text + self.AddTOCItems(root, level + 1)
				else:
					text = text + """insDoc(%s, gLnk('S', "%s", "%s"))\n""" % (nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), "../Pub/" + filename)
			else:
				print "Item " + root.content.name + " is marked private and was not published."
		return text