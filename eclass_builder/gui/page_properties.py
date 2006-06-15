import string, sys, os
from wxPython.wx import *
from fileutils import *
import utils
import plugins

class PagePropertiesDialog (wxDialog):
	"""
	Content page editing modal dialog window
	"""
	def __init__(self, parent, node, content, dir):
		"""
		"""
		wxDialog.__init__ (self, parent, -1, _("Page Properties"),
						 wxPoint(100,100),
						   wxSize(260,300),
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)

		# Storage for the attribute name/value pair
		self.node = node
		self.content = content 
		self.parent = parent
		self.dir = dir
		self.filename = ""
		self.updatetoc = False

		self.notebook = wxNotebook(self, -1)
		self.notebook.AddPage(self.GeneralPanel(), _("General"))
		self.notebook.AddPage(self.CreditPanel(), _("Credits"))
		self.notebook.AddPage(self.ClassificationPanel(), _("Categories"))

		self.btnOK = wxButton(self,wxID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(wxNotebookSizer(self.notebook), 1, wxEXPAND | wxALL, 4)
		
	 	self.buttonsizer = wxStdDialogButtonSizer()
		self.buttonsizer.AddButton(self.btnOK)
		self.buttonsizer.AddButton(self.btnCancel)
		self.buttonsizer.Realize()
		self.mysizer.Add(self.buttonsizer, 0, wxALL|wxALIGN_RIGHT, 4)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		if self.content.filename != "":
			filename = self.content.filename
			self.txtExistingFile.SetValue(filename)

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)	

	def GeneralPanel(self):
		icnFolder = wxBitmap(os.path.join(self.parent.AppDir, "icons", "Open.gif"), wxBITMAP_TYPE_GIF)
	
		mypanel = wxPanel(self.notebook, -1)
		self.lblTitle = wxStaticText(mypanel, -1, _("Name"))
		self.lblDescription = wxStaticText(mypanel, -1, _("Description"))
		self.lblKeywords = wxStaticText(mypanel, -1, _("Keywords"))
		#self.lblPublic = wxStaticText(mypanel, -1, _("Public"))
		self.lblContent = wxStaticText(mypanel, -1, _("Page Content:"))

		self.txtTitle = wxTextCtrl(mypanel, -1, self.content.metadata.name)
		self.txtDescription = wxTextCtrl(mypanel, -1, self.content.metadata.description, style=wxTE_MULTILINE)
		self.txtKeywords = wxTextCtrl(mypanel, -1, self.content.metadata.keywords, size=wxSize(160, -1))
		#public_values = [_("true"), _("false")]
		#self.txtPublic = wxChoice(mypanel, -1, wxDefaultPosition, wxSize(160,-1), public_values)
		#if self.content.public == "True":
		#	self.txtPublic.SetSelection(0)
		#else:
		#	self.txtPublic.SetSelection(1)

		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(-1, -1)

		self.btnSelectFile = wxBitmapButton(mypanel, -1, icnFolder, size=wxSize(20, 18))
		self.txtExistingFile = wxTextCtrl(mypanel, -1, "", size=wxSize(160, -1))


   		mysizer = wxBoxSizer(wxVERTICAL)
   		self.gridSizer = wxFlexGridSizer(0, 2, 4, 4)
   		self.gridSizer.Add(self.lblTitle, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtTitle, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblDescription, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtDescription, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblKeywords, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtKeywords, 1, wxEXPAND|wxALL, 4)
   		#self.gridSizer.Add(self.lblPublic, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		#self.gridSizer.Add(self.txtPublic, 1, wxEXPAND|wxALL, 4)
   		#self.gridSizer.Add(self.lblTemplate, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		#self.gridSizer.Add(self.cmbTemplate, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblContent, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
  
   		self.smallsizer = wxBoxSizer(wxHORIZONTAL)
   		self.smallsizer.Add(self.txtExistingFile, 1, wxEXPAND|wxALL, 4)
   		self.smallsizer.Add(self.btnSelectFile, 0, wxALIGN_CENTER|wxALL, 4)
  
   		self.gridSizer.Add(self.smallsizer, 1, wxEXPAND|wxALL, 4)
   		mysizer.Add(self.gridSizer, 1, wxEXPAND)
		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)

		return mypanel

	def CreditPanel(self):
		mypanel = wxPanel(self.notebook, -1)
		peopleIcon = wxBitmap(os.path.join(self.parent.AppDir, "icons", "users16.gif"), wxBITMAP_TYPE_GIF)
		self.lblAuthor = wxStaticText(mypanel, -1, _("Author"))
		self.txtAuthor = wxComboBox(mypanel, -1)
		self.btnAuthor = wxBitmapButton(mypanel, -1, peopleIcon, size=wxSize(20, 18))
		
		self.lblDate = wxStaticText(mypanel, -1, _("Creation/Publication Date (Format: YYYY-MM-DD)"))
		self.txtDate = wxTextCtrl(mypanel, -1)

		self.lblOrganization = wxStaticText(mypanel, -1, _("Organization/Publisher"))
		self.txtOrganization = wxComboBox(mypanel, -1)
		self.btnOrganization = wxBitmapButton(mypanel, -1, peopleIcon, size=wxSize(20, 18))

		#self.lblContributors = wxStaticText(mypanel, -1, _("Contributors"))
		#self.lstContributors = wxListCtrl(mypanel, -1, style=wxLC_REPORT)
		#self.lstContributors.InsertColumn(0, _("Role"))
		#self.lstContributors.InsertColumn(1, _("Entity"))
		#self.lstContributors.InsertColumn(2, _("Date"))

		#self.btnAdd = wxButton(mypanel, -1, _("Add"))
		#self.btnEdit = wxButton(mypanel, -1, _("Edit"))
		#self.btnRemove = wxButton(mypanel, -1, _("Remove"))

		self.lblCredit = wxStaticText(mypanel, -1, _("Credits"))
		self.txtCredit = wxTextCtrl(mypanel, -1, self.content.metadata.rights.description, style=wxTE_MULTILINE)

		mysizer = wxBoxSizer(wxVERTICAL)
		mysizer.Add(self.lblAuthor, 0, wxALL, 4)
		authorsizer = wxBoxSizer(wxHORIZONTAL)
		authorsizer.Add(self.txtAuthor, 1, wxEXPAND | wxALL, 4)
		authorsizer.Add(self.btnAuthor, 0, wxALL, 4)
		mysizer.Add(authorsizer, 0, wxEXPAND)

		mysizer.Add(self.lblDate, 0, wxALL, 4)
		mysizer.Add(self.txtDate, 0, wxALL | wxEXPAND, 4)

		mysizer.Add(self.lblOrganization, 0, wxALL, 4)
		orgsizer = wxBoxSizer(wxHORIZONTAL)
		orgsizer.Add(self.txtOrganization, 1, wxEXPAND | wxALL, 4)
		orgsizer.Add(self.btnOrganization, 0, wxALL, 4)
		mysizer.Add(orgsizer, 0, wxEXPAND)

		#mysizer.Add(self.lblContributors, 0, wxALL, 4)
		#mysizer.Add(self.lstContributors, 0, wxEXPAND | wxALL, 4)
		#buttonsizer = wxBoxSizer(wxHORIZONTAL)
		#buttonsizer.Add(self.btnAdd)
		#buttonsizer.Add(self.btnEdit)
		#buttonsizer.Add(self.btnRemove)
		#mysizer.Add(buttonsizer, 0, wxALIGN_CENTRE)
		
		mysizer.Add(self.lblCredit, 0, wxALL, 4)
		mysizer.Add(self.txtCredit, 0, wxALL | wxEXPAND, 4)

		self.UpdateAuthorList()

		EVT_BUTTON(self.btnAuthor, self.btnAuthor.GetId(), self.OnLoadContacts)
		EVT_BUTTON(self.btnOrganization, self.btnOrganization.GetId(), self.OnLoadContacts)
		#EVT_TEXT(self.txtAuthor, self.txtAuthor.GetId(), self.CheckAuthor)
		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		return mypanel

	def ClassificationPanel(self):
		mypanel = wxPanel(self.notebook, -1)
		
		self.lblCategories = wxStaticText(mypanel, -1, _("Categories"))
		self.lstCategories = wxListBox(mypanel, -1)

		self.btnAddCategory = wxButton(mypanel, -1, _("Add"))
		self.btnEditCategory = wxButton(mypanel, -1, _("Edit"))
		self.btnRemoveCategory = wxButton(mypanel, -1, _("Remove"))

		mysizer = wxBoxSizer(wxVERTICAL)
		mysizer.Add(self.lblCategories, 0, wxALL, 4)
		mysizer.Add(self.lstCategories, 0, wxEXPAND | wxALL, 4)
		buttonsizer = wxBoxSizer(wxHORIZONTAL)
		buttonsizer.Add(self.btnAddCategory)
		buttonsizer.Add(self.btnEditCategory)
		buttonsizer.Add(self.btnRemoveCategory)
		mysizer.Add(buttonsizer, 0, wxALIGN_CENTRE)

		for item in self.content.metadata.classification.categories:
			self.lstCategories.Append(item)
		
		EVT_BUTTON(self.btnAddCategory, self.btnAddCategory.GetId(), self.AddCategory)
		EVT_BUTTON(self.btnEditCategory, self.btnEditCategory.GetId(), self.EditCategory)
		EVT_BUTTON(self.btnRemoveCategory, self.btnRemoveCategory.GetId(), self.RemoveCategory)
		EVT_ACTIVATE(self, self.UpdateAuthorList)

		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		return mypanel

	def AddCategory(self, event):
		dialog = wxTextEntryDialog(self, _("Please type the name of the new category here."), _("Add Category"))
		if dialog.ShowModal() == wxID_OK:
			value = dialog.GetValue()
			if value != "":
				self.lstCategories.Append(value)

	def EditCategory(self, event):
		selitem = self.lstCategories.GetSelection()
		if selitem != wxNOT_FOUND:
			dialog = wxTextEntryDialog(self, _("Type the new value for your category here."), _("Edit Category"), self.lstCategories.GetStringSelection())
			if dialog.ShowModal() == wxID_OK:
				value = dialog.GetValue()
				if value != "":
					self.lstCategories.SetString(selitem, value)

	def RemoveCategory(self, event):
		selitem = self.lstCategories.GetSelection()
		if selitem != wxNOT_FOUND:
			self.lstCategories.Delete(selitem)

	def OnLoadContacts(self, event):
		ContactsDialog(self.parent).ShowModal()
		self.UpdateAuthorList()

	def UpdateAuthorList(self, event=None):
		oldvalue = self.txtAuthor.GetValue()
		self.txtAuthor.Clear()
		for name in self.parent.vcardlist.keys():
			self.txtAuthor.Append(name, self.parent.vcardlist[name])

		oldorg = self.txtOrganization.GetValue()
		self.txtOrganization.Clear()
		for name in self.parent.vcardlist.keys():
			self.txtOrganization.Append(name, self.parent.vcardlist[name])

		if oldvalue != "":
			self.txtAuthor.SetValue(oldvalue)
		else:
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Author":
					self.txtAuthor.SetValue(person.entity.fname.value)
					if person.date != "":
						self.txtDate.SetValue(person.date)
				elif person.role == "Content Provider":
					self.txtOrganization.SetValue(person.entity.fname.value)

		if oldorg != "":
			self.txtOrganization.SetValue(oldorg)
		else:
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Content Provider":
					self.txtOrganization.SetValue(person.entity.fname.value)

	def CheckAuthor(self, event):
		text = self.txtAuthor.GetValue()
		for name in self.parent.vcardlist.keys():
			if string.find(name, text) == 0:
				self.txtAuthor.SetValue(name)
			self.txtAuthor.SetInsertionPoint(len(text))
			self.txtAuthor.SetSelection(len(text), len(name))

	def btnSelectFileClicked(self, event):
		filtertext = "All Files (*.*)|*.*"
		for plugin in plugins.pluginList:
			if filtertext != "":
				filtertext = filtertext + "|"
			textext = ""
			filterext = ""
			for count in range(0, len(plugin.plugin_info["Extension"])):
				textext = textext + "*." + plugin.plugin_info["Extension"][count]
				filterext = filterext + "*." + plugin.plugin_info["Extension"][count]
				if not count == (len(plugin.plugin_info["Extension"]) - 1):
					textext = textext + ", "
					filterext = filterext + "; "
			filtertext = filtertext + plugin.plugin_info["FullName"] + " Files (" + textext + ")|" + filterext
			
		f = wxFileDialog(self, _("Select a file"), os.path.join(settings.CurrentDir), "", filtertext, wxOPEN)
		if f.ShowModal() == wxID_OK:
			self.filedir = f.GetDirectory()
			self.filename = f.GetFilename()
			self.file = f.GetPath()
			isEClassPluginPage = False
			fileext = os.path.splitext(self.filename)[1][1:]
			page_plugin = None
			for myplugin in plugins.pluginList:
				if (fileext in myplugin.plugin_info["Extension"]):
					isEClassPluginPage = True
					page_plugin = myplugin
					break

			if isEClassPluginPage and page_plugin:
				overwrite = False 
				if os.path.join(self.parent.CurrentDir, page_plugin.plugin_info["Directory"], self.filename) == os.path.join(self.filedir, self.filename):
					pass
				elif os.path.exists(os.path.join(self.parent.CurrentDir, page_plugin.plugin_info["Directory"], self.filename)):
					msg = wxMessageDialog(self, _("The file %(filename)s already exists. Do you want to overwrite this file?") % {"filename": self.content.filename}, _("Save Project?"), wxYES_NO)
					answer = msg.ShowModal()
					msg.Destroy()
					if answer == wxID_YES:
						overwrite = True
				else:
					overwrite = True
				if overwrite:
					files.CopyFile(self.filename, self.filedir, os.path.join(self.parent.CurrentDir, page_plugin.plugin_info["Directory"]))
				self.filename = os.path.join(page_plugin.plugin_info["Directory"], self.filename)
			elif self.filename == "imsmanifest.xml": #another publication
				self.node = conman.ConMan()
				self.node.LoadFromXML(os.path.join(self.filedir, self.filename))
			else:
				self.filename = os.path.join("File", self.filename)
				if not os.path.exists(os.path.join(self.parent.CurrentDir, self.filename)):
					shutil.copy(self.file, os.path.join(self.parent.CurrentDir, "File"))
			
			self.txtExistingFile.SetValue(self.filename)
		f.Destroy()

	def btnOKClicked(self, event):
		public = "True"
		if self.txtTitle.GetValue() == "":
			wxMessageBox(_("Please enter a name for your page."))
			return

		if self.txtExistingFile.GetValue() == "":
			wxMessageBox(_("Please select a file to provide the content for this page."))
			return 

		#if self.txtPublic.GetSelection() == 1:
		#	public = "False"
		#else:
		#	public = "True"

		self.content.public = "True"

		#if self.content.public != public:
		#	self.content.public = public
		#	self.parent.Update()
		self.content.metadata.keywords = self.txtKeywords.GetValue()
		self.content.metadata.description = self.txtDescription.GetValue()
		self.content.metadata.name = self.txtTitle.GetValue()
		self.content.metadata.rights.description = self.txtCredit.GetValue()
		if not self.txtAuthor.GetValue() == "":
			self.UpdateContactInfo(self.txtAuthor.GetValue(), "Author")

		if not self.txtOrganization.GetValue() == "":
			self.UpdateContactInfo(self.txtOrganization.GetValue(), "Content Provider")

		if not self.txtDate.GetValue() == "":
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Author":
					person.date = self.txtDate.GetValue()
		else:
			#check if we can remove any empty contact info that might be there
			for person in self.content.metadata.lifecycle.contributors:
				try:
					if person.role == "Author" and self.txtAuthor.GetValue() == "":
						self.content.metadata.lifecycle.contributors.remove(person)
					elif person.role == "Content Provider" and self.txtOrganization.GetValue() == "":
						self.content.metadata.lifecycle.contributors.remove(person)
				except:
					self.parent.log.write(_("Error removing empty contact."))

		
		self.content.metadata.classification.categories = []
		for num in range(0, self.lstCategories.GetCount()):
			self.content.metadata.classification.categories.append(self.lstCategories.GetString(num))

		self.content.filename = self.txtExistingFile.GetValue()
		#self.content.template = self.cmbTemplate.GetStringSelection()
		self.EndModal(wxID_OK)

	def UpdateContactInfo(self, name, role):
		"""
		Updates the contact's information, or adds them to the contact database
		if there's no info on the contact.
		"""
		if role == "":
			role = "Author"
		newcard = None
		if not name in self.parent.vcardlist.keys():
			newcard = vcard.VCard()
			newcard.fname.value = name
			newcard.filename = os.path.join(self.parent.PrefDir, "Contacts", MakeFileName2(name) + ".vcf")
			myfile = utils.openFile(newcard.filename, "wb")
			myfile.write(newcard.asString())
			myfile.close()
			self.parent.vcardlist[newcard.fname.value] = newcard
		else:
			newcard = self.parent.vcardlist[name]

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