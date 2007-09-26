import sys, string, os
import utils
import settings
import time
import traceback

def getTraceback():
	import traceback
	type, value, trace = sys.exc_info()
	list = traceback.format_exception_only(type, value) + ["\n"] + traceback.format_tb(trace)
	return string.join(list, "")
	
def exceptionAsString(exctype, value, trace):
	return string.join(traceback.format_exception(exctype, value, trace), "\n")
	
def exceptionHook(exctype, value, trace):
    print exceptionAsString(exctype, value, trace)
	
class errorCallbacks:
    def displayError(self, message):
        print "ERROR: " + message
        if appErrorLog:
            appErrorLog.write(message)
        
    def displayWarning(self, message):
        print "WARNING: " + message
        if appErrorLog:
            appErrorLog.write(message)
            
    def displayInformation(self, message):
        print "INFO: " + message
        if appErrorLog:
            appErrorLog.write(message)
            

class AppErrorLog(utils.LogFile):
	def __init__(self):
		utils.LogFile.__init__(self)
		logdir = settings.AppDir
		try:
			import guiutils
			logdir = guiutils.getAppDataDir()
		except:
			pass
		self.filename = os.path.join(logdir, "errors.txt")
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

