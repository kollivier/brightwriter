import wx
import sys, string
import utils

browserlist = []

if sys.platform.startswith("win32"): 
    import wx.lib.iewin
    browserlist.append("ie")


try: 
    import wx.html
    browserlist.append("htmlwindow")
except:
    pass

if sys.platform.startswith("darwin"): 
    try:
        import wx.webkit
        browserlist.append("webkit")
    except:
        pass
    
def getDefaultBrowser():
    global browserlist
    default = "htmlwindow"
    if sys.platform.startswith("win") and "ie" in browserlist:
        default = "ie"
    elif sys.platform.startswith("darwin") and "webkit" in browserlist:
        default = "webkit"

    return default

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

        if preferredBrowser == "":
            preferredBrowser = getDefaultBrowser()
            
        assert preferredBrowser != ""

        if string.lower(preferredBrowser) == "ie":
            if self._LoadIE():
                return
        elif string.lower(preferredBrowser) == "webkit":
            if self._LoadWebKitWindow():
                return
        elif string.lower(preferredBrowser) == "htmlwindow":
            if self._LoadHTMLWindow():
                return
        else:
            if self.browser == None:
                print "Error: No browser could be found."

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
        if self.engine == "mozilla" or self.engine == "webkit":
            if self.engine == "webkit":
                url = "file://" + url
                url = string.replace(url, " ", "%20")
            self.browser.LoadURL(url)
        elif self.engine == "ie":
            self.browser.Navigate(url)
        else:
            self.browser.LoadPage(url)
            
    def SetPage(self, text):
        if self.engine == "ie":
            self.browser.LoadString(text)
        elif self.engine == "webkit":
            self.browser.SetPageSource(text)
        else:
            self.browser.SetPage(text)

    def GetBrowserName(self):
        if self.engine == "webkit":
            return "Safari"
        elif self.engine == "ie":
            return "Internet Explorer"
        else:
            return "HTML Window"

    def Refresh(self):
        if self.engine == "mozilla":
            self.browser.Reload()
        elif self.engine == "ie":
            self.browser.Refresh(wxIEHTML_REFRESH_COMPLETELY)
        else:
            self.browser.LoadPage(self.currenturl)

    def _LoadIE(self):
        try:
            global browserlist
            if not "ie" in browserlist:
                return False

            self.browser = wx.lib.iewin.IEHtmlWindow(self.parent, self.id)
            self.engine = "ie"
            return True
        except:
            return False

    def _LoadHTMLWindow(self):
        try:
            global browserlist
            if not "htmlwindow" in browserlist:
                return False

            self.browser = wx.html.HtmlWindow(self.parent, self.id)
            self.engine = "htmlwindow"
            return True
        except:
            return False

    def _LoadWebKitWindow(self):
        try:
            global browserlist
            if not "webkit" in browserlist:
                return False 

            self.browser = wx.webkit.WebKitCtrl(self.parent, self.id)
            self.engine = "webkit"
            return True
        except:
            return False
