import os

import wx
import wx.lib.sized_controls as sc

import settings


class KolibriExportDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Export to Kolibri"),
                                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        pane = self.GetContentsPane()

        self.export_studio_radio = wx.RadioButton(pane, -1, "Export to Kolibri Studio")
        self.export_studio_radio.SetValue(True)

        token_panel = sc.SizedPanel(pane, -1)
        token_panel.SetSizerType("form")
        token_panel.SetSizerProps(expand=True)
        label = wx.StaticText(token_panel, -1, "API Token: ")
        label.SetSizerProps(align="center")
        self.studio_token = wx.TextCtrl(token_panel, -1)
        self.studio_token.SetMinSize((10*32, 24))
        self.studio_token.SetValue(settings.AppSettings['StudioAPIToken'] or '')
        self.studio_token.SetSizerProps(expand=True, proportion=1, align="center")
        token_panel.Fit()
        token_panel.SetMinSize(token_panel.GetSize())

        self.export_kolibri_radio = wx.RadioButton(pane, -1, "Export to external device or KOLIBRI_DATA folder")
        self.dir_picker = wx.DirPickerCtrl(pane, -1)
        self.dir_picker.SetSizerProps(expand=True)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))

        self.Fit()
        self.SetMinSize(self.GetSize())
