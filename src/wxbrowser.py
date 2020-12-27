from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
import atexit
import json
import logging
import os
import platform
import sys
import time
import urllib.parse
import utils
import webbrowser

import wx

from wx.lib.pubsub import pub

import settings

browserlist = []

logging.info("Loading wxBrowser")

try:
    import wx.html2 as webview
    browserlist.append("webview")
except:
    pass

try:
    if True:  # not sys.platform.startswith("darwin"):
        from cefpython3 import cefpython
        WindowUtils = cefpython.WindowUtils()
        browserlist.append("cef")
        logging.info("CEFPython loaded")
except Exception as e:
    import traceback
    logging.error("Unable to import CEFPython")
    logging.error(traceback.format_exc())

if sys.platform.startswith("darwin"):
    try:
        import wx.webkit
        browserlist.append("webkit")
    except:
        pass
    
if "cef" in browserlist:
    cef_dir = os.path.dirname(cefpython.__file__)
    log_filename = os.path.join(settings.getAppDataDir(), "chromium.log")
    if os.path.exists(log_filename):
        os.remove(log_filename)
    settings = {
        "debug": True,
        "log_severity": cefpython.LOGSEVERITY_INFO,
        "log_file": log_filename,
    }
    if 'darwin' in sys.platform:
        cefpython_dir = os.path.dirname(os.path.abspath(cefpython.__file__))
        cef_framework_dir = os.path.join(cefpython_dir, 'Chromium Embedded Framework.framework')
        settings['external_message_pump'] = True
        settings['framework_dir_path'] = cef_framework_dir
        settings["resources_dir_path"] = os.path.join(cef_framework_dir, 'Resources')
        settings["browser_subprocess_path"] = os.path.join(cefpython_dir, 'subprocess')
    cefpython.Initialize(settings)
    logging.info("CEFPython initialized.")
    
    @atexit.register
    def ShutDown():
        cefpython.Shutdown()
    
    class ClientHandler(object):
        # --------------------------------------------------------------------------
        # RequestHandler
        # --------------------------------------------------------------------------
        loaded = False
        controller = None

        def __init__(self, controller):
            self.controller = controller

        def OnBeforePopup(self, browser, frame, targetUrl, targetFrameName, 
                targetDisposition, userGesture, popupFeatures, windowInfo, client):

            if self.loaded:
                self.controller.ProcessAppURL(targetUrl)
            # Always return True as there is no cross-platform support for having the browser natively
            # create its own popup window yet.
            return True

        def OnBeforeBrowse(self, browser, frame, request, user_gesture, is_redirect):
            url = request.GetUrl()

            if self.callback is not None:
                self.callback(url)
                return True

            if self.loaded:
                return self.controller.ProcessAppURL(url)

            return False

        def OnKeyEvent(self, browser, event, event_handle):
            if event["type"] == cefpython.KEYEVENT_KEYUP:
                # OnKeyEvent is called twice for F5/Esc keys, with event
                # type KEYEVENT_RAWKEYDOWN and KEYEVENT_KEYUP.
                # Normal characters a-z should have KEYEVENT_CHAR.
                return False
            if sys.platform.startswith("darwin"):
                print("OnKeyEvent, modifiers = %r, keyCode = %r" % (event["modifiers"], event["native_key_code"]))
                if event["modifiers"] == 128:
                    if event["native_key_code"] == 7:
                        browser.GetFocusedFrame().Cut()
                        return True
                    elif event["native_key_code"] == 8:
                        browser.GetFocusedFrame().Copy()
                        return True
                    elif event["native_key_code"] == 9:
                        browser.GetFocusedFrame().Paste()
                        return True
            return False

        def OnLoadEnd(self, browser, frame, http_code):
            if frame == browser.GetMainFrame():
                self.loaded = True

                jsBindings = cefpython.JavascriptBindings(
                        bindToFrames=True, bindToPopups=True)
                jsBindings.SetObject("app", self.controller)
                browser.SetJavascriptBindings(jsBindings)
                self.controller.jsBindings = jsBindings
    

def getDefaultBrowser():
    global browserlist

    if False:  # sys.platform.startswith("darwin") and "webkit" in browserlist:
        default = "webkit"
    elif "cef" in browserlist:
        default = "cef"
    elif "webview" in browserlist:
        default = "webview"
    elif sys.platform.startswith("win") and "ie" in browserlist:
        default = "ie"

    return default

class wxBrowser(wx.Panel):
    """
    Wrapper for the various HTML engines available in wxPython. It will first try to load
    the standard browsers (IE, Safari and Chrome) and will default to wxHtmlWindow if neither is
    available. Users can also specify the preferred browser in the constructor to choose a
    specific browser. However, if that browser is not available, a fallback will be automatically
    chosen. The developer can find out which engine they are using by checking the engine property.

    Example:

    > mybrowser = wxBrowser(parent, -1, "webview")
    > mybrowser.LoadPage("http://www.google.com")
    > print mybrowser.engine
    webview

    """
    def __init__(self, parent, id, preferredBrowser="", messageHandler=None):
        wx.Panel.__init__(self, parent, id, style=wx.WANTS_CHARS)
        self.parent = parent
        self.id = id
        self.browser = None
        self.messageHandler = messageHandler
        self.currenturl = ""
        self.engine = ""
        self.OnPageChanged = lambda x: x
        self.OnStatusChanged = lambda x,y: x
        self.OnTitleChanged = lambda x: x
        self.OnProgress = lambda x: x

        if not preferredBrowser:
            preferredBrowser = getDefaultBrowser()
            
        assert preferredBrowser

        logging.info("Preferred browser = %r" % preferredBrowser)

        if preferredBrowser.lower() == "webview":
            if self._LoadWebViewWindow():
                return
        elif preferredBrowser.lower() == "cef":
            self.callback = None
            parent = self
            if sys.platform.startswith("darwin"):
                parent = self.parent
                try:
                    # noinspection PyUnresolvedReferences
                    from AppKit import NSApp
                    # Make the content view for the window have a layer.
                    # This will make all sub-views have layers. This is
                    # necessary to ensure correct layer ordering of all
                    # child views and their layers. This fixes Window
                    # glitchiness during initial loading on Mac (Issue #371).
                    NSApp.windows()[0].contentView().setWantsLayer_(True)
                except ImportError:
                    logging.error("PyObjC needs to be installed to use Chromium on Mac.")
            window_info = cefpython.WindowInfo()
            settings = {
                'dom_paste_disabled': False
            }
            (width, height) = parent.GetClientSize().Get()
            window_info.SetAsChild(self.GetHandle(),
                                   [0, 0, width, height])
            self.browser = cefpython.CreateBrowserSync(window_info, settings=settings,
                                                       url="about:blank")

            client = ClientHandler(self)
            client.callback = None
            self.browser.SetClientHandler(client)

            self.timer = None
            self.CreateCEFTimer()

            self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
            self.Bind(wx.EVT_SIZE, self.OnSize)

        elif preferredBrowser.lower() == "ie":
            if self._LoadIE():
                return
        elif preferredBrowser.lower() == "webkit":
            if self._LoadWebKitWindow():
                return
        else:
            if self.browser is None:
                print("Error: No browser could be found.")

        self.engine = preferredBrowser
        self.SetBrowserFocus()

        if not self.engine == "cef":
            self.Sizer = wx.BoxSizer(wx.VERTICAL)
            self.Sizer.Add(self.browser, 1, wx.EXPAND)

    def OnSetFocus(self, _):
        if not self.browser or not self.engine == "cef":
            return
        if sys.platform.startswith("win"):
            WindowUtils.OnSetFocus(self.GetHandle(),
                                   0, 0, 0)
        self.browser.SetFocus(True)

    def OnSize(self, _):
        logging.info("OnSize called...")
        if not self.browser or not self.engine == "cef":
            return
        if platform.system() == "Windows":
            WindowUtils.OnSize(self.GetHandle(),
                               0, 0, 0)
        elif platform.system() == "Linux":
            (x, y) = (0, 0)
            (width, height) = self.GetSize().Get()
            self.browser.SetBounds(x, y, width, height)
        self.browser.NotifyMoveOrResizeStarted()

    def CreateCEFTimer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnCEFTimer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def OnCEFTimer(self, event):
        cefpython.MessageLoopWork()

    def SetBrowserFocus(self):
        if not self.browser:
            return

        if self.engine == "cef":
            if sys.platform.startswith('win'):
                WindowUtils.OnSetFocus(self.parent.GetHandle(),
                                       0, 0, 0)
            self.browser.SetFocus(True)
        else:
            self.browser.SetFocus()

    def OnClose(self, _):
        if self.browser and self.engine == "cef":
            logging.info("Shutting down Chromium...")
            self.browser.ParentWindowWillClose()
            self.browser = None

    def EditorReady(self):
        print("Sending page loaded event?")
        pub.sendMessage("page_load_complete")

    def GoBack(self):
        if self.engine == "ie":
            self.browser.GoBack()
        else:
            self.browser.HistoryBack()

    def GoForward(self):
        if self.engine == "ie":
            self.browser.GoForward()
        else:
            self.browser.HistoryForward()

    def LoadPage(self, url):
        self.currenturl = url
        self.editable = False  # Disable editing behavior when we reload.
        logging.info("Loading URL %r" % url)
        logging.info("engine = %s" % self.engine)
        if self.engine in ["webkit", "webview"]:
            if not url.startswith('http'):
                url = "file://" + url
            url = url.replace(" ", "%20")
            self.browser.LoadURL(url)
        elif self.engine == "ie":
            self.browser.Navigate(url)
        elif self.engine == "cef":
            prefix = ''
            if not url.startswith('http'):
                prefix = "file://"
                if sys.platform.startswith("win"):
                    prefix += "/"  # Windows has a third slash before a file URL
                if not os.path.exists(url):
                    logging.warning("File %s doesn't exist, not loading." % url)
                    return
            url = prefix + url
            logging.info("full URL is %s" % url)
            self.browser.GetMainFrame().LoadUrl(url)
        else:
            self.browser.LoadPage(url)

    def OnWebViewLoaded(self, event):
        logging.info("On WebView loaded called?")
        pub.sendMessage("page_load_complete")

    def OnWebKitLoad(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            logging.info("Sending page load complete?")
            pub.sendMessage("page_load_complete")

    def ProcessAppURL(self, url):
        data = urllib.parse.urlparse(url)
        args = urllib.parse.parse_qs(data.query)
        if data.scheme == "bw":
            if self.messageHandler and hasattr(self.messageHandler, data.netloc):
                method = "self.messageHandler." + data.netloc + "(args)"
                eval(method)
            
            return True
        return False

    def OnWebKitBeforeLoad(self, event):
        print("OnWebKitBeforeLoad called with %r" % event.URL)
        if self.ProcessAppURL(event.URL):
            event.Cancel()
            return

        if event.GetNavigationType() == wx.webkit.WEBKIT_NAV_LINK_CLICKED:
            if self.editable:
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
            self.browser.GetMainFrame().LoadString(text, baseurl)

    def GetPageSource(self):
        if self.engine == "webkit":
            return self.EvaluateJavaScript("var xml = new XMLSerializer();xml.serializeToString(document)")

    def GetBrowserName(self):
        if self.engine == "webkit":
            return "Safari"
        elif self.engine == "cef":
            return "Chromium"
        elif self.engine == "ie":
            return "Internet Explorer"
        else:
            return "HTML Window"

    def Reload(self):
        if self.engine == "ie":
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
        logging.debug("value = %r" % json_value[:500])
        data = json.loads(json_value)
        if self.callback:
            self.callback(data['value'])
        self.callback = None

    def EvaluateJavaScript(self, script, callback=None):

        #print("Running script %s" % script)
        self.js_return_value = None
        if self.engine in ["webkit", "webview"]:
            if callback:
                return callback(self.browser.RunScript(script))
            return self.browser.RunScript(script)
        elif self.engine == "cef":
            if not hasattr(self, 'jsBindings') or not self.jsBindings:
                callback = None

            if callback:
                self.callback = callback
                script = "app.SendJSValue(JSON.stringify({value: %s}))" % script
            self.browser.GetMainFrame().ExecuteJavascript(script)
            return ""

    def ExecuteEditCommand(self, command, value=None):
        value_exec = ""
        if value is not None:
            value = value.replace("\n", "\\\n")
            value_exec = ", '%s'" % value
        self.EvaluateJavaScript("document.execCommand('%s', false%s)" % (command, value_exec))

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
