import wx

class IMSCPTreeControl(wx.TreeCtrl):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TR_HAS_BUTTONS):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        
    def AddIMSItemsToTree(self, root):
        #treeimages = wxImageList(15, 15)
        #imagepath = os.path.join(settings.AppDir, "icons")
        #treeimages.Add(wxBitmap(os.path.join(imagepath, "bookclosed.gif"), wxBITMAP_TYPE_GIF))
        #treeimages.Add(wxBitmap(os.path.join(imagepath, "chapter.gif"), wxBITMAP_TYPE_GIF))
        #treeimages.Add(wxBitmap(os.path.join(imagepath, "page.gif"), wxBITMAP_TYPE_GIF))
        #self.AssignImageList(treeimages)
        self.DeleteAllItems()
        node = self.AddRoot(
            "",
            -1,-1,
            None)
        if len(root.items) > 0:
            self.AddIMSChildItemsToTree(node, root.items)
        
    def AddIMSChildItemsToTree(self, node, imsitems):
        """
        Given an xTree, create a branch beneath the current selection
        using an xTree
        """
        for child in imsitems:
            text = child.title.text
            if not text:
                text = ""
            childnode = self.AppendItem(node,
                    text,
                    -1,-1,
                    wx.TreeItemData(child))
            # Recurisive call to insert children of each child
            self.SetItemText(childnode, text)
            self.AddIMSChildItemsToTree(childnode, child.items)
            #self.Expand(NewwxNode)
        self.Refresh()
        
    def GetCurrentTreeItem(self):
        selitem = self.GetSelection()
                    
        if selitem.IsOk() and not selitem == self.GetRootItem():
            return selitem
            
        return None
        
    def GetCurrentTreeItemData(self):
        selitem = self.GetCurrentTreeItem()
        if selitem:
            return self.GetPyData(selitem)
            
        return None
    
    def AddIMSItemUnderCurrentItem(self, imsitem):
        # Since we hide the root, we need to create a 'fake' root item
        # to attach the first node to.
        if self.IsEmpty():
            parentitem = self.AddRoot(
                imsitem.title.text,
                -1,-1,
                wx.TreeItemData(imsitem))
                
        else:
            parentitem = self.GetCurrentTreeItem()
        
        newtreenode = self.AppendItem(parentitem, 
                                   imsitem.title.text, -1, -1, 
                                   wx.TreeItemData(imsitem))
       
        if newtreenode.IsOk():
            self.SelectItem(newtreenode)
            
        return newtreenode
