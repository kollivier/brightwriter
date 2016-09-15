# constants.py - often used constant values
import os

eclassdirs = ["EClass", "Text", "pub", os.path.join("pub", "audio"), os.path.join("pub", "video"), "Graphics", "File", "Present"]

if not "_" in dir():
    def _(text):
        return text

errorInfoMsg = _(" Detailed error information can be found by selecting 'Tools->Error Viewer' from the menu.")
createPageErrorMsg = _("There was an unknown error when creating the new page. The page was not created.")

# common file filters for supported multimedia formats
image_exts = ["jpg", "jpeg", "gif", "bmp", "png"]
video_exts = ["avi", "mov" , "mpg", "asf", "wmv", "rm", "ram", "swf", "flv"]
audio_exts = ["wav", "aif", "mp3", "asf", "wma", "rm" , "ram"]
doc_exts   = ["htm", "html", "doc", "rtf"]
pres_exts  = ["ppt", "htm", "html", "swf", "pdf"]
