import getopt,sys
import os
import cStringIO
import string
import tempfile

hasOOo = True
hasMSOffice = False
wordApp = None

try: 
	import win32com
	wordapp = win32com.client.gencache.EnsureDispatch("Word.Application")
	hasMSOffice = True
except:
	hasMSOffice = False

class DocConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"

	def ConvertFile(self, filename, outformat="html"):
		try:
			ext = os.path.splitext(filename)[1][1:]
			converter = None
			if ext in ["doc", "rtf"]:
				if hasMSOffice:
					converter = WordDocConverter(self.parent)
				elif hasOOo:
					converter = OOoDocConverter(self.parent)
    
			elif ext == "pdf":
				converter = PDFConverter(self.parent)
    
			if converter: 
				return converter.ConvertFile(filename, outformat)
			else:
				print "No converter found!"
				return ""
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
		handle, htmlfile = tempfile.mkstemp()
		os.close(handle)
		thirdpartydir = self.parent.parent.ThirdPartyDir
		pdfconvert = "pdftohtml"
		if os.name == "nt":
			pdfconvert = pdfconvert + ".exe"
		path = os.path.join(thirdpartydir, pdfconvert)
		if os.path.exists(path):
			os.system(path + " " + filename + " " + htmlfile)
		return htmlfile
			
			
class WordDocConverter:
	def __init__(self, parent):
		self.parent = parent
		self.infile = ""
		self.outformat = "html"
		self.outfilters = {"html": win32com.client.constants.wdFormatHTML,
							"txt": win32com.client.constants.wdFormatText}

	def ConvertFile(self, filename, outformat="html"):
		try:
			wordapp.Documents.Open(os.path.join(self.node.dir, self.node.content.filename))

			handle, htmlfile = tempfile.mkstemp()
			os.close(handle)
			wordapp.ActiveDocument.SaveAs(htmlfile, FileFormat=self.outfilters[outformat])
			wordapp.ActiveDocument.Close()
			return htmlfile
		except:
			import traceback
			print traceback.print_exc()
			return ""

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
			oodir = self.parent.parent.settings["OpenOffice"]
			if oodir != "":
				oldcwd = os.getcwd()
				os.chdir(self.parent.parent.AppDir)
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
				return htmlfile

			return ""
		