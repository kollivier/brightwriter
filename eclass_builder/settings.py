AppDir = ""
ThirdPartyDir = ""
ProjectDir = ""
LangDirName = "en"
Project = None
AppSettings = {}
ProjectSettings = {}
PrefDir = ""
plugins = []
utf8_html = True
encoding = "iso-8859-1"
webkit = False
logfile = None

app_name = "BrightWriter"

# NOTE: Do not load any non-system modules in this file, nor set up logging.
import os
import sys


def getUserHomeDir():
    home_dir = None
    if sys.platform.startswith('win'):
        if "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
            home_dir = os.environ["HOMEDRIVE"] + os.environ["HOMEPATH"]
        if "USERPROFILE" in os.environ and (not home_dir or not os.path.exists(home_dir)):
            home_dir = os.environ["USERPROFILE"]
    else:
        if "HOME" in os.environ:
            home_dir = os.environ["HOME"]
    return home_dir


def getAppDataDir():
    prefdir = ""
    if sys.platform.startswith('win'):
        if "APPDATA" in os.environ:
            prefdir = os.environ["APPDATA"]
            if not os.path.exists(prefdir):
                prefdir = os.path.join(getUserHomeDir(), "Application Data")
            prefdir = os.path.join(prefdir, app_name)
    elif sys.platform.startswith('darwin'):
        prefdir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)

    else:
        prefdir = os.path.join(os.path.expanduser("~"), "." + app_name.lower())

    return prefdir


def getApplicationsDir():
    app_dir = os.path.dirname(sys.executable)
    if sys.platform.startswith('darwin'):
        app_dir = app_dir.replace("/Contents/MacOS", "")

    return app_dir


def getDocumentsDir():
    docsfolder = ""
    if sys.platform.startswith('win'):
        try:
            import _winreg as wreg
            key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
            my_documents_dir = wreg.QueryValueEx(key, 'Personal')[0]
            key.Close()
            docsfolder = os.path.join(my_documents_dir)
        except:
            key.Close()

    elif sys.platform.startswith('darwin'):
        docsfolder = os.path.join(os.path.expanduser("~"), "Documents")
    else:
        docsfolder = os.path.expanduser("~")

    if not os.path.exists(docsfolder):
        os.mkdir(docsfolder)

    return docsfolder


def getProjectsDir():
    return os.path.join(getDocumentsDir(), "%s Projects" % app_name)


def initializeDirs():
    app_data_dir = getAppDataDir()
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

initializeDirs()
