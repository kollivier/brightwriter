import sys, os, string
import HTMLTemplates

convertable_formats = ["mpg", "mpeg", "mp4", "avi", "wav", "wmv", "wma", "asf", "mov"]

def getExt(filename):
    myfilename = string.lower(filename)
    ext = os.path.splitext(myfilename)[1]
    return ext

def canConvertFile(filename):
    ext = getExt(filename)
    ext = ext[1:] # remove the period
    
    if ext in convertable_formats:
        return True
    else:
        return False

def getMediaMimeType(filename, isVideo=True):
    ext = getExt(fileanme)
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

    return mimetype
    
def getHTMLTemplate(filename, isVideo=True):
    
    ext = getExt(fileanme)
    html = ""
    
    if ext in [".mpg", ".mpeg", ".wmv", ".avi", ".asf", ".wma", ".wav"]:
        html = HTMLTemplates.wmTemp
    elif ext in [".rm", ".ram"]:
        if isVideo:
            html = HTMLTemplates.rmVideoTemp
        else:
            html = HTMLTemlpates.rmAudioTemp
    elif ext == ".swf":
        html = HTMLTemplates.flashTemp
    elif ext == ".mp3":
        html = HTMLTemplates.mp3Temp
    
    return html
    