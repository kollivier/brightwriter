from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str

import subprocess

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

def open_with_app(filename, app_path):
    return subprocess.call(['open', '-a', app_path, filename])

def get_apps_for_filename(filename, role = "viewer"):
    url = "file://" + urllib.parse.quote(filename)
    app_list = []
    
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
            parts = urllib.parse.urlparse(str(appurl))
            appfile = urllib.request.url2pathname(parts.path)[:-1]
            app_list.append({'path': appfile, 'name': name})

    return app_list
