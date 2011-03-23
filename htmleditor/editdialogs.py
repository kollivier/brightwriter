import wx
import wx.lib.sized_controls as sc

import htmledit.htmlattrs as htmlattrs

def _(text):
    return text

class TagEditorDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        self.tagName = None
        # FIXME: Add a notebook with a "style" section here
    
    def setProps(self, props):
        assert self.tagName
        
        attrs = htmlattrs.tag_attrs[self.tagName]
        
        for prop in props:
            assert prop in attrs["required"] + attrs["optional"]
            control = self.FindWindowByName(prop)
            if control:
                value = props[prop]
                if isinstance(control, wx.TextCtrl):
                    control.SetValue(value)
                elif isinstance(control, wx.SpinCtrl):
                    if value.isdigit():
                        control.SetValue(int(value))
                elif isinstance(control, wx.Choice) or isinstance(control, wx.ComboBox):
                    tagattrs = htmlattrs.attr_values[self.tagName][prop]
                    in_list = False
                    for tagattr in tagattrs:
                        if tagattrs[tagattr] == value:
                            if isinstance(control, wx.Choice):
                                control.SetStringSelection(tagattr)
                            else:
                                control.SetValue(tagattr)
                            in_list = True
                    if not in_list and isinstance(control, wx.ComboBox):
                        control.SetValue(value)
                elif isinstance(control, wx.FilePickerCtrl):
                    control.GetTextCtrl().SetValue(value)
                    
    def getProps(self):
        assert self.tagName
        retattrs = {}
        attrs = htmlattrs.tag_attrs[self.tagName]
        all_attrs = attrs["required"] + attrs["optional"]
        for attr in all_attrs:
            control = self.FindWindowByName(attr)
            if control:
                if isinstance(control, wx.TextCtrl):
                    retattrs[attr] = control.GetValue()
                elif isinstance(control, wx.SpinCtrl):
                    retattrs[attr] = "%d" % control.GetValue()
                elif isinstance(control, wx.Choice) or isinstance(control, wx.ComboBox):
                    if isinstance(control, wx.Choice):
                        value = control.GetStringSelection()
                    else:
                        value = control.GetValue()
                    if value in htmlattrs.attr_values[self.tagName][attr]:
                        retattrs[attr] = htmlattrs.attr_values[self.tagName][attr][value]
                    elif isinstance(control, wx.ComboBox):
                        retattrs[attr] = value
                elif isinstance(control, wx.FilePickerCtrl):
                    retattrs[attr] = control.GetTextCtrl().GetValue()
        return retattrs

class LinkPropsDialog(TagEditorDialog):
    def __init__(self, parent, linkProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Link Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "A"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        wx.StaticText(pane, -1, _("Link"))
        self.fileURL = wx.FilePickerCtrl(pane, -1, style=wx.FLP_OPEN | wx.FLP_USE_TEXTCTRL, name="href")
        self.fileURL.SetSizerProps(expand=True)

        wx.StaticText(pane, -1, _("Open in"))
        target = wx.ComboBox(pane, -1, choices=htmlattrs.attr_values["A"]["target"].keys(), name="target")
        target.SetSizerProps(expand=True)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.fileURL.SetFocus()
        self.Fit()
        self.MinSize = self.Size
        self.MaxSize = (-1, self.Size.y)
        
        self.setProps(linkProps)

class BookmarkPropsDialog(TagEditorDialog):
    def __init__(self, parent, bookmarkProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Bookmark Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "A"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Name"))
        wx.TextCtrl(pane, -1, name="name")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(bookmarkProps)

class OLPropsDialog(TagEditorDialog):
    def __init__(self, parent, listProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Ordered List Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "OL"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        
        wx.StaticText(pane, -1, _("List Type"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["OL"]["type"].keys(), name="type")

        wx.StaticText(pane, -1, _("Start at"))
        self.spnStartNum = wx.SpinCtrl(pane, -1, "1", name="start")
        self.spnStartNum.SetRange(1, 100)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(listProps)

class ULPropsDialog(TagEditorDialog):
    def __init__(self, parent, listProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Unordered List Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "UL"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("List Type"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["UL"]["type"].keys(), name="type")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(listProps)

class ImagePropsDialog(TagEditorDialog):
    def __init__(self, parent, imageProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Image Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "IMG"
        
        pane = self.GetContentsPane()
 
        self.imageProps = imageProps

        pane.SetSizerType("form")
        
        wx.StaticText(pane, -1, _("Image Location"))
        self.txtImageSrc = wx.FilePickerCtrl(pane, -1, name="src")
        self.txtImageSrc.SetSizerProps(expand=True)
        wx.StaticText(pane, -1, _("Text Description"))
        self.txtDescription = wx.TextCtrl(pane, -1, name="alt")
        self.txtDescription.SetSizerProps(expand=True)
        wx.StaticText(pane, -1, _("Image Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['IMG']['align'].keys(), name="align")

        wx.StaticText(pane, -1, _("Width"))
        wx.TextCtrl(pane, -1, name="width")
        wx.StaticText(pane, -1, _("Height"))
        wx.TextCtrl(pane, -1, name="height")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(imageProps)

class RowPropsDialog(TagEditorDialog):
    def __init__(self, parent, props):
        TagEditorDialog.__init__ (self, parent, -1, _("Row Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TR"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Horizontal Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TR']['align'].keys(), name="align")
    
        wx.StaticText(pane, -1, _("Vertical Alignment:"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TR']['valign'].keys(), name="valign")
        
        wx.StaticText(pane, -1, _("Background Color"))
        wx.TextCtrl(pane, -1, name="bgcolor")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(props)

class CellPropsDialog(TagEditorDialog):
    def __init__(self, parent, props):
        TagEditorDialog.__init__ (self, parent, -1, _("Cell Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TD"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Horizontal Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TD']['align'].keys(), name="align")
    
        wx.StaticText(pane, -1, _("Vertical Alignment:"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TD']['valign'].keys(), name="valign")
        
        wx.StaticText(pane, -1, _("Background Color"))
        wx.TextCtrl(pane, -1, name="bgcolor")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(props)

class TablePropsDialog(TagEditorDialog):
    def __init__(self, parent, tableProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Table Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TABLE"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Width"))
        wx.TextCtrl(pane, -1, name="width")

        #alignment options
#
        wx.StaticText(pane, -1, _("Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["TABLE"]["align"].keys(), name="align")

        wx.StaticText(pane, -1, _("Border"))
        wx.SpinCtrl(pane, -1, "0", name="border")
        
        wx.StaticText(pane, -1, _("Spacing"))
        wx.SpinCtrl(pane, -1, "0", name="cellspacing")
        
        wx.StaticText(pane, -1, _("Padding"))
        wx.SpinCtrl(pane, -1, "0", name="cellpadding")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(tableProps)

class CreateTableDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__ (self, *args, **kwargs)

        self.trows = "1"
        self.tcolumns = "1"
        self.twidth= "100"

        panel = self.GetContentsPane()

        rcpane = sc.SizedPanel(panel, -1)
        rcpane.SetSizerType("horizontal")
        self.lblRows = wx.StaticText(rcpane, -1, _("Rows:"))
        self.lblRows.SetSizerProps(valign="center")
        self.txtRows = wx.SpinCtrl(rcpane, -1, self.trows)
        self.lblColumns = wx.StaticText(rcpane, -1, _("Columns:"))
        self.lblColumns.SetSizerProps(valign="center")
        self.txtColumns = wx.SpinCtrl(rcpane, -1, self.tcolumns)

        widthPane = sc.SizedPanel(panel, -1)
        widthPane.SetSizerType("horizontal")
        self.lblWidth = wx.StaticText(widthPane, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(widthPane, -1, self.twidth)
        self.cmbWidthType = wx.Choice(widthPane, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbWidthType.SetStringSelection(_("Percent"))
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.SetMinSize(self.GetSize())

    def GetValues(self):
        trows = self.txtRows.GetValue()
        tcolumns = self.txtColumns.GetValue() 
        twidth = self.txtWidth.GetValue()
        if twidth.isdigit() and self.cmbWidthType.GetStringSelection() == _("Percent"):
            twidth += "%"

        return (trows, tcolumns, twidth)
