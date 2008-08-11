# Script for publishing EClass from the command line.
import sys, os
import settings
import appdata
import ims

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
	rootdir = os.path.dirname(rootdir)

settings.AppDir = rootdir
	
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
			"en": gettext.translation('eclass', localedir, languages=['en']), 
			"es": gettext.translation('eclass', localedir, languages=['es']),
			"fr": gettext.translation('eclass', localedir, languages=['fr'])
			}

import conman
import plugins
plugins.LoadPlugins()
import themes.themes as themes
	
class EClassPublisher:
    def __init__(self, eclass, pubdir, format="html"):
        self.imscp = ims.contentpackage.ContentPackage()
        self.imscp.loadFromXML(eclass)
        appdata.currentPackage = self.imscp
        
        settings.ProjectDir = os.path.dirname(eclass)
        # TODO: We should store the project as a global rather than its settings
        settings.ProjectSettings = xml_settings.XMLSettings()
        settingsfile = os.path.join(settings.ProjectDir, "settings.xml")
        theme = ""
        if os.path.exists(settingsfile):
            settings.ProjectSettings.LoadFromXML(settingsfile)
                    
            theme = settings.ProjectSettings["Theme"]

        if theme == "":
            theme = "Simple"
        
        themeList = themes.ThemeList(os.path.join(rootdir, "themes"))
        self.currentTheme = themeList.FindTheme(theme)
        settings.ProjectDir = os.path.dirname(eclass)
        publisher = self.currentTheme.HTMLPublisher(self, dir=pubdir)
        publisher.Publish()
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "You must specify an EClass to publish. Exiting."
        
    eclass = sys.argv[1]
    if not os.path.isfile(eclass):
        eclass = os.path.join(eclass, "imsmanifest.xml")
        if not os.path.exists(eclass):
            print "Could not find EClass at %s. Exiting" % sys.argv[1]
            sys.exit(1)
    
    # publish to the 
    EClassPublisher(eclass, os.path.dirname(eclass))
    
    print "Finished publishing %s!" % eclass