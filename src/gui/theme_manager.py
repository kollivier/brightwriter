from __future__ import print_function
from __future__ import absolute_import
import string, sys, os
import shutil

import wx
import wx.lib.sized_controls as sc
import persistence
import wxbrowser

import conman
import fileutils
import utils
import settings

from . import editbox

class ThemeManager(sc.SizedDialog):
    def __init__(self, parent):
        sc.SizedDialog.__init__ (self, parent, -1, _("Theme Manager"),
                              size=wx.Size(760, 540), 
                              style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        pane = self.GetContentsPane()
        
        self.parent = parent
        
        previewPane = sc.SizedPanel(pane, -1)
        previewPane.SetSizerType("horizontal")
        previewPane.SetSizerProps(expand=True, proportion=1, align="center")
        #wx.StaticText(previewPane, -1, _("Installed Themes"))
        #wx.StaticText(previewPane, -1, _("Theme Preview"))

        self.lstThemeList = editbox.EditListBox(previewPane, -1, size=(200, -1))
        self.lstThemeList.SetSizerProps(expand=True)
        self.lstThemeList.SetChoices(choices=self.parent.themes.GetPublicThemeNames())

        self.browser = wxbrowser.wxBrowser(previewPane, -1)
        self.browser.browser.SetSizerProps(expand=True, proportion=1)

        line = wx.StaticLine(pane, -1)
        line.SetSizerProp("expand", True)
        themeBtnPane = sc.SizedPanel(pane, -1)
        themeBtnPane.SetSizerType("horizontal")
        themeBtnPane.SetSizerProp("expand", True)
        self.btnSetTheme = wx.Button(themeBtnPane, -1, _("Use this theme"))
        self.btnExportTheme = wx.Button(themeBtnPane, -1, _("Export theme"))
        self.btnImportTheme = wx.Button(themeBtnPane, -1, _("Import theme"))

        # spacer
        spacer = sc.SizedPanel(themeBtnPane, -1)
        spacer.SetSizerProps(expand=True, proportion=1)
        self.btnOK = wx.Button(themeBtnPane, wx.ID_OK, _("Close"))
        self.btnOK.SetSizerProp("align", "center")
        
        # load data
        if self.parent.currentTheme and self.parent.currentTheme.themename in self.parent.themes.GetPublicThemeNames():
            self.lstThemeList.listbox.SetStringSelection(self.parent.currentTheme.themename)
        else:
            self.lstThemeList.listbox.SetStringSelection("Default (frames)")

        self.themeTempDir = os.path.join(os.path.dirname(os.tmpnam()), "EClassPreview")
        if not os.path.exists(self.themeTempDir):
            os.makedirs(self.themeTempDir)

        self.themeDir = os.path.join(settings.AppDir, "themes", "ThemePreview")
        self.pub = conman.ConMan()
        self.pub.LoadFromXML(os.path.join(self.themeDir, "imsmanifest.xml"))
        
        self.SetMinSize(self.GetSizer().GetMinSize())

        self.OnThemeChanged(None)

        wx.EVT_BUTTON(self, self.lstThemeList.GetNewButton().GetId(), self.OnNewTheme)
        wx.EVT_BUTTON(self, self.lstThemeList.GetCopyButton().GetId(), self.OnCopyTheme)
        wx.EVT_BUTTON(self, self.lstThemeList.GetDeleteButton().GetId(), self.OnDeleteTheme)
        wx.EVT_BUTTON(self, self.btnSetTheme.GetId(), self.OnSetTheme)
        wx.EVT_BUTTON(self, self.btnExportTheme.GetId(), self.ExportTheme)
        wx.EVT_BUTTON(self, self.btnImportTheme.GetId(), self.ImportTheme)
        wx.EVT_LISTBOX(self.lstThemeList, self.lstThemeList.GetListBox().GetId(), self.OnThemeChanged)
    
    def OnThemeChanged(self, event):
        themename = self.lstThemeList.GetListBox().GetStringSelection()
        shutil.rmtree(self.themeTempDir)
        print("selection is %s" % themename)
        # load the theme preview
        self.oldProjectDir = settings.ProjectDir 
        settings.ProjectDir = self.themeDir
        self.currentTheme = self.parent.themes.FindTheme(themename)
        publisher = self.currentTheme.HTMLPublisher(self, dir=self.themeTempDir)
        result = publisher.Publish()
        if result:
            print('loading page?')
            filename = os.path.join(self.themeTempDir, "index.htm")
            print(repr(os.path.exists(filename)))
            self.browser.LoadPage(filename)
        settings.ProjectDir = self.oldProjectDir

    def OnSetTheme(self, event):
        self.UpdateTheme()

    def ReloadThemes(self):
        self.parent.themes.LoadThemes()
        self.lstThemeList.Clear()
        for theme in self.parent.themes.GetPublicThemeNames():
            self.lstThemeList.Append(theme)

    def UpdateTheme(self):
        mythememodule = ""
        mytheme = self.lstThemeList.GetStringSelection()
        if not mytheme == "":
            theme = self.parent.themes.FindTheme(mytheme)
            self.parent.currentTheme = theme
            settings.ProjectSettings["Theme"] = mytheme

            publisher = self.parent.currentTheme.HTMLPublisher(self.parent)
            result = publisher.Publish()
            self.parent.Preview()
            self.updateTheme = False

    def OnNewTheme(self, event):
        dialog = wx.TextEntryDialog(self, _("Please type a name for your new theme"), 
                                    _("New Theme"), _("New Theme"))
        if dialog.ShowModal() == wx.ID_OK:
            themedir = os.path.join(settings.AppDir, "themes")
            filename = string.replace(fileutils.MakeFileName2(dialog.GetValue()) + ".py", "-", "_")
            foldername = utils.createSafeFilename(dialog.GetValue())
            try:
                os.mkdir(os.path.join(themedir, foldername))
            except:
                message = _("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(settings.AppDir, "themes")}
                self.parent.log.error(message)
                wx.MessageBox(message)
                return 
            myfile = utils.openFile(os.path.join(themedir, filename), "w")


            data = """
from BaseTheme import *
themename = "%s"
import settings

class HTMLPublisher(BaseHTMLPublisher):
    def __init__(self, parent):
        BaseHTMLPublisher.__init__(self, parent)
        self.themedir = os.path.join(settings.AppDir, "themes", themename)
""" % (string.replace(dialog.GetValue(), "\"", "\\\""))


            myfile.write(data)
            myfile.close()

            #copy support files from Default (no frames)
            fileutils.CopyFiles(os.path.join(themedir, "Default (no frames)"), os.path.join(themedir, foldername), 1)
            self.parent.themes.LoadThemes()
            self.ReloadThemes()
        dialog.Destroy()

    def OnDeleteTheme(self, event):
        filename = string.replace(fileutils.MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
        modulename = string.replace(filename, ".py", "")
        if self.parent.currentTheme == [self.lstThemeList.GetStringSelection(), modulename]:
            wx.MessageBox(_("Cannot delete theme because it is currently in use for this EClass. To delete this theme, please change your EClass theme."))
            return 
        dialog = wx.MessageDialog(self, _("Are you sure you want to delete the theme '%(theme)s'? This action cannot be undone.") % {"theme":self.lstThemeList.GetStringSelection()}, 
                                      _("Confirm Delete"), wx.YES_NO)
        if dialog.ShowModal() == wx.ID_YES:
            themedir = os.path.join(settings.AppDir, "themes")
            themefile = os.path.join(themedir, filename)
            if os.path.exists(themefile):
                os.remove(themefile)
            # remove the .pyc file if it exists
            if os.path.exists(themefile + "c"):
                os.remove(themefile + "c")
            foldername = os.path.join(themedir, self.lstThemeList.GetStringSelection())
            if os.path.exists(foldername):
                shutil.rmtree(foldername)
            
            self.parent.themes.LoadThemes()
            self.ReloadThemes()

        dialog.Destroy()

    def OnCopyTheme(self, event):
        dialog = wx.TextEntryDialog(self, _("Please type a name for your new theme"), 
                                          _("New Theme"), "")
        if dialog.ShowModal() == wx.ID_OK:  
            themedir = os.path.join(settings.AppDir, "themes")
            filename = string.replace(fileutils.MakeFileName2(dialog.GetValue()) + ".py", " ", "_")
            otherfilename = string.replace(fileutils.MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
            otherfilename = string.replace(otherfilename, "(", "")
            otherfilename = string.replace(otherfilename, ")", "")
            foldername = utils.createSafeFilename(dialog.GetValue())
            try:
                os.mkdir(os.path.join(themedir, foldername))
            except:
                message = _("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(settings.AppDir, "themes")}
                self.parent.log.error(message)
                wx.MessageBox(message)
                return 

            copyfile = utils.openFile(os.path.join(themedir, otherfilename), "r")
            data = copyfile.read()
            copyfile.close()

            oldthemeline = 'themename = "%s"' % (string.replace(self.lstThemeList.GetStringSelection(), "\"", "\\\""))
            newthemeline = 'themename = "%s"' % (string.replace(dialog.GetValue(), "\"", "\\\""))
            data = string.replace(data, oldthemeline, newthemeline) 
            myfile = utils.openFile(os.path.join(themedir, filename), "w")
            myfile.write(data)
            myfile.close()

            #copy support files from Default (no frames)
            fileutils.CopyFiles(os.path.join(themedir, self.lstThemeList.GetStringSelection()), os.path.join(themedir, foldername), 1)
            self.parent.themes.LoadThemes()
            self.ReloadThemes()

        dialog.Destroy()

    def ExportTheme(self, event=None):
        import zipfile
        themename = fileutils.MakeFileName2(self.lstThemeList.GetStringSelection())
        dialog = wx.FileDialog(self, _("Export Theme File"), "", themename + ".theme", _("Theme Files") + " (*.theme)|*.theme", wxSAVE|wxOVERWRITE_PROMPT) 
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            themezip = zipfile.ZipFile(filename, "w")
            themepyfile = string.replace(themename + ".py", " ", "_")
            themezip.write(os.path.join(settings.AppDir, "themes", themepyfile), themepyfile)
            themefolder = utils.createSafeFilename(self.lstThemeList.GetStringSelection())
            self.AddDirToZip(themefolder, themezip)
            themezip.close()
            wx.MessageBox(_("Theme successfully exported."))
        dialog.Destroy()

    def AddDirToZip(self, dir, zip):
        for item in os.listdir(os.path.join(settings.AppDir, "themes", dir)):
            if os.path.isfile(os.path.join(settings.AppDir, "themes", dir, item)):
                zip.write(os.path.join(settings.AppDir, "themes", dir, item), os.path.join(dir, item))
            elif os.path.isdir(os.path.join(settings.AppDir, "themes", dir, item)):
                self.AddDirToZip(os.path.join(dir, item), zip)

    def ImportTheme(self, event=None):
        import zipfile
        dialog = wx.FileDialog(self, _("Select Theme to Import"), "", "",
                      _("Theme Files") + " (*.theme)|*.theme", wx.FD_OPEN) 
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            themezip = zipfile.ZipFile(filename, "r")
            files = themezip.infolist()
            for file in files:
                data = themezip.read(file.filename)
                if not os.path.exists(os.path.join(settings.AppDir, "themes", os.path.dirname(file.filename))):
                    os.mkdir(os.path.join(settings.AppDir, "themes", os.path.dirname(file.filename)))

                file = utils.openFile(os.path.join(settings.AppDir, "themes", file.filename), "wb")
                file.write(data)
                file.close()
                self.ReloadThemes()
            wx.MessageBox(_("Theme imported successfully."))
