from __future__ import print_function
from __future__ import absolute_import
import os
import sys

from .core import *

if sys.platform.startswith("darwin"):
    from .launch_mac import *
else:
    from .launch_none import *

if __name__ == "__main__":
    apps = getAppsForFilename('/Users/kevino/Documents/EClass Projects/Business Plan for Social Entrepreneurial Organizations/Text/Page 4 Course Description and Introduction.htm', "all")
    for anapp in apps:
        print("%s, %s" % (apps[anapp].name, apps[anapp].filename))
