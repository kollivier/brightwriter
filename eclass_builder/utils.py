
class LogFile:
	def __init__(self, filename="log.txt"):
		self.filename = filename

	def write(self, message):
		print message
		myfile = open(self.filename, "a")
		myfile.write(message + "\n")
		myfile.close()

def getStdErrorMessage(type = "IOError", args={}):
	if type == "IOError":
		if args["type"] == "write":
			return _("There was an error writing the file '%(filename)s' to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file.") % {"filename":args["filename"]}
		elif args["type"] == "read":
			return _("Could not read file '%(filename)s from disk. Please check that the file exists in the location specified and that you have permission to open/view the file.") % {"filename":args["filename"]}
	elif type == "UnknownError":
		return _("An unknown error has occurred. A traceback has been written to the 'errlog.txt' file within your program directory.")