import string, sys, os
import wx
import wxaddons.sized_controls as sc
import persistence

from conman import vcard
import utils
import fileutils
import settings
import appdata

class ContactsDialog(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("Contact Manager"), 
		                          wx.Point(100,100),wx.Size(300,300), 
		                          wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		                          
		self.parent = parent
		pane = self.GetContentsPane()
		
		wx.StaticText(pane, -1, _("Contacts"))
		
		self.lstContacts = wx.ListBox(pane, -1)
		self.lstContacts.SetSizerProps({"expand":True, "proportion":1})

		btnPane = sc.SizedPanel(pane, -1)
		btnPane.SetSizerType("horizontal")
		btnPane.SetSizerProp("halign", "center")
		
		self.btnImport = wx.Button(btnPane, -1, _("Import"))
		self.btnAdd = wx.Button(btnPane, -1, _("Add"))
		self.btnEdit = wx.Button(btnPane, -1, _("Edit"))
		self.btnRemove = wx.Button(btnPane, -1, _("Remove"))

		wx.EVT_BUTTON(self.btnAdd, self.btnAdd.GetId(), self.OnAdd)
		wx.EVT_BUTTON(self.btnImport, self.btnImport.GetId(), self.OnImport)
		wx.EVT_BUTTON(self.btnEdit, self.btnEdit.GetId(), self.OnEdit)
		wx.EVT_LISTBOX_DCLICK(self.lstContacts, self.lstContacts.GetId(), self.OnEdit)
		wx.EVT_BUTTON(self.btnRemove, self.btnRemove.GetId(), self.OnRemove)

		self.LoadContacts()
		self.Fit()
		self.SetMinSize(self.GetSize())

	def LoadContacts(self):
		self.lstContacts.Clear()
		for name in appdata.vcards.keys():
			if not string.strip(name) == "":
				self.lstContacts.Append(name, appdata.vcards[name])

	def OnAdd(self, event):
		thisvcard = vcard.VCard()
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wx.ID_OK:
			thisname = editor.vcard.fname.value
			appdata.vcards[thisname] = editor.vcard
			self.lstContacts.Append(thisname, appdata.vcards[thisname])

	def OnImport(self, event):
		dialog = wx.FileDialog(self, _("Choose a vCard"), "", "", 
		                      _("vCard Files") + " (*.vcf)|*.vcf", wx.OPEN)
		
		if dialog.ShowModal() == wx.ID_OK:
			filename = ""
			try:
				contactsdir = os.path.join(settings.PrefDir, "Contacts")
				shutil.copy(dialog.GetPath(), contactsdir)
				newvcard = vcard.VCard()
				filename = os.path.join(contactsdir, dialog.GetFilename())
				#if sys.platform == "win32":
				#	filename = win32api.GetShortPathName(filename)
				newvcard.parseFile(filename)
				
				# make a fullname entry if one doesn't exist
				if newvcard.fname.value == "":
					myvcard.fname.value = myvcard.name.givenName + " "
					if myvcard.name.middleName != "":
						myvcard.fname.value = myvcard.fname.value + myvcard.name.middleName + " "
					myvcard.fname.value = myvcard.fname.value + myvcard.name.familyName
				
				appdata.vcards[newvcard.fname.value] = newvcard
				self.lstContacts.Append(newvcard.fname.value, newvcard)
			except:
				message = _("The VCard %(filename)s could not be imported.") % {"filename": dialog.GetFilename()}
				if filename != "":
					try:
						os.remove(filename)
					except:
						pass
				self.parent.log.write(message)
				wx.MessageBox(message)

	def OnEdit(self, event):
		thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
		name = thisvcard.fname.value
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wx.ID_OK:
			thisname = editor.vcard.fname.value
			if name != thisname:
				appdata.vcards.pop(name)
			appdata.vcards[thisname] = editor.vcard
			self.lstContacts.SetClientData(self.lstContacts.GetSelection(), editor.vcard)
		editor.Destroy()

	def OnRemove(self, event):
		result = wx.MessageDialog(self, 
		                       _("This action cannot be undone. Would you like to continue?"), 
		                       _("Remove Contact?"), wx.YES_NO).ShowModal()
		if result == wx.ID_YES:
			thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
			try:
				os.remove(thisvcard.filename)
			except:
				message = _("The contact could not be deleted. Please ensure you have the proper permissions to access the EClass.Builder data directory.")
				self.parent.log.write(message)
				wx.MessageBox(message)
				return

			del appdata.vcards[thisvcard.fname.value]
			self.lstContacts.Delete(self.lstContacts.GetSelection())

class ContactEditor(sc.SizedDialog):
	def __init__(self, parent, myvcard):
		sc.SizedDialog.__init__ (self, parent, -1, _("Contact Editor"), 
		                          wx.Point(100,100), wx.Size(300,300), 
		                          wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.myvcard = myvcard
		self.parent = parent
		pane = self.GetContentsPane()
		pane.SetSizerType("form")
		wx.StaticText(pane, -1, _("Full Name"))
		self.txtFullName = wx.TextCtrl(pane, -1, myvcard.fname.value)
		
		wx.StaticText(pane, -1, _("First"))
		self.txtFirstName = wx.TextCtrl(pane, -1, myvcard.name.givenName)
		
		wx.StaticText(pane, -1, _("Middle"))
		self.txtMiddleName = wx.TextCtrl(pane, -1, myvcard.name.middleName)
		
		wx.StaticText(pane, -1, _("Last"))
		self.txtLastName = wx.TextCtrl(pane, -1, myvcard.name.familyName)
		
		wx.StaticText(pane, -1, _("Prefix"))
		self.txtPrefix = wx.TextCtrl(pane, -1, myvcard.name.prefix, size=wx.Size(40, -1))
		
		wx.StaticText(pane, -1, _("Suffix"))
		self.txtSuffix = wx.TextCtrl(pane, -1, myvcard.name.suffix, size=wx.Size(40, -1))

		wx.StaticText(pane, -1, _("Title"))
		self.txtTitle = wx.TextCtrl(pane, -1, myvcard.title.value)

		wx.StaticText(pane, -1, _("Organization"))
		self.txtOrganization = wx.TextCtrl(pane, -1, myvcard.organization.name)

		wx.StaticText(pane, -1, _("Email"))
		email = ""
		if len(myvcard.emails) > 0:
			email = myvcard.emails[0].value

		self.txtEmail = wx.TextCtrl(pane, -1, email)

		self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))

		self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)

	def OnOK(self, event):
		if self.txtFullName.GetValue() == "":
			wx.MessageBox(_("You must enter a full name for this contact."))
			return

		self.myvcard.fname.value = self.txtFullName.GetValue()
		self.myvcard.name.prefix = self.txtPrefix.GetValue()
		self.myvcard.name.suffix = self.txtSuffix.GetValue()
		self.myvcard.name.familyName = self.txtLastName.GetValue()
		self.myvcard.name.middleName = self.txtMiddleName.GetValue()
		self.myvcard.name.givenName = self.txtFirstName.GetValue()
		self.myvcard.title.value = self.txtTitle.GetValue()
		self.myvcard.organization.name = self.txtOrganization.GetValue()
		if len(self.myvcard.emails) == 0: 
			self.myvcard.emails.append(vcard.Email())
		self.myvcard.emails[0].value = self.txtEmail.GetValue()
		if self.myvcard.filename == "":
			prefdir = settings.PrefDir
			thisfilename = os.path.join(prefdir, "Contacts", 
			                           fileutils.MakeFileName2(self.myvcard.fname.value) + ".vcf")
			if os.path.exists(thisfilename):
				result = wx.MessageDialog(self, _("A contact with this name already exists. Overwrite existing contact file?"),
				                                _("Overwrite contact?"), 
				                                wx.YES_NO).ShowModal()
				if result == wx.ID_YES: 
					self.myvcard.filename = thisfilename
				else:
					return 
			else:
				self.myvcard.filename = thisfilename

		myfile = utils.openFile(self.myvcard.filename, "wb")
		myfile.write(self.myvcard.asString())
		myfile.close()

		self.vcard = self.myvcard
		self.EndModal(wx.ID_OK)