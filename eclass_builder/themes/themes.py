import string, os

class ThemeList:
	def __init__(self, themedir):
		self.themedir = themedir
		self.themes = {}
		self.LoadThemes()

	def LoadThemes(self):
		for item in os.listdir(self.themedir):
			if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and string.find(item, "themes.py") == -1 and not item[0] == ".":
				theme = string.replace(item, ".py", "")
				if theme != "BaseTheme":
					exec("import " + theme)
					exec("mytheme = " + theme)
					self.themes[mytheme.themename] = mytheme 

	def GetPublicThemeNames(self):
		result = []
		for key in self.themes.keys():
			if self.themes[key].isPublic:
				result.append(key)

		return result

	def FindTheme(self, themename):
		if themename in self.themes.keys():
			return self.themes[themename]
		else:
			return None