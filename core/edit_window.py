""" 
We're using this rather simple window to edit the node code. 

This should be probably powered by more powerful text editor with syntax highlight et al. Also it might be a good idea
to show the names of parameters. Or maybe just incorporate this into the prefs_window as separate tab?

"""

import wx

class EditDialog(wx.Dialog):
    
    def __init__(self, parent, title, value = ""):
        wx.Dialog.__init__(self, parent, title=title, style=wx.RESIZE_BORDER+wx.DEFAULT_DIALOG_STYLE)
	
	self.SetSize((400,500))
	
        self.editor = wx.TextCtrl(self, -1, value, size=(200, 100), style=wx.TE_MULTILINE)
	
	self.btnOK = wx.Button(self, wx.ID_OK, " Save ", pos=(440, 80))
	self.btnOK.SetDefault()
	
	self.btnCancel = wx.Button(self, wx.ID_CANCEL, " Cancel ", pos=(440, 80))
	
	self.Bind(wx.EVT_SIZE, self.OnSize)
	self.Bind(wx.EVT_BUTTON, self.CancelClick, self.btnCancel)
	self.Bind(wx.EVT_BUTTON, self.OKClick, self.btnOK)
	
    def SetValue(self, value):
	self.editor.SetValue(value)
	
    def GetValue(self):
	return self.editor.GetValue()
	
    def OnExit(self, event):
        self.Close()
	event.Skip()
    
    def OKClick(self, event):
        self.Close()
	event.Skip()
  
    def CancelClick(self, event):
        self.Close()
	event.Skip()
  
    def OnSize(self, event):
	w,h = self.size = self.GetClientSize()
	bw, bh = self.btnOK.GetClientSizeTuple()
	
	self.editor.SetDimensions(5, 5, w-10, h-bh-25)
	
	self.btnOK.SetPosition((w-bw-10, h-bh-10))
	self.btnCancel.SetPosition((10, h-bh-10))
