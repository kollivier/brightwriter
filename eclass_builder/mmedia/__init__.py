import sys, os, string
import HTMLTemplates
import tasks
import utils
import settings

convertable_formats = ["wav", "wma"] # ["mpg", "mpeg", "mp4", "avi", "wav", "wmv", "wma", "asf", "mov"]

def splitExt(filename):
    myfilename = string.lower(filename)
    base, ext = os.path.splitext(myfilename)
    return base, ext

def canConvertFile(filename):
    base, ext = splitExt(filename)
    ext = ext[1:] # remove the period
    
    if ext in convertable_formats:
        return True
    else:
        return False
        
def findFFMpeg():
    ffmpeg = os.path.join(settings.ThirdPartyDir, "ffmpeg", "ffmpeg")
    if os.path.exists(ffmpeg):
        return ffmpeg
    else:
        pathlist = string.split(os.environ['PATH'], os.pathsep)
        for dir in pathlist:
            ffmpeg = os.path.join(dir, "ffmpeg")
            if os.path.exists(ffmpeg):
                return ffmpeg
                
    return ""
        
def convertFile(filename, format=""):
    if format == "":
        basename, ext = os.path.splitext(filename)
        if ext.lower() in [".wav", ".wma"]:
            format = "mp3"
        else:
            format = "psp"
        
    command = findFFMpeg()
    if command != "":
        args = ["-y", "-f", format, "-i", filename, basename + "." + format]
        tasks.addTask(command, args)

def getMediaMimeType(filename, isVideo=True):
    base, ext = splitExt(filename)
    mimetype = ""
    
    if ext in [".mpg", ".mpeg"]:
        mimetype = "video/x-ms-asf-plugin" 
    elif ext in [".wmv", ".asf"]:
        if isVideo:
            mimetype = "video/x-ms-asf" 
        else:
            mimetype = "audio/x-ms-asf"
    elif ext == ".avi":
        mimetype = "video/avi"
    elif ext in [".rm", ".ram"]:
        mimetype = "application/vnd.rn-realmedia"
    elif ext == ".mov":
        mimetype = "video/quicktime"
    elif ext in [".swf", ".mp3"]:
        mimetype = "application/x-shockwave-flash"
    elif ext == ".wma":
        mimetype = "audio/x-ms-asf" 
    elif ext == ".wav":
        mimetype = "audio/wav"
    elif ext == ".mp3":
        mimetype = "audio/mp3"
    elif ext == ".mp4":
        mimetype = "video/mp4"

    return mimetype
    
def wasConverted(filename):
    base, ext = os.path.splitext(filename)
    if os.path.exists(base + ".mp4"):
        return True
    if os.path.exists(base + ".mp3"):
        return True
    
    return False
    
def getHTMLTemplate(filename, isVideo=True):
    
    base, ext = os.path.splitext(filename)
    # check if we have a streaming version of the same file first, 
    # and use that if so

    if os.path.exists(base + ".mp4"):
        ext = ".mp4"
    if os.path.exists(base + ".mp3"):
        ext = ".mp3"
    mimetype = getMediaMimeType(filename, isVideo)
    html = ""
    
    if ext.lower() in [".mpg", ".mpeg", ".wmv", ".avi", ".asf", ".wma", ".wav"]:
        html = HTMLTemplates.wmTemp
    elif ext.lower() in [".rm", ".ram"]:
        if isVideo:
            html = HTMLTemplates.rmVideoTemp
        else:
            html = HTMLTemlpates.rmAudioTemp
    elif ext.lower() == ".swf":
        html = HTMLTemplates.flashTemp
    elif ext.lower() == ".mp3":
        html = HTMLTemplates.mp3Temp
    elif ext.lower() == ".mp4":
        html = HTMLTemplates.mp4Temp
    elif ext.lower() == ".flv":
        html = HTMLTemplates.flvTemp
        
    html = string.replace(html, "_mimetype_", mimetype)
    
    return html
    