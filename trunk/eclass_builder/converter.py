import getopt,sys
import os
import cStringIO
import string

import uno
from unohelper import Base,systemPathToFileUrl, absolutize
from com.sun.star.beans import PropertyValue
from com.sun.star.beans.PropertyState import DIRECT_VALUE
from com.sun.star.uno import Exception as UnoException
from com.sun.star.io import IOException,XInputStream, XOutputStream

class OutputStream( Base, XOutputStream ):
	def __init__( self):
		self.closed = 0
		self.data = ""

	def closeOutput(self):
		self.closed = 1

	def writeBytes( self, seq ):
		self.data = self.data + seq.value

	def flush( self ):
		pass
		

class DocConverter:
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
		outfile = OutputStream()
		ctxLocal = uno.getComponentContext()
		smgrLocal = ctxLocal.ServiceManager

		try:
			resolver = smgrLocal.createInstanceWithContext(
				 "com.sun.star.bridge.UnoUrlResolver", ctxLocal )
			ctx = resolver.resolve( self.url )
			smgr = ctx.ServiceManager
		except:
			try:
				os.system(os.path.join(self.parent.settings["OpenOffice"], "program", "soffice"))
				resolver = smgrLocal.createInstanceWithContext(
					 "com.sun.star.bridge.UnoUrlResolver", ctxLocal )
				ctx = resolver.resolve( self.url )
				smgr = ctx.ServiceManager
			except:
				print "error... could not start openoffice."


		desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx )
		directory, file = os.path.split(filename)
		print "My directory = " + directory + ", my file = " + file
		cwd = systemPathToFileUrl(directory)
		self.outformat = outformat
		outProps = (
			PropertyValue( "FilterName" , 0, self.outfilters[string.lower(self.outformat)] , 0 ),
			PropertyValue( "OutputStream",0, outfile,0))
		filebase, fileext = os.path.splitext(file)
		fileext = fileext[1:]
		if fileext == "htm":
			fileext == "html"
		elif fileext == "text":
			fileext = "txt"
		
		try:
			inProps = PropertyValue( "Hidden" , 0 , True, 0 ),
			inProps = inProps + ( PropertyValue( "FilterName", 0, self.infilters[string.lower(fileext)], 0 ),)
			url = filename
			if not ( filename.startswith( "ftp:" ) or \
					filename.startswith( "http:" ) or \
					filename.startswith("file:") ):
				url = uno.absolutize( cwd, systemPathToFileUrl(filename) )
			doc = desktop.loadComponentFromURL( url , "_blank", 0,inProps)
			
			if not doc:
				raise UnoException( "Couldn't open stream for unknown reason", None )		  
			doc.storeToURL(systemPathToFileUrl(os.path.join(os.getcwd(), "temp", filebase + "." + self.outformat)),outProps)
			return os.path.join(os.getcwd(), "temp", filebase + "." + self.outformat)
			
		except IOException, e:
			sys.stderr.write( "Error during conversion: " + e.Message + "\n" )
			retVal = 1
		except UnoException, e:
			sys.stderr.write( "Error ("+repr(e.__class__)+") during conversion:" + e.Message + "\n" )
			retVal = 1
		
		if doc:
			doc.dispose()
		