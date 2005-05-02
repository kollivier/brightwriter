import os, sys, string

try:
	#attempt to silence errors on Windows
	import win32api
	win32api.SetErrorMode(65001)
except:
	pass
	
if len(sys.argv) < 2:
	print "Need program arguments to run"
else:
	command = string.join(sys.argv[1:], " ")
	print command
	os.system(command)
