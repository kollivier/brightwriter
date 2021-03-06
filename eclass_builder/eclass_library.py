import sys, os
import wx

# this is needed for the freeze scripts.
import wxaddons.wxblox.events 
import wxaddons.wxblox.menus

import wxaddons.wxblox.events as eventblox
import wxaddons.wxblox.menus as menublox

#import psyco
#psyco.log()
#psyco.profile()

has_figleaf = False
try:
    import figleaf
    figleaf.start()
    has_figleaf = True
except:
    pass

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)

# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('library', localedir)
lang_dict = {
            "en": gettext.translation('library', localedir, languages=['en']), 
            "es": gettext.translation('library', localedir, languages=['es']),
            "fr": gettext.translation('library', localedir, languages=['fr'])
            }
            
# setup our translation system before importing project-specific files.
import settings
import utils
import guiutils

import library
import library.gui as libgui
import library.gui.MainFrame
import library.gui.constants as constants

class MyApp(wx.PySimpleApp, eventblox.AppEventHandlerMixin, menublox.MenuManager): #uiblox.AppUIManager, menublox.MenuManager):

    # because a dict randomly re-orders the keys so menus are not sequential
    menus = [
            _("&File"),
            _("&Edit"),
            _("&Library"),
            _("&Window"),
            _("&Help"),
            ]
            
    menuItems = {
            _("&File"):
            [
                (wx.ID_NEW, _("&New Library"), _("Create a new library")),
                (constants.ID_DEL_LIBRARY, _("&Delete Library"), _("Deletes a library from your collection.")),
            ],
            _("&Edit"):
            [
                (wx.ID_CUT, _("Cut\tCTRL+X"), _("Cut items")),
                (wx.ID_COPY, _("Copy\tCTRL+C"), _("Copy items")),
                (wx.ID_PASTE, _("Paste\tCTRL+V"), _("Paste Items")),
                (-1, "-", "-"),
                (wx.ID_SELECTALL, _("Select All\tCTRL+A"), _("Select all items")),
            ],
            _("&Library"):
            [
                (constants.ID_ADD_FILES, _("Add File(s)"), 
                            _("Add file(s) to current library.")),
                (constants.ID_ADD_FOLDERS, _("Add Folder(s)"), 
                            _("Add folder(s) to current library.")),
                (constants.ID_INDEX, _("&Index\tCTRL+R"),
                            _("Index files in contents folder.")),
                (constants.ID_UPDATE_INDEX, _("&Update Index\tCTRL+U"),
                            _("Update index for files in current library.")),
                (-1, "-", "-"),
                (constants.ID_LIB_SETTINGS, _("&Settings"),
                            _("View and set options for current library."))
            ],
            _("&Window"):
            [
                (constants.ID_PROPS, _("Property Editor\tCTRL+E"), _("Edit item properties")),
                (constants.ID_ERROR_LOG, _("Error Log"), _("View any program errors")),
            ],
            _("&Help"):
            [
                (wx.NewId(), _("Testing"), _("Testing...")),
            ],
    }
    
    def __init__(self, redirect=False):
        eventblox.AppEventHandlerMixin.__init__(self) 
        wx.PySimpleApp.__init__(self, redirect)      

    def OnInit(self):
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 0)
        self.SetAppName("EClass.Library")
        
        wx.App.SetMacPreferencesMenuItemId(constants.ID_APP_PREFS)
        # configure app-global settings.
        settings.AppDir = rootdir
        settings.PrefDir = guiutils.getAppDataDir()
        if not os.path.exists(settings.PrefDir):
            os.makedirs(settings.PrefDir)
            
        settings.ThirdPartyDir = os.path.join(settings.AppDir, "3rdparty", utils.getPlatformName())

        
        self.interfaceStyle = "MDI"
        self.CreateNewWindow()
        return True

    def OnExit(self):
        if has_figleaf:
            figleaf.stop()
            figleaf.write_coverage("eclass_library_run.figleaf")
        
        return True #wx.PySimpleApp.OnExit(self)

    def GetMenuBar():
        return self.GetTopWindow().GetMenuBar()

    def CreateNewWindow(self, filename=""):
        if self.interfaceStyle == "MFI":
            frame = libgui.MainFrame.MainFrame(None, -1, self.GetAppName(), size=(600, 400))
        elif self.interfaceStyle == "MDI":
            frame = libgui.MainFrame.AUIMainFrame(None, -1, self.GetAppName(), size=(600,400))

        frame.SetMenuBar(self.CreateMenuBar())
        frame.Show(True)
        self.SetTopWindow(frame)
        
app = MyApp(0)
app.MainLoop()

