import os
import sys

import logging
log = logging.getLogger('EClass')

themeList = None

import BaseTheme
import Default_frames
import epub
import IMS_Package


class ThemeList:
    def __init__(self):
        self.themes = {}
        self.LoadThemes()

    def LoadThemes(self):
        self.themes = {
            BaseTheme.themename: BaseTheme,
            Default_frames.themename: Default_frames,
            IMS_Package.themename: IMS_Package,
            epub.themename: epub
        }

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
            return self.themes["epub"]
        else:
            return None


def FindTheme(themename, returnDefault=True):
    return themeList.FindTheme(themename, returnDefault)


def GetPublicThemeNames():
    return themeList.GetPublicThemeNames()

themeList = ThemeList()
