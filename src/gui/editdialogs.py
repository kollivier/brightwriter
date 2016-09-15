import string

import wx
import wx.lib.filebrowsebutton as filebrowse
import wx.lib.sized_controls as sc

import htmledit.htmlattrs as htmlattrs


def _(text):
    return text

ALPHA_ONLY = 1
DIGIT_ONLY = 2


class TextValidator(wx.PyValidator):
    def __init__(self, flag=None, pyVar=None):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return TextValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        
        if self.flag == ALPHA_ONLY:
            for x in val:
                if x not in string.letters:
                    return False

        elif self.flag == DIGIT_ONLY:
            for x in val:
                if x not in string.digits:
                    return False

        return True

    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if self.flag == ALPHA_ONLY and chr(key) in string.letters:
            event.Skip()
            return

        if self.flag == DIGIT_ONLY and chr(key) in string.digits:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            wx.Bell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return
        
    def TransferToWindow(self):
        return True # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wxDialog from complaining.


class TagEditorDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        self.tagName = None
        # FIXME: Add a notebook with a "style" section here
    
    def setProps(self, props):
        tags = self.tagName
        attrs = {}

        if isinstance(self.tagName, basestring):
            tags = [self.tagName]

        for tag in tags:
            attrs[tag] = htmlattrs.tag_attrs[tag]

            if tag in props:
                tagProps = props[tag]
                for prop in tagProps:
                    control = self.FindWindowByName(prop)
                    if control:
                        value = tagProps[prop]
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
        retattrs = {}
        attrs = {}
        tags = self.tagName
        if isinstance(self.tagName, basestring):
            tags = [self.tagName]
        
        for tag in tags:
            attrs[tag] = htmlattrs.tag_attrs[tag]
        for tag in tags:
            tagAttrs = attrs[tag]
            all_attrs = tagAttrs["required"] + tagAttrs["optional"]
            retattrs[tag] = {}
            for attr in all_attrs:
                control = self.FindWindowByName(attr)
                if control:
                    value = None
                    if isinstance(control, wx.TextCtrl):
                        value = control.GetValue()
                    elif isinstance(control, wx.SpinCtrl):
                        value = "%d" % control.GetValue()
                    elif isinstance(control, wx.Choice) or isinstance(control, wx.ComboBox):
                        if isinstance(control, wx.Choice):
                            value = control.GetStringSelection()
                        else:
                            value = control.GetValue()
                        if value in htmlattrs.attr_values[tag][attr]:
                            value = htmlattrs.attr_values[self.tagName][attr][value]
                    elif isinstance(control, wx.FilePickerCtrl):
                        value = control.GetTextCtrl().GetValue()
                    retattrs[tag][attr] = value
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

class VideoPropsDialog(TagEditorDialog):
    def __init__(self, parent, props=None):
        TagEditorDialog.__init__ (self, parent, -1, _("Video Properties"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "VIDEO"
        
        self.SetMinSize((400, -1))

        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        wx.StaticText(pane, -1, "MP4 Video").SetSizerProps(halign="right")
        self.mp4_text = filebrowse.FileBrowseButton(pane, -1, labelText="", fileMask="MP4 Video (*.mp4,*.m4v)|*.mp4;*.m4v")
        self.mp4_text.SetSizerProps(expand=True)
        
        wx.StaticText(pane, -1, _("Width")).SetSizerProps(halign="right")
        self.width_text = wx.TextCtrl(pane, -1, "", validator=TextValidator(DIGIT_ONLY))
        
        wx.StaticText(pane, -1, _("Height")).SetSizerProps(halign="right")
        self.height_text = wx.TextCtrl(pane, -1, "", validator=TextValidator(DIGIT_ONLY))

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.mp4_text.SetFocus()
        self.Fit()
        self.MinSize = self.Size
        self.MaxSize = (-1, self.Size.y)
        
        if props is not None:
            self.setProps(props)


class AudioPropsDialog(TagEditorDialog):
    def __init__(self, parent, props=None):
        TagEditorDialog.__init__ (self, parent, -1, _("Audio Properties"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.useJWPlayer = False

        panel = self.GetContentsPane()
        audio_panel = sc.SizedPanel(panel, -1)
        audio_panel.SetSizerProps(expand=True, proportion=1)

        audio_panel.SetSizerType("form")

        self.SetMinSize((400, -1))
        wx.StaticText(audio_panel, -1, "MP3 Audio").SetSizerProps(halign="right")
        self.mp3_text = filebrowse.FileBrowseButton(audio_panel, -1, labelText="", fileMask="MP3 Audio (*.mp3)|*.mp3")
        self.mp3_text.SetSizerProps(expand=True)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        self.Fit()

        if props is not None:
            self.setProps(props)


class BookmarkPropsDialog(TagEditorDialog):
    def __init__(self, parent, bookmarkProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Bookmark Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "A"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("ID"))
        wx.TextCtrl(pane, -1, name="id")

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
        choice = wx.Choice(pane, -1, choices=htmlattrs.attr_values['IMG']['align'].keys(), name="align")
        choice.SetStringSelection(_("Default"))

        wx.StaticText(pane, -1, _("Width"))
        wx.TextCtrl(pane, -1, name="width", validator=TextValidator(DIGIT_ONLY))
        wx.StaticText(pane, -1, _("Height"))
        wx.TextCtrl(pane, -1, name="height", validator=TextValidator(DIGIT_ONLY))

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
        self.txtWidth = wx.TextCtrl(widthPane, -1, self.twidth, validator=TextValidator(DIGIT_ONLY))
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
