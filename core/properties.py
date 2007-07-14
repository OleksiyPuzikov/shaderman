""" This is the current code I'm using for brick/node properties editor.
 
 It's gonna be phased out and replaced with the better class from prefs_window.py.
 
 """

import wx
import os
import sys

import wx.lib.mixins.listctrl as listmixo # old standard one 
import mixin2 as listmix # new patched one, part of the old standard one
import wx.html

from core import node

class TestListCtrl(wx.ListCtrl,
                   listmixo.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)

        listmixo.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self, parent)

class PropertiesFrame(wx.Frame):
    
    def __init__(self, parent, title=""):
        wx.Frame.__init__(self, parent, title=title, style=wx.RESIZE_BORDER+wx.DEFAULT_DIALOG_STYLE)
	
	self.node = None
	
	self.html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
        	self.html.SetStandardFonts()
	self.html.SetBorders(4)
	
	self.list = TestListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_VRULES | wx.LC_HRULES | wx.LC_SINGLE_SEL)
	
        self.list.InsertColumn(0, "Parameter")
        self.list.InsertColumn(1, "Value")
	
        self.list.SetColumnWidth(0, 200)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
	
	self.btnClose = wx.Button(self, -1, " Close ", pos=(440, 80))
	self.btnClose.SetDefault()

	self.Bind(wx.EVT_BUTTON, self.CloseClick, self.btnClose)
	self.Bind(wx.EVT_SIZE, self.OnSize)
	self.Bind(wx.EVT_SHOW, self.OnSize)
	self.Bind(wx.EVT_CLOSE, self.OnClose)
	self.Bind(listmix.EVT_UPDATE_NODE, self.OnUpdate)
	
    def __del__(self):
	#print "pform destructor called"
	pass
	
    def AssignNode(self, node):
	self.node = node
	self.SetTitle(node.name)
	self.list.DeleteAllItems()
	
	for inp in self.node.in_params:
		pname = str(inp["name"])
		pvalue = str(inp["default"])
		connection = self.node.in_connections.get(pname, None)
		if (connection == None): # there's no connection
			self.AddElement(pname, pvalue)
	
	self.html.SetPage(node.help)
	
    def OnUpdate(self, event):
	for inp in self.node.in_params:
		pname = str(inp["name"])
		connection = self.node.in_connections.get(pname, None)
		if (connection == None): # there's no connection
			pvalue2 = self.GetElement(pname)
			inp["default"] = pvalue2
	
    def AddElement(self, name, value):
	index = self.list.InsertStringItem(sys.maxint, name)
	self.list.SetStringItem(index, 1, value)
	
    def GetElement(self, aname):
	for i in range(self.list.GetItemCount()):
		name = self.list.GetItemText(i)
		if name == aname:
			return self.list.GetItem(i, 1).GetText()
	
    def OnClose(self, event):
	event.Veto()
	self.Show(False)
	
    def CloseClick(self, event):
	self.Show(False)
    
    def OnSize(self, event):
	try: # this one is to catch the C++ exception that happened when I'm closing the main window first
		w,h = self.size = self.GetClientSize()
		bw, bh = self.btnClose.GetClientSizeTuple()
		
		self.html.SetDimensions(0, 0, w, 48)
		self.list.SetDimensions(0, 48, w, h-bh-20-48)
		
		if wx.Platform == "__WXMAC__":
			self.btnClose.SetPosition((w-bw-20, h-bh-10))
		else:
			self.btnClose.SetPosition((w-bw-10, h-bh-10))
	except:
		pass
	
if __name__ == '__main__': # simple test
    
	app = wx.PySimpleApp(redirect=False)
	frm = PropertiesFrame(None, "Properties editor")
	
	frm.SetSize((300,500))
	
	frm.AddElement("color", "1,1,1")
	frm.AddElement("opacity", "1,0,1")
	
	frm.Show(True)
	app.SetTopWindow(frm)
	app.MainLoop()
