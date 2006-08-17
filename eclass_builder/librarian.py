import sys, os
import ConfigParser
import encodings
import string

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
import index_manager
import utils
import settings

settings.AppDir = rootdir
settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName()) 

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

manager = index_manager.IndexManager()    
command = sys.argv[1].lower().strip()
if command == "add":
    name = sys.argv[2].strip()
    folder = sys.argv[3].strip()
    try:
        manager.addIndex(name, folder)
    except index_manager.IndexExistsError, text:
        print text
        
elif command == "index":
    name = sys.argv[2].strip()
    indexer = manager.getIndex(name)
        
    if indexer: 
        folder = manager.getIndexProp(name, "content_directory")
        currentdir = os.getcwd()
        os.chdir(folder)
        os.path.walk(folder, walker, indexer)
    
        os.chdir(currentdir)

elif command == "search":
    name = sys.argv[2].strip()
    term = sys.argv[3].strip()
    indexer = manager.getIndex(name)

    if indexer:
        print "searching for term: %s" % term
        results = indexer.search("contents", term)
        print "Search returned %d results." % len(results)
        for result in results:
            print result["url"]
