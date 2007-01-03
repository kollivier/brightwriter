import string, sys, os
import wx

class MyApp(wx.App):
	def OnInit(self):
		wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 0)
		self.SetAppName("EClass.Builder")
		import editor
		self.frame = editor.MainFrame2(None, -1, "EClass.Builder")
		self.frame.Show(True)
		self.SetTopWindow(self.frame)
		return True

for arg in sys.argv:
	if arg == "--debug":
		debug = 1

app = MyApp(0)
app.MainLoop()
