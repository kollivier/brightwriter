import string, sys, os
import wx
import wx.lib.sized_controls as sc
import persistence
import settings
import encrypt
import conman
import ims
import ims.contentpackage
import appdata

import select_box as picker

class ProjectPropsDialog(sc.SizedDialog):
    def __init__(self, parent):
        """
        Dialog for setting various project properties.

        """
        sc.SizedDialog.__init__(self, parent, -1, _("Project Settings"), wx.Point(100, 100), wx.Size(400, 400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        self.notebook = wx.Notebook(pane, -1)
        self.notebook.SetSizerProps({"proportion":1, "expand":True})
        self.parent = parent
        self.searchchanged = False
        
        self.project = None
        if "pub" in dir(self.parent):
            self.project = self.parent.pub
        elif "imscp" in dir(self.parent):
            self.project = self.parent.imscp
        
        self.generalPanel = GeneralPanel(self.notebook, self.project)
        self.notebook.AddPage(self.generalPanel, _("General"))
        
        self.publishPanel = PublishPanel(self.notebook)
        self.notebook.AddPage(self.publishPanel, _("Publish"))
        
        self.ftpPanel = FTPPanel(self.notebook)
        self.notebook.AddPage(self.ftpPanel, _("FTP"))
        if wx.Platform == '__WXMAC__':
            self.notebook.SetSelection(0)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))

        self.SetMinSize(self.GetSize())
        
        # TODO: Can this be removed?
        if wx.Platform == '__WXMSW__':
            wx.EVT_CHAR(self.notebook, self.SkipNotebookEvent)
        wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)

    def SkipNotebookEvent(self, event):
        event.Skip()
        
    def btnOKClicked(self, event):
    
        if isinstance(self.project, conman.conman.ConMan):
            self.project.name = self.generalPanel.txtname.GetValue()
            self.project.description = self.generalPanel.txtdescription.GetValue()
            self.project.keywords = self.generalPanel.txtkeywords.GetValue()
            self.parent.pub.pubid = self.searchPanel.txtpubid.GetValue()
               
        elif isinstance(self.project, ims.contentpackage.ContentPackage):
            lang = appdata.projectLanguage
            self.project.metadata.lom.general.title[lang] = self.generalPanel.txtname.GetValue()
            self.project.metadata.lom.general.description[lang] = self.generalPanel.txtdescription.GetValue()
            self.project.metadata.lom.general.keyword[lang] = self.generalPanel.txtkeywords.GetValue()

        settings.ProjectSettings["FTPHost"] = self.ftpPanel.txtFTPSite.GetValue()
        settings.ProjectSettings["FTPDirectory"] = self.ftpPanel.txtDirectory.GetValue()
        settings.ProjectSettings["FTPUser"] = self.ftpPanel.txtUsername.GetValue()
        settings.ProjectSettings["FTPPassword"] = encrypt.encrypt(self.ftpPanel.txtPassword.GetValue())

        if self.ftpPanel.chkPassiveFTP.GetValue() == True:
            settings.ProjectSettings["FTPPassive"] = "Yes"
        else:
            settings.ProjectSettings["FTPPassive"] = "No"

        settings.ProjectSettings["UploadOnSave"] = "No"

        settings.ProjectSettings["CDSaveDir"] = self.publishPanel.txtCDDir.GetValue()
        settings.ProjectSettings["WebSaveDir"] = self.publishPanel.txtWebDir.GetValue()

        self.parent.isDirty = True
        self.EndModal(wx.ID_OK)
        
class GeneralPanel(sc.SizedPanel):
    def __init__(self, parent, project):
        sc.SizedPanel.__init__(self, parent, -1)
        
        name = ""
        description = ""
        keywords = ""
        if isinstance(project, conman.conman.ConMan):
            name = project.name
            description = project.description
            keywords = project.keywords
               
        elif isinstance(project, ims.contentpackage.ContentPackage):
            lang = appdata.projectLanguage
            name = project.metadata.lom.general.title.getKeyOrEmptyString(lang)
            description = project.metadata.lom.general.description.getKeyOrEmptyString(lang)
            keywords = project.metadata.lom.general.keyword.getKeyOrEmptyString(lang)
        
        self.SetSizerType("form")
        self.lblname = wx.StaticText(self, -1, _("Name"))
        self.txtname = wx.TextCtrl(self, -1, name)
        self.txtname.SetSizerProp("expand", True)
        self.lbldescription = wx.StaticText(self, -1, _("Description"))
        self.txtdescription = wx.TextCtrl(self, -1, description, style=wx.TE_MULTILINE)
        self.txtdescription.SetSizerProps({"expand":True, "proportion":1})
        self.lblkeywords = wx.StaticText(self, -1, _("Keywords"))
        self.txtkeywords = wx.TextCtrl(self, -1, keywords) 
        self.txtkeywords.SetSizerProp("expand", True)
        self.txtname.SetFocus()
        self.txtname.SetSelection(0, -1)
        
class SearchPanel(sc.SizedPanel):
    def __init__(self, parent, project):
        sc.SizedPanel.__init__(self, parent, -1)
        self.chkSearch = wx.CheckBox(self, -1, _("Enable Search Function"))
        
        if not appdata.hasPyLucene:
            self.chkSearch.Enable(False)
        
        self.LoadSettings()

        wx.EVT_CHECKBOX(self, self.chkSearch.GetId(), self.chkSearchClicked)
        
    def whichSearchClicked(self, event):
        self.updatePubIdState()
        self.searchchanged = True
        
    def updatePubIdState(self):
        value = (self.chkSearch.IsChecked() and self.whichSearch.GetStringSelection() == self.options[1])
        self.lblpubid.Enable(value)
        self.txtpubid.Enable(value)
        self.lblpubidhelp.Enable(value)
    
    def chkSearchClicked(self, event):
        value = self.chkSearch.GetValue()
        self.whichSearch.Enable(value)
        self.updatePubIdState()
        self.searchchanged = True
 
    def LoadSettings(self):
        ischecked = settings.ProjectSettings["SearchEnabled"]
        searchtool = ""
        if not ischecked == "":
            try:
                searchbool = int(ischecked)
            except:
                searchbool = 0

            self.chkSearch.SetValue(searchbool)
        #    if searchbool:
        #        searchtool = settings.ProjectSettings["SearchProgram"]
        #        if searchtool == "": #since there wasn't an option selected, must be Greenstone
        #            searchtool = "Greenstone"
                    
        #if searchtool == "Greenstone":
        #    self.whichSearch.SetStringSelection(self.options[1])
        #elif searchtool == "Lucene":
        #    self.whichSearch.SetStringSelection(self.options[0])
            
        value = self.chkSearch.GetValue()
        #self.lblpubid.Enable(value)
        #self.txtpubid.Enable(value)
        #self.lblpubidhelp.Enable(value)
        
class PublishPanel(sc.SizedPanel):
    def __init__(self, parent):
        sc.SizedPanel.__init__(self, parent, -1)
        self.lblCDDir = wx.StaticText(self, -1, _("CD Export Directory:"))
        
        cdpanel = sc.SizedPanel(self, -1)
        cdpanel.SetSizerType("horizontal")
        cdpanel.SetSizerProp("expand", True)
        self.txtCDDir = wx.TextCtrl(cdpanel, -1, "")
        self.txtCDDir.SetSizerProps({"expand":True, "proportion":1})
        
        icnFolder = wx.Bitmap(os.path.join(settings.AppDir, "icons", "fatcow", "folder.png"))
        self.btnSelectFile = wx.BitmapButton(cdpanel, -1, icnFolder)
        self.btnSelectFile.SetSizerProp("valign", "center")

        wx.StaticText(self, -1, _("Web Export Directory:"))

        self.txtWebDir = picker.SelectBox(self, "", type="Directory")

        self.LoadSettings()

        wx.EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)
    
    def LoadSettings(self):
        if settings.ProjectSettings["CDSaveDir"] != "":
            self.txtCDDir.SetValue(settings.ProjectSettings["CDSaveDir"])
            
        if settings.ProjectSettings["WebSaveDir"] != "":
            self.txtWebDir.SetValue(settings.ProjectSettings["WebSaveDir"])
            
    def btnSelectFileClicked(self, event):
        dialog = wx.DirDialog(self, _("Choose a folder to store CD files."), style=wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            self.txtCDDir.SetValue(dialog.GetPath())
        dialog.Destroy()
        
class FTPPanel(sc.SizedPanel):
    def __init__(self, parent):
        sc.SizedPanel.__init__(self, parent, -1)
        ftppanel = sc.SizedPanel(self, -1)
        ftppanel.SetSizerType("form")
        ftppanel.SetSizerProp("expand", True)
        self.lblFTPSite = wx.StaticText(ftppanel, -1, _("FTP Site"))
        self.txtFTPSite = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPHost"])
        self.txtFTPSite.SetSizerProp("expand", True)
        self.lblUsername = wx.StaticText(ftppanel, -1, _("Username"))
        self.txtUsername = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPUser"])
        self.txtUsername.SetSizerProp("expand", True)
        self.lblPassword = wx.StaticText(ftppanel, -1, _("Password"))
        # FIXME - restore this setting once I clean up the FTP support
        self.txtPassword = wx.TextCtrl(ftppanel, -1, encrypt.decrypt(settings.ProjectSettings["FTPPassword"]), style=wx.TE_PASSWORD)
        self.txtPassword.SetSizerProp("expand", True)
        self.lblDirectory = wx.StaticText(ftppanel, -1, _("Directory"))
        self.txtDirectory = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPDirectory"])
        self.txtDirectory.SetSizerProp("expand", True)
        
        self.chkPassiveFTP = wx.CheckBox(self, -1, _("Use Passive FTP"))
        
        self.txtFTPSite.SetFocus()
        self.txtFTPSite.SetSelection(0, -1)
        
    def LoadSettings(self):
        if settings.ProjectSettings["FTPPassive"] == "Yes":
            self.chkPassiveFTP.SetValue(True)
        else:
            self.chkPassiveFTP.SetValue(False)
