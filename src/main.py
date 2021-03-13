from builtins import object
import datetime
import glob
import logging
import os
import shutil
import string
import sys

if hasattr(sys, 'frozen'):
    class StdErrLog(object):
        def __init__(self):
            self.log = ""

        def write(self, msg):
            self.log += msg + "\n"

        def flush(self):
            pass

    class StdOutLog(object):
        def __init__(self):
            self.log = ""

        def write(self, msg):
            self.log += msg + "\n"

        def flush(self):
            pass

    sys.stdout = StdOutLog()
    sys.stderr = StdErrLog()

logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)

import settings
settings.logfile = os.path.join(settings.getAppDataDir(), 'BrightWriter.log')
logging.info("Settings imported")

formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
file_handler = logging.FileHandler(filename=settings.logfile, mode='w')
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)
logging.getLogger('EClass').addHandler(file_handler)

log = logging # .getLogger('BrightWriter')
# log.setLevel(logging.DEBUG)

logging.info("Importing version")
import version

log.info("Starting %s %s" % (settings.app_name, version.asString()))
log.info(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))

# do this first because other modules may rely on _()
import i18n
lang_dict = i18n.installEClassGettext()

import pew

cwd = os.path.dirname(sys.argv[0])

rootdir = os.path.abspath(cwd)

# os.path.dirname will chop the last dir if the path is to a directory
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)

import settings, appdata, errors
import conman.xml_settings as xml_settings
import conman.vcard as vcard
import gui
import fileutils

# workaround for http://bugs.python.org/issue843590
import encodings
encodings.aliases.aliases['macintosh'] = 'mac_roman'

use_wx = True
try:
    import wx
    import wxblox.events as events
    import guiutils
    import gui.error_viewer as error_viewer
except Exception as e:
    logging.warning("Unable to import wxPython.")
    import traceback
    logging.warning(traceback.format_exc(e))

oldexcepthook = sys.excepthook
if getattr(sys, 'frozen', False):
    # if we're running as an app, show the user a dialog when an error happens
    # so they can report it, and potentially continue.
    sys.excepthook = error_viewer.guiExceptionHook

#imports for packaging tools
if sys.platform.startswith("win"):
    import ctypes
    import ctypes.wintypes

if use_wx:
    import wx.stc
    import wx.lib.pubsub


use_pew_cache = False
try:
    import pew.cache
    use_pew_cache = True
except:
    pass

settings.AppDir = rootdir


if use_wx:
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
                    raise
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
                message = _("EClass could not load the following vCards from your Contacts folder: %(badCards)s. You may want to try deleting these cards and re-creating or re-importing them.") % {"badCards":repr(errCards)}
                wx.MessageBox(message)


for arg in sys.argv:
    if arg == "--debug":
        debug = 1
    elif arg == "--webkit":
        settings.webkit = True

if use_wx:
    app = BuilderApp(0)
    app.MainLoop()
else:
    import gui.app

    app = gui.app.Application()
    app.run()

