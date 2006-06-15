import string, sys, os
from wxPython.wx import *
from conman import vcard
import utils
import fileutils

class ContactsDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Contact Manager"), wxPoint(100,100),wxSize(300,300), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.lstContacts = wxListBox(self, -1)

		self.btnAdd = wxButton(self, -1, _("Add"))
		self.btnEdit = wxButton(self, -1, _("Edit"))
		self.btnRemove = wxButton(self, -1, _("Remove"))

		self.btnImport = wxButton(self, -1, _("Import"))
		self.btnClose = wxButton(self, wxID_CANCEL, _("Close"))

		EVT_BUTTON(self.btnAdd, self.btnAdd.GetId(), self.OnAdd)
		EVT_BUTTON(self.btnImport, self.btnImport.GetId(), self.OnImport)
		EVT_BUTTON(self.btnEdit, self.btnEdit.GetId(), self.OnEdit)
		EVT_BUTTON(self.btnRemove, self.btnRemove.GetId(), self.OnRemove)

		mysizer = wxBoxSizer(wxVERTICAL)
		contactsizer = wxBoxSizer(wxHORIZONTAL)
		contactsizer.Add(self.lstContacts, 1, wxEXPAND | wxALL, 4)

		contactBtnSizer = wxBoxSizer(wxVERTICAL)
		contactBtnSizer.Add(self.btnAdd)
		contactBtnSizer.Add(self.btnEdit)
		contactBtnSizer.Add(self.btnRemove)
		contactsizer.Add(contactBtnSizer, 0, wxALL | wxALIGN_CENTRE, 4)

		mysizer.Add(contactsizer, 1, wxEXPAND)

		btnsizer = wxBoxSizer(wxHORIZONTAL)
		btnsizer.Add(self.btnImport, 0, wxALL, 4)
		btnsizer.Add((1,1), 1, wxEXPAND)
		btnsizer.Add(self.btnClose, 0, wxALL, 4)
		
		mysizer.Add(btnsizer, 0, wxEXPAND)

		self.SetSizer(mysizer)
		self.SetAutoLayout(True)

		self.LoadContacts()
		self.Layout()

	def LoadContacts(self):
		self.lstContacts.Clear()
		for name in self.parent.vcardlist.keys():
			if not string.strip(name) == "":
				self.lstContacts.Append(name, self.parent.vcardlist[name])

	def OnAdd(self, event):
		thisvcard = vcard.VCard()
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wxID_OK:
			thisname = editor.vcard.fname.value
			self.parent.vcardlist[thisname] = editor.vcard
			self.lstContacts.Append(thisname, self.parent.vcardlist[thisname])

	def OnImport(self, event):
		dialog = wxFileDialog(self, _("Choose a vCard"), "", "", _("vCard Files") + " (*.vcf)|*.vcf", wxOPEN)
		if dialog.ShowModal() == wxID_OK:
			filename = ""
			try:
				contactsdir = os.path.join(self.parent.PrefDir, "Contacts")
				shutil.copy(dialog.GetPath(), contactsdir)
				newvcard = vcard.VCard()
				filename = os.path.join(contactsdir, dialog.GetFilename())
				#if sys.platform == "win32":
				#	filename = win32api.GetShortPathName(filename)
				newvcard.parseFile(filename)
				if newvcard.fname.value == "":
					myvcard.fname.value = myvcard.name.givenName + " "
					if myvcard.name.middleName != "":
						myvcard.fname.value = myvcard.fname.value + myvcard.name.middleName + " "
					myvcard.fname.value = myvcard.fname.value + myvcard.name.familyName
				self.parent.vcardlist[newvcard.fname.value] = newvcard
				self.lstContacts.Append(newvcard.fname.value, newvcard)
			except:
				message = _("The VCard %(filename)s could not be imported.") % {"filename": dialog.GetFilename()}
				if filename != "":
					try:
						os.remove(filename)
					except:
						pass
				self.parent.log.write(message)
				wxMessageBox(message)

	def OnEdit(self, event):
		thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
		name = thisvcard.fname.value
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wxID_OK:
			thisname = editor.vcard.fname.value
			if name != thisname:
				self.parent.vcardlist.pop(name)
			self.parent.vcardlist[thisname] = editor.vcard
			self.lstContacts.SetClientData(self.lstContacts.GetSelection(), editor.vcard)
		editor.Destroy()

	def OnRemove(self, event):
		result = wxMessageDialog(self, _("This action cannot be undone. Would you like to continue?"), _("Remove Contact?"), wxYES_NO).ShowModal()
		if result == wxID_YES:
			thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
			try:
				os.remove(thisvcard.filename)
			except:
				message = _("The contact could not be deleted. Please ensure you have the proper permissions to access the EClass.Builder data directory.")
				self.parent.log.write(message)
				wxMessageBox(message)
				return

			del self.parent.vcardlist[thisvcard.fname.value]
			self.lstContacts.Delete(self.lstContacts.GetSelection())

class ContactEditor(wxDialog):
	def __init__(self, parent, myvcard):
		wxDialog.__init__ (self, parent, -1, _("Contact Editor"), wxPoint(100,100),wxSize(300,300), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.myvcard = myvcard
		self.parent = parent
		self.lblFullName = wxStaticText(self, -1, _("Full Name"))
		self.txtFullName = wxTextCtrl(self, -1, myvcard.fname.value)
		self.lblFirstName = wxStaticText(self, -1, _("First"))
		self.txtFirstName = wxTextCtrl(self, -1, myvcard.name.givenName)
		self.lblMiddleName = wxStaticText(self, -1, _("Middle"))
		self.txtMiddleName = wxTextCtrl(self, -1, myvcard.name.middleName)
		self.lblLastName = wxStaticText(self, -1, _("Last"))
		self.txtLastName = wxTextCtrl(self, -1, myvcard.name.familyName)
		self.lblPrefix = wxStaticText(self, -1, _("Prefix"))
		self.txtPrefix = wxTextCtrl(self, -1, myvcard.name.prefix, size=wxSize(40, -1))
		self.lblSuffix = wxStaticText(self, -1, _("Suffix"))
		self.txtSuffix = wxTextCtrl(self, -1, myvcard.name.suffix, size=wxSize(40, -1))

		self.lblTitle = wxStaticText(self, -1, _("Title"))
		self.txtTitle = wxTextCtrl(self, -1, myvcard.title.value)

		self.lblOrganization = wxStaticText(self, -1, _("Organization"))
		self.txtOrganization = wxTextCtrl(self, -1, myvcard.organization.name)

		self.lblEmail = wxStaticText(self, -1, _("Email"))
		email = ""
		if len(myvcard.emails) > 0:
			email = myvcard.emails[0].value

		self.txtEmail = wxTextCtrl(self, -1, email)

		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))

		mysizer = wxBoxSizer(wxVERTICAL)
		prefixsizer = wxBoxSizer(wxHORIZONTAL)
		prefixsizer.AddMany([(self.lblFullName, 0, wxALL, 4), (self.txtFullName, 1, wxALL | wxEXPAND, 4)])
		mysizer.Add(prefixsizer)
		propsizer = wxFlexGridSizer(2, 6, 2, 2)
		propsizer.AddMany([
						(self.lblFirstName, 0, wxALL, 4), (self.txtFirstName, 0, wxALL | wxEXPAND, 4),
						(self.lblMiddleName, 0, wxALL, 4), (self.txtMiddleName, 0, wxALL, 4),
						(self.lblLastName, 0, wxALL, 4), (self.txtLastName, 0, wxALL | wxEXPAND, 4),
						(self.lblPrefix, 0, wxALL, 4), (self.txtPrefix, 0, wxALL, 4), 
						(self.lblSuffix, 0, wxALL, 4), (self.txtSuffix, 0, wxALL, 4),((1,1))])
		mysizer.Add(propsizer, 0, wxEXPAND)
		propsizer2 = wxFlexGridSizer(2, 4, 2, 2)
		propsizer2.AddMany([(self.lblTitle, 0, wxALL, 4), (self.txtTitle, 1, wxALL | wxEXPAND, 4), 
						(self.lblOrganization, 0, wxALL, 4), (self.txtOrganization, 1, wxALL | wxEXPAND, 4),
						(self.lblEmail, 0, wxALL, 4), (self.txtEmail, 1, wxALL | wxEXPAND, 4)])
		mysizer.Add(propsizer2, 0, wxEXPAND)
		
		btnsizer = wxStdDialogButtonSizer()
		btnsizer.AddButton(self.btnOK)
		btnsizer.AddButton(self.btnCancel)
		btnsizer.Realize()
		mysizer.Add(btnsizer, 0, wxEXPAND | wxALL, 4)

		self.SetSizerAndFit(mysizer)
		self.SetAutoLayout(True)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOK)

	def OnOK(self, event):
		if self.txtFullName.GetValue() == "":
			wxMessageBox(_("You must enter a full name for this contact."))

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
			prefdir = self.parent.parent.PrefDir
			thisfilename = os.path.join(prefdir, "Contacts", fileutils.MakeFileName2(self.myvcard.fname.value) + ".vcf")
			if os.path.exists(thisfilename):
				result = wxMessageDialog(self, _("A contact with this name already exists. Overwrite existing contact file?"), _("Overwrite contact?"), wxYES_NO).ShowModal()
				if result == wxID_YES: 
					self.myvcard.filename = thisfilename
				else:
					return 
			else:
				self.myvcard.filename = thisfilename

		myfile = utils.openFile(self.myvcard.filename, "wb")
		myfile.write(self.myvcard.asString())
		myfile.close()

		self.vcard = self.myvcard
		self.EndModal(wxID_OK)