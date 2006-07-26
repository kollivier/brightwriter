import string, sys, os
import wx
import wxaddons.sized_controls as sc
import wxaddons.persistence
import autolist

import ftplib
import traceback
import settings
import utils
import errors
import encrypt

class FTPEventCallback:
    def uploadCanceled(self):
        print "Upload canceled."
        
    def uploadFileStarted(self, thefile):
        print "Starting upload for %s" % thefile
        
    def uploadFileProgressEvent(self, thefile, percent):
        print "Uploading %s... %s%% complete" % (thefile, str(percent))
        
    def uploadFileFailed(self, thefile, error):
        print "Upload for %s failed. Error message is: \n" % (thefile, error)
    
    def uploadFileCompleted(self, thefile):
        print "Successfully uploaded %s" % thefile
        
    def uploadFinished(self):
        print "Upload is complete."
        
    def dirCreated(self, dir):
        print "Created directory: %s" % dir
    
class FTPDialogEventCallback:
    def __init__(self, parent):
        self.parent = parent
    
    def uploadCanceled(self):
        wx.CallAfter(self.parent.OnUploadCanceled)
        
    def uploadFileStarted(self, thefile):
        wx.CallAfter(self.parent.OnNewFile, thefile)
        
    def uploadFileFailed(self, thefile, error):
        wx.CallAfter(self.parent.OnUploadFailed, thefile, error)
        
    def uploadFileProgressEvent(self, thefile, percent):
        wx.CallAfter(self.parent.OnFileProgress, thefile, percent)

    def uploadFileCompleted(self, thefile):
        wx.CallAfter(self.parent.OnFileUploaded, thefile)
        
    def uploadFinished(self):
        wx.CallAfter(self.parent.OnUploadFinished)
        
    def dirCreated(self, dir):
        wx.CallAfter(self.parent.OnDirCreated, dir)
        
class ftpService:
    def __init__(self, host, user="", passwd="", hostdir="", passive=False):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.hostdir = self.normalizeHostDir(hostdir)
        self.passive = passive
        self.stopNow = False
        self.connection = None
        
    def normalizeHostDir(self, hostdir):
        """
        Make sure the FTP host directory is an absolute path.
        """
        normdir = hostdir
        if len(normdir) > 0:
            if not normdir[0] == "/":
                normdir = "/" + normdir 
            if not len(normdir) == 1 and not normdir[-1] == "/":
                normdir = normdir + "/"
        
        return normdir
    
    def connect(self):
        self.connection = ftplib.FTP(self.host, self.user, self.passwd)
        self.connection.set_pasv(self.passive)
        self.connection.sock.setblocking(1)
        self.connection.sock.settimeout(30)
        
    def cwd(self, dir):
        if self.connection:
            self.connection.cwd(dir)
        
    def mkd(self, dir):
        if self.connection:
            self.connection.mkd(dir)
            
    def stop(self):
        """
        Don't close the connection, but stop whatever we were doing.
        """
        self.stopNow = True

    def close(self):
        self.connection.quit()
        self.connection = None
        
    def uploadFile(self, sourcename, destname, callback=None):
        success = False
        myfile = utils.openFile(sourcename, "rb")
        bytes = os.path.getsize(sourcename)

        self.connection.voidcmd('TYPE I')
        mysocket = self.connection.transfercmd('STOR ' + destname)
        self.filepercent = 0

        if callback:
            callback.uploadFileStarted(destname)
            # TODO: What is this needed for?
            #callback.uploadFileProgressEvent(destname, self.filepercent)

        onepercent = bytes/100
        if onepercent == 0:
            onepercent = 1
        if mysocket:
            mysocket.setblocking(1)
            mysocket.settimeout(30)

            bytesuploaded = 0
            while 1:
                if self.stopNow:
                    break 
                    
                block = myfile.read(4096)
                if not block:
                    break

                resp = mysocket.sendall(block)
                bytesuploaded = bytesuploaded + len(block)
                if callback:
                    percent = int((float(bytesuploaded)/float(bytes))*100.0)
                    callback.uploadFileProgressEvent(destname, percent) 

            mysocket.close()
            mysocket = None

        if bytesuploaded >= bytes:
            success = True

        myfile.close()
        self.connection.voidresp()
        
        return success    
        

#--------------------------- FTP Upload Dialog Class --------------------------------------
class FTPUpload:
	def __init__(self, parent):
		self.filelist = []
		self.dirlist = []
		self.parent = parent
		self.isDialog = False
		isPassive = False
		if settings.ProjectSettings["FTPPassive"] == "yes":
			isPassive = True
			
		self.ftpService = ftpService( settings.ProjectSettings["FTPHost"], 
		                              settings.ProjectSettings["FTPUser"],
		                              encrypt.decrypt(settings.ProjectSettings["FTPPassword"]),
		                              settings.ProjectSettings["FTPDirectory"],
		                              isPassive 
		                            )
		self.stopupload = False
		self.useSearch = 0
		self.projpercent = 0
		self.filepercent = 0
		self.callback = FTPEventCallback()

		if settings.ProjectSettings["SearchEnabled"] != "":
			self.useSearch = int(settings.ProjectSettings["SearchEnabled"])

	def StartFTP(self):
		if self.ftpService.host == "":
			wx.MessageBox(_("The FTP server for this project has not been specified. Please enter a FTP server by going to File->Project Settings and selecting the FTP tab."), _("Error: No FTP Server Specified"), wx.ICON_ERROR)
			return False
		if self.ftpService.passwd == "" and self.ftpService.user != "":
			dialog = wx.TextEntryDialog(self.parent, _("Please enter a password to upload to FTP."), _("Enter Password"), "", wx.TE_PASSWORD | wx.OK | wx.CANCEL)
			if dialog.ShowModal() == wx.ID_OK:
				self.ftpService.passwd = dialog.GetValue()
			else:
				return False

		self.ftpService.connect()
		# TODO: Fix this, it's a major hack while we work out the  
		return True

	def GetUploadDirName(self, indir):
		#first, strip out any hardcoded path reference
		parentdir = settings.ProjectDir
		#print "Parentdir: " + parentdir

		mydir = string.replace(indir, parentdir, "")
		if sys.platform.startswith("win"):
			mydir = string.replace(mydir, "\\", "/")

		#now construct the subdir as relative to the start URL
		#for the EClass
		fulldir = self.ftpService.hostdir + mydir
		if not fulldir[0] == "/":
			fulldir = "/" + fulldir
		#print "Fulldir: " + fulldir
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
				finalname = string.replace(myitem, settings.ProjectDir, "")
				if wx.Platform == "__WXMSW__":
					finalname = string.replace(finalname, "\\", "/")
				#finalname = string.replace(finalname, os.pathsep, "/")
				if not self.useSearch and string.find(myitem, "cgi-bin") == -1:
					# TODO: test for extensions instead of this
					if string.find(item, ".dll") == -1 and string.find(item, ".pyd") == -1 and string.find(item, ".exe") == -1:
						self.filelist.append(finalname)
				else:
					self.filelist.append(finalname)
			elif os.path.isdir(myitem):
				self.GenerateFileList(myitem)

	def CreateDirectories(self):
		if not self.StartFTP():
			return
		ftpdir = self.ftpService.hostdir
		self.cwd(ftpdir)

		for item in self.dirlist:
			self.cwd(item) #create the folders if they don't already exist

	def CreateDestFilename(self, sourcefile):
		destdir = self.ftpService.hostdir
		inputfile = sourcefile.replace(settings.ProjectDir, "")

		adir, aname = os.path.split(inputfile)
		if adir != "":
			destdir = destdir + string.replace(adir, "\\", "/")
			if not destdir[-1] == "/":
				destdir = destdir + "/"
		
		outputfile = destdir + aname
		return outputfile

	def UploadFiles(self):
		import time
		if self.stopupload:
			self.ftpService.close()
			return
			
		#self.dirlist = []
		self.CreateDirectories()

		for item in self.filelist[:]:
			try:
				if self.stopupload:
					self.ftpService.close()
					self.callback.uploadCanceled()
					return

				sourcename = settings.ProjectDir + os.sep + item
				destname = self.CreateDestFilename(item)
				try:
					success = self.ftpService.uploadFile(   sourcename, 
				                                        destname, self.callback)
				except:
					self.ftpService.close()
					self.callback.uploadFileFailed(destname, _("There was a connection error. Please try uploading again."))
					return

				if success:
					myindex = self.filelist.index(item)
					self.filelist.remove(item)
					self.callback.uploadFileCompleted(destname)

			except ftplib.all_errors, e:
				raise

		self.ftpService.close()
		self.callback.uploadFinished()

	def getFtpErrorMessage(self, e):
		""" Given an ftplib error object, generate some common error messages. """
		code = ""
		try:
			code = e.args[0][:3]
		except:
			code = repr(e)[:3]

		if code == "550":
			return _("Attempt to create a file or directory on the server failed. Please check your file permissions. The error reported was: \n\n") + str(e.args[0]) 
		elif code == "530":
			return _("EClass was unable to connect to the specified FTP server. Please check to ensure your server name, username and password are correct. The error message returned was:") + "\n\n" + str(e)
		elif code == "425":
			return _("Cannot open a data connection. Try changing the \"Use Passive FTP\" setting and uploading again.")
		elif code == "426":
			return _("Connection closed by server. Click Upload again to resume upload.")
		elif code == "452":
			return _("Server is full. You will need to either delete files from the server or ask for more server space from your system administrator.")
		else: 
			return _("An unexpected error has occurred while uploading. Please click 'Upload' again to attempt to resume uploading. The error reported was: \n\n") + repr(e) 
			#self.parent.logfile.write(str(e))

	def cwd(self, item):
		myitem = item
		try:
			if myitem[-1] == "/":
				myitem = myitem + "/"
			self.ftpService.cwd(myitem)
		except:
			try:
				self.ftpService.mkd(myitem)
				self.callback.dirCreated(myitem)
				self.ftpService.cwd(myitem)
			except ftplib.all_errors, e:
				raise
				

class FTPUploadDialog(sc.SizedDialog, FTPUpload):
	def __init__(self, parent):
		FTPUpload.__init__(self, parent)
		self.isDialog = True
		sc.SizedDialog.__init__(self, parent, -1, _("Publish to web site"), 
		                      wx.Point(100,100),wx.Size(400,440), 
		                      wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		pane = self.GetContentsPane()
		
		self.parent = parent
		self.makefilelist = True
		self.mythread = None
		self.closewindow = False
		self.filelist = []
		self.folderlist = []
		self.currentFileNo = 0
		self.filesUploaded = 0
		self.itemCount = 0
		self.projpercent = 0
		self.filepercent = 0
		self.callback = FTPDialogEventCallback(self)

		ftpPane = sc.SizedPanel(pane, -1)
		ftpPane.SetSizerType("form")
		ftpPane.SetSizerProp("expand", True)
		
		self.txtFTPSite = self.AddFormField(ftpPane, _("FTP Site"), settings.ProjectSettings["FTPHost"])
		self.txtUsername = self.AddFormField(ftpPane, _("Username"), settings.ProjectSettings["FTPUser"])
		# TODO: Reinstate password once we've figured out how to get/store password
		self.txtPassword = self.AddFormField(ftpPane, _("Password"), encrypt.decrypt(settings.ProjectSettings["FTPPassword"]), wx.TE_PASSWORD)
		self.txtDirectory = self.AddFormField(ftpPane, _("Directory"), settings.ProjectSettings["FTPDirectory"]) 
		
		self.chkPassive = wx.CheckBox(pane, -1, _("Use Passive FTP"))
		
		self.fileList = autolist.AutoSizeListCtrl(pane, -1, style=wx.LC_REPORT)
		self.fileList.SetSizerProps({"expand":True, "proportion":1})
		self.fileList.InsertColumn(0, _("File"), width=200)
		self.fileList.InsertColumn(1, _("Status"), width=200)

		self.txtTotalProg = wx.StaticText(pane, -1, "Total Progress:")
		self.projGauge = wx.Gauge(pane, -1, 1, style=wx.GA_PROGRESSBAR)
		self.projGauge.SetRange(100)
		self.projGauge.SetSizerProp("expand", True)
		#self.lstFiles = wxListBox(self, -1, style=wxLB_SINGLE)
		self.stopupload = False

		self.btnOK = wx.Button(pane,-1,_("Upload"))
		self.btnOK.SetSizerProps({"halign":"right", "valign":"center"})

		#self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		#EVT_TIMER(self, self.mytimer.GetId(), self.OnHang)
		wx.EVT_CLOSE(self, self.OnClose)
		
	def AddFormField(self, parent, label, value, textstyle=0):
		wx.StaticText(parent, -1, label)
		textbox = wx.TextCtrl(parent, -1, value, style=textstyle)
		textbox.SetSizerProp("expand", True)
		return textbox
		
	def OnDirCreated(self, dirname):
		self.txtTotalProg.SetLabel(_("Created Directory: ") + dirname)

	def OnUploadFinished(self):
		self.parent.SetStatusText(_("Finished uploading."))
		self.projGauge.SetValue(0)
		self.btnOK.SetLabel(_("Upload"))

	def OnFileUploaded(self, filename):
		self.fileList.DeleteItem(0)
		self.filesUploaded += 1
		filePercentUploaded = int((float(self.filesUploaded)/float(self.itemCount))* 100.0)
		print "FilesUploaded: %s, TotalFiles: %s" % (self.filesUploaded, self.itemCount)
		print "FilePercentUploaded is: " + `filePercentUploaded`
		self.projGauge.SetValue(filePercentUploaded)

	def OnNewFile(self, filename):
		self.fileList.SetStringItem(0, 1, _("Uploading..."))
		
	def OnUploadCanceled(self):
		self.btnOK.SetLabel(_("Upload"))
		self.stopupload = False
		if self.closewindow == True:
			self.EndModal(wxID_OK)
		
	def OnFileProgress(self, filename, percent):
		self.txtTotalProg.SetLabel(_("Uploading files..."))
		self.fileList.SetStringItem(0, 1, _("%(percent)s%% uploaded...") % {"percent":percent})
		
	def OnUploadFailed(self, filename, error):
		wx.MessageBox(error)
		self.makefilelist = False
		self.btnOK.SetLabel(_("Upload"))

	def OnClose(self, event):
		if not self.mythread == None and self.mythread.isAlive():
			self.ftpService.stop()
			self.stopupload = True
			self.closewindow = True
			self.txtTotalProgress.SetValue(_("Shutting down FTP connection, please wait."))
			while self.mythread.isAlive():
				pass
				
			settings.ProjectSettings["FTPHost"] = self.txtFTPSite.GetValue()
			settings.ProjectSettings["FTPUser"] = self.txtUsername.GetValue()
			settings.ProjectSettings["FTPPassword"] = encrypt.encrypt(self.txtPassword.GetValue())
			settings.ProjectSettings["FTPDirectory"] = self.txtDirectory.GetValue()
			settings.ProjectSettings["FTPPassive"] = int(self.chkPassive.GetValue())
			#self.parent.pub.settings.SaveAsXML()
		self.EndModal(wx.ID_OK)

	def OnHang(self, event):
		wx.MessageBox(_("The FTP server has failed to respond for over 1 minute, and so the connection is being disconnected. Please click Upload to try again."))
		self.btnCancelClicked(event)

	def LoadFileList(self):
		self.itemCount = 0
		for item in self.filelist:
			self.fileList.InsertStringItem(self.itemCount, item)
			self.fileList.SetStringItem(self.itemCount, 1, _("Queued"))
			self.itemCount += 1

	def btnOKClicked(self, event):
		if self.btnOK.GetLabel() == _("Stop"):
			self.stopupload = True
			self.closewindow = False
			if self.ftpService:
				self.ftpService.stop()
			return

		self.btnOK.SetLabel(_("Stop"))
		import threading
		self.ftpService.host = self.txtFTPSite.GetValue()
		self.ftpService.user = self.txtUsername.GetValue()
		self.ftpService.passwd = self.txtPassword.GetValue()
		self.ftpService.hostdir = self.txtDirectory.GetValue()
		if self.chkPassive.IsChecked():
			self.ftpService.isPassive = True
		else:
			self.ftpService.isPassive = False

		try:
			self.StartFTP()
		except:
			self.handleError()

		#self.btnOK.Enable(False)
		#self.btnCancel.SetLabel(_("Cancel"))
		if self.makefilelist:
			self.GenerateFileList(settings.ProjectDir)
			self.makefilelist = False
		self.LoadFileList()
		self.txtTotalProg.SetLabel(_("Total Progress: "))
		self.mythread = threading.Thread(None, self.UploadFiles)
		try:
			self.mythread.start()
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
		elif name.find("socket") != -1:
			errortext = str(info[1])
			print "Type is: " + `type(info[1])`
			if len(info[1]) == 2:
				errortext = info[1][1]
			message = _("Socket Error: ") + errortext 
		else:
			message = str(info[1])
		
		wx.MessageBox(`message`)
		self.parent.log.write(`message`)
		self.ftpService.close()
		self.OnUploadCanceled(None)