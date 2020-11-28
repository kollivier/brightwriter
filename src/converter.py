from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
import getopt,sys, os, string
import io, tempfile, glob, time
import settings
import subprocess
import killableprocess
import utils
import shutil

import unittest

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

class DocConverter(object):
    def __init__(self):
        self.infile = ""
        self.outformat = "html"

    def ConvertFile(self, filename, outformat="html", mode="command_line"):
        try:
            global hasOOo
            #check for OOo first, we can only do this once EClass settings are loaded
            if "OpenOffice" in list(settings.AppSettings.keys()) and os.path.exists(settings.AppSettings["OpenOffice"]):
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
                converter = CommandLineDocConverter()
    
            if converter: 
                return converter.ConvertFile(filename, outformat)
            else:
                return "", ""
        except:
            import traceback
            print(traceback.print_exc())
            return "", ""
            
class WordDocConverter(object):
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
            print(traceback.print_exc())
            return "", ""

class CommandLineDocConverter(object):
    def __init__(self):
        self.infile = ""
        self.outformat = "html"

    def ConvertFile(self, filename, outformat="html"):
        #we ignore outformat for command line tools and just use HTML
        import tempfile
        handle, htmlfile = tempfile.mkstemp()
        htmlfile = htmlfile.encode( utils.getCurrentEncoding() )
        os.close(handle)
        thirdpartydir = settings.ThirdPartyDir
        ext = string.lower(os.path.splitext(filename)[1])
        path = ""
        command = ""
        html = ""
        env = None
        use_stdout = True
        outformat = "html"

        if os.name == "nt":
            thirdpartydir = win32api.GetShortPathName(thirdpartydir)
            filename = win32api.GetShortPathName(filename)

        if sys.platform.startswith("darwin") and ext in [".doc", ".docx", ".rtf", ".rtfd"]:
            command = "textutil"
            args = ["-convert", "html", "-output", htmlfile, filename]
            use_stdout = False

        elif ext == ".doc":
            path = os.path.join(thirdpartydir, "wv")
            command = "wvWare"
            if not sys.platform.startswith("win"):
                env = {"LD_LIBRARY_PATH": "../lib"}
            args = ["--config " + os.path.join("..", "share", "wv", "wvHtml.xml")]
            args.append(filename)
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
        elif ext == ".pdf":
            path = os.path.join(thirdpartydir, "pdftohtml")
            command = "pdftohtml"
            args = ["-noframes", "-stdout", filename]
        else:
            print("Cannot convert file because of unknown extension: " + filename)
            
        if os.path.exists( os.path.join(path, "bin") ):
            path = os.path.join(path, "bin")
            
            if not sys.platform.startswith("win"):
                command = "./" + command

        try:
            oldcwd = os.getcwd()
            if os.path.exists(path):
                os.chdir(path)
            #print "working directory is %s" % path
            #Let's check for hung programs
            seconds = 0.0
            
            if not os.path.exists(filename):
                print("File '%s' doesn't exist!" % filename)
 
            if sys.platform.startswith("win"):
                htmlfile = win32api.GetShortPathName(htmlfile)

            command = command.encode( utils.getCurrentEncoding() )
            
            mycommand = [command] + args
            print("Running command: '%s'" % string.join(mycommand, " "))
            myprocess = killableprocess.Popen( mycommand, stdout=subprocess.PIPE, env=env)
            
            import time
            runtime = 0.0
            killed = False
            while myprocess.poll() == None:
                time.sleep(0.01)
                runtime += 0.01
                if runtime >= 20.00:
                    myprocess.kill()
                    killed = True
                    break
            
            if use_stdout:
                if not killed:
                    html = myprocess.stdout.read()
                    
                output = utils.openFile(htmlfile, "wb")
                output.write(html) 
                output.close()

            #some utilities assume their own path for extracted images
            self._CleanupTempFiles(path)
            os.chdir(oldcwd)
            
        except:
            import traceback
            if traceback.print_exc() != None:
                print(traceback.print_exc())
            print("Unable to convert document: " + filename) #if we can't convert, oh well ;-)

        return htmlfile, outformat

    def _CleanupTempFiles(self, path):
        for ext in ["png", "jpg", "jpeg", "wmf", "gif", "$$$", "emf"]:
            for afile in glob.glob(os.path.join(path, "*." + ext)):
                os.remove(os.path.join(path, afile))
        
class OOoDocConverter(object):
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
            
class ConversionTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()
        rootdir = os.path.abspath(sys.path[0])
        if not os.path.isdir(rootdir):
            rootdir = os.path.dirname(rootdir)
        self.filesRootDir = os.path.join(rootdir, "testFiles", "convertTest")
        settings.ThirdPartyDir = os.path.join(rootdir, "3rdparty", utils.getPlatformName())
        self.converter = DocConverter()
    
    def tearDown(self):
        shutil.rmtree(self.tempdir)
        
    def testCommandLineHang(self):
        filename = os.path.join(self.filesRootDir, "hung_process_test", "ANEXO1.xls")
        self.converter.ConvertFile(filename)

def getTestSuite():
    return unittest.makeSuite(ConversionTests)

if __name__ == '__main__':
    unittest.main()
