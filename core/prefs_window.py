""" 
I'm experimenting with advanced UI concepts for general properties editor. Thus this file.
The class is names the same as the old one (which can be found in properties.py); make sure
they don't clash.

This is a work in progress; I'm already using this for mode settings.

"""

import wx
from core.utils import *

spacer = wx.Size(10, 20)

class NodePropertyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
	self.parameters = None
	
    def AssignParameters(self, params):
	self.parameters = params
    
class TextEditPanel(NodePropertyPanel):
    def __init__(self, parent, label, value):
	self.label = label
	self.value = value
	self.parent = parent
	
        NodePropertyPanel.__init__(self, parent)
	
	self.SetSizeHints(-1, 24, -1, 24) #minw, minh, maxw, maxh

	sizer  = wx.BoxSizer( wx.HORIZONTAL )
	
	sizer.Add( spacer )

	self._label_lo = wx.StaticText( self, -1, self.label, size = wx.Size(100, 20), style = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE )
	parent.labels.append(self._label_lo)
	sizer.Add( self._label_lo, 0, wx.ALIGN_CENTER_VERTICAL )
	
	sizer.Add( spacer )
	
	self.text = wx.TextCtrl( self, -1, value, size  = wx.Size( 56, 20 ), style = wx.TE_PROCESS_ENTER )
	sizer.Add( self.text, 1,  wx.EXPAND)
	
	sizer.Add( spacer )
	
	self.SetSizer( sizer )
	
        self.text.Bind(wx.EVT_TEXT, self.update_object)
	
    def update_object(self, event):
	for p in self.parameters:
		if p["name"] == self.label:
			p["default"] = self.text.GetValue()
	event.Skip()

class RangeEditPanel(NodePropertyPanel):
    def __init__(self, parent, label, value, backupvalue = None):
	self.label = label
	self.value = value
	self.parent = parent
	if backupvalue == None:		
		backupvalue = value
	
	if backupvalue == "0":
		backupvalue = "1"
	
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
	
	self.SetSizeHints(-1, 24, -1, 24) #minw, minh, maxw, maxh

	sizer  = wx.BoxSizer( wx.HORIZONTAL )
	
	sizer.Add( spacer )

	self._label_lo = wx.StaticText( self, -1, self.label, size = wx.Size(100, 20), style = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE )
	parent.labels.append(self._label_lo)
	sizer.Add( self._label_lo, 0, wx.ALIGN_CENTER_VERTICAL )
	
	sizer.Add( spacer )

	self.slider = wx.Slider( self, -1, float(self.value)*1000, -1000*float(backupvalue), 2000*float(backupvalue), size = wx.Size( 120, 20 ), style  = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS )
	self.slider.SetTickFreq( 100, 1 )
	self.slider.SetPageSize( 100 )
	self.slider.SetLineSize( 10 )
	
	sizer.Add( self.slider, 1, wx.EXPAND )
	
	self.text = wx.TextCtrl( self, -1, self.value, size  = wx.Size( 56, 20 ), style = wx.TE_PROCESS_ENTER )
	sizer.Add( self.text, 0, wx.LEFT | wx.EXPAND, 4 )
	
	sizer.Add( spacer )
	
	self.SetSizer( sizer )
	
        self.text.Bind(wx.EVT_TEXT, self.update_object)
	self.slider.Bind(wx.EVT_SCROLL, self.update_object_on_scroll)
	
    def update_object_on_scroll(self, event):
	self.text.SetValue(str(self.slider.GetValue()/1000.0))
	event.Skip()
	
    def update_object(self, event):
	sv = str(self.slider.GetValue()/1000.0)
	nv = self.text.GetValue() # to avoid cycle
	if nv != "":
		if sv != nv:
			
			try:
				value = float(nv)
				self.slider.SetValue(float(nv)*1000.0)
			except ValueError:
				pass
			
		for p in self.parameters:
			if p["name"] == self.label:
				p["default"] = nv
	event.Skip()

class PropertiesFrame(wx.Frame):

	def __init__(self, parent, params=None, connections=None, title="Edit preferences"):
		wx.Frame.__init__(self, parent, -1, title = title)
		
		self.labels = []
		
		self.bigSizer = wx.BoxSizer(wx.VERTICAL)
		
		self.Freeze() # Disable screen updates on the parent control while we build the view
		
		self.params = params
		if params != None:
			for p in self.params:
				self.AddElement(p)
		
		self.Bind(wx.EVT_SIZE, self.OnSize)
		
		self.SetSizer(self.bigSizer)
		
		self.Thaw() # Allow screen updates to occur again
		
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		
	def OnSize(self, event):
		w, h = self.GetClientSizeTuple()
		for l in self.labels:
			l.SetSizeHints(w/3, -1, -1, -1) #minw, minh, maxw, maxh
		event.Skip()
		
	def AddElement(self, p):
		if (p["type"] == "float") and (isNumber(p["default"])): # is a number
			panel = RangeEditPanel(self, p["name"], p["default"], p["backup"])
		else:
			panel = TextEditPanel(self, p["name"], p["default"])
		panel.AssignParameters(self.params)
			
		self.bigSizer.Add(wx.Size(-1, 5), 0, wx.EXPAND) # vertical spacer between the editors
		self.bigSizer.Add(panel, 0, wx.EXPAND)
		
	def AssignNode(self, anode):
		self.Freeze()
		self.bigSizer.Clear(True)
		del self.labels[:]
		
		self.params = anode.in_params
		self.SetTitle(anode.name)
		
		for inp in self.params:
			pname = str(inp["name"])
			pvalue = str(inp["default"])
			connection = anode.in_connections.get(pname, None)
			if (connection == None): # there's no connection
				self.AddElement(inp)
		
		#self.html.SetPage(node.help)
		self.SetSizer(self.bigSizer)
		
		self.Thaw()
		
	def OnClose(self, event):
		event.Veto()
		self.Show(False)
		
	def CloseClick(self, event):
		self.Show(False)
		
	
if __name__ == '__main__': # test the code
	
	parArr = []
	parArr.append({'default': u'color(0,0.5,1)', 'backup': u'color(0,0.5,1)', 'type': u'color', 'name': u'SurfaceColor', 'hint': ''})
	parArr.append({'default': u'0.8', 'backup': u'0.8', 'type': u'float', 'name': u'Kd', 'hint': ''})
	parArr.append({'default': u'color(0,0,0)', 'backup': u'color(0,0,0)', 'type': u'color', 'name': u'incandescence', 'hint': ''})
	parArr.append({'default': u'0', 'backup': u'0', 'type': u'float', 'name': u'translucence', 'hint': ''})
	
	import pprint	
	pprint.pprint(parArr)
	
	app = wx.PySimpleApp()
	dlg = PropertiesFrame(None, parArr)
	dlg.Show()
	app.MainLoop()
	
	pprint.pprint(parArr)
