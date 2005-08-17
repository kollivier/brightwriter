
from BaseTheme import *
themename = "Simple"
isPublic = True

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)
		self.isPublic = True
		
	def CreateTOC(self):
		return
		
