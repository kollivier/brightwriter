import string, sys, os
import wx
import wxaddons.sized_controls as sc
import wxaddons.persistence
import select_box as picker
import settings
import gui.contacts

import conman
import conman.vcard as vcard
import fileutils
import utils
import plugins

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
		self.parent = parent
		self.dir = dir
		self.filename = ""
		self.updatetoc = False

		self.notebook = wx.Notebook(pane, -1)
		self.notebook.SetSizerProps({"expand":True, "proportion":1})
		
		self.notebook.AddPage(self.GeneralPanel(), _("General"))
		self.notebook.AddPage(self.CreditPanel(), _("Credits"))
		self.notebook.AddPage(self.ClassificationPanel(), _("Categories"))

		self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))

		self.Fit()
		self.SetMinSize(self.GetSize())

		if self.content.filename != "":
			filename = self.content.filename
			self.txtExistingFile.SetValue(filename)

		wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)	

	def GeneralPanel(self):	
		mypanel = sc.SizedPanel(self.notebook, -1)
		mypanel.SetSizerType("form")
		
		wx.StaticText(mypanel, -1, _("Name"))
		self.txtTitle = wx.TextCtrl(mypanel, -1, self.content.metadata.name)
		self.txtTitle.SetSizerProp("expand", True)
		
		wx.StaticText(mypanel, -1, _("Description"))
		self.txtDescription = wx.TextCtrl(mypanel, -1, self.content.metadata.description, style=wx.TE_MULTILINE)
		self.txtDescription.SetSizerProp("expand", True)
		
		wx.StaticText(mypanel, -1, _("Keywords"))
		self.txtKeywords = wx.TextCtrl(mypanel, -1, self.content.metadata.keywords, size=wx.Size(160, -1))
		self.txtKeywords.SetSizerProp("expand", True)

		wx.StaticText(mypanel, -1, _("Page Content:"))
		self.txtExistingFile = picker.SelectBox(mypanel, self.content.filename)

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
		peopleIcon = wx.Bitmap(os.path.join(settings.AppDir, "icons", "users16.gif"), wx.BITMAP_TYPE_GIF)
		contactBtn = wx.BitmapButton(authorPanel, -1, peopleIcon)
		
		wx.EVT_BUTTON(contactBtn, contactBtn.GetId(), handler)
				
		return combobox

	def CreditPanel(self):
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
		self.txtCredit = wx.TextCtrl(mypanel, -1, self.content.metadata.rights.description, style=wx.TE_MULTILINE)
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
		dir = os.path.dirname(event.filename)
		basename = os.path.basename(event.filename)
		filename = event.filename
		isEClassPluginPage = False

		if basename == "imsmanifest.xml": #another publication
			self.node = conman.ConMan()
			self.node.LoadFromXML(os.path.join(filename))
			self.filename = filename
		else:
			plugin = plugins.GetPluginForFilename(filename)
			copyfile = False 
			destdir = os.path.join(settings.ProjectDir, plugin.plugin_info["Directory"])
			# Don't do anything if the user selected the same file
			destfile = os.path.join(destdir, basename) 
			if destfile == filename:
				pass
			elif os.path.exists(destfile):
				msg = wx.MessageDialog(self, _("The file %(filename)s already exists. Do you want to overwrite this file?") % {"filename": self.content.filename},
										   _("Overwrite File?"), wx.YES_NO)
				answer = msg.ShowModal()
				msg.Destroy()
				if answer == wx.ID_YES:
					copyfile = True
			else:
				copyfile = True
				
			if copyfile:
				fileutils.CopyFile(basename, dir, destdir)
			self.filename = os.path.join(plugin.plugin_info["Directory"], basename)
		
		self.txtExistingFile.SetValue(self.filename)

	def btnOKClicked(self, event):
		if self.txtTitle.GetValue() == "":
			wx.MessageBox(_("Please enter a name for your page."))
			return

		if self.txtExistingFile.GetValue() == "":
			wx.MessageBox(_("Please select a file to provide the content for this page."))
			return 

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
		self.EndModal(wx.ID_OK)

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
			newcard.filename = os.path.join(settings.PrefDir, "Contacts", MakeFileName2(name) + ".vcf")
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