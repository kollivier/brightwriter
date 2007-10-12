import string, sys, os, shutil, glob

rootdir = os.path.abspath(sys.path[0])
# os.path.dirname will chop the last dir if the path is to a directory
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)
    
# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
            "en": gettext.translation('eclass', localedir, languages=['en']), 
            "es": gettext.translation('eclass', localedir, languages=['es']),
            "fr": gettext.translation('eclass', localedir, languages=['fr'])
            }

import wx
import gui.error_viewer as errors
sys.excepthook = errors.guiExceptionHook

import settings, guiutils, appdata, errors
import conman.xml_settings as xml_settings
import conman.vcard as vcard
import wxblox.events as events
import gui
import fileutils

settings.AppDir = rootdir
new_editor = True
        
class BuilderApp(wx.App, events.AppEventHandlerMixin):
    def OnInit(self):
        events.AppEventHandlerMixin.__init__(self)
        
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 0)
        self.SetAppName("EClass.Builder")

        # initialize the environment
        self.LoadPrefs()
        self.LoadLanguage()
        self.SetDefaultDirs()
        self.CreateAppDirsIfNeeded()
        self.LoadVCards()

        global test_new_editor
        
        if new_editor:
            import gui.main_frame
            self.frame = gui.main_frame.MainFrame2(None, -1, "EClass.Builder")
        else:
            import editor
            self.frame = editor.MainFrame2(None, -1, "EClass.Builder")
                
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
        
    def CreateAppDirsIfNeeded(self):
        contactsdir = os.path.join(settings.PrefDir, "Contacts")
        if not os.path.exists(contactsdir):
            os.mkdir(contactsdir)
            
        if not os.path.exists(settings.AppSettings["CourseFolder"]):
            os.makedirs(settings.AppSettings["CourseFolder"])
    
    def LoadPrefs(self):
        settings.PrefDir = guiutils.getAppDataDir()
        oldprefdir = guiutils.getOldAppDataDir()

        # Move old AppDataDir if it exists.
        if oldprefdir and os.path.exists(oldprefdir) and not oldprefdir == settings.PrefDir:
            fileutils.CopyFiles(oldprefdir, settings.PrefDir, 1)
            shutil.rmtree(oldprefdir)

        settings.AppSettings = xml_settings.XMLSettings()
        if os.path.exists(os.path.join(settings.PrefDir, "settings.xml")):
            settings.AppSettings.LoadFromXML(os.path.join(settings.PrefDir, "settings.xml"))
        
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
        coursefolder = settings.AppSettings["CourseFolder"]
        gsdlfolder = settings.AppSettings["GSDL"]
        htmleditor = settings.AppSettings["HTMLEditor"]

        if coursefolder == "":
            settings.AppSettings["CourseFolder"] = guiutils.getEClassProjectsDir()

        if gsdlfolder == "":
            if sys.platform.startswith("win"):
                gsdlfolder = "C:\Program Files\gsdl"
            
            if os.path.exists(gsdlfolder):
                settings.AppSettings["GSDL"] = gsdlfolder       

        if htmleditor == "":
            if wxPlatform == '__WXMSW__':
                htmleditor = "C:\Program Files\OpenOffice.org1.0\program\oooweb.exe"
            
            if os.path.exists(htmleditor):
                settings.AppSettings["HTMLEditor"] = htmleditor

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
    elif arg == "--old-editor":
        new_editor = False

app = BuilderApp(0)
app.MainLoop()


import unittest

class UITests(unittest.TestCase):
    def setUp(self):
        self.app = BuilderApp(0)
        
    def tearDown(self):
        shutil.rmtree(self.tempdir)
        

def getTestSuite():
    return unittest.makeSuite(IndexingTests)

if __name__ == '__main__':
    unittest.main()