import os

# FIXME: Switch over to straight Python logging.

class LogFile:
    def __init__(self, filename="log.txt"):
        self.filename = filename
        
    def read(self):
        if os.path.exists(self.filename):
            return unicode(open(self.filename, "rb").read(), "utf-8")
        else:
            return ""

    def write(self, message):
        if message == None:
            return
        try:
            myfile = open(self.filename, "ab")
            myfile.write(message.encode("utf-8") + "\n")
            myfile.close()
        except IOError:
            print "WARNING: Unable to write to %s" % self.filename

    def clear(self):
        os.remove(self.filename)
