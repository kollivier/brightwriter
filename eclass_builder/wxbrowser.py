from wxPython.wx import *
import string

class wxBrowser:
	"""
	Wrapper for the various HTML engines available in wxPython. It will first try to load
	the standard browsers (Mozilla, then IE) and will default to wxHtmlWindow if neither is
	available. Users can also specify the preferred browser in the constructor to choose a
	specific browser. However, if that browser is not available, a fallback will be automatically
	chosen. The developer can find out which engine they are using by checking the engine property.

	Example:

	> mybrowser = wxBrowser(parent, -1, "Mozilla")
	> mybrowser.LoadPage("http://www.google.com")
	> print mybrowser.engine
	Mozilla

	"""
	def __init__(self, parent, id, preferredBrowser=""):
		self.parent = parent
		self.id = id
		self.browser = None
		self.currenturl = ""
		self.engine = ""

		if preferredBrowser != "":
			if string.lower(preferredBrowser) == "mozilla":
				if self._LoadMozilla():
					return
			elif string.lower(preferredBrowser) == "ie":
				if self._LoadIE():
					return 
			elif string.lower(preferredBrowser) == "htmlwindow":
				if self._LoadHTMLWindow():
					return 

		#default order - Mozilla, IE, HTMLWindow
		if self._LoadMozilla():
			return 
		
		if self._LoadIE():
			return 

		if self._LoadHTMLWindow():
			return 

		return None #should never happen, but...

	def GoBack(self):
		if self.engine == "mozilla":
			if self.browser.CanGoBack():
				self.browser.GoBack()
		elif self.engine == "ie":
			self.browser.GoBack()
		else:
			self.browser.HistoryBack()

	def GoForward(self):
		if self.engine == "mozilla":
			if self.browser.CanGoForward():
				self.browser.GoForward()
		elif self.engine == "ie":
			self.browser.GoForward()
		else:
			self.browser.HistoryForward()

	def LoadPage(self, url):
		self.currenturl = url
		if self.engine == "mozilla":
			self.browser.LoadURL(url)
		elif self.engine == "ie":
			self.browser.Navigate(url)
		else:
			self.browser.LoadPage(url)

	def Refresh(self):
		if self.engine == "mozilla":
			self.browser.Reload()
		elif self.engine == "ie":
			self.browser.Refresh(wxIEHTML_REFRESH_COMPLETELY)
		else:
			self.browser.LoadPage(self.currenturl)

	def _LoadMozilla(self):
		try:
			from wxPython.mozilla import *
			self.browser = wxMozillaBrowser(self.parent, self.id)
			self.engine = "mozilla"
			return True
		except:
			return False

	def _LoadIE(self):
		try:
			if wxPlatform != "__WXMSW__":
				return False
			else:
				from wxPython.iewin import *
				self.browser = wxIEHtmlWin(self.parent, self.id)
				self.engine = "ie"
				return True
		except:
			return False

	def _LoadHTMLWindow(self):
		try:
			from wxPython.html import wxHtmlWindow
			self.browser = wxHtmlWindow(self.parent, self.id)
			self.engine = "htmlwindow"
			return True
		except:
			return False