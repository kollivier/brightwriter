import cgi
import cgitb; cgitb.enable()
import string
import sys
import os
import win32api
import win32pipe
        
scriptname = "search.py"
scriptdir = "cgi-bin"
eclassdir = "" #indicates current directory
isiis = 0

import ConfigParser
if os.path.exists('search.cfg'):
    config = ConfigParser.ConfigParser()
    config.read(open('search.cfg'))
    scriptdir = config.get("directories", "scriptdir")
    eclassdir = config.get("directories", "eclassdir")
    isiis = config.get("options", "iis_server")
else:
    scriptdir = os.path.dirname(sys.argv[0])
    if not os.path.exists(os.path.join(scriptdir, scriptname)):
        #we're in the local server...
        scriptdir = os.path.join(scriptdir, "cgi-bin")
    if os.name == "nt":
        scriptdir = win32api.GetShortPathName(scriptdir)
    eclassdir = "../pub"

form = QUERY
#print "Content-type: text/html" # identify response as HTML

content = """
<FORM method=POST>
<INPUT type=text name=term
"""
if form.has_key("term"):
    content = content + "value='" + string.replace(form["term"], "\"", "&quot;") + "'" 

content = content + ">"
if form.has_key("page"):
    content = content + "<INPUT name=page type=hidden value=%(page)s>" % {"page":form["page"]}
content = content + """
<select name=searchtype>
    <option name=all>All text</option>
    <option name=title>Titles</option>
    <option name=keywords>Keywords</option>
</select>
<INPUT type=submit name="Search" value="Search">
</FORM>
    """

if form.has_key("term"):
    content = content + "<hr><h3>Search Results</h3>"
    #show search results
    import os
    search = "-w "
    term = form["term"]
    if os.name == "nt":
        #Windows command line needs double-quotes to be escaped
        term = string.replace(term, "\"", "\\\"")
        #print term
    if form.has_key("searchtype"):
        if form["searchtype"] == "All text":
            search = search + term
        elif form["searchtype"] == "Titles":
            search = search + term + " -t t"
        elif form["searchtype"] == "Keywords":
            search = search + "Keywords=" + term
        else:
            search = search + term
    #print search
    page = ""
    if form.has_key("page"):
        #print "page value = " + form["page"]
        page = "-b " + `(1 + (20 * (int(form["page"]) - 1)))`
        #print page

    index = os.path.join(scriptdir, "..", "index.swish-e")
    swishbin = os.path.join(scriptdir,"swish-e.exe")
    if not os.path.exists(index):
        content = content + "<br>Index file " + index + " does not exist."
    if not os.path.exists(swishbin):
        content = content + "<br>program " + swishbin + " does not exist."
    try:
        command = swishbin + " -d :: -f \"" + index + "\" -m 20 -p Description " + search + " " + page
        #content = content + command
        if 0:
            myout = win32pipe.popen(command, "r")
        else:
            myout = os.popen(command, "r")
    except:
        content = content + "Error running swish-e."
    results = 0
    while 1:
        line = myout.readline()
        if not line:
            break
        else:
            if not string.find(line, "err: no results") == -1:
                content = content + "Sorry, your search returned no results."
                break
            elif not string.find(line, "# Number of hits:") == -1:
                results = int(string.split(line, ":")[1])
                content = content + "<p><i>Your search returned %(results)d results.</i></p>" % {"results":results}
            elif not string.find(line, "#") == 0:
                #print line
                values = string.split(line, "::")
                try:
                    file = values[1]
                    if string.find(file, ".") == 0:
                        file = file[2:]

                    title = values[2]
                    file = "../" + file
                    description = ""
                    try: 
                        description = values[4]
                    except:
                        pass
                    link = "<p><a href=%(file)s target='_blank'>%(title)s</a><br><font size='-1'><i>Ranking: %(percent)d%% &nbsp;&nbsp;Size: %(bytes)s bytes</i></font><br>%(description)s</p>" % {"file":string.replace(file, " ", "%20"), "title":title, "percent":(int(values[0])/10), "bytes":values[3], "description":description}
                    content = content + link
                    
                except:
                    pass
            #else:
            #    content = content + str(line)
                    
    if results > 20:
        result = divmod(results, 20)
        pages = result[0]
        if not result[1] == 0:
            pages = pages + 1
        for page in range(1, pages + 1):
            content = content + "[ <a href=/cgi-bin/%(scriptname)s?searchtype=%(searchtype)s&amp;term=%(term)s&amp;page=%(page)d>%(page)d</a> ]" % {"scriptname": scriptname, "term":form["term"], "page":page, "searchtype":string.replace(form["searchtype"], " ", "%20")}
                
    myout.close()
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

templatefile = os.path.join(scriptdir, "default.tpl")
if os.path.exists(templatefile):
    myfile = open(templatefile, "rb")
    data = myfile.read()
    myfile.close()
    mypage = data
    mypage = string.replace(mypage, "--[name]--", "EClass Search Page")
    mypage = string.replace(mypage, "--[credit]--", "")
    mypage = string.replace(mypage, "--[backlink]--", "")
    mypage = string.replace(mypage, "--[nextlink]--", "")
    mypage = string.replace(mypage, "--[content]--", content)
    print mypage
else:
    print content