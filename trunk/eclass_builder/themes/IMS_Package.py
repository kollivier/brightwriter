
from BaseTheme import *
themename = "IMS Package"
isPublic = False

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)
		self.isPublic = False
