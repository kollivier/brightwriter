import string, sys, os
from wxPython.wx import *
from wxPython.lib import newevent
import utils

try:
	import win32api
except:
	pass

(UpdateOutputEvent, EVT_OUTPUT_UPDATE) = newevent.NewEvent()
(IndexingCanceledEvent, EVT_INDEXING_CANCELED) = newevent.NewEvent()
(IndexingFinishedEvent, EVT_INDEXING_FINISHED) = newevent.NewEvent()

#--------------------------- Export to CD Progress Dialog Class --------------------------------------
class UpdateIndexDialog(wxDialog):
	def __init__(self, parent, usegsdl=False):
		"""
		Dialog for creating a full-text index of an EClass.

		"""
		wxDialog.__init__ (self, parent, -1, _("Indexing EClass"), wxPoint(100,100),wxSize(400,230), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		lblstart = 10
		txtstart = 80
		self.gsdl = ""
		self.usegsdl = usegsdl
		self.eclassdir = ""
		self.mythread = None
		self.stopthread = False
		self.exportfinished = False
		self.dialogtext = ""
		self.olddir = ""
		self.status = wxStaticText(self, -1, _("Updating full-text index..."), wxPoint(lblstart, 12))
		self.txtProgress = wxTextCtrl(self, -1, "", wxPoint(lblstart, 40), wxSize(360, height*6), wxTE_MULTILINE|wxTE_READONLY)

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.status, 0, wxALL, 4)
		self.mysizer.Add(self.txtProgress, 1, wxEXPAND | wxALL, 4)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()
 
		EVT_CLOSE(self, self.OnClose)
		EVT_OUTPUT_UPDATE(self, self.OnOutputUpdate)
		EVT_INDEXING_FINISHED(self, self.OnIndexingFinished)
		EVT_INDEXING_CANCELED(self, self.OnIndexingCanceled)
		self.Show(True)

	def OnOutputUpdate(self, event):
		self.txtProgress.WriteText("\n" + event.text)
		
	def OnIndexingCanceled(self, event):
		self.EndModal(wxID_CANCEL)
		
	def OnIndexingFinished(self, event):
		self.exportfinished = True
		if wxPlatform != '__WXMSW__' and os.path.exists(self.olddir):
			os.chdir(self.olddir)
		self.EndModal(wxID_OK)
		
	def OnClose(self, event):
		if not self.mythread == None:	
			#return
			self.stopthread = True
			self.txtProgress.WriteText(_("Sending cancel command to process. Please wait...")+"\n")
		else:
			self.EndModal(wxID_OK)	
	
	def UpdateIndex(self, gsdl, eclassdir):
		import threading
		captureoutput = True
		if self.parent.pub.settings["SearchProgram"] == "Greenstone":
			self.gsdl = self.parent.settings["GSDL"]
			self.eclassdir = os.path.join(self.gsdl, "collect", self.parent.pub.pubid) 
			self.processfinished = False
	
			if not os.path.exists(eclassdir):	
				self.call = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "mkcol.bat")) + " " + self.parent.pub.pubid + " " + win32api.GetShortPathName(self.gsdl)
				if captureoutput:
					self.mythread = threading.Thread(None, self.cmdline)
					self.mythread.start()
	
				else:
					os.system(call)
	
			if os.path.exists(eclassdir):
				collecttext = ""
				configfile = os.path.join(self.parent.AppDir, "greenstone", "collect.cfg")
				try:
					collectcfg = utils.openFile(configfile, "r")
					collecttext = collectcfg.read()
					collectcfg.close()
				except:
					message = _("There was an error reading the file '%(filename)s'. Please ensure that the file exists and that you have read permissions.") % {"filename": configfile}
					self.log.write(message)
					self.txtProgress.WriteText(message)

				outfile = os.path.join(eclassdir, "etc", "collect.cfg")
				try:
					collecttext = string.replace(collecttext, "**[title]**", self.parent.pub.name)
					collectout = utils.openFile(outfile, "w")
					collectout.write(collecttext)
					collectout.close()
				except:
					message = _("There was an error writing the file '%(collectfile)s'. Please ensure that the file exists and that you have write permissions.") % {"collectfile": outfile}
					self.log.write(message)
					self.txtProgress.WriteText(message)
	
				files.CopyFiles(os.path.join(self.parent.ProjectDir, "pub"), os.path.join(eclassdir, "import"), 1)
					#...and build the collection
				self.call = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "buildcol.bat")) + " " + self.parent.pub.pubid + " " + win32api.GetShortPathName(gsdl) 
				if captureoutput:	 
					self.mythread = threading.Thread(None, self.cmdline)
					self.mythread.start()
				else:
					doscall = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "buildcol.bat"))
					os.spawnv(os.P_WAIT, doscall, [doscall, self.parent.pub.pubid, win32api.GetShortPathName(gsdl)])
					self.txtProgress.WriteText(_("Copying eClass publication files to Greenstone..."))
					exportdir = os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid)
					if not os.path.exists(os.path.join(exportdir, "gsdl", "eclass")):
						os.mkdir(os.path.join(exportdir, "gsdl", "eclass"))
					files.CopyFiles(self.parent.ProjectDir, os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "eclass"), 1)
					files.CopyFile("home.dm", os.path.join(self.parent.AppDir, "greenstone"), os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "macros"))
					files.CopyFile("style.dm", os.path.join(self.parent.AppDir, "greenstone"), os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "macros"))
					self.status.SetLabel(_("""Finished exporting. You can find the exported 
collection at:""") + os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid))
		elif self.parent.pub.settings["SearchProgram"] == "Swish-E":
			olddir = ""
			swishedir = os.path.join(self.parent.ThirdPartyDir, "SWISH-E")
			swisheconf = os.path.join(self.parent.pub.directory, "swishe.conf")
			swisheindex = os.path.join(self.parent.pub.directory, "index.swish-e")
			swisheinclude = self.parent.pub.directory
			if wxPlatform == "__WXMSW__":
				#swishedir = win32api.GetShortPathName(os.path.join(swishedir, "swish.bat"))
				swisheconf = win32api.GetShortPathName(swisheconf)
				swisheindex = os.path.join(win32api.GetShortPathName(self.parent.pub.directory), "index.swish-e")
				#swisheinclude = win32api.GetShortPathName(self.parent.pub.directory)
				self.call = win32api.GetShortPathName(os.path.join(swishedir, "swish.bat")) + " " + win32api.GetShortPathName(self.parent.pub.directory) + " " + win32api.GetShortPathName(os.path.join(swishedir, "swish-e.exe"))
			else:
				swishedir = os.path.join(swishedir, "bin")
				self.olddir = os.getcwd()
				os.chdir(self.parent.pub.directory)
				self.call = os.path.join(swishedir, "swish-e") + " -c ./swishe.conf -f index.swish-e"				
			#self.call = swishedir + " -c \"" + swisheconf + "\" -f \"" + swisheindex + "\"" # -i \"" + swisheinclude + "\""
			#self.txtProgress.WriteText("Using swish-e!\n")
			self.txtProgress.WriteText(self.call + "\n")
			print self.call
			self.dialogtext = ""
			self.mythread = threading.Thread(None, self.cmdline)
			self.mythread.start()

			while self.mythread.isAlive():
				wxSleep(1)
			self.mythread = None
			if wxPlatform != '__WXMSW__' and os.path.exists(olddir):
				os.chdir(olddir)
			if self.stopthread == True:
				self.EndModal(wxID_OK)
			self.status.SetLabel(_("Finished exporting!"))
		elif self.parent.pub.settings["SearchProgram"] == "Lucene":
			engine = indexer.SearchEngine(self, os.path.join(self.parent.ProjectDir, "index.lucene"), os.path.join(self.parent.ProjectDir, "File"))
			
			self.mythread = threading.Thread(None, engine.IndexFiles, "Indexer", [self.parent.pub.nodes[0]])
			self.mythread.run()
			
		self.exportfinished = True

	def cmdline(self):
		import time
		if wxPlatform == "__WXMSW__":
			myin, myout = win32pipe.popen4(self.call)
		else:
			myin, myout = os.popen4(self.call)
		while 1:
			line = myout.readline()
			if not line:
				break
			elif self.stopthread == True:
				evt = IndexingCanceledEvent()
				wxPostEvent(self, evt)
				#self.txtProgress.WriteText(_("Cancelling process...")+"\n")
				break
			else:
				evt = UpdateOutputEvent(text = line)
				wxPostEvent(self, evt)
			time.sleep(0.01)
			
		evt = IndexingFinishedEvent()
		wxPostEvent(self, evt)
		myin.close()
		myout.close()

	def write(self, s):
		self.txtProgress.WriteText(s)

	def btnViewFolderClicked(self, event):
		if self.usegsdl:
			win32api.ShellExecute(0, "open",os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid), "", os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid), 1)
		else:
			win32api.ShellExecute(0, "open",self.parent.pub.directory, "", self.parent.pub.directory, 1)

	def btnTestCDClicked(self, event):
		win32api.ShellExecute(0, "open", "server.exe", "", os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl"), 1)

	def btnCloseWindowClicked(self, event):
		self.Destroy()