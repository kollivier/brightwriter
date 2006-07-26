from BaseTheme import *
import settings
themename = "Simple"
isPublic = True

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent=None, dir=""):
		BaseHTMLPublisher.__init__(self, parent, dir)
		self.themedir = os.path.join(settings.AppDir, "themes", themename)
		self.isPublic = True
		
	def CreateTOC(self):
		return
		
