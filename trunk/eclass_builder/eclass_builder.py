import string, sys, os
from wxPython.wx import *

class MyApp(wxApp):
	def OnInit(self):
		self.SetAppName("EClass.Builder")
		import editor
		self.frame = editor.MainFrame2(None, -1, "EClass.Builder")
		self.frame.Show(True)
		self.SetTopWindow(self.frame)
		return True

for arg in sys.argv:
	if arg == "--autostart-pyuno":
		import re
		myfilename = ""
		if os.name == "nt":
			myfilename = "C:\\Program Files\\OpenOffice.org1.1beta\\share\\registry\\data\\org\\openoffice\\Setup.xcu"
		try:
			print "Registering Pyuno... Location is: " + myfilename
			file = utils.openFile(myfilename, "r")
			data = file.read()
			file.close()
			file = utils.openFile(myfilename + ".bak", "w")
			file.write(data)
			file.close()
			if string.find(data, "<prop oor:name=\"ooSetupConnectionURL\">") == -1:
				if string.find(data, "<node oor:name=\"Office\">") > -1:
					myterm = re.compile("(<node oor:name=\"Office\">)", re.IGNORECASE|re.DOTALL)
					data = myterm.sub("\\1\n<prop oor:name=\"ooSetupConnectionURL\"><value>socket,host=localhost,port=2002;urp;</value></prop>\n", data)
				else:
					data = data + """
					<node oor:name="Office">
						<prop oor:name="ooSetupConnectionURL">socket,host=localhost,port=2002;urp;</prop>
					</node>
					"""
				file = utils.openFile(myfilename, "w")
				file.write(data)
				file.close()
		except:
			print "Sorry, cannot register OpenOffice."
		exit(0)
	if arg == "--debug":
		debug = 1

app = MyApp(0)
app.MainLoop()
