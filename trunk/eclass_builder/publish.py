# Script for publishing EClass from the command line.
import sys, os
import settings

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
        self.pub = conman.ConMan()
        self.pub.LoadFromXML(eclass)
        
        theme = self.pub.settings["Theme"]
        if theme == "":
            theme = "Simple"
        
        themeList = themes.ThemeList(os.path.join(rootdir, "themes"))
        self.currentTheme = themeList.FindTheme(theme)
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