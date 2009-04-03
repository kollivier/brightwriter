# Script for publishing EClass from the command line.
import sys, os
import settings
import conman.xml_settings as xml_settings
import appdata
import ims
import ims.utils
import eclassutils
import eclass_convert

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
import themes
	
class EClassPublisher:
    def __init__(self, filename, pubdir, format="html"):
        converter = eclass_convert.EClassIMSConverter(filename)
        self.imscp = None
        if converter.IsEClass():
            # TODO: detect if there are non-ascii characters,
            # and prompt the user for language to convert from
            self.imscp = converter.ConvertToIMSContentPackage()
        else:
            self.imscp = ims.contentpackage.ContentPackage()
            self.imscp.loadFromXML(filename)
        appdata.currentPackage = self.imscp
        
        settings.ProjectDir = os.path.dirname(filename)
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
        settings.ProjectDir = os.path.dirname(filename)
        publisher = self.currentTheme.HTMLPublisher(self, dir=pubdir)
        publisher.Publish()
        
    def PublishPage(self, imsitem):
        if imsitem != None:
            filename = eclassutils.getEditableFileForIMSItem(self.imscp, imsitem)
            publisher = plugins.GetPublisherForFilename(filename)
            if publisher:
                publisher.Publish(self, imsitem, settings.ProjectDir)
    
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
