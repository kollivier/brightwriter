from BaseTheme import *
themename = "Default (no frames)"
import utils
import settings
import ims
import appdata
import eclassutils

rootdir = "../"

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent=None, dir=""):
		BaseHTMLPublisher.__init__(self, parent, dir)
		self.themedir = os.path.join(settings.AppDir, "themes", themename)

	def CreateTOC(self):
		node = self.parent.imscp.organizations[0].items[0]
	
		resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, node)
		filename = eclassutils.getEClassPageForIMSResource(resource)
		if not filename:
			filename = resource.getFilename()
		filename = utils.GetFileLink(filename)

		text = """foldersTree = gFld("%s", "%s")\n""" % (string.replace(node.title.text, "\"", "\\\""), filename)
		text = text + self.AddTOCItems(node, 1)

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
		data = string.replace(data, "<!-- INSERT FIRST PAGE HERE -->", utils.GetFileLink(filename))
		file.write(data.encode("utf-8"))
		file.close()

	def AddTOCItems(self, node, level):
		text = ""
		for root in node.items:
			filename = ""

			resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, root)
			filename = eclassutils.getEClassPageForIMSResource(resource)
			if not filename:
				filename = resource.getFilename()
			filename =	rootdir + utils.GetFileLink(filename)

			nodeName = "foldersTree"
			if (level > 1):
				nodeName = "level" + `level` + "Node"
			if len(root.items) > 0:
				nodeType = rootdir + "Graphics/menu/win/chapter.gif"
			else:
				nodeType = rootdir + "Graphics/menu/win/page.gif"
			self.counter = self.counter + 1							   
		
			if len(root.children) > 0:
				text = text + """level%sNode = insFld(%s, gFld("%s", "%s"))\n""" % (level + 1, nodeName, string.replace(root.title.text, "\"", "\\\""), filename)
				text = text + self.AddTOCItems(root, level + 1)
			else:
				text = text + """insDoc(%s, gLnk('S', "%s", "%s"))\n""" % (nodeName, string.replace(root.title.text, "\"", "\\\""), filename)

		return text