import sys, string, os
import utils
import guiutils
import time

def getTraceback():
	import traceback
	type, value, trace = sys.exc_info()
	list = traceback.format_exception_only(type, value) + ["\n"] + traceback.format_tb(trace)
	return string.join(list, "")

class AppErrorLog(utils.LogFile):
	def __init__(self):
		utils.LogFile.__init__(self)
		self.filename = os.path.join(guiutils.getAppDataDir(), "errors.txt")
		self.separator = u"|"

	def write(self, message):
		#get traceback if available
		tb = ""
		try:
			tb = getTraceback()
		except:
			pass

		message = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + self.separator + message + self.separator + tb + self.separator
		utils.LogFile.write(self, message)

appErrorLog = AppErrorLog()

