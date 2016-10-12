import datetime
import glob
import os
import shutil
import string
import sys

import settings
settings.logfile = os.path.join(settings.getAppDataDir(), 'BrightWriter.log')

import logging

formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
logging.basicConfig(filename=settings.logfile, filemode='w', format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)
log = logging.getLogger('BrightWriter')
log.setLevel(logging.DEBUG)

import version

log.info("Starting %s %s" % (settings.app_name, version.asString()))
log.info(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))

# do this first because other modules may rely on _()
import i18n
lang_dict = i18n.installEClassGettext()

import wx

import gui.error_viewer as error_viewer

oldexcepthook = sys.excepthook
sys.excepthook = error_viewer.guiExceptionHook

rootdir = os.path.abspath(os.path.dirname(sys.argv[0]))

logging.info("rootdir = %r" % rootdir)
# os.path.dirname will chop the last dir if the path is to a directory
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)

logging.info("rootdir is now %r" % rootdir)

import settings, guiutils, appdata, errors
import conman.xml_settings as xml_settings
import conman.vcard as vcard
import wxblox.events as events
import gui
import fileutils
import externals.BeautifulSoup

import gui.error_viewer as error_viewer

# workaround for http://bugs.python.org/issue843590
import encodings
encodings.aliases.aliases['macintosh'] = 'mac_roman'

#imports for packaging tools
if sys.platform.startswith("win"):
    import ctypes
    import ctypes.wintypes
    import wx.stc


use_pew_cache = False
try:
    import pew.cache
    use_pew_cache = True
except:
    pass

settings.AppDir = rootdir
        
class BuilderApp(wx.App, events.AppEventHandlerMixin):
    def OnInit(self):
        events.AppEventHandlerMixin.__init__(self)
        
        self.SetAppName(settings.app_name)
        
        #wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 0)
        
        # initialize the environment
        self.LoadPrefs()
        self.LoadLanguage()
        self.SetDefaultDirs()
        self.CreateAppDirsIfNeeded()
        self.LoadVCards()

        import gui.main_frame
        self.frame = gui.main_frame.MainFrame2(None, -1, self.GetAppName())
        self.frame.CentreOnScreen()
        if use_pew_cache:
            pew.cache.set_cache_dir(settings.getAppDataDir())
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
        
    def OnExit(self):
        sys.excepthook = oldexcepthook
        return 0
        
    def CreateAppDirsIfNeeded(self):
        contactsdir = os.path.join(settings.PrefDir, "Contacts")
        if not os.path.exists(contactsdir):
            os.mkdir(contactsdir)
            
        if not os.path.exists(settings.AppSettings["ProjectsFolder"]):
            os.makedirs(settings.AppSettings["ProjectsFolder"])
    
    def LoadPrefs(self):
        settings.PrefDir = settings.getAppDataDir()

        settings.AppSettings = xml_settings.XMLSettings()
        if os.path.exists(os.path.join(settings.PrefDir, "settings.xml")):
            try:
                settings.AppSettings.LoadFromXML(os.path.join(settings.PrefDir, "settings.xml"))
            except:
                wx.MessageBox(_("Unable to load application preferences due to an error reading the file. Using default preferences."))
        
    def LoadLanguage(self):
        self.langdir = "en"
        if settings.AppSettings["Language"] == "English":
            self.langdir = "en"
        elif settings.AppSettings["Language"] == "Espanol":
            self.langdir = "es"
        elif settings.AppSettings["Language"] == "Francais":
            self.langdir = "fr"
        lang_dict[self.langdir].install()

    def SetDefaultDirs(self):
        #check settings and if blank, apply defaults
        coursefolder = settings.AppSettings["ProjectsFolder"]

        if coursefolder == "":
            settings.AppSettings["ProjectsFolder"] = settings.getProjectsDir()

    def LoadVCards(self):
        #load the VCards
        vcards = glob.glob(os.path.join(settings.PrefDir, "Contacts", "*.vcf"))
        errOccurred = False
        errCards = []
        for card in vcards:
            try:
                myvcard = vcard.VCard()
                myvcard.parseFile(os.path.join(settings.PrefDir, "Contacts", card))
                # accomodate for missing fields EClass expects
                if myvcard.fname.value == "":
                    myvcard.fname.value = myvcard.name.givenName + " "
                    if myvcard.name.middleName != "":
                        myvcard.fname.value = myvcard.fname.value + myvcard.name.middleName + " "
                    myvcard.fname.value = myvcard.fname.value + myvcard.name.familyName
                appdata.vcards[myvcard.fname.value] = myvcard
            except:
                errors.appErrorLog.write("Error loading vCard '%s'" % (card))
                errOccurred = True
                errCards.append(string.join(card, " "))

        if errOccurred:
            message = _("EClass could not load the following vCards from your Contacts folder: %(badCards)s. You may want to try deleting these cards and re-creating or re-importing them.") % {"badCards":`errCards`}
            wx.MessageBox(message)
        

for arg in sys.argv:
    if arg == "--debug":
        debug = 1
    elif arg == "--webkit":
        settings.webkit = True

app = BuilderApp(0)
app.MainLoop()
