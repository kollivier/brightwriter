from __future__ import absolute_import
from .BaseTheme import *
import settings
themename = "IMS Package"
isPublic = False

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent=None, dir=""):
		BaseHTMLPublisher.__init__(self, parent, dir)
		self.themedir = os.path.join(settings.AppDir, "themes", themename)
		self.isPublic = False
