from __future__ import print_function
import sys, os
import string
import ConfigParser
import mimetypes
import stat
import encodings
import string
import shutil
from user import home

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
import library.metadata
import PyMeld

# We can run this script in either command line, or CGI, mode

isCGI = False

settings.AppDir = rootdir
settings.PrefDir = os.path.join(home, ".librarian")
if not os.path.exists(settings.PrefDir):
    os.makedirs(settings.PrefDir)
    
settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName()) 

def getHTMLFieldList(indexer):
    htmlfields = """<option value="contents" selected>All Text</option>\n"""
    for field in indexer.getIndexInfo()["MetadataFields"]:
        htmlfields += """<option value="%s">%s</option>\n""" % (field, field)
        
    return htmlfields

def getTemplateMeld(template, collection="", language="en"):
    template_file = os.path.join("templates", template, language, "template.html")    
    
    # local templates take precedence over system ones
    if collection != "":
        global manager
        indexdir = manager.getIndexProp(collection, "index_directory")
        
        fullpath = os.path.join(indexdir, template_file)
        if os.path.exists(fullpath):
            template_file = fullpath
    
    if not os.path.exists(template_file):
        template_file = os.path.join("library", template_file)
        
    meld = None
    
    try:
        meld = PyMeld.Meld(utils.openFile(template_file, "r").read())
    except:
        sys.stderr.write("Could not load template %s" % template_file)
        
    return meld
   
def getContentPage(page, collection="", language="en"):
    contents_file = os.path.join("pages", language, "%s.html" % page)
    
    # local pages take precedence over system ones
    if collection != "":
        global manager
        indexdir = manager.getIndexProp(collection, "index_directory")
        
        fullpath = os.path.join(indexdir, contents_file)
        if os.path.exists(fullpath):
            contents_file = fullpath    
    
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
        print("Usage: %s <operation> <value>" % progname)
        sys.exit(1)
else:
    isCGI = True
    
manager = index_manager.IndexManager("indexes.cfg")    

if isCGI:
    appname = "librarian"
    if not sys.platform.startswith("win"):
        appname = "librarian-cgi"
    import cgi
    import cgitb; cgitb.enable()
    
    content = ""
    
    form = cgi.FieldStorage()
    
    collection = ""
    page = ""
    language = "en"
    
    sort = "0-Z"
    sortBy = ""
    if "sort" in form:
        sort = form["sort"].value
    
    if "sortby" in form:
        sortBy = form["sortby"].value.lower()
    
    if "collection" in form:
        collection = form["collection"].value
    
    if "page" in form:
        page = form["page"].value
        
    if "language" in form:
        language = form["language"].value
    
    if "query" in form:
        query = form["query"].value
        field = form["field"].value.lower()
        
        if query == "":
            query = "%s:[%s]" % (field, sort.replace("-", " TO ") )
        
        results_pageno = 1
        if "results_pageno" in form:
            results_pageno = int(form["results_pageno"].value)
        
        indexer = manager.getIndex(collection)
        results = indexer.search(field, query)
        if sortBy != "":
            results.sort( lambda x, y: cmp(x[sortBy], y[sortBy]) )
            
        numpages = len(results) / 30
        if len(results) % 30 > 0:
            numpages += 1
            
        page_start = (results_pageno - 1) * 30
        page_end = page_start + 30
        if page_end > len(results):
            page_end = len(results)
        page_results = results[page_start:page_start+29]
        
        content += "<b>Search for \"%s\" returned %d results. " % (query, len(results))
        if len(results) > 0:
            content += "Showing results %d through %d." % (page_start+1, page_end)
            
        content += "</b><br/><br/>\n"

        for result in page_results:
            url = result["url"]
            title = result["url"]
            if "title" in result:
                title = result["title"]
                
            content += """<p><a class="hit_link" href="%s?collection=%s&page=viewitem&item=%s">%s</a></p>\n""" % \
                        (appname, urllib.quote(collection), urllib.quote(url), title)
        
        if numpages > 1:
            content += "<p>Result Pages: "
            for pageno in range(1, numpages+1):
                content += """<a href="%s?collection=%s&field=%s&query=%s&results_pageno=%d&language=%s">%d</a> """ % (appname, 
                            urllib.quote(collection), urllib.quote(field), urllib.quote(query), pageno, language, pageno)
            content += "</p>"
        
    elif page == "search":
        content = getContentPage("search", collection)
        
    elif page == "browse":
        field = ""
        sort = "0-Z"
        
        if "field" in form:
            field = form["field"].value.lower()
        
        indexer = manager.getIndex(collection)
        results = indexer.getUniqueFieldValues(field, sort)
        
        for result in results:                
            content += """<p><a class="hit_link" href="%s?collection=%s&page=search&field=%s&query=%s&language=%s">%s</a></p>\n""" % \
                            (appname, urllib.quote(collection), urllib.quote(field), urllib.quote(result), urllib.quote(language), result)
        

    elif page == "viewitem":
        contentsdir = manager.getIndexProp(collection, "content_directory")
        if "item" in form:
            item = form["item"].value
            fullpath = os.path.join(contentsdir, item)
            if os.path.exists(fullpath):
                type = mimetypes.guess_type(item)[0]
                props = os.stat(fullpath)
                print("Content-Type: %s" % (type))
                print("Content-Length: %d" % (props[stat.ST_SIZE]))
                print("Content-Disposition: inline; filename = \"%s\"" % os.path.basename(fullpath))
                print("")
                print(utils.openFile(fullpath, "rb").read())
                sys.exit(0)
                
            content += "Could not locate the file %s." % fullpath
                
    elif page == "indexinfo":
        indexer = manager.getIndex(collection)
        info = indexer.getIndexInfo()
        content += "<b>Index Name:</b> %s<br/>\n" % (collection)
        content += "<b>Number of Documents:</b> %s<br/>\n" % (info["NumDocs"])
        content += "<b>Metadata Fields:</b> %s<br/>\n" % ( string.join(info["MetadataFields"], ", ") )
        
    elif page != "":
        content = getContentPage(page, collection)
        if content == "":
            content = """<h3><font color="red">Unable to find page %s.</font></h3>""" % page

    else:
        content = getContentPage("index", collection)
        for section in manager.getIndexList():
            content += """<p><a href="%s?collection=%s&page=search&language=%s">%s</a> (<a href="%s?collection=%s&page=indexinfo&language=%s">Info</a>)</p>\n""" % (appname, urllib.quote(section), language,  section, appname, urllib.quote(section), language)
        
    meld = None
    
    template = manager.getIndexProp(collection, "template")         
    if template == "":
        template = "simple"
    
    meld = getTemplateMeld(template, collection)
    meld.page_contents._content = content
    
    if hasattr(meld, "collection"):
        meld.collection.value = collection
        
    if hasattr(meld, "collectionname"):
        meld.collectionname.value = collection
        
    if hasattr(meld, "field"):
        indexer = manager.getIndex(collection)
        htmlfields = getHTMLFieldList(indexer)
        meld.field._content = htmlfields
        
    print("Content-Type: text/html")
    print("")
    print(str(meld))
            
else:
    command = sys.argv[1].lower().strip()
    if command == "add":
        name = sys.argv[2].strip()
        folder = sys.argv[3].strip()
        try:
            manager.addIndex(name, folder)
        except index_manager.IndexExistsError as text:
            print(text)
            
    elif command == "index":
        name = sys.argv[2].strip()
        indexer = manager.getIndex(name)
        
        if indexer: 
            callback = index.IndexingCallback(name)
            indexer.indexLibrary(callback)
            
    elif command == "browse":
        name = sys.argv[2].strip()
        field = sys.argv[3].strip()
        
        indexer = manager.getIndex(name)
        result_list = indexer.getUniqueFieldValues(field)
        
        for result in result_list:
            print(result)
    
    elif command == "export":
        name = sys.argv[2].strip()
        
        manager.exportIndex(name)
    
    elif command == "search":
        name = sys.argv[2].strip()
        term = sys.argv[3].strip()
        indexer = manager.getIndex(name)
    
        if indexer:
            print("searching for term: %s" % term)
            results = indexer.search("contents", term)
            print("Search returned %d results." % len(results))
            for result in results:
                print(result["url"])
                
    elif command == "list":
        print("Available collections:")
        for collection in manager.getIndexList():
            print("-\t%s" % collection)
            
    elif command == "info": 
        name = sys.argv[2].strip()
        indexer = manager.getIndex(name)
        info = indexer.getIndexInfo()
        print("Index Name: %s" % (name))
        print("Number of Documents: %s" % (info["NumDocs"]))
        print("Metadata Fields: %s" % (info["MetadataFields"]))
        
    elif command == "export":
        name = sys.argv[2].strip()
        folder = manager.getIndexProp(name, "content_directory")
        indexdir = manager.getIndexProp(name, "index_directory")
        content_dir = os.path.join(indexdir, "contents")
        if os.path.exists(content_dir):
            shutil.rmtree(content_dir)
            
        print("Please wait, copying files...")
        
        shutil.copytree(folder, content_dir)
   
                
 
