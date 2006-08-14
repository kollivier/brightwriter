import sys, os
import ConfigParser

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
			
import index
import utils
import settings

settings.AppDir = rootdir
settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName()) 

config = ConfigParser.ConfigParser()
config.read(["indexes.cfg"])

def walker(indexer, dirname, names):
    for name in names:
        fullpath = os.path.join(dirname, name)
        if os.path.isfile(fullpath):
            print "updating index for %s" % (fullpath)
            indexer.updateFile(fullpath, {})

if len(sys.argv) <= 2:
    print "Usage: %s <operation> <value>" % os.path.basename(__file__)

command = sys.argv[1].lower().strip()
if command == "add":
    name = sys.argv[2].strip()
    folder = sys.argv[3].strip()
    if not config.has_section(name):
        config.add_section(name)
        config.set(name, "directory", folder)
        config.write(open("indexes.cfg", "w"))
        
    else:
        print "Collection with name %s already exists. Please enter another name." % name
    
elif command == "index":
    name = sys.argv[2].strip()
    folder = config.get(name, "directory")
    
    if not folder == "":
        lucenedir = os.path.join(folder, "index.lucene")
    
        currentdir = os.getcwd()
        os.chdir(folder)
        indexer = index.Index(None, lucenedir, folder)
        os.path.walk(folder, walker, indexer)
    
        os.chdir(currentdir)
    else:
        print "No folder specified for collection %s. Cannot continue." % name

elif command == "search":
    name = sys.argv[2].strip()
    term = sys.argv[3].strip()
    folder = config.get(name, "directory")
    if not folder == "":
        print "searching for term: %s" % term
        lucenedir = os.path.join(folder, "index.lucene")
        searcher = index.Index(None, lucenedir, folder)
        results = searcher.search("contents", term)
        print `results`
    
    else:
        print "No folder specified for collection %s. Cannot continue." % name