import string, sys, os
import wx
import wx.lib.sized_controls as sc
import persistence
import gui.contacts

import appdata
import conman
import conman.vcard as vcard
import eclassutils
import fileutils
import guiutils
import htmlutils
import ims
import ims.contentpackage
import plugins
import select_box as picker
import settings
import utils

class PagePropertiesDialog (sc.SizedDialog):
    """
    Content page editing modal dialog window
    """
    def __init__(self, parent, node, content, dir):
        """
        """
        sc.SizedDialog.__init__ (self, parent, -1, _("Page Properties"),
                           wx.Point(100,100),
                         
                           style = wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        pane = self.GetContentsPane()
        
        # Storage for the attribute name/value pair
        self.node = node
        self.content = content
        
        if isinstance(self.node, ims.contentpackage.Item):
            self.content = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)
        
        self.parent = parent
        self.dir = dir
        self.filename = ""
        self.updatetoc = False

        self.notebook = wx.Notebook(pane, -1)
        self.notebook.SetSizerProps({"expand":True, "proportion":1})
        
        self.notebook.AddPage(self.GeneralPanel(), _("General"))
        self.notebook.AddPage(self.CreditPanel(), _("Credits"))
        # For now, we'll only support classification with the old editor
        if not isinstance(self.node, ims.contentpackage.Item):
            self.notebook.AddPage(self.ClassificationPanel(), _("Categories"))

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))

        self.Fit()
        self.SetMinSize(self.GetSize())

        wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)    

    def GeneralPanel(self): 
        mypanel = sc.SizedPanel(self.notebook, -1)
        mypanel.SetSizerType("form")
        
        name = ""
        description = ""
        keywords = ""
        filename = ""
        
        if isinstance(self.node, conman.conman.ConNode):
            name = self.content.metadata.name
            description = self.content.metadata.description
            keywords = self.content.metadata.keywords
            filename = self.content.filename
            
        elif isinstance(self.node, ims.contentpackage.Item):
            lang = appdata.projectLanguage
            
            name = self.node.title.text
            description = self.content.metadata.lom.general.description.getKeyOrEmptyString(lang)
            keywords = self.content.metadata.lom.general.keyword.getKeyOrEmptyString(lang)
            filename = eclassutils.getEClassPageForIMSResource(self.content)
            if not filename:
                filename = self.content.getFilename()
        
        wx.StaticText(mypanel, -1, _("Name"))
        self.txtTitle = wx.TextCtrl(mypanel, -1, name)
        self.txtTitle.SetSizerProp("expand", True)
        
        wx.StaticText(mypanel, -1, _("Description"))
        self.txtDescription = wx.TextCtrl(mypanel, -1, description, style=wx.TE_MULTILINE)
        self.txtDescription.SetSizerProp("expand", True)
        
        wx.StaticText(mypanel, -1, _("Keywords"))
        self.txtKeywords = wx.TextCtrl(mypanel, -1, keywords, size=wx.Size(160, -1))
        self.txtKeywords.SetSizerProp("expand", True)

        wx.StaticText(mypanel, -1, _("Page Content:"))
        self.txtExistingFile = picker.SelectBox(mypanel, filename)

        self.txtTitle.SetFocus()
        self.txtTitle.SetSelection(-1, -1)
  
        #wx.EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)
        picker.EVT_FILE_SELECTED(self.txtExistingFile, self.btnSelectFileClicked)

        return mypanel
        
    def CreateAuthorBox(self, parent, handler):
        authorPanel = sc.SizedPanel(parent, -1)
        authorPanel.SetSizerType("horizontal")
        authorPanel.SetSizerProp("expand", True)
        
        combobox = wx.ComboBox(authorPanel, -1)
        combobox.SetSizerProps({"expand": True, "proportion":1})
        peopleIcon = wx.Bitmap(os.path.join(settings.AppDir, "icons", "fatcow", "book_addresses.png"))
        contactBtn = wx.BitmapButton(authorPanel, -1, peopleIcon)
        
        wx.EVT_BUTTON(contactBtn, contactBtn.GetId(), handler)
                
        return combobox

    def CreditPanel(self):
        if isinstance(self.node, conman.conman.ConNode):
            credits = self.content.metadata.rights.description
            
        elif isinstance(self.node, ims.contentpackage.Item):
            lang = appdata.projectLanguage
            credits = self.content.metadata.lom.rights.description.getKeyOrEmptyString(lang)
        
        mypanel = sc.SizedPanel(self.notebook, -1)
        #mypanel.SetSizerProp("expand", True)
        
        wx.StaticText(mypanel, -1, _("Author"))
        self.txtAuthor = self.CreateAuthorBox(mypanel, self.OnLoadContacts)
        
        wx.StaticText(mypanel, -1, _("Creation/Publication Date (Format: YYYY-MM-DD)"))
        self.txtDate = wx.TextCtrl(mypanel, -1)
        self.txtDate.SetSizerProp("expand", True)

        wx.StaticText(mypanel, -1, _("Organization/Publisher"))
        self.txtOrganization = self.CreateAuthorBox(mypanel, self.OnLoadContacts)

        wx.StaticText(mypanel, -1, _("Credits"))
        self.txtCredit = wx.TextCtrl(mypanel, -1, credits, style=wx.TE_MULTILINE)
        self.txtCredit.SetSizerProp("expand", True)

        self.UpdateAuthorList()

        return mypanel

    def ClassificationPanel(self):
        mypanel = sc.SizedPanel(self.notebook, -1)
        
        wx.StaticText(mypanel, -1, _("Categories"))
        self.lstCategories = wx.ListBox(mypanel, -1)
        self.lstCategories.SetSizerProps({"expand":True, "proportion":1})
        
        btnPanel = sc.SizedPanel(mypanel, -1)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProp("align", "center")
        
        self.btnAddCategory = wx.Button(btnPanel, -1, _("Add"))
        self.btnEditCategory = wx.Button(btnPanel, -1, _("Edit"))
        self.btnRemoveCategory = wx.Button(btnPanel, -1, _("Remove"))

        for item in self.content.metadata.classification.categories:
            self.lstCategories.Append(item)
        
        wx.EVT_BUTTON(self.btnAddCategory, self.btnAddCategory.GetId(), self.AddCategory)
        wx.EVT_BUTTON(self.btnEditCategory, self.btnEditCategory.GetId(), self.EditCategory)
        wx.EVT_BUTTON(self.btnRemoveCategory, self.btnRemoveCategory.GetId(), self.RemoveCategory)
        wx.EVT_ACTIVATE(self, self.UpdateAuthorList)

        return mypanel

    def AddCategory(self, event):
        dialog = wx.TextEntryDialog(self, _("Please type the name of the new category here."), _("Add Category"))
        if dialog.ShowModal() == wx.ID_OK:
            value = dialog.GetValue()
            if value != "":
                self.lstCategories.Append(value)

    def EditCategory(self, event):
        selitem = self.lstCategories.GetSelection()
        if selitem != wx.NOT_FOUND:
            dialog = wx.TextEntryDialog(self, _("Type the new value for your category here."), 
                                         _("Edit Category"), self.lstCategories.GetStringSelection())
            if dialog.ShowModal() == wx.ID_OK:
                value = dialog.GetValue()
                if value != "":
                    self.lstCategories.SetString(selitem, value)

    def RemoveCategory(self, event):
        selitem = self.lstCategories.GetSelection()
        if selitem != wx.NOT_FOUND:
            self.lstCategories.Delete(selitem)

    def OnLoadContacts(self, event):
        gui.contacts.ContactsDialog(self.parent).ShowModal()
        self.UpdateAuthorList()

    def UpdateAuthorList(self, event=None):
        oldvalue = self.txtAuthor.GetValue()
        self.txtAuthor.Clear()
        for name in appdata.vcards.keys():
            self.txtAuthor.Append(name, appdata.vcards[name])

        oldorg = self.txtOrganization.GetValue()
        self.txtOrganization.Clear()
        for name in appdata.vcards.keys():
            self.txtOrganization.Append(name, appdata.vcards[name])

        if oldvalue != "":
            self.txtAuthor.SetValue(oldvalue)
        else:
            if isinstance(self.node, conman.conman.ConNode):
                for person in self.content.metadata.lifecycle.contributors:
                    if person.role == "Author":
                        self.txtAuthor.SetValue(person.entity.fname.value)
                        if person.date != "":
                            self.txtDate.SetValue(person.date)
                    elif person.role == "Content Provider":
                        self.txtOrganization.SetValue(person.entity.fname.value)

            elif isinstance(self.node, ims.contentpackage.Item):
                lang = appdata.projectLanguage
                for person in self.content.metadata.lom.lifecycle.contributors:
                    if person.role.value.getKeyOrEmptyString(lang) == "Author":
                        vcard = conman.vcard.VCard()
                        vcard.parseString(person.centity.vcard.text)
                        self.txtAuthor.SetValue(vcard.fname.value)
                        if person.date.datetime.text and person.date.datetime.text != "":
                            self.txtDate.SetValue(person.date.datetime.text)

        if oldorg != "":
            self.txtOrganization.SetValue(oldorg)
        else:
            if isinstance(self.node, conman.conman.ConNode):
                for person in self.content.metadata.lifecycle.contributors:
                    if person.role == "Content Provider":
                        self.txtOrganization.SetValue(person.entity.fname.value)

            elif isinstance(self.node, ims.contentpackage.Item):
                lang = appdata.projectLanguage
                for person in self.content.metadata.lom.lifecycle.contributors:
                    if person.role.value.getKeyOrEmptyString(lang) == "Content Provider":
                        vcard = conman.vcard.VCard()
                        vcard.parseString(person.centity.vcard.text)
                        self.txtOrganization.SetValue(vcard.fname.value)

    def CheckAuthor(self, event):
        text = self.txtAuthor.GetValue()
        for name in self.parent.vcardlist.keys():
            if string.find(name, text) == 0:
                self.txtAuthor.SetValue(name)
            self.txtAuthor.SetInsertionPoint(len(text))
            self.txtAuthor.SetSelection(len(text), len(name))

    def btnSelectFileClicked(self, event):
        isEClassPluginPage = False

        self.filename = guiutils.importFile(event.filename)
        
        self.txtExistingFile.SetValue(self.filename)

    def btnOKClicked(self, event):
        if self.txtTitle.GetValue() == "":
            wx.MessageBox(_("Please enter a name for your page."))
            return

        if self.txtExistingFile.GetValue() == "":
            wx.MessageBox(_("Please select a file to provide the content for this page."))
            return 

        lang = appdata.projectLanguage
        
        assert self.txtTitle.GetValue() is not None and self.txtTitle.GetValue() != ""
        self.node.title.text = self.txtTitle.GetValue()
        self.content.metadata.lom.general.description[lang] = self.txtDescription.GetValue()
        self.content.metadata.lom.general.keyword[lang] = self.txtKeywords.GetValue()
        self.content.metadata.lom.rights.description[lang] = self.txtCredit.GetValue()
        
        filename = self.txtExistingFile.GetValue()            
        self.content.setFilename(filename)
            
        for person in self.content.metadata.lom.lifecycle.contributors:
            role = person.role.value.getKeyOrEmptyString(lang)
            if role in ["Author", "Content Provider"]:
                if (role == "Author" and self.txtAuthor.GetValue() == "" and self.txtDate.GetValue() == "") \
                    or (role == "Content Provider" and self.txtOrganization.GetValue() == ""):
                    self.content.metadata.lom.lifecycle.contributors.remove(person)
                else:
                    vcard = conman.vcard.VCard()
                    vcard.parseString(person.centity.vcard.text)
                    if role == "Author":
                        vcard.fname.value = self.txtAuthor.GetValue()
                        if self.txtDate.GetValue() != "":
                            person.date.datetime.text = self.txtDate.GetValue()
                    else:
                        vcard.fname.value = self.txtOrganization.GetValue()
                    

        if not self.txtAuthor.GetValue() == "":
            self.UpdateContactInfo(self.txtAuthor.GetValue(), "Author")

        if not self.txtOrganization.GetValue() == "":
            self.UpdateContactInfo(self.txtOrganization.GetValue(), "Content Provider")

        self.EndModal(wx.ID_OK)

    def UpdateContactInfo(self, name, role):
        """
        Updates the contact's information, or adds them to the contact database
        if there's no info on the contact.
        """
        if role == "":
            role = "Author"
        newcard = None
        if not name in appdata.vcards.keys():
            newcard = vcard.VCard()
            newcard.fname.value = name
            newcard.filename = os.path.join(settings.PrefDir, "Contacts", fileutils.MakeFileName2(name) + ".vcf")
            myfile = utils.openFile(newcard.filename, "wb")
            myfile.write(newcard.asString())
            myfile.close()
            appdata.vcards[newcard.fname.value] = newcard
        else:
            newcard = appdata.vcards[name]

        if isinstance(self.node, conman.conman.ConNode):        
            hasPerson = False
            for person in self.content.metadata.lifecycle.contributors:
                if person.role == role:
                    hasPerson = True
                    person.entity = newcard
    
            if not hasPerson:
                contrib = conman.Contributor()
                contrib.role = role
                contrib.entity = newcard
                self.content.metadata.lifecycle.contributors.append(contrib)
