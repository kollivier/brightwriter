import string, sys, os
from wxPython.wx import *
from wxPython.lib import newevent
import ftplib
import traceback

(UpdateFTPDialogEvent, EVT_UPDATE_FTPDIALOG) = newevent.NewEvent()
(UploadFinishedEvent, EVT_UPLOAD_FINISHED) = newevent.NewEvent()
(UploadCanceledEvent, EVT_UPLOAD_CANCELED) = newevent.NewEvent()

#--------------------------- FTP Upload Dialog Class --------------------------------------
class FTPUpload:
	def __init__(self, parent):
		self.filelist = []
		self.dirlist = []
		self.parent = parent
		self.isDialog = False
		self.FTPSite = parent.pub.settings["FTPHost"]
		self.Username = parent.pub.settings["FTPUser"]
		self.Directory = parent.pub.settings["FTPDirectory"]
		self.Password = parent.ftppass #munge(parent.pub.settings["FTPUsername"], "foobar")
		self.stopupload = False
		self.useSearch = 0
		self.projpercent = 0
		self.filepercent = 0

		if parent.pub.settings["FTPPassive"] == "yes":
			self.usePasv = True
		else:
			self.usePasv = False

		if parent.pub.settings["SearchEnabled"] != "":
			self.useSearch = int(parent.pub.settings["SearchEnabled"])

	def StartFTP(self):
		if self.FTPSite == "":
			wxMessageBox(_("The FTP server for this project has not been specified. Please enter a FTP server by going to File->Project Settings and selecting the FTP tab."), _("Error: No FTP Server Specified"), wxICON_ERROR)
			return False
		if self.Password == "" and self.Username != "":
			dialog = wxTextEntryDialog(self.parent, _("Please enter a password to upload to FTP."), _("Enter Password"), "", wxTE_PASSWORD | wxOK | wxCANCEL)
			if dialog.ShowModal() == wxID_OK:
				self.Password = dialog.GetValue()
			else:
				return False

		self.host = ftplib.FTP(self.FTPSite, self.Username, self.Password)
		self.host.set_pasv(self.usePasv)
		self.host.sock.setblocking(1)
		self.host.set_debuglevel(2)
		self.host.sock.settimeout(30)
		return True

	def GetUploadDirName(self, indir):
		#first, strip out any hardcoded path reference
		parentdir = settings.CurrentDir
		print "Parentdir: " + parentdir

		mydir = string.replace(indir, parentdir, "")
		if wxPlatform == "__WXMSW__":
			mydir = string.replace(mydir, "\\", "/")

		#now construct the subdir as relative to the start URL
		#for the EClass
		fulldir = self.Directory + mydir
		if not fulldir[0] == "/":
			fulldir = "/" + fulldir
		print "Fulldir: " + fulldir
		return fulldir

	def GetUploadDirs(self, filelist):
		"""
		When uploading all files, do NOT use this, use GenerateFileList instead.
		This is only when we have a small list of files which may point to various
		directories.
		"""
		for afile in filelist:
			uploaddir = self.GetUploadDirName(os.path.dirname(afile))
			if not uploaddir in self.dirlist:
				self.dirlist.append(uploaddir)

	def GenerateFileList(self, indir):
		if self.useSearch == 0 and string.find(indir, "cgi-bin") != -1:
			return
		uploaddir = self.GetUploadDirName(indir)
		if not uploaddir in self.dirlist:
			self.dirlist.append(uploaddir)

		for item in os.listdir(indir):
			myitem = os.path.join(indir, item)
			
			if os.path.isfile(myitem) and not string.find(item, "._") == 0 and string.find(item, "Karrigell") == -1 and string.find(item, "httpserver") == -1 and string.find(item, "ftppass.txt") == -1:
				finalname = string.replace(myitem, settings.CurrentDir, "")
				if wxPlatform == "__WXMSW__":
					finalname = string.replace(finalname, "\\", "/")
				#finalname = string.replace(finalname, os.pathsep, "/")
				if not self.useSearch and string.find(myitem, "cgi-bin") == -1:
					if string.find(item, ".dll") == -1 and string.find(item, ".pyd") == -1 and string.find(item, ".exe") == -1:
						self.filelist.append(finalname)
				else:
					self.filelist.append(finalname)
			elif os.path.isdir(myitem):
				self.GenerateFileList(myitem)

	def CreateDirectories(self):
		if not self.StartFTP():
			return
		ftpdir = self.Directory
		if not ftpdir == "" and not ftpdir[0] == "/":
			ftpdir = "/" + ftpdir 
		if not ftpdir == "" and not ftpdir[-1] == "/":
			ftpdir = ftpdir + "/"
		self.cwd(ftpdir)
		for item in self.dirlist:
			self.cwd(item) #create the folders if they don't already exist

	def UploadFiles(self):
		import time
		if self.stopupload:
			self.host.close()
			return
		if not self.StartFTP():
			return
		self.CreateDirectories()

		#lastdir = self.Directory #this should have gotten created already
		if self.Directory == "" or not self.Directory[-1] == "/":
			self.Directory = self.Directory + "/"
		if self.isDialog:
			if wxPlatform != "__WXMAC__":
				self.projGauge.SetRange(len(self.filelist))
		myfile = None
		for item in self.filelist[:]:
			try:
				if self.stopupload:
					self.host.close()
					evt = UploadCanceledEvent()
					if self.isDialog:
						wxPostEvent(self, evt)
					return

				myitem = settings.CurrentDir + "/" + item
				myfile = utils.openFile(myitem, "rb")
				bytes = os.path.getsize(myitem)
				dir = self.Directory
				if not dir[-1] == "/":
					dir = dir + "/"
				if not dir[0] == "/":
					dir = "/" + dir
				if string.find(item, "/") != -1:
					mydir, myitem = os.path.split(item)					
					dir = dir + string.replace(mydir, "\\", "/")
					if not dir[-1] == "/":
						dir = dir + "/"
				else:
					myitem = item
		
				self.host.voidcmd('TYPE I')
				self.mysocket = self.host.transfercmd('STOR ' + dir + myitem)
				self.filepercent = 0

				evt = UpdateFTPDialogEvent(filename = myitem, projpercent = self.projpercent, filepercent = self.filepercent)
				if self.isDialog:
					wxPostEvent(self, evt)

				onepercent = bytes/100
				if onepercent == 0:
					onepercent = 1
				if self.mysocket:
					self.mysocket.setblocking(1)
					self.mysocket.settimeout(30)
					if self.isDialog:
						self.txtProgress.SetLabel(_("Current File: ") + myitem)
					elif self.parent:
						self.parent.SetStatusText(_("Uploading file %(file)s...") % {"file": myitem})
					bytesuploaded = 0
					while 1:
						block = myfile.read(4096)
						if not block or self.stopupload:
							break

						resp = self.mysocket.sendall(block)
						#time.sleep(0.001)
						bytesuploaded = bytesuploaded + 4096
						if self.isDialog:
							self.filepercent = bytesuploaded/onepercent
							evt = UpdateFTPDialogEvent(filename = myitem, projpercent = self.projpercent, filepercent = self.filepercent)
							if self.isDialog:
								wxPostEvent(self, evt)
						elif self.parent:
							self.parent.SetStatusText(_("Uploaded %(current)d of %(total)d bytes for file %(filename)s." % {"current":bytesuploaded, "total":bytes, "filename":myitem})) 
						wxYield()
					self.mysocket.close()
					self.mysocket = None
					self.host.voidresp()
					myindex = self.filelist.index(item)
					self.filelist.remove(item)

				myfile.close()

				self.projpercent = self.projpercent + 1
				evt = UpdateFTPDialogEvent(filename = myitem, projpercent = self.projpercent, filepercent = self.filepercent)
				if self.isDialog:
					wxPostEvent(self, evt)

			except ftplib.all_errors, e:
				if myfile:
					myfile.close()
				raise

		self.host.quit()
		evt = UploadFinishedEvent()
		if self.isDialog:
			wxPostEvent(self, evt)

	def getFtpErrorMessage(self, e):
		""" Given an ftplib error object, generate some common error messages. """
		code = ""
		try:
			code = e.args[0][:3]
		except:
			code = repr(e)[:3]

		if code == "550":
			return _("Attempt to create a file or directory on the server failed. Please check your file permissions. The error reported was: \n\n" + str(e.args[0]))
		elif code == "530":
			return _("EClass was unable to connect to the specified FTP server. Please check to ensure your server name, username and password are correct. The error message returned was:") + "\n\n" + str(e)
		elif code == "425":
			return _("Cannot open a data connection. Try changing the \"Use Passive FTP\" setting and uploading again.")
		elif code == "426":
			return _("Connection closed by server. Click Upload again to resume upload.")
		elif code == "452":
			return _("Server is full. You will need to either delete files from the server or ask for more server space from your system administrator.")
		else: 
			return _("An unexpected error has occurred while uploading. Please click 'Upload' again to attempt to resume uploading. The error reported was: \n\n" + repr(e)) 
			#self.parent.logfile.write(str(e))

	def cwd(self, item):
		myitem = item
		try:
			if not string.rfind(myitem, "/") == 0:
				myitem = myitem + "/"
			self.host.cwd(myitem)
		except:
			try:
				self.host.mkd(myitem)
				self.host.cwd(myitem)
			except ftplib.all_errors, e:
				raise

class FTPUploadDialog(wxDialog, FTPUpload):
	def __init__(self, parent):
		FTPUpload.__init__(self, parent)
		self.isDialog = True
		wxDialog.__init__ (self, parent, -1, _("Publish to web site"), wxPoint(100,100),wxSize(250,260), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.makefilelist = True
		self.mythread = None
		self.closewindow = False
		self.filelist = []
		self.folderlist = []
		self.projpercent = 0
		self.filepercent = 0
		#lines up labels and textboxes
		lblstart = 10
		txtstart = 80
		
		self.lblFTPSite = wxStaticText(self, -1, _("FTP Site"))
		self.txtFTPSite = wxTextCtrl(self, -1, self.parent.pub.settings["FTPHost"])
		self.lblUsername = wxStaticText(self, -1, _("Username"))
		self.txtUsername = wxTextCtrl(self, -1, self.parent.pub.settings["FTPUser"], wxPoint(txtstart, 30), wxSize(180, -1))
		self.lblPassword = wxStaticText(self, -1, _("Password"))
		self.txtPassword = wxTextCtrl(self, -1, self.parent.ftppass, style=wxTE_PASSWORD)
		self.lblDirectory = wxStaticText(self, -1, _("Directory"))
		self.txtDirectory = wxTextCtrl(self, -1, self.parent.pub.settings["FTPDirectory"])
		self.txtProgress = wxStaticText(self, -1, "Current File:") #wxTextCtrl(self, -1, "", style=wxTE_MULTILINE|wxTE_READONLY)
		self.fileGauge = wxGauge(self, -1, 1, style=wxGA_PROGRESSBAR)
		self.fileGauge.SetRange(100)
		self.txtTotalProg = wxStaticText(self, -1, "Total Progress:")
		self.projGauge = wxGauge(self, -1, 1, style=wxGA_PROGRESSBAR)
		self.projGauge.SetRange(100)
		#self.lstFiles = wxListBox(self, -1, style=wxLB_SINGLE)
		self.chkPassive = wxCheckBox(self, -1, _("Use Passive FTP"))
		self.stopupload = False

		self.btnOK = wxButton(self,-1,_("Upload"))
		self.btnOK.SetDefault()
		self.txtFTPSite.SetFocus()
		self.txtFTPSite.SetSelection(0, -1)
		self.btnCancel = wxButton(self,-1,_("Close"))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.gridsizer = wxFlexGridSizer(0, 2, 4, 4)
		self.gridsizer.Add(self.lblFTPSite, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtFTPSite, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblUsername, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtUsername, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblPassword, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtPassword, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblDirectory, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtDirectory, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add((1, 1), 0, wxALL, 4)
		self.gridsizer.Add(self.chkPassive, 0, wxALIGN_RIGHT|wxALL, 4)
		self.mysizer.Add(self.gridsizer, 3, wxEXPAND|wxALL)
		self.mysizer.Add(self.txtProgress, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.fileGauge, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.txtTotalProg, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.projGauge, 0, wxEXPAND|wxALL, 4)
		#self.mysizer.Add(self.lstFiles, 2, wxEXPAND|wxALL, 4)
		
		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0, wxALIGN_RIGHT)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.mytimer = wxTimer(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnCancel, self.btnCancel.GetId(), self.btnCancelClicked)
		#EVT_TIMER(self, self.mytimer.GetId(), self.OnHang)
		EVT_CLOSE(self, self.OnClose)
		EVT_UPDATE_FTPDIALOG(self, self.OnUpdateDialog)
		EVT_UPLOAD_FINISHED(self, self.OnUploadFinished)
		EVT_UPLOAD_CANCELED(self, self.OnUploadCanceled)
		
	def OnUploadFinished(self, event):
		self.mytimer.Stop()
		self.txtProgress.SetLabel(_("Finished uploading.\n"))
		self.parent.SetStatusText(_("Finished uploading."))
		self.fileGauge.SetValue(0)
		self.projGauge.SetValue(0)
		self.btnCancel.SetLabel(_("Close"))
		self.btnOK.Enable(True)
		
	def OnUploadCanceled(self, event):
		self.mytimer.Stop()
		self.txtProgress.SetLabel(_("Disconnected. Upload cancelled by user.\n"))
		self.btnCancel.SetLabel(_("Close"))
		self.btnOK.Enable(True)
		self.stopupload = False
		if self.closewindow == True:
			self.EndModal(wxID_OK)
		
	def OnUpdateDialog(self, event):
		self.mytimer.Stop()
		self.mytimer.Start(60000)
		self.txtProgress.SetLabel("Current File: " + event.filename)
		self.projGauge.SetValue(event.projpercent)
		self.fileGauge.SetValue(event.filepercent)

	def OnClose(self, event):
		if not self.mythread == None:
			self.stopupload = True
			self.closewindow = True
		else:
			self.EndModal(wxID_OK)

	def btnCancelClicked(self, event):
		if self.btnCancel.GetLabel() == _("Cancel"):
			self.stopupload = True

		else:				
			self.parent.pub.settings["FTPHost"] = self.txtFTPSite.GetValue()
			self.parent.pub.settings["FTPUser"] = self.txtUsername.GetValue()
			self.parent.pub.settings["FTPDirectory"] = self.txtDirectory.GetValue()
			#self.parent.pub.settings["FTPPassword"] = `munge(self.txtPassword.GetValue(), "foobar")`
			self.stopupload = True
			#self.parent.pub.settings["FTPPassive"] = int(self.chkPassive.GetValue())
			self.EndModal(wxID_CANCEL)

	def OnHang(self, event):
		wxMessageBox(_("The FTP server has failed to respond for over 1 minute, and so the connection is being disconnected. Please click Upload to try again."))
		self.btnCancelClicked(event)

	def btnOKClicked(self, event):
		import threading
		self.FTPSite = self.txtFTPSite.GetValue()
		self.Username = self.txtUsername.GetValue()
		self.Password = self.txtPassword.GetValue()
		self.Directory = self.txtDirectory.GetValue()
		if self.chkPassive.IsChecked():
			self.usePasv = True
		else:
			self.usePasv = False

		try:
			self.StartFTP()
		except:
			self.handleError()

		self.btnOK.Enable(False)
		self.btnCancel.SetLabel(_("Cancel"))
		if self.makefilelist:
			self.GenerateFileList(self.parent.CurrentDir)
			self.makefilelist = False
		self.mythread = threading.Thread(None, self.UploadFiles)
		try:
			self.mytimer.Start(60000)
			self.mythread.run()
		except:
			self.handleError()
		return

	def handleError(self):
		import traceback
		info = sys.exc_info()
		lines = traceback.format_exception(info[0], info[1], info[2])
		name = str(info[0])
		print name
		message = ""
		if name.find("IOError") != -1:
			message = utils.getStdErrorMessage(name, {"filename":info[1].filename})
		elif name.find("ftplib") != -1:
			message	= self.getFtpErrorMessage(info[1])
		else:
			message = str(info[1])
		
		wxMessageBox(`message`)
		self.parent.log.write(`message`)
		self.host.close()
		self.OnUploadCanceled(None)