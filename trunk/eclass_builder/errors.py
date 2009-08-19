import locale
import platform
import sys, string, os
import settings
import time
import traceback

import eclasslog
import utils

def getTraceback():
	import traceback
	type, value, trace = sys.exc_info()
	list = traceback.format_exception_only(type, value) + ["\n"] + traceback.format_tb(trace)
	return string.join(list, "")

def exceptionAsString(exctype, value):
	return string.join(traceback.format_exception(exctype, value, None), "\n")	
	
# taken from http://code.activestate.com/recipes/52215/
def print_exc_plus(exctype, value, trace):
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    tb = trace
    stack = []
    
    while tb:
        stack.append(tb.tb_frame)
        tb = tb.tb_next

    #exception = exceptionAsString(exctype, value, trace)
    exception = "Traceback (most recent call last):\n"
    for frame in stack:
        exception += "\n"
        exception += "File \"%s\", line %s, in %s\n" % (frame.f_code.co_filename,
                                             frame.f_lineno,
                                             frame.f_code.co_name)
        for key, keyvalue in frame.f_locals.items():
            exception += "        %s = " % `key`
            #We have to be careful not to cause a new error in our error
            #printer! Calling str() on an unknown object could cause an
            #error we don't want.
            try:
                valuestring = `keyvalue`
                if len(valuestring) > 500:
                    valuestring = valuestring[:500]
                exception += valuestring
            except:
                exception += "<ERROR WHILE PRINTING VALUE>"
            exception += "\n"
        exception += "\n"
            
    exception += exceptionAsString(exctype, value)        
    
    return exception
    
def get_platform_info():
    info = """
Platform: %s
Processor: %s
Version: %s
Language: %s
""" % (platform.platform(), platform.machine(), platform.release(), "%s, %s" % locale.getdefaultlocale())
    
    return info

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
            

class AppErrorLog(eclasslog.LogFile):
	def __init__(self):
		eclasslog.LogFile.__init__(self)
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
		eclasslog.LogFile.write(self, message)

appErrorLog = AppErrorLog()

