from __future__ import print_function
import os, sys

try:
	#attempt to silence errors on Windows
	import win32api
	win32api.SetErrorMode(65001)
except:
	pass
	
if len(sys.argv) < 2:
	print("Need program arguments to run")
else:
	command = sys.argv[1:].join(" ")
	print(command)
	os.system(command)
