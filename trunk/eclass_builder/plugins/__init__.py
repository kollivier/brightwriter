import string, os, sys
import settings
import csv
from htmlutils import *
from xmlutils import *
import types
import locale
import utils
import conman
import ims
import ims.contentpackage
import eclassutils
import appdata

pluginList = []
def LoadPlugins():
    global pluginList
    for item in os.listdir(os.path.join(settings.AppDir, "plugins")):
        if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
            plugin = string.replace(item, ".py", "")
            exec("import plugins." + plugin)
            exec("pluginList.append(plugins." + plugin + ")") 

def GetPluginForFilename(filename):
    fileext = os.path.splitext(filename)[1][1:]
    return GetPluginForExtension(fileext)

def GetPluginForExtension(fileext):
    global pluginList
    for plugin in pluginList:
        if fileext in plugin.plugin_info["Extension"]:
            return plugin

    # As a default, return the file plugin  
    for plugin in pluginList:
        if plugin.plugin_info["Name"] == "file":
            return plugin

    return None

def GetPlugin(name):
    global pluginList
    for plugin in pluginList:
        if plugin.plugin_info["Name"] == name or plugin.plugin_info["FullName"] == name:
            return plugin

    return None

def GetExtensionsForPlugin(name):
    plugin = self.GetPlugin(name)
    if plugin:
        return plugin.plugin_info["Extension"]

    return []

def GetPublisherForFilename(filename):
    publisher = None
    plugin = GetPluginForFilename(filename)
    publisher = plugin.HTMLPublisher()
    return publisher
    
# base plugin data types

class Plugin:
    def __init__(self, modname, fullname, ext, mimetype, requires):
        self.modulename = modname
        self.fullname = fullname
        self.extension = ext
        self.mimetype = mimetype
        self.requires = requires

class PluginData:
    def __init__(self):
        self.encoding = utils.getCurrentEncoding()
        
    def __setattr__(self, name, value):
        # make sure internally we're always using Unicode
        if not name == "encoding":
            self.__dict__[name] = utils.makeUnicode(value, self.encoding)
        else:
            self.__dict__[name] = value 
            
#a base publisher to be overridden by plugins 
class BaseHTMLPublisher:
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
        #isPublic determines if this theme is selectable from EClass.Builder
        self.rename = None #should we rename long files if found?
        self.data = {} #data dictionary used to hold template variables
        #self.language, self.encoding = locale.getdefaultlocale()   
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
                lang = self.node.metadata.lom.rights.description.keys()
                if len(lang) > 0:
                    description = self.node.metadata.lom.rights.description[lang[0]]
                contributors = self.node.metadata.lom.lifecycle.contributors
            
            if description == "" and len(contributors) == 0:
                return ""

            creditText = ""
            thisauthor = ""

            if description != "":
                creditstring = string.replace(description, "\r\n", "<br>")#mac
                creditstring = string.replace(creditstring, "\n", "<br>")#win
                creditstring = string.replace(creditstring, "\r", "<br>")#unix
                creditstring = creditstring + "<h5 align=\'center\'>[ <a href=\'javascript:window.close()\'>" + _("Close") + "</a> ]</h5>"
                creditstring = string.replace(creditstring, "'", "\\'")
                creditText = """[ <b><a href="javascript:openCredit('newWin','%s')">%s</a></b> ]""" % (TextToHTMLChar(creditstring), _("Credit"))

            for contrib in contributors:
                role = ""
                if isinstance(self.node, conman.conman.ConNode):
                    role = contrib.role
                    fname = contrib.entity.fname.value
                elif isinstance(item, ims.contentpackage.Item):
                    lang = contrib.role.value.keys()
                    if len(lang) > 0:
                        role = contrib.role.value[lang[0]]
                    fname = conman.vcard.VCard().parseString(contrib.centity.text)
                    
                if role == "Author":
                    thisauthor = fname
            creditText = "<h5>" + thisauthor + " " + creditText + "</h5>"
            return creditText
            
    def EncodeHTMLToCharset(self, myhtml, convert_encoding):
        if type(myhtml) == types.UnicodeType:
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
        
        self.data['name'] = TextToHTMLChar(name)
        self.data['description'] = TextToXMLAttr(description)
        self.data['keywords'] = TextToXMLAttr(keywords)
        self.data['URL'] = utils.GetFileLink(filename)
        self.data['SourceFile'] = filename
        self.data['credit'] = self.GetCreditString()
        filename = os.path.join(self.dir, "Text", filename)
        filename = self.GetFilename(filename)
        self.GetLinks()
        self.GetData()
        templatefile = os.path.join(settings.AppDir, "themes", self.parent.currentTheme.themename, "default.tpl")
        self.data['charset'] = self.GetConverterEncoding()

        myhtml = self.ApplyTemplate(templatefile, self.data)
        myhtml = self.EncodeHTMLToCharset(myhtml, self.data['charset']) 


        try:        
            myfile = open(os.path.join(self.dir, "pub", os.path.basename(filename)), "wb")
            myfile.write(myhtml)
            myfile.close()
        except: 
            message = "There was an error writing the file", filename + " to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file."
            import traceback
            print `traceback.print_exc()`
            print `message`
            raise IOError, message
            return false
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

    def ApplyTemplate(self, template="default.tpl", data={}):
        if template == "default.tpl":
            #get the template file from the current theme
            template = os.path.join(settings.AppDir, "themes", self.parent.currentTheme.themename, template)
        temp = utils.openFile(template, "r")
        html = temp.read()
        temp.close()
        charset = "utf-8"
        if 'charset' in self.data.keys():
            charset = self.data['charset']
        ext = os.path.splitext(template)[1]
        if ext == ".tpl":
            for key in data.keys():
                value = data[key]
                import types
                if not type(value) == types.UnicodeType:
                    value = value.decode(charset, 'replace')
                html = string.replace(html, "--[" + key + "]--", value)
        elif ext == ".tal": #SimpleTAL support
            pass #for now.... =)
        return html
        

