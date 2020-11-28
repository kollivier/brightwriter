from __future__ import print_function
from builtins import object
import os
import string
import types

import appdata
import conman
import eclassutils
import ims
import ims.contentpackage
import settings
import themes
import utils

from bs4 import BeautifulSoup, Tag
from xmlutils import *
# base plugin data types


class Plugin(object):
    def __init__(self, modname, fullname, ext, mimetype, requires):
        self.modulename = modname
        self.fullname = fullname
        self.extension = ext
        self.mimetype = mimetype
        self.requires = requires


# FIXME: left for now to keep compatibility with classes using it.
class PluginData(object):
    def __init__(self):
        pass


# a base publisher to be overridden by plugins
class BaseHTMLPublisher(object):
    """
    Class: conman.plugins.BaseHTMLPublisher()
    Last Updated: 11/25/03
    Description: This class creates an HTML version of the currently open EClass Page.

    Attributes:
    - parent: parent wxWindow which called the function
    - node: the ConNode containing information on the current page
    - dir: The root directory of the currently open project
    - templates: a list of templates available to the publisher
    - mypage: the EClassPage being published
    """

    def __init__(self, parent=None, node=None, dir=None):
        self.encoding = "ISO-8859-1"
        self.parent = parent
        self.node = node
        self.dir = dir
        self.templates = None
        self.mypage = None
        #isPublic determines if this theme is selectable from BrightWriter
        self.rename = None  # should we rename long files if found?
        self.data = {}  # data dictionary used to hold template variables
        self.data['backlink'] = ""
        self.data['nextlink'] = ""

    def GetConverterEncoding(self):
        convert_encoding = 'utf-8'

        if not settings.utf8_html:
            if settings.encoding:
                convert_encoding = settings.encoding
            else:
                convert_encoding = utils.getCurrentEncoding()

        return convert_encoding

    def GetCreditString(self):
        description = ""
        contributors = []
        if self.node:
            if isinstance(self.node, conman.conman.ConNode):
                description = self.node.content.metadata.rights.description
                contributors = self.node.content.metadata.lifecycle.contributors

            elif isinstance(self.node, ims.contentpackage.Item):
                # FIXME: Address issues with multiple language text
                lang = list(self.node.metadata.lom.rights.description.keys())
                if len(lang) > 0:
                    description = self.node.metadata.lom.rights.description[lang[0]]
                contributors = self.node.metadata.lom.lifecycle.contributors

            if description == "" and len(contributors) == 0:
                return ""

            creditText = ""
            thisauthor = ""

            if description != "":
                creditstring = string.replace(description, "\r\n", "<br>")  # mac
                creditstring = string.replace(creditstring, "\n", "<br>")  # win
                creditstring = string.replace(creditstring, "\r", "<br>")  # unix
                creditstring = creditstring + "<h5 align=\'center\'>[ <a href=\'javascript:window.close()\'>" + _("Close") + "</a> ]</h5>"
                creditstring = string.replace(creditstring, "'", "\\'")
                creditText = """[ <b><a href="javascript:openCredit('newWin','%s')">%s</a></b> ]""" % (TextToHTMLChar(creditstring), _("Credit"))

            for contrib in contributors:
                role = ""
                if isinstance(self.node, conman.conman.ConNode):
                    role = contrib.role
                    fname = contrib.entity.fname.value
                elif isinstance(self.node, ims.contentpackage.Item):
                    lang = list(contrib.role.value.keys())
                    if len(lang) > 0:
                        role = contrib.role.value[lang[0]]
                    fname = conman.vcard.VCard().parseString(contrib.centity.text)

                if role == "Author":
                    thisauthor = fname
            creditText = "<h5>" + thisauthor + " " + creditText + "</h5>"
            return creditText

    def EncodeHTMLToCharset(self, myhtml, convert_encoding):
        if type(myhtml) == str:
            try:
                myhtml = myhtml.encode(convert_encoding)
            except:
                pass

        return myhtml

    def Publish(self, parent=None, node=None, dir=None):
        """
        This function prepares the Page to be converted by putting variables into self.data
        and then calling ApplyTemplate to insert the data into the template.

        In many cases, the GetData function (and possibly the GetFilename function) will be
        all that needs to be overridden in the plugin.
        """
        self.parent = parent
        self.node = node
        self.dir = dir

        name = ""
        description = ""
        keywords = ""
        filename = ""

        if isinstance(self.node, conman.conman.ConNode):
            name = node.content.metadata.name
            description = node.content.description
            keywords = node.content.keywords
            filename = node.content.filename

        elif isinstance(self.node, ims.contentpackage.Item):
            lang = appdata.projectLanguage
            name = self.node.title.text
            resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)

            description = resource.metadata.lom.general.description.getKeyOrEmptyString(lang)
            keywords = resource.metadata.lom.general.keyword.getKeyOrEmptyString(lang)
            filename = eclassutils.getEClassPageForIMSResource(resource)
            if not filename:
                filename = resource.getFilename()

        self.data['name'] = TextToXMLChar(name)
        self.data['description'] = TextToXMLAttr(description)
        self.data['keywords'] = TextToXMLAttr(keywords)
        self.data['URL'] = self.GetFileLink(filename)
        self.data['SourceFile'] = filename
        filename = os.path.join(self.dir, "Text", filename)
        filename = self.GetFilename(filename)
        self.GetLinks()
        self.GetData()
        
        templatedir = os.path.join(settings.AppDir, "themes", themes.FindTheme(settings.ProjectSettings["Theme"]).themename)
        templatefile = os.path.join(templatedir, "default.meld")
        self.data['charset'] = self.GetConverterEncoding()

        myhtml = self.ApplyTemplate(templatefile, self.data)
        myhtml = self.EncodeHTMLToCharset(myhtml, "utf8") 

        try:        
            myfile = open(os.path.join(self.dir, "pub", os.path.basename(filename)), "wb")
            myfile.write(myhtml)
            myfile.close()
        except IOError: 
            message = "There was an error writing the file", filename + " to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file."
            import traceback
            print(repr(traceback.print_exc()))
            print(repr(message))
            raise

        return myhtml

    def GetLinks(self):
        """
        Retrieve the back and next links for the page.
        """
        self.data['SCORMAction'] = ""
        
        isroot = False
        if isinstance(self.node, conman.conman.ConNode) and self.node.parent:
            isroot = True
        elif isinstance(self.node, ims.contentpackage.Item):
            isroot = (self.node.attrs["identifier"] == appdata.currentPackage.organizations[0].items[0].attrs["identifierref"]) 
            
        # Do this only for the first page in the module
        if isroot:
            self.data['SCORMAction'] = "onload=\"initAPI(window)\""

        return 
            
    def GetFileLink(self, filename):
        """
        This function is overridden by plugins which store the published file
        is different from the source file (e.g the pub file is generated).
        """
        return self.GetFilename(filename)

    def GetFilename(self, filename):
        """
        Function: GetFilename(filename)
        Last Updated: 9/24/02
        Description: Given the filename of an EClassPage, returns the filename of the converted HTML file.

        Arguments:
        - filename: the filename, without directory, of an EClassPage

        Return values:
        Returns the filename, without directory, of the HTML page generated by HTMLPublisher
        """

        return filename

    def _CreateHTMLPage(self, mypage, filename):
        pass #overridden in child classes

    def ApplyTemplate(self, template="default.meld", data={}):
        if not os.path.exists(template):
            template = os.path.join(settings.AppDir, "themes", themes.FindTheme(settings.ProjectSettings["Theme"]).themename, "default.meld")
        temp = utils.openFile(template, "r")
        html = temp.read()
        temp.close()
        charset = "utf-8"
        if 'charset' in list(self.data.keys()):
            charset = self.data['charset']
        ext = os.path.splitext(template)[1]
        soup = BeautifulSoup(html)
        for key in list(data.keys()):
            value = data[key]
            key = key.lower()
            global metaTags
            if key in metaTags:
                tag = soup.find("meta", attrs={"http_equiv": key})
                if not tag:
                    tag = Tag(soup, "meta")
                    tag['http-equiv'] = key
                    soup.html.head.insert(0, tag)

                tag['content'] = value
                if key == 'name':
                    soup.html.head.title.insert(0, value)
            elif key == 'content':
                    soup.html.body.insert(0, value)
        
        html = soup.prettify(charset)
                
        return html
