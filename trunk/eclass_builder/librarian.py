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
import urllib
import settings
import PyMeld

# We can run this script in either command line, or CGI, mode

isCGI = False

settings.AppDir = rootdir
settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName()) 

def walker(indexer, dirname, names):
    for name in names:
        fullpath = os.path.join(dirname, name)
        if os.path.isfile(fullpath):
            print "updating index for %s" % (fullpath)
            indexer.updateFile(fullpath, {})


def getTemplateMeld(self, template, language="en"):
    template_file = os.path.join("templates", template, language, "template.html")
    if not os.path.exists(template_file):
        template_file = os.path.join("library", template_file)
        
    meld = None
    
    try:
        meld = PyMeld.Meld(utils.openFile(template_file, "r").read())
    except:
        sys.stderr.write("Could not load template %s" % template_file)
        
    return meld
   
def getContentPage(self, page, language="en"):
    contents_file = os.path.join("pages", template, language, "%s.html" % page)
    if not os.path.exists(contents_file):
        contents_file = os.path.join("library", contents_file)
        
    contents = ""
    try:
        contents = utils.openFile(contents_file, "r").read()
    except:
        sys.stderr.write("Could not load page %s" % contents_file)
        
    return contents

if len(sys.argv) > 1:
    isCGI = False
    if len(sys.argv) < 2:
        progname = os.path.basename(sys.executable)
        if progname.find("librarian") == -1:
            progname = os.path.basename(__file__)
        print "Usage: %s <operation> <value>" % progname
        sys.exit(1)
else:
    isCGI = True
    
manager = index_manager.IndexManager()    

if isCGI:
    import cgi
    import cgitb; cgitb.enable()
    
    content = ""
    
    form = cgi.FieldStorage()
    
    collection = ""
    page = ""
    language = "en"
    
    if form.has_key("collection"):
        collection = form["collection"]
    
    if form.has_key("page"):
        page = form["page"]
        
    if form.has_key("language"):
        language = form["language"]
    
    if form.has_key("query"):
        query = form["query"]
        field = form["field"]
        results_pageno = form["results_pageno"]
        
        indexer = manager.getIndex(collection)
        results = indexer.search(field, query)
        
        page_start = (results_pageno - 1) * 30
        page_results = results[page_start:page_start+29]
        for result in page_results:
            url = result["url"]
            title = result["url"]
            if result.has_key("title"):
                title = result["title"]
                
            content += """<a class="hit_link" href="%s">%s</a>""" % (url, title)
            
    elif page == "search":
        content = getContentsPage("search")
        
    else:
        content = getContentsPage("index")
        for section in self.indexes.sections():
            content += """<p><a href="librarian?collection=%s&page=search&language=%s">%s</a></p>""" % (urllib.urlquote(section), section, language)
        
    meld = None
    
    template = manager.getIndexProp(collection, "template")         
    if template == "":
        template = "simple"
    
    meld = getTemplateMeld(template)
    meld.contents._content = contents
    
    print "Content-Type: text/html"
    print ""
    print str(meld)
            
else:
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
                
 
