import sys, os
import ConfigParser
import encodings

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
    progname = os.path.basename(sys.executable)
    if progname.find("librarian") == -1:
        progname = os.path.basename(__file__)
    print "Usage: %s <operation> <value>" % progname
    sys.exit(1)

command = sys.argv[1].lower().strip()
if command == "add":
    name = sys.argv[2].strip()
    folder = sys.argv[3].strip()
    if not config.has_section(name):
        config.add_section(name)
        config.set(name, "content_directory", folder)
        indexdir = os.path.join(settings.AppDir, "indexes")
        if not os.path.exists(indexdir):
            os.makedirs(indexdir)
            
        thisindexdir = os.path.join(indexdir, utils.createSafeFilename(name))
        if not os.path.exists(thisindexdir):
            os.makedirs(thisindexdir)
        config.set(name, "index_directory", thisindexdir)
        config.write(open("indexes.cfg", "w"))
        
    else:
        print "Collection with name %s already exists. Please enter another name." % name
    
elif command == "index":
    name = sys.argv[2].strip()
    folder = config.get(name, "content_directory")
    indexdir = config.get(name, "index_directory")
    
    if not folder == "":
        lucenedir = os.path.join(indexdir, "index.lucene")
    
        currentdir = os.getcwd()
        os.chdir(folder)
        indexer = index.Index(None, lucenedir, folder)
        os.path.walk(folder, walker, indexer)
    
        os.chdir(currentdir)
    else:
        print "Cannot read information on collection %s from indexes.cfg. Cannot continue." % name

elif command == "search":
    name = sys.argv[2].strip()
    term = sys.argv[3].strip()
    folder = config.get(name, "directory")
    if not folder == "":
        print "searching for term: %s" % term
        lucenedir = os.path.join(folder, "index.lucene")
        searcher = index.Index(None, lucenedir, folder)
        results = searcher.search("contents", term)
        print results.split("\n")
    
    else:
        print "No folder specified for collection %s. Cannot continue." % name