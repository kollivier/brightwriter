import getopt,sys, os, string
import cStringIO, tempfile, glob, time
import settings
import subprocess
import utils

hasOOo = False
hasMSOffice = False
wordApp = None

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
	
docFormats = ["doc", "rtf", "ppt", "xls", "txt"]

class DocConverter:
	def __init__(self):
		self.infile = ""
		self.outformat = "html"

	def ConvertFile(self, filename, outformat="html", mode="command_line"):
		try:
			global hasOOo
			#check for OOo first, we can only do this once EClass settings are loaded
			if "OpenOffice" in settings.AppSettings.keys() and os.path.exists(settings.AppSettings["OpenOffice"]):
				hasOOo = True
			ext = string.lower(os.path.splitext(filename)[1][1:])
			#print "ext = " + ext
			converter = None
			if ext in docFormats:
				if hasMSOffice and mode == "ms_office":
					converter = WordDocConverter()
				elif hasOOo and mode == "open_office":
					converter = OOoDocConverter()
				else:
					#OpenOffice likes to crash when it can't read a doc. ;-/
					converter = CommandLineDocConverter()
    
			elif ext == "pdf":
				converter = PDFConverter()
    
			if converter: 
				return converter.ConvertFile(filename, outformat)
			else:
				return "", ""
		except:
			import traceback
			print traceback.print_exc()
			return "", ""

class PDFConverter:
	def __init__(self):
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
				time.sleep(0.1)
				seconds = seconds + 0.1
			print "File took %f seconds to convert." % (seconds)
			os.chdir(oldcwd)
		except:
			pass
		return htmlfile, "html"
			
class WordDocConverter:
	def __init__(self):
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
	def __init__(self):
		self.infile = ""
		self.outformat = "html"

	def ConvertFile(self, filename, outformat="html"):
		#we ignore outformat for command line tools and just use HTML
		import tempfile
		handle, htmlfile = tempfile.mkstemp()
		os.close(handle)
		thirdpartydir = settings.ThirdPartyDir
		ext = string.lower(os.path.splitext(filename)[1])
		path = ""
		command = ""
		html = ""
		outformat = "html"

		if os.name == "nt":
			thirdpartydir = win32api.GetShortPathName(thirdpartydir)
			filename = win32api.GetShortPathName(filename)
			exe = win32api.GetShortPathName(exe)
			
		#filename = utils.escapeFilename(filename)

		if ext == ".doc":
			path = os.path.join(thirdpartydir, "wv")
			command = "wvWare"
			#args = ["--config " + os.path.join("..", "share", "wv", "wvHtml.xml")]
			args = [filename]
			#outformat = "txt"
		elif ext == ".rtf":
			path = os.path.join(thirdpartydir, "unrtf")
			command = "unrtf" 
			args = [filename]
		elif ext == ".xls":
			path = os.path.join(thirdpartydir, "xlhtml")
			command = "xlhtml" 
			# -te is important, otherwise if a person has 30,000 blank
			# cells they'll end up in the converted document, making a
			# 30MB HTML page!
			args = ["-te", filename]
		elif ext == ".ppt":
			path = os.path.join(thirdpartydir, "xlhtml")
			command = "ppthtml" 
			args = [filename]
		else:
			print "Cannot convert file because of unknown extension: " + filename
			
		if os.path.exists( os.path.join(path, "bin") ):
			path = os.path.join(path, "bin")
			
		if not sys.platform.startswith("win"):
			command = "./" + command

		try:
			oldcwd = os.getcwd()
			os.chdir(path)
			#Let's check for hung programs
			seconds = 0.0
 
			if sys.platform.startswith("win"):
				htmlfile = win32api.GetShortPathName(htmlfile)
			
			exe = exe.encode( utils.getCurrentEncoding() )
			commmand = command.encode( utils.getCurrentEncoding() )
			htmlfile = htmlfile.encode( utils.getCurrentEncoding() )
			
			mycommand = [command] + args + [">"] + [htmlfile]
			retcode = subprocess.call( mycommand )
			
			if retcode != 0:
				sys.stderr.write('ERROR: command "%s" failed.\n' % command)
			else:
				print "File took %f seconds to convert." % (seconds)
				html = utils.openFile(htmlfile, "r").read()

			#some utilities assume their own path for extracted images
			self._CleanupTempFiles(path)
			os.chdir(oldcwd)
			
		except:
			import traceback
			if traceback.print_exc() != None:
				print traceback.print_exc()
			print "Unable to convert document: " + filename #if we can't convert, oh well ;-)

		return html, outformat

	def _CleanupTempFiles(self, path):
		for ext in ["png", "jpg", "jpeg", "wmf", "gif", "$$$", "emf"]:
			for afile in glob.glob(os.path.join(path, "*." + ext)):
				os.remove(os.path.join(path, afile))
		
if hasOOo:
    class OOoDocConverter:
    	def __init__(self):
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
			oodir = settings.AppSettings["OpenOffice"]
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
		