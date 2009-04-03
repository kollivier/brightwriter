import string, os
import utils
import errors

log = errors.appErrorLog #utils.LogFile("errlog.txt")

themeList = None

class ThemeList:
    def __init__(self, themedir):
        self.themedir = themedir
        self.themes = {}
        self.LoadThemes()

    def LoadThemes(self):
        self.themes = {}
        for item in os.listdir(self.themedir):
            if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and string.find(item, "themes.py") == -1 and not item[0] == ".":
                theme = string.replace(item, ".py", "")
                if theme != "BaseTheme":
                    try:
                        exec("import " + theme)
                        exec("mytheme = " + theme)
                        self.themes[mytheme.themename] = mytheme
                    except:
                        global log
                        log.write("Couldn't load theme: " + theme)
                        import traceback
                        if traceback.print_exc() != None:
                            log.write(traceback.print_exc())                                

    def GetPublicThemeNames(self):
        result = []
        for key in self.themes.keys():
            if self.themes[key].isPublic:
                result.append(key)

        return result

    def FindTheme(self, themename, returnDefault=True):
        if themename in self.themes.keys():
            return self.themes[themename]
        elif returnDefault:
            return self.themes["Default (frames)"]
        else:
            return None


def FindTheme(themename, returnDefault=True):
    return themeList.FindTheme(themename, returnDefault)

def GetPublicThemeNames():
    return themeList.GetPublicThemeNames()

rootdir = os.path.abspath(os.path.dirname(__file__))
themeList = ThemeList(rootdir)
themeList.LoadThemes()
