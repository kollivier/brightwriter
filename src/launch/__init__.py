import sys

from .core import *

if sys.platform.startswith("darwin"):
    from .launch_mac import *
else:
    from .launch_none import *
