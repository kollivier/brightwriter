from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from .core import *

from AppKit import *
from LaunchServices import *

import urllib.request, urllib.parse, urllib.error

kLSRolesNone = 0x00000001
kLSRolesViewer = 0x00000002
kLSRolesEditor = 0x00000004
kLSRolesShell = 0x00000008
kLSRolesAll = 0xFFFFFFFF

NSApplicationLoad()

def getAppsForFilename(filename, role = "viewer"):
    url = "file://" + urllib.parse.quote(filename)
    appdict = {}
    
    role_constant = {
        "viewer": kLSRolesViewer,
        "editor": kLSRolesEditor,
        "all"   : kLSRolesAll,
    }[role]

    nsurl = NSURL.URLWithString_(url)
    result = LSCopyApplicationURLsForURL(nsurl, role_constant)
    
    if result:
        for appfile in result:
            appurl = NSURL.URLWithString_(str(appfile))
            name = LSCopyDisplayNameForURL(appurl, None)[1]
            appfile = urllib.request.url2pathname(str(appurl))[:-1]
            appfile = appfile.replace('file://localhost', '')
            appdict[name] = Application(appfile, name)

    return appdict
