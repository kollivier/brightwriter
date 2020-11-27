from __future__ import print_function
# Script for publishing EClass from the command line.
import sys, os

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)
    
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
            "en": gettext.translation('eclass', localedir, languages=['en']), 
            "es": gettext.translation('eclass', localedir, languages=['es']),
            "fr": gettext.translation('eclass', localedir, languages=['fr'])
            }

import settings
import conman.xml_settings as xml_settings
import appdata
import ims
import ims.utils
import eclassutils
import eclass_convert
import fileutils
import utils

import themes

settings.AppDir = rootdir

class CLFileCopyCallback:
    def fileChanged(self, filename):
        print("Copying %s" % filename)

class EClassExporter:
    def __init__(self, filename, pubdir=None, format="html"):
        self.imscp = None
        self.imscp = ims.contentpackage.ContentPackage()
        self.imscp.loadFromXML(filename)
        self.pubdir = pubdir
        appdata.currentPackage = self.imscp
        
        settings.ProjectDir = os.path.dirname(filename)
        # TODO: We should store the project as a global rather than its settings
        settings.ProjectSettings = xml_settings.XMLSettings()
        settingsfile = os.path.join(settings.ProjectDir, "settings.xml")

    def CopyWebFiles(self):
        utils.CreateJoustJavascript(self.imscp.organizations[0].items[0], self.pubdir)
        utils.CreateiPhoneNavigation(self.imscp.organizations[0].items[0], self.pubdir)
        self.currentTheme = themes.FindTheme(settings.ProjectSettings["Theme"])
        if self.currentTheme:
            self.currentTheme.HTMLPublisher(self, self.pubdir).CopySupportFiles()

    def ExportToWeb(self):
        if not self.pubdir:
            if settings.ProjectSettings["WebSaveDir"] == '':
                print("ERROR: No output directory specified. Exiting.")
                sys.exit(1)
            else:
                self.pubdir = settings.ProjectSettings["WebSaveDir"]
        callback = CLFileCopyCallback()
        fileutils.CopyFiles(settings.ProjectDir, self.pubdir, 1, callback)
        self.CopyWebFiles()
    
if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] eclass_dir")
    parser.add_option("-o", "--output-directory", dest="output_dir",
                  help="Directory to store exported files", default=None)

    (options, args) = parser.parse_args()

    if len(args) < 1:
        print("You must specify an EClass to publish. Exiting.")
        
    eclass = args[0]
    if not os.path.isfile(eclass):
        eclass = os.path.join(eclass, "imsmanifest.xml")
        if not os.path.exists(eclass):
            print("Could not find EClass at %s. Exiting" % sys.argv[1])
            sys.exit(1)
    
    # publish to the 
    exporter = EClassExporter(eclass, options.output_dir)
    exporter.ExportToWeb()
    
    print("Finished publishing %s!" % eclass)
