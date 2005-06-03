import string, os, sys

class PluginList:
	def __init__(self, programdir):
		self.plugins = []
		self.programdir = programdir
		self.filename = ""

	def LoadPlugins(self):
		for item in os.listdir(os.path.join(self.programdir, "plugins")):
			if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
				plugin = string.replace(item, ".py", "")
				exec("import plugins." + plugin)
				exec("self.plugins.append(plugins." + plugin + ".plugin_info)") 

		return self.plugins

	def GetPluginForExtension(self, fileext):
		for plugin in self.plugins:
			if extension in plugin["Extension"]:
				return plugin
		
		return None

	def GetPlugin(self, name):
		for plugin in self.plugins:
			if plugin["Name"] == name or plugin["FullName"] == name:
				return plugin

		return None

	def GetExtensionsForPlugin(self, name):
		plugin = self.GetPlugin(name)
		if plugin:
			return plugin["Extensions"]

		return []