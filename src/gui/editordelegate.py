from __future__ import print_function
from __future__ import absolute_import
import glob
import json
import logging
import os

import wx

from wx.lib.pubsub import pub

from .editactions import *
from .editdialogs import *

import settings

from .htmledit import htmlattrs
from .htmledit import templates


def _(text):
    return text

edit_functions = """
    function elementToObject(el, o) {
        var o = {
           tagName: el.tagName
        };
        var i = 0;
        for (i ; i < el.attributes.length; i++) {
            o[el.attributes[i].name] = el.attributes[i].value;
        }

        var children = el.childNodes;
        if (children.length) {
          o.children = [];
          i = 0;
          for (i ; i < children.length; i++) {
            var child = children[i];
            if (child.nodeType == 1) {
                o.children[i] = elementToObject(child, o.children) ;
            }
          }
        }
        return o;
    };

    function getSelectedNode(tagName) {
        var selection = window.getSelection();
        var range = selection.getRangeAt(0);
        var node = range.commonAncestorContainer;
        while (node) {
            if (node.nodeType == 1 && node.tagName.toLowerCase() == tagName.toLowerCase()) {
                return node;
            }
            node = node.parentNode;
        };

        var child = range.commonAncestorContainer.getElementsByTagName(tagName);
        console.log("child = " + child);
        if (child.length == 1 && child[0].nodeType == 1) {
            return child[0];
        }
        return null;
    };

    function getTagAttributes(tagName) {
        var node = getSelectedNode(tagName);
        if (node) {
            var obj = elementToObject(node);
            return JSON.stringify(obj)
        }
        return "";
    };

    function setTagAttributes(attributes) {
        var attrs = JSON.parse(attributes);
        for (var tagName in attrs) {
            var node = getSelectedNode(tagName);
            if (node) {
                for (var key in attrs[tagName]) {
                    node.setAttribute(key, attrs[tagName][key]);
                }
            }
        }
    };
"""

class HTMLEditorDelegate(wx.EvtHandler):
    def __init__(self, source, *args, **kwargs):
        logging.info("Initializing HTMLEditor Delegate...")
        wx.EvtHandler.__init__(self, *args, **kwargs)
        self.webview = source
        self.currentSearchText = None
        self.RegisterHandlers()
        self.searchId = None
        pub.subscribe(self.OnDoSearch, ('search', 'text', 'changed'))

        
    def OnSetFocus(self, event):
        self.RegisterHandlers()
        event.Skip()
        
    def OnKillFocus(self, event):
        self.RemoveHandlers()
        event.Skip()
        
    def RegisterHandlers(self):
        app = wx.GetApp()
        logging.info("Calling RegisterHandlers")
        app.AddHandlerForID(ID_UNDO, self.OnUndo)
        app.AddHandlerForID(ID_REDO, self.OnRedo)
        # app.AddHandlerForID(ID_CUT, self.OnCut)
        # app.AddHandlerForID(ID_COPY, self.OnCopy)
        # app.AddHandlerForID(ID_PASTE, self.OnPaste)
        app.AddHandlerForID(ID_REMOVE_LINK, self.OnRemoveLink)
        app.AddHandlerForID(ID_BOLD, self.OnBoldButton)
        app.AddHandlerForID(ID_ITALIC, self.OnItalicButton)
        app.AddHandlerForID(ID_UNDERLINE, self.OnUnderlineButton)
        app.AddHandlerForID(ID_FONT_COLOR, self.OnFontColorButton)
        app.AddHandlerForID(ID_ALIGN_LEFT, self.OnLeftAlignButton)
        app.AddHandlerForID(ID_ALIGN_CENTER, self.OnCenterAlignButton)
        app.AddHandlerForID(ID_ALIGN_RIGHT, self.OnRightAlignButton)
        app.AddHandlerForID(ID_INDENT, self.OnIndentButton)
        app.AddHandlerForID(ID_DEDENT, self.OnOutdentButton)
        app.AddHandlerForID(ID_BULLETS, self.OnBullet)
        app.AddHandlerForID(ID_NUMBERING, self.OnNumbering)
        app.AddHandlerForID(ID_SELECTALL, self.OnSelectAll)
        app.AddHandlerForID(ID_SELECTNONE, self.OnSelectNone)

        app.AddHandlerForID(ID_FIND_NEXT, self.OnFindNext)

        app.AddHandlerForID(ID_INSERT_IMAGE, self.OnImageButton)
        app.AddHandlerForID(ID_INSERT_LINK, self.OnLinkButton)
        app.AddHandlerForID(ID_INSERT_HR, self.OnHRButton)
        app.AddHandlerForID(ID_INSERT_TABLE, self.OnTableButton)
        app.AddHandlerForID(ID_INSERT_BOOKMARK, self.OnBookmarkButton)
        app.AddHandlerForID(ID_INSERT_VIDEO, self.OnInsertVideo)
        app.AddHandlerForID(ID_INSERT_AUDIO, self.OnInsertAudio)

        app.AddHandlerForID(ID_EDITIMAGE, self.OnImageProps)
        app.AddHandlerForID(ID_EDITLINK, self.OnLinkProps)
        app.AddHandlerForID(ID_EDITOL, self.OnListProps)
        app.AddHandlerForID(ID_EDITTABLE, self.OnTableProps)
        app.AddHandlerForID(ID_EDITROW, self.OnRowProps)
        app.AddHandlerForID(ID_EDITCELL, self.OnCellProps)
        
        app.AddHandlerForID(ID_BACK_COLOR, self.OnBackColorButton)

        app.AddHandlerForID(ID_TEXT_SUP, self.OnSuperscript)
        app.AddHandlerForID(ID_TEXT_SUB, self.OnSubscript)
        app.AddHandlerForID(ID_TEXT_REMOVE_STYLES, self.OnRemoveStyle)
        app.AddHandlerForID(ID_SPELLING_GUESS, self.OnSpellingGuessChosen)
        
        app.AddUIHandlerForID(ID_UNDO, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_REDO, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_REMOVE_LINK, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_BOLD, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_ITALIC, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_UNDERLINE, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_FONT_COLOR, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_ALIGN_LEFT, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_ALIGN_CENTER, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_ALIGN_RIGHT, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INDENT, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_DEDENT, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_BULLETS, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_NUMBERING, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_SELECTALL, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_SELECTNONE, self.UpdateEditCommand)

        app.AddUIHandlerForID(ID_INSERT_IMAGE, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_VIDEO, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_AUDIO, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_LINK, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_HR, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_TABLE, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_INSERT_BOOKMARK, self.UpdateEditCommand)

        app.AddUIHandlerForID(ID_EDITIMAGE, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_EDITLINK, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_EDITOL, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_EDITTABLE, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_EDITROW, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_EDITCELL, self.UpdateEditCommand)
        
        app.AddUIHandlerForID(ID_BACK_COLOR, self.UpdateEditCommand)

        app.AddUIHandlerForID(ID_TEXT_SUP, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_TEXT_SUB, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_TEXT_REMOVE_STYLES, self.UpdateEditCommand)
        app.AddUIHandlerForID(ID_SPELLING_GUESS, self.UpdateEditCommand)
        
        self.webview.browser.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClick)

    def RemoveHandlers(self):
        app = wx.GetApp()
        app.RemoveHandlerForID(ID_UNDO)
        app.RemoveHandlerForID(ID_REDO)
        app.RemoveHandlerForID(ID_CUT)
        app.RemoveHandlerForID(ID_COPY)
        app.RemoveHandlerForID(ID_PASTE)
        app.RemoveHandlerForID(ID_REMOVE_LINK)
        app.RemoveHandlerForID(ID_BOLD)
        app.RemoveHandlerForID(ID_ITALIC)
        app.RemoveHandlerForID(ID_UNDERLINE)
        app.RemoveHandlerForID(ID_FONT_COLOR)
        app.RemoveHandlerForID(ID_ALIGN_LEFT)
        app.RemoveHandlerForID(ID_ALIGN_CENTER)
        app.RemoveHandlerForID(ID_ALIGN_RIGHT)
        app.RemoveHandlerForID(ID_INDENT)
        app.RemoveHandlerForID(ID_DEDENT)
        app.RemoveHandlerForID(ID_BULLETS)
        app.RemoveHandlerForID(ID_NUMBERING)
        app.RemoveHandlerForID(ID_SELECTALL)
        app.RemoveHandlerForID(ID_SELECTNONE)

        app.RemoveHandlerForID(ID_FIND_NEXT)

        app.RemoveHandlerForID(ID_INSERT_IMAGE)
        app.RemoveHandlerForID(ID_INSERT_LINK)
        app.RemoveHandlerForID(ID_INSERT_HR)
        app.RemoveHandlerForID(ID_INSERT_TABLE)
        app.RemoveHandlerForID(ID_INSERT_BOOKMARK)
        app.RemoveHandlerForID(ID_INSERT_VIDEO)
        app.RemoveHandlerForID(ID_INSERT_AUDIO)

        app.RemoveHandlerForID(ID_EDITIMAGE)
        app.RemoveHandlerForID(ID_EDITLINK)
        app.RemoveHandlerForID(ID_EDITOL)
        app.RemoveHandlerForID(ID_EDITTABLE)
        app.RemoveHandlerForID(ID_EDITROW)
        app.RemoveHandlerForID(ID_EDITCELL)

        app.RemoveHandlerForID(ID_TEXT_SUP)
        app.RemoveHandlerForID(ID_TEXT_SUB)
        app.RemoveHandlerForID(ID_TEXT_REMOVE_STYLES)

    def UpdateEditCommand(self, event):
        event.Enable(True)

    def OnDoSearch(self, message):
        self.Find(message)

    def OnFindNext(self, event):
        self.Find(findFirst=False)

    def Find(self, text=None, findFirst=True):
        if wx.GetTopLevelParent(self.webview).IsActive():
            if text is None and not findFirst:
                text = self.currentSearchText

            if findFirst:
                self.webview.ExecuteEditCommand("Unselect")
            if text and text != "":
                self.currentSearchText = text
                self.webview.EvaluateJavaScript("window.find('%s', false, false, true);" % text)

    def OnSpellingGuessChosen(self, event):
        menu = event.GetEventObject()
        item = menu.FindItemById(event.GetId())
        self.webview.ExecuteEditCommand("InsertText", item.GetItemLabelText())
        self.webview.ExecuteEditCommand("Unselect")

    def OnSelectAll(self, evt):
        self.webview.ExecuteEditCommand("SelectAll")

    def OnSelectNone(self, evt):
        self.webview.ExecuteEditCommand("Unselect")

    def OnRedo(self, evt):
        self.RunCommand("Redo", evt)

    def OnCut(self, evt):
        self.RunCommand("Cut", evt)

    def OnCopy(self, evt):
        self.webview.ExecuteEditCommand("Copy")

    def OnPaste(self, evt):
        self.RunCommand("Paste", evt)
        
    def OnInsertVideo(self, evt):
        dlg = VideoPropsDialog(self.webview)
        dlg.CentreOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            mp4video = dlg.mp4_text.GetValue()

            videoHTML = templates.html5video

            if os.path.exists(mp4video):
                mp4video = self.CopyFileIfNeeded(mp4video)

            videoHTML = videoHTML.replace("__VIDEO__.MP4", mp4video)
            videoHTML = videoHTML.replace("_filename_", mp4video)
            videoHTML = videoHTML.replace("_autostart_", "false")
            videoHTML = videoHTML.replace("__VIDEO_ID__", os.path.splitext(os.path.basename(mp4video))[0])
            dimensions = ""
            if dlg.width_text.GetValue() != "":
                dimensions += "\n        width: %s," % dlg.width_text.GetValue()

            if dlg.height_text.GetValue() != "":
                dimensions += "\n        height: %s," % dlg.height_text.GetValue()

            videoHTML = videoHTML.replace("__DIMENSIONS__", dimensions)
            self.webview.ExecuteEditCommand("InsertHTML", videoHTML)
        dlg.Destroy()

    def OnInsertAudio(self, evt):
        dlg = AudioPropsDialog(self.webview)
        dlg.CentreOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            mp3audio = dlg.mp3_text.GetValue()

            jsmediaelement_dir = os.path.join(settings.ThirdPartyDir, "..", "jsmediaelement")

            for afile in glob.glob(os.path.join(jsmediaelement_dir, "*.*")):
                self.CopyFileIfNeeded(afile, overwrite="always", subdir="jsmediaelement")

            if os.path.exists(mp3audio):
                mp3audio = self.CopyFileIfNeeded(mp3audio)

            audioHTML = templates.jmediaplayer_audio
            audioHTML = audioHTML.replace("__AUDIO__.MP3", mp3audio)

            print("Inserting %s" % audioHTML)
            self.webview.ExecuteEditCommand("InsertHTML", audioHTML)
        dlg.Destroy()

    def OnTableButton(self, evt):
        tableProps = []
        mydialog = CreateTableDialog(self.webview, -1, _("Table Properties"), size=(400,400))
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            trows, tcolumns, twidth = mydialog.GetValues()
            tablehtml = """<table border="%s" width="%s">""" % ("1", twidth)
            for counter in range(0, int(trows)):
                tablehtml = tablehtml + "<tr>"
                for counter in range(0, int(tcolumns)):
                    tablehtml = tablehtml + "<td>&#160;</td>"
                tablehtml = tablehtml + "</tr>"
            tablehtml = tablehtml + "</table><p>&nbsp;</p>"
            self.webview.ExecuteEditCommand("InsertHTML", tablehtml)
            self.dirty = True
        mydialog.Destroy()
        
    def OnTableProps(self, evt):
        self.ShowEditorForTag("TABLE", TablePropsDialog)

    def OnRowProps(self, evt):
        self.ShowEditorForTag("TR", RowPropsDialog)

    def OnCellProps(self, evt):
        self.ShowEditorForTag("TD", CellPropsDialog)

    def OnImageProps(self, evt):
        self.ShowEditorForTag("IMG", ImagePropsDialog)
    
    def ShowEditorForTag(self, tag, editorClass):
        """
        Just a compatibility wrapper for single tag cases. 
        """
        self.ShowEditorForTags([tag], editorClass)

    def ShowEditorForTags(self, tags, editorClass):
        props = {}
        all_attrs = {}
        
        for tag in tags:
            attrs = htmlattrs.tag_attrs[tag]
            tagAttrs = self.GetParent(tag)
            all_attrs = attrs["required"] + attrs["optional"]
            for attr in all_attrs:
                if attr in tagAttrs:
                    if not tag in props:
                        props[tag] = {}
                    props[tag][attr] = tagAttrs[attr]

        mydialog = editorClass(self.webview, props)
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            return_props = mydialog.getProps()
            for tag in return_props:
                for prop in return_props[tag]:
                    if prop in ["href", "src"]:
                        return_props[tag][prop] = self.CopyFileIfNeeded(return_props[tag][prop])

            self.SetAttributes(tags, return_props)

        mydialog.Destroy()

    def SetAttributes(self, tags, attrs):
        print("Calling setTagAttributes with %r" % attrs)
        self.webview.EvaluateJavaScript(edit_functions + "setTagAttributes('%s');" % (json.dumps(attrs)))
        self.dirty = True

    def OnLinkProps(self, evt):
        linkProps = {}
        link = self.GetParent("A")
        if link:
            if "href" in link and link["href"] != "":
                self.ShowEditorForTag("A", LinkPropsDialog)

            elif "id" in link and link["id"] != "":
                self.ShowEditorForTag("A", BookmarkPropsDialog)

    def OnListProps(self, evt):
        listProps = []
        list = self.GetParent("ol")
        if list:
            self.ShowEditorForTag("OL", OLPropsDialog)
        else:
            self.ShowEditorForTag("UL", ULPropsDialog)

    # FIXME: Find out a way of getting the relative URL to the page and copy files in if needed
    def CopyFIleIfNeeded(self, filepath):
        return filepath

    def GetParent(self, elementName):
        elementName = elementName.lower()
        js = edit_functions + " getTagAttributes('%s');" % (elementName)
        result = self.webview.EvaluateJavaScript(js)
        if result != '':
            return json.loads(result)
        return None

    def OnLinkButton(self, evt):
        if self.GetParent("A"):
            self.OnLinkProps(evt)
            return

        linkProps = {}
        mydialog = LinkPropsDialog(self.webview, linkProps)
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            props = mydialog.getProps()["A"]
            self.webview.ExecuteEditCommand("CreateLink", self.CopyFileIfNeeded(props["href"]))
            if "target" in props:
                url = self.GetParent("A")
                if url:
                    self.SetAttributes("A", {"A": {"target": props["target"]}})
        mydialog.Destroy()

    def OnBookmarkButton(self, evt):    
        dialog = BookmarkPropsDialog(self.webview, {})
        dialog.CentreOnParent()
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            props = dialog.getProps()["A"]
            html = "<a id=\"" + props["id"] + "\"></a>"
            self.webview.ExecuteEditCommand("InsertHTML", html)
            self.dirty = True
        dialog.Destroy()

    def OnImageButton(self, evt):
        if self.GetParent("IMG"):
            self.OnImageProps(evt)
            return
        imageFormats = _("Image files") +"|*.gif;*.jpg;*.png;*.jpeg;*.bmp"
        dialog = wx.FileDialog(self.webview, _("Select an image"), "","", imageFormats, wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.webview.ExecuteEditCommand("InsertImage", self.CopyFileIfNeeded(dialog.GetPath()))
        self.dirty = True

    def OnHRButton(self, evt):
        self.webview.ExecuteEditCommand("InsertHorizontalRule")
        self.dirty = True

    def getHexColorFromRGB(self, color):
        red = str(hex(color[0])).replace("0x", "")
        if len(red) == 1:
            red = "0" + red
        green = str(hex(color[1])).replace("0x", "")
        if len(green) == 1:
            green = "0" + green
        blue = str(hex(color[2])).replace("0x", "")
        if len(blue) == 1:
            blue = "0" + blue
        value = "#" + red + green + blue
        return value

    def OnFontColorButton(self, evt):
        dlg = wx.ColourDialog(self.webview)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            value = self.getHexColorFromRGB(dlg.GetColourData().GetColour().Get()) #RGB tuple
            self.webview.ExecuteEditCommand("ForeColor", value)
        dlg.Destroy()
        self.dirty = True

    def OnBackColorButton(self, evt):
        dlg = wx.ColourDialog(self.webview)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            value = self.getHexColorFromRGB(dlg.GetColourData().GetColour().Get()) #RGB tuple
            self.webview.ExecuteEditCommand("BackColor", value)
        dlg.Destroy()
        self.dirty = True

    def OnRightClick(self, evt):
        popupmenu = wx.Menu()

        if self.GetParent("IMG"):
            popupmenu.Append(ID_EDITIMAGE, "Image Properties")
        link = self.GetParent("A")
        if link and link['href'] != '':
            popupmenu.Append(ID_EDITLINK, "Link Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Link")
        if self.GetParent("ol") or self.GetParent("ul"):
            popupmenu.Append(ID_EDITOL, "Bullets and Numbering")
        if self.GetParent("table"):
            popupmenu.Append(ID_EDITTABLE, "Table Properties")
        if self.GetParent("tr"):
            popupmenu.Append(ID_EDITROW, "Row Properties")
        if self.GetParent("td"):
            popupmenu.Append(ID_EDITCELL, "Cell Properties")
        position = evt.GetPosition()
        self.webview.PopupMenu(popupmenu, self.webview.ScreenToClient(position))

    def OnUndo(self, evt):
        self.webview.ExecuteEditCommand("Undo")

    def OnKeyEvent(self, evt):
        #for now, we're just interested in knowing when to ask for save
        self.UpdateStatus(evt)

    def OnRemoveStyle(self, evt):
        self.RunCommand("RemoveFormat", evt)

    def OnBullet(self, evt):
        self.RunCommand("InsertUnorderedList", evt)

    def OnNumbering(self, evt):
        self.RunCommand("InsertOrderedList", evt)

    def OnBoldButton(self, evt):
        self.RunCommand("Bold", evt)
        
    def OnItalicButton(self, evt):
        self.RunCommand("Italic", evt)

    def OnUnderlineButton(self, evt):
        self.RunCommand("Underline", evt)

    def OnLeftAlignButton(self, evt):
        self.RunCommand("JustifyLeft", evt)

    def OnCenterAlignButton(self, evt):
        self.RunCommand("JustifyCenter", evt)
        
    def OnRightAlignButton(self, evt):
        self.RunCommand("JustifyRight", evt)

    def OnOutdentButton(self, evt):
        self.RunCommand("Outdent", evt)

    def OnIndentButton(self, evt):
        self.RunCommand("Indent", evt)

    def RunCommand(self, command, evt):
        logging.debug("Executing command %s" % command)
        self.webview.ExecuteEditCommand(command)
        self.dirty = True

    def OnSuperscript(self, evt):
        self.RunCommand("Superscript", evt)

    def OnSubscript(self, evt):
        self.RunCommand("Subscript", evt)

    def OnRemoveLink(self, evt):
        # FIXME: This only works when the entire link is in the selection. To make this
        # work from anywhere inside the link, we must expand the selection to contain
        # the whole link, which will require adding more of WebCore::SelectionController API
        # to wxWebKitSelection.
        self.RunCommand("Unlink", evt)
