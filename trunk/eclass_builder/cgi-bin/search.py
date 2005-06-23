import cgi
import cgitb; cgitb.enable()
import string
import sys
import os
import PyLucene
import win32api
#from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory
#from PyLucene import VERSION, LUCENE_VERSION
       
scriptname = "search.py"
scriptdir = os.path.dirname(os.path.abspath(sys.path[0]))
eclassdir = "" #indicates current directory
isiis = 0
numresults_perpage = 20

#import ConfigParser
#if os.path.exists('search.cfg'):
#    config = ConfigParser.ConfigParser()
#    config.read(open('search.cfg'))
#    eclassdir = config.get("directories", "eclassdir")
#    isiis = config.get("options", "iis_server")
#else:
#    eclassdir = "../pub"

form = cgi.FieldStorage()
print "Content-type: text/html" # identify response as HTML

content = """
"""

if form.has_key("term"):
    content = content + "<h3>Search Results</h3>"
    import os
    field = "contents"

    if form.has_key("searchtype"):
        if form["searchtype"].value == "Titles":
            field = "title"
        elif form["searchtype"].value == "Keywords":
            field = "keywords"

    startitem = 1
    if form.has_key("page"):
        startitem = 1 + (numresults_perpage * (int(form["page"].value) - 1))

    if 1:
        directory = PyLucene.FSDirectory.getDirectory(os.path.join(scriptdir, "..", "index.lucene"), False)
        searcher = PyLucene.IndexSearcher(directory)
        analyzer = PyLucene.StandardAnalyzer()
        query = PyLucene.QueryParser.parse(form["term"].value, field, analyzer)
        hits = searcher.search(query)

        if hits.length() == 0:
            content = content + "Sorry, your search returned no results."
        else:
            content = content + "<p><i>Your search returned %(results)d results.</i></p>" % {"results":hits.length()}

        for num in range(startitem, startitem + numresults_perpage):
            hit = None
            if num < hits.length():
                try:
                    hit = hits.doc(num)
                except:
                    pass
            if hit:
                link = "<p><a href=../%(file)s target='text'>%(title)s</a><br>%(description)s</p>" % {"file":string.replace(hit.get("url"), " ", "%20"), "title":hit.get("title"), "description":hit.get("description")}
                content = content + link            

        if hits.length() > 20:
            result = divmod(results, 20)
            pages = result[0]
            if not result[1] == 0:
                pages = pages + 1
            for page in range(1, pages + 1):
                content = content + "[ <a href=/cgi-bin/%(scriptname)s?searchtype=%(searchtype)s&amp;term=%(term)s&amp;page=%(page)d>%(page)d</a> ]" % {"scriptname": scriptname, "term":form["term"].value, "page":page, "searchtype":string.replace(form["searchtype"].value, " ", "%20")}
    if 0:
        content = content + "Error running Lucene search. The error message returned by the server is: <br><br><code>"
        import traceback
        content = content + `traceback.print_exc()` + "</code>"
        
else:
    content = content + """
<hr>
<h2>Search Tips</h2>
<p>
There are many techniques you can use to increase the results of your seach. Here are a few of the features that EClass supports.
</p>    
<h3>Words and Phrases</h3>
<p>To search for a word, you can simply type the word and click search. If you wish to search for a phrase, enclose it in quotes like so:</p>
    
<p>"search engine"</p>

<p>If you type multiple words or phrases, it will try to match only those pages that contain all the words and phrases you searched for.</p>

<h3>AND/OR/NOT Searches</h3>
<p>You can specify optional words or phrases, and also specify words or phrases which should not appear in the results. For example, if you wanted to search for information on the Titanic, but not about the movie, you could write: 
</p>
<p>Titanic NOT movie</p>
<p>NOT specifies that you do not want the word to appear. OR specifies that words A or B are acceptable. AND means that the word must be in the results.</p>
<p>You can also group terms by using parentheses. For example:</p>
<p>Titanic NOT (movie OR film)<p>
<p>This search looks for pages with the word Titanic, but that do not have either the terms movie or film in them.</p>
    """

templatefile = os.path.join("default.tpl")
if os.path.exists(templatefile):
    myfile = open(templatefile, "rb")
    data = myfile.read()
    myfile.close()
    mypage = data
    mypage = string.replace(mypage, "--[name]--", "EClass Search Page")
    mypage = string.replace(mypage, "--[credit]--", "")
    mypage = string.replace(mypage, "--[content]--", content)
    print mypage
else:
    print content