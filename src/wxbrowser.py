import atexit
import json
import logging
import os
import sys
import time
import utils
import webbrowser

import wx

from wx.lib.pubsub import pub

browserlist = []

logging.info("Loading wxBrowser")

try:
    import wx.html2 as webview
    browserlist.append("webview")
except:
    pass

try:
    if not sys.platform.startswith("darwin"):
        from cefpython3 import cefpython
        import cefpython3.wx.chromectrl as cefwx
        browserlist.append("cef")
        logging.info("CEFPython loaded")
except Exception, e:
    import traceback
    logging.error("Unable to import CEFPython")
    logging.error(traceback.format_exc(e))

if sys.platform.startswith("darwin"):
    try:
        import wx.webkit
        browserlist.append("webkit")
    except:
        pass
    
if "cef" in browserlist:
    settings = {
        "log_severity": cefpython.LOGSEVERITY_INFO,
        "log_file": "chromium.log",
    }
    cefwx.Initialize(settings)
    
    @atexit.register
    def ShutDown():
        cefpython.Shutdown()
    
    class ClientHandler:
        # --------------------------------------------------------------------------
        # RequestHandler
        # --------------------------------------------------------------------------
        loaded = False
        controller = None

        def __init__(self, controller):
            self.controller = controller

        def OnBeforeBrowse(self, browser, frame, request, isRedirect):
            if self.callback is not None:
                self.callback(request.GetUrl())

            return self.loaded
        
        def OnLoadEnd(self, browser, frame, httpStatusCode):
            if frame == browser.GetMainFrame():
                self.loaded = True
                print("Sending page loaded event?")
                pub.sendMessage("page_load_complete")

                jsBindings = cefpython.JavascriptBindings(
                        bindToFrames=True, bindToPopups=True)
                jsBindings.SetObject("app", self.controller)
                browser.SetJavascriptBindings(jsBindings)
                self.controller.jsBindings = jsBindings
    

def getDefaultBrowser():
    global browserlist

    if sys.platform.startswith("darwin") and "webkit" in browserlist:
        default = "webkit"
    elif "cef" in browserlist:
        default = "cef"
    elif "webview" in browserlist:
        default = "webview"
    elif sys.platform.startswith("win") and "ie" in browserlist:
        default = "ie"

    return default

class wxBrowser(wx.Window):
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
        wx.Window.__init__(self, parent, id, style=wx.WANTS_CHARS)
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

        logging.info("Preferred browser = %r" % preferredBrowser)

        if preferredBrowser.lower() == "webview":
            if self._LoadWebViewWindow():
                return
        elif preferredBrowser.lower() == "cef":
            self.callback = None
            self.browser = cefwx.ChromeWindow(self, url="file://" + os.path.abspath(os.path.join("gui", "html", "index.html")), timerMillis=25, useTimer=True, style=wx.WANTS_CHARS)
            # self.browser.SetSizerProps(expand=True, proportion=1)



            # override the ChromeWindow __del__ handler, it calls Unbind when the
            # wx control is in an indeterminate state, which leads to a crash,
            # and in fact the Unbind call is not necessary.
            def delhandler(self):
                self.browser.CloseBrowser()
            self.browser.__del__ = delhandler
            client = ClientHandler(self)
            client.callback = None
            self.browser.GetBrowser().SetClientHandler(client)

        elif preferredBrowser.lower() == "ie":
            if self._LoadIE():
                return
        elif preferredBrowser.lower() == "webkit":
            if self._LoadWebKitWindow():
                return
        else:
            if self.browser is None:
                print "Error: No browser could be found."

        self.engine = preferredBrowser
        self.browser.SetFocus()

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.browser, 1, wx.EXPAND)

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
        self.editable = False  # Disable editing behavior when we reload.
        logging.info("Loading URL %r" % url)
        if self.engine in ["webkit", "webview"]:
            url = "file://" + url
            url = url.replace(" ", "%20")
            self.browser.LoadURL(url)
        elif self.engine == "ie":
            self.browser.Navigate(url)
        elif self.engine == "cef":
            if not os.path.exists(url):
                return
            self.browser.GetBrowser().GetMainFrame().LoadUrl("file://" + url)
        else:
            self.browser.LoadPage(url)

    def OnWebViewLoaded(self, event):
        logging.info("On WebView loaded called?")
        pub.sendMessage("page_load_complete")

    def OnWebKitLoad(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            logging.info("Sending page load complete?")
            pub.sendMessage("page_load_complete")

    def OnWebKitBeforeLoad(self, event):
        if self.editable and event.GetNavigationType() == wx.webkit.WEBKIT_NAV_LINK_CLICKED:
            event.Cancel()
        elif not self.editable and event.URL.startswith("http"):
            webbrowser.open(event.URL)
            event.Cancel()

    def SetPage(self, text, baseurl, mimetype="text/html"):
        self.editable = False
        if self.engine == "ie":
            self.browser.LoadString(text)
        elif self.engine == "webkit":
            self.browser.SetPageSource(text, baseurl)
        elif self.engine == "webview":
            self.browser.SetPage(text, baseurl)
        elif self.engine == "cef":
            self.browser.GetBrowser().GetMainFrame().LoadString(text, baseurl)

    def GetPageSource(self):
        if self.engine == "webkit":
            return self.EvaluateJavaScript("var xml = new XMLSerializer();xml.serializeToString(document)")

    def GetBrowserName(self):
        if self.engine == "webkit":
            return "Safari"
        elif self.engine == "ie":
            return "Internet Explorer"
        else:
            return "HTML Window"

    def Reload(self):
        if self.engine == "mozilla":
            self.browser.Reload()
        elif self.engine == "ie":
            self.browser.Refresh(wxIEHTML_REFRESH_COMPLETELY)
        else:
            self.LoadPage(self.currenturl)

    def MakeEditable(self, editable=True):
        logging.info("Calling MakeEditable")
        self.editable = editable

        if self.engine == "webview":
            logging.info("Calling SetEditable")
            self.browser.SetEditable(editable)
            assert self.browser.IsEditable() == editable
        elif self.engine == "webkit":
            self.browser.MakeEditable(editable)
        else:
            mode = 'on'
            if not editable:
                mode = 'off'
            self.EvaluateJavaScript("document.designMode = '%s'" % mode)

        self.ExecuteEditCommand("styleWithCSS", "true")
        self.EvaluateJavaScript('dirty = false; document.body.addEventListener("input", function() { dirty = true; }, false);')

    def SendJSValue(self, json_value):
        # Handle the JSON data, which is the Python dict: {foo: 'bar'}
        print("value = %r" % json_value)
        data = json.loads(json_value)
        self.js_return_value = data['value']
        print("js_return_value = %r" % self.js_return_value)

    def WaitForJSValue(self, timeout=0.5):
        elapsed = 0
        while not self.js_return_value and elapsed < timeout:
            time.sleep(0.05)
            elapsed += 0.05

        if self.js_return_value:
            return self.js_return_value

        return None

    def EvaluateJavaScript(self, script, returnsValue=False):
        #print("Running script %s" % script)
        self.js_return_value = None
        if self.engine in ["webkit", "webview"]:
            return self.browser.RunScript(script)
        elif self.engine == "cef":
            if not hasattr(self, 'jsBindings') or not self.jsBindings:
                returnsValue = False

            if returnsValue:
                script = "app.SendJSValue(JSON.stringify({value: %s}))" % script
            self.browser.GetBrowser().GetMainFrame().ExecuteJavascript(script)
            if returnsValue:
                return self.WaitForJSValue()
            return ""

    def ExecuteEditCommand(self, command, value=None):
        value_exec = ""
        if value is not None:
            value = value.replace("\n", "\\\n")
            value_exec = ", '%s'" % value
        return self.EvaluateJavaScript("document.execCommand('%s', false%s)" % (command, value_exec), returnsValue=False)

    def GetEditCommandValue(self, command):
        value = self.EvaluateJavaScript("document.queryCommandValue('%s')" % command, returnsValue=True)
        if not value:
            return ""

    def GetEditCommandState(self, command):
        value = self.EvaluateJavaScript("document.queryCommandState('%s')" % command, returnsValue=True)
        if not value:
            return ""

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

    def _LoadWebViewWindow(self):
        try:
            global browserlist
            if not "webview" in browserlist:
                return False

            logging.info("Loading webview...")
            self.browser = webview.WebView.New(self.parent)
            self.engine = "webview"
            self.browser.Bind(webview.EVT_WEB_VIEW_LOADED, self.OnWebViewLoaded)
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
            self.browser.Bind(wx.webkit.EVT_WEBKIT_STATE_CHANGED, self.OnWebKitLoad)
            self.browser.Bind(wx.webkit.EVT_WEBKIT_BEFORE_LOAD, self.OnWebKitBeforeLoad)
            return True
        except:
            return False