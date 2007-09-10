import string, sys, os, shutil
import settings, guiutils
import conman.xml_settings as xml_settings
import wx

rootdir = os.path.abspath(sys.path[0])
# os.path.dirname will chop the last dir if the path is to a directory
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)

settings.AppDir = rootdir
test_new_editor = False

# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
            "en": gettext.translation('eclass', localedir, languages=['en']), 
            "es": gettext.translation('eclass', localedir, languages=['es']),
            "fr": gettext.translation('eclass', localedir, languages=['fr'])
            }

class MyApp(wx.App):
    def OnInit(self):
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 0)
        self.SetAppName("EClass.Builder")

        # initialize the environment
        self.LoadPrefs()
        self.LoadLanguage()
        self.SetDefaultDirs()

        global test_new_editor
        
        if test_new_editor:
            import gui.main_frame
            self.frame = gui.main_frame.MainFrame2(None, -1, "EClass.Builder")
        else:
            import editor
            self.frame = editor.MainFrame2(None, -1, "EClass.Builder")
                
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
        
    def LoadPrefs(self):
        settings.PrefDir = guiutils.getAppDataDir()
        oldprefdir = guiutils.getOldAppDataDir()

        # Move old AppDataDir if it exists.
        if oldprefdir and os.path.exists(oldprefdir) and not oldprefdir == settings.PrefDir:
            try:
                fileutils.CopyFiles(oldprefdir, settings.PrefDir, 1)
                shutil.rmtree(oldprefdir)
            except:
                self.log.write(_("Error moving preferences."))

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

for arg in sys.argv:
    if arg == "--debug":
        debug = 1
    elif arg == "--new-editor":
        test_new_editor = True

app = MyApp(0)
app.MainLoop()
