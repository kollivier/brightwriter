import getopt,sys, os, string
import cStringIO, tempfile, glob, time
import settings
import process
import extprocess

hasOOo = False
hasMSOffice = False
wordApp = None
from wxPython.wx import *

try: 
	import win32api
	import win32com.client
	import pythoncom
	wordapp = win32com.client.dynamic.Dispatch("Word.Application")
	wordapp.Quit()
	del wordapp
	hasMSOffice = True
except:
	hasMSOffice = False

class DocConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"
		self.ThirdPartyDir = settings.ThirdPartyDir

	def ConvertFile(self, filename, outformat="html", mode="command_line"):
		try:
			global hasOOo
			#check for OOo first, we can only do this once EClass settings are loaded
			if settings.options["OpenOffice"] != "" and os.path.exists(settings.options["OpenOffice"]):
				hasOOo = True
			ext = string.lower(os.path.splitext(filename)[1][1:])
			#print "ext = " + ext
			converter = None
			if ext in ["doc", "rtf", "ppt", "xls", "txt"]:
				if hasMSOffice and mode == "ms_office":
					converter = WordDocConverter(self.parent)
				elif hasOOo and mode == "open_office":
					converter = OOoDocConverter(self.parent)
				else:
					#OpenOffice likes to crash when it can't read a doc. ;-/
					converter = CommandLineDocConverter(self.parent)
    
			elif ext == "pdf":
				converter = PDFConverter(self.parent)
    
			if converter: 
				converter.ThirdPartyDir = self.ThirdPartyDir
				return converter.ConvertFile(filename, outformat)
			else:
				return "", ""
		except:
			import traceback
			print traceback.print_exc()

class PDFConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"

	def ConvertFile(self, filename, outformat="html"):
		import tempfile
		handle, htmlfile = tempfile.mkstemp(".html")
		os.close(handle)
		thirdpartydir = settings.ThirdPartyDir
		pdfconvert = "pdftohtml"
		exe = os.path.join(settings.AppDir, "python.exe")
		if not os.path.exists(exe):
			exe = sys.executable
		#exe.replace("editor.exe", "python.exe")
		if os.name == "nt":
			pdfconvert = pdfconvert + ".exe"
			exe = win32api.GetShortPathName(exe)
			filename = win32api.GetShortPathName(filename)
			# don't alter htmlfile, tempfile uses the short path name
			# anyways and if we do this ourselves, HTML will become HTM
			# which will confuse pdftohtml.
			#htmlfile = win32api.GetShortPathName(htmlfile)

		path = os.path.join(thirdpartydir, pdfconvert)
		try:
			seconds = 0.0
			mycommand = [exe, os.path.join(settings.AppDir, "process.py"), 
						 path, "-noframes", filename, htmlfile]
			myproc = extprocess.ExtProcess(mycommand)
			
			while myproc.isAlive():
				if seconds > 120: #the process has probably hung
					print "Conversion process appears frozen. Stopping process."
					myproc.kill()
					return ("", "")
				wxSafeYield()
				time.sleep(0.1)
				seconds = seconds + 0.1
			print "File took %f seconds to convert." % (seconds)
			os.chdir(oldcwd)
		except:
			pass
		return htmlfile, "html"
			
class WordDocConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"
		self.outfilters = {"html": 8,
							"txt": 2,
							"unicodeTxt": 7}

	def ConvertFile(self, filename, outformat="html"):
		mydoc = None
		myapp = None
		formatNum = self.outfilters[outformat]
		try:
			pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
			fileext = string.lower(os.path.splitext(filename)[1])
			if fileext == ".doc":
				myapp = win32com.client.dynamic.Dispatch("Word.Application")
			if fileext == ".ppt":
				myapp = win32com.client.dynamic.Dispatch("Powerpoint.Application")
			elif fileext == ".xls":
				myapp = win32com.client.dynamic.Dispatch("Excel.Application")

			try:
				myapp.DisplayAlerts=False
				myapp.Visible=False
			except:
				pass #for some reason, setting Visible for PPT throws a 'can't set property' error

			outext = ".txt"
			if outformat == "html":
				outext = ".html"

			handle, htmlfile = tempfile.mkstemp(outext)
			os.close(handle)

			if os.path.exists(htmlfile):
				os.remove(htmlfile) #the converters will re-create it

			if fileext == ".doc":
				mydoc = myapp.Documents.Open(filename)
				#apprently this doesn't work... ARGH! mydoc.SaveEncoding(65001) #msoEncodingUTF8
			elif fileext == ".xls":
				mydoc = myapp.Workbooks.Open(filename)
				if outformat == "unicodeTxt":
					formatNum = 42
			elif fileext == ".ppt":
				mydoc = myapp.Presentations.Open(filename)

			if mydoc:
				mydoc.SaveAs(htmlfile, FileFormat=formatNum)
				mydoc.Close()
				del mydoc

			if myapp:
				myapp.Quit()
				del myapp

			pythoncom.CoUninitialize()

			return htmlfile, outformat
		except:
			if mydoc:
				try:
					mydoc.Close()
				except:
					pass
				del mydoc
			if myapp:
				try:
					myapp.Quit()
				except:
					pass
				del myapp

			pythoncom.CoUninitialize()

			import traceback
			print traceback.print_exc()
			return "", ""

class CommandLineDocConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"

	def ConvertFile(self, filename, outformat="html"):
		#we ignore outformat for command line tools and just use HTML
		import tempfile
		handle, htmlfile = tempfile.mkstemp()
		os.close(handle)
		thirdpartydir = self.ThirdPartyDir
		ext = string.lower(os.path.splitext(filename)[1])
		path = ""
		command = ""
		outformat = "html"
		exe = os.path.join(settings.AppDir, "python.exe")
		if not os.path.exists(exe):
			exe = sys.executable
		#exe.replace("editor.exe", "python.exe")
		if os.name == "nt":
			thirdpartydir = win32api.GetShortPathName(thirdpartydir)
			filename = win32api.GetShortPathName(filename)
			exe = win32api.GetShortPathName(exe)

		if ext == ".doc":
			path = os.path.join(thirdpartydir, "wv", "bin")
			command = "wvWare"
			args= "--config " + os.path.join("..", "share", "wv", "wvHtml.xml") + " " + filename
			#outformat = "txt"
		elif ext == ".rtf":
			path = os.path.join(thirdpartydir, "unrtf", "bin")
			command = "unrtf" 
			args = filename
		elif ext == ".xls":
			path = os.path.join(thirdpartydir, "xlHtml")
			command = "xlhtml" 
			# -te is important, otherwise if a person has 30,000 blank
			# cells they'll end up in the converted document, making a
			# 30MB HTML page!
			args = "-te " + filename
		elif ext == ".ppt":
			path = os.path.join(thirdpartydir, "xlHtml")
			command = "ppthtml" 
			args = filename
		else:
			print "Cannot convert file because of unknown extension: " + filename

		try:
			oldcwd = os.getcwd()
			os.chdir(path)
			#Let's check for hung programs
			seconds = 0.0
			mycommand = [exe, os.path.join(settings.AppDir, "process.py"), 
						command, args, ">", win32api.GetShortPathName(htmlfile)]
			myproc = extprocess.ExtProcess(mycommand)
			
			while myproc.isAlive():
				if seconds > 120: #the process has probably hung
					print "Conversion process appears frozen. Stopping process."
					myproc.kill()
					return ("", "")
				wxSafeYield()
				time.sleep(0.1)
				seconds = seconds + 0.1
			print "File took %f seconds to convert." % (seconds)
			#some utilities assume their own path for extracted images
			self._CleanupTempFiles(path)
			os.chdir(oldcwd)
		except:
			import traceback
			if traceback.print_exc() != None:
				print traceback.print_exc()
			print "Unable to convert document: " + filename #if we can't convert, oh well ;-)

		return htmlfile, outformat

	def _CleanupTempFiles(self, path):
		for ext in ["png", "jpg", "jpeg", "wmf", "gif", "$$$", "emf"]:
			for afile in glob.glob(os.path.join(path, "*." + ext)):
				os.remove(os.path.join(path, afile))
		
if hasOOo:
    class OOoDocConverter:
    	def __init__(self, parent):
    		self.parent = parent
    		self.infile = ""
    		self.outformat = "html"
    		self.outfilters = {"html": "HTML (StarWriter)",
    							"txt": "Text (Encoded)",
    							"pdf": "writer_pdf_Export"}
    		self.infilters = {"doc":"MS Word 97",
    						"html": "HTML (StarWriter)", 
    						"rtf":"Rich Text Format",
    						"txt":"Text"}
    		self.url = "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
    		
    	def ConvertFile(self, filename, outformat="html"):
			oodir = settings.options["OpenOffice"]
			if oodir != "":
				oldcwd = os.getcwd()
				os.chdir(settings.AppDir)
				import win32api
				#get the output and send it to a file
				command = "ooconvert.bat \"" + win32api.GetShortPathName(oodir) + "\" \"" + win32api.GetShortPathName(filename) + "\""
				import win32pipe
				myin, mystream = win32pipe.popen4(command)
				filetext = mystream.read() 				
				mystream.close()
				handle, htmlfile = tempfile.mkstemp()
				os.close(handle)
				myfile = open(htmlfile, "wb")
				myfile.write(filetext)
				myfile.close()
				os.chdir(oldcwd)
				return htmlfile, "html"

			return ""
		