import string, os, sys
import settings

pluginList = []
def LoadPlugins():
	global pluginList
	for item in os.listdir(os.path.join(settings.AppDir, "plugins")):
		if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
			plugin = string.replace(item, ".py", "")
			exec("import plugins." + plugin)
			exec("pluginList.append(plugins." + plugin + ")") 

def GetPluginForFilename(filename):
	fileext = os.path.splitext(filename)[1][1:]
	return GetPluginForExtension(fileext)

def GetPluginForExtension(fileext):
	global pluginList
	for plugin in pluginList:
		if fileext in plugin.plugin_info["Extension"]:
			return plugin

	# As a default, return the file plugin	
	for plugin in pluginList:
		if plugin.plugin_info["Name"] == "file":
			return plugin

	return None

def GetPlugin(name):
	global pluginList
	for plugin in pluginList:
		if plugin.plugin_info["Name"] == name or plugin.plugin_info["FullName"] == name:
			return plugin

	return None

def GetExtensionsForPlugin(name):
	plugin = self.GetPlugin(name)
	if plugin:
		return plugin.plugin_info["Extensions"]

	return []