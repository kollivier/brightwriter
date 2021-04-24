from __future__ import print_function
from builtins import object
import sys, os
import wx
import wx.lib.sized_controls as sc
import persistence
import settings
import threading

import utils

try:
	import win32api
except:
	pass

class IndexingCallback(object):
	def indexingFinished(self):
		print("Indexing complete.")
	
	def indexingCanceled(self):
		print("Indexing cancelled.")
		
	def update(self, text):
		print(text)
		
class IndexingGUICallback(object):
	def __init__(self, parent):
		self.parent = parent
		
	def indexingFinished(self):
		wx.CallAfter(parent.OnIndexingFinished)

	def indexingCancelled(self):
		wx.CallAfter(parent.OnIndexingCancelled)
		
	def update(self, text):
		wx.CallAfter(parent.OnOutputUpdate, text)

#--------------------------- Export to CD Progress Dialog Class --------------------------------------
class UpdateIndexDialog(sc.SizedDialog):
	def __init__(self, parent, usegsdl=False):
		"""
		Dialog for creating a full-text index of an EClass.

		"""
		sc.SizedDialog.__init__ (self, parent, -1, _("Indexing EClass"), wx.Point(100,100),
								  wx.Size(400,230), wx.DEFAULT_DIALOG_STYLE)

		pane = self.GetContentsPane()
		
		self.callback = IndexingGUICallback(self)
		self.parent = parent
		self.running_thread = None
		self.stopthread = False
		self.olddir = ""
		
		self.status = wx.StaticText(pane, -1, _("Updating full-text index..."))
		self.txtProgress = wx.TextCtrl(pane, -1, "", wx.TE_MULTILINE|wx.TE_READONLY)

		self.Fit()
 
		wx.EVT_CLOSE(self, self.OnClose)
		self.Show(True)

	def OnOutputUpdate(self, event):
		self.txtProgress.WriteText("\n" + event.text)
		
	def OnIndexingCanceled(self, event):
		self.EndModal(wx.ID_CANCEL)
		
	def OnIndexingFinished(self, event):
		if wx.Platform != '__WXMSW__' and os.path.exists(self.olddir):
			os.chdir(self.olddir)
		self.EndModal(wx.ID_OK)
		
	def OnClose(self, event):
		if not self.running_thread == None:	
			#return
			self.stopthread = True
			self.txtProgress.WriteText(_("Sending cancel command to process. Please wait...")+"\n")
		else:
			self.EndModal(wx.ID_OK) 

	def UpdateIndex(self, eclassdir):
		gsdl = settings.AppSettings["GSDL"]
		eclassdir = os.path.join(gsdl, "collect", self.parent.pub.pubid) 
		self.processfinished = False
		gsdl_supportdir = os.path.join(settings.AppDir, "greenstone")

		if not os.path.exists(eclassdir):	
			self.call = win32api.GetShortPathName(os.path.join(gsdlsupport_dir, "mkcol.bat")) + " " + \
								self.parent.pub.pubid + " " + win32api.GetShortPathName(gsdl)
			self.running_thread = threading.Thread(None, self.cmdline)
			self.running_thread.start()

		if os.path.exists(eclassdir):
			collecttext = ""
			configfile = os.path.join(gsdl_supportdir, "collect.cfg")
			try:
				collectcfg = utils.openFile(configfile, "r")
				collecttext = collectcfg.read()
				collectcfg.close()
			except:
				message = _("There was an error reading the file '%(filename)s'. Please ensure that the file exists and that you have read permissions.") % {"filename": configfile}
				self.log.error(message)
				wx.MessageBox(message)
				return

			outfile = os.path.join(eclassdir, "etc", "collect.cfg")
			try:
				collecttext = collecttext.replace("**[title]**", self.parent.pub.name)
				collectout = utils.openFile(outfile, "w")
				collectout.write(collecttext)
				collectout.close()
			except:
				message = _("There was an error writing the file '%(collectfile)s'. Please ensure that the file exists and that you have write permissions.") % {"collectfile": outfile}
				self.log.error(message)
				wx.MessageBox(message)
				return

			files.CopyFiles(os.path.join(settings.ProjectDir, "pub"), os.path.join(eclassdir, "import"), 1)
			#...and build the collection
			self.call = win32api.GetShortPathName(os.path.join(gsdl_supportdir, "buildcol.bat")) + " " + \
												self.parent.pub.pubid + " " + win32api.GetShortPathName(gsdl) 
			 
			self.running_thread = threading.Thread(None, self.cmdline)
			self.running_thread.start()

			self.txtProgress.WriteText(_("Copying EClass publication files to Greenstone..."))
			exportdir = os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid)
			if not os.path.exists(os.path.join(exportdir, "gsdl", "eclass")):
				os.mkdir(os.path.join(exportdir, "gsdl", "eclass"))
			outputDir = os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl")
			files.CopyFiles(settings.ProjectDir, os.path.join(outputDir, "eclass"), 1)
			files.CopyFile("home.dm", gsdl_supportdir, os.path.join(outputDir, "macros"))
			files.CopyFile("style.dm", gsdl_supportdir, os.path.join(outputDir, "macros"))
			self.status.SetLabel(_("""Finished exporting. You can find the exported collection at:""") + exportdir)

	def cmdline(self):
		import time
		if sys.platform.startswith("win"):
			myin, myout = win32pipe.popen4(self.call)
		else:
			myin, myout = os.popen4(self.call)
		while 1:
			line = myout.readline()
			if not line:
				break
			elif self.stopthread == True:
				self.callback.indexingCancelled()
				break
			else:
				self.callback.update(line)
				
			time.sleep(0.01)
			
		self.callback.indexingFinished()
		myin.close()
		myout.close()

	def write(self, s):
		self.txtProgress.WriteText(s)

	def btnCloseWindowClicked(self, event):
		self.Destroy()
