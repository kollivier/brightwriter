from wxPython.wx import *
import string

browserlist = []

try:
	from wxPython.mozilla import *
	browserlist.append("mozilla")
except:
	pass 

try: 
	from wxPython.iewin import *
	browserlist.append("ie")
except:
	pass

try: 
	from wxPython.html import wxHtmlWindow
	browserlist.append("htmlwindow")
except:
	pass

try: 
	from wxPython.webkit import *
	browserlist.append("webkit")
except:
	pass


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
		self.OnPageChanged = lambda x: x
		self.OnStatusChanged = lambda x,y: x
		self.OnTitleChanged = lambda x: x
		self.OnProgress = lambda x: x

		if preferredBrowser != "":
			if string.lower(preferredBrowser) == "mozilla":
				if self._LoadMozilla():
					return
			elif string.lower(preferredBrowser) == "ie":
				if self._LoadIE():
					return 
			elif string.lower(preferredBrowser) == "webkit":
				if self._LoadWebKitWindow():
					return 
			elif string.lower(preferredBrowser) == "htmlwindow":
				if self._LoadHTMLWindow():
					return 

		#default order - WebKit (on Mac), Mozilla, IE, HTMLWindow
		if self._LoadWebKitWindow():
			return

		if self._LoadMozilla():
			return 
		
		if self._LoadIE():
			return 

		if self._LoadHTMLWindow():
			return 

		if self.browser == None:
			print "Error: No browser could be found."

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
			global browserlist
			if not "mozilla" in browserlist:
				return False

			self.browser = wxMozillaBrowser(self.parent, self.id)
			self.engine = "mozilla"

			def __OnUrlChanged(self, event):
				self.currenturl = event.GetNewURL()
				self.OnPageChanged(self.currenturl) 

			def __OnStatusChanged(self, event):
				self.OnStatusChanged(event.GetStatusText(), event.IsBusy())

			def __OnTitleChanged(self, event):
				self.OnTitleChanged(event.GetTitle())

			def __OnProgress(self, event):
				if event.GetTotalMaxProgress() != -1:
					self.OnProgress(float(event.GetTotalCurrentProgress()) /
									float(event.GetTotalMaxProgress()))
				elif event.GetSelfMaxProgress() != -1:
					self.OnProgress(float(event.GetSelfCurrentProgress()) /
									float(event.GetSelfMaxProgress()))

			#EVT_MOZILLA_URL_CHANGED(self.browser, -1, self.__OnUrlChanged)
			#EVT_MOZILLA_STATUS_CHANGED(self.browser, -1, self.__OnStatusChanged)
			#EVT_MOZILLA_TITLE_CHANGED(self.browser, -1, self.__OnTitleChanged)
			#EVT_MOZILLA_PROGRESS(self.browser, -1, self.__OnProgress)

			return True
		except:
			if self.browser:
				self.browser.Destroy()

			import traceback
			print traceback.print_exc()
			return False

	def _LoadIE(self):
		try:
			global browserlist
			if not "ie" in browserlist:
				return False

			self.browser = wxIEHtmlWin(self.parent, self.id)
			self.engine = "ie"
			return True
		except:
			return False

	def _LoadHTMLWindow(self):
		try:
			global browserlist
			if not "htmlwindow" in browserlist:
				return False

			self.browser = wxHtmlWindow(self.parent, self.id)
			self.engine = "htmlwindow"
			return True
		except:
			return False

	def _LoadWebKitWindow(self):
		try:
			global browserlist
			if not "webkit" in browserlist:
				return False 

			self.browser = wxWebKitCtrl(self.parent, self.id)
			self.engine = "webkit"
			return True
		except:
			return False