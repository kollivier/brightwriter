from __future__ import absolute_import
from builtins import object
import os
import sys

import logging
log = logging.getLogger('EClass')

themeList = None

from . import BaseTheme
from . import Default_frames
from . import epub
from . import IMS_Package


class ThemeList(object):
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
        for key in list(self.themes.keys()):
            if self.themes[key].isPublic:
                result.append(key)

        return result

    def FindTheme(self, themename, returnDefault=True):
        if themename in list(self.themes.keys()):
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
