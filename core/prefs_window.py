""" 
I'm experimenting with advanced UI concepts for general properties editor. Thus this file.
The class is names the same as the old one (which can be found in properties.py); make sure
they don't clash.

This is a work in progress; I'm already using this for mode settings.

"""

import wx

spacer = wx.Size(10, 20)

import re

vaNUMBER = r'\d+$'
vaFLOAT = r'\d+\.\d+$'

class PrefValidator(wx.PyValidator):

     def __init__(self, regex = None):
         wx.PyValidator.__init__(self)
         self.regex = regex
         if self.regex:
             self.re = re.compile(regex)

     def Clone(self):
         return PrefValidator(self.regex)

     def Validate(self, win):
	 print "enter validate"
         if not self.regex:
             return True
         window = self.GetWindow()
         text = window.GetValue().strip()
	 print self.re.match(text)
         if self.re.match(text):
             return True
         else:
             return False

     def TransferToWindow(self):
         return true

     def TransferFromWindow(self):
         return true

class FloatValidator( wx.PyValidator ):
        
	def Clone (self):
                return self.__class__()
	
        def Validate(self, window):
                window = wx.PyTypeCast(window, "wx.TextCtrl")
                try:
                        value = float(window.GetValue())
                        return true
                except ValueError:
                        return false

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
	
	# validators doesn't work for wx.Frame, only for wx.Dialog?
	#self.text = wx.TextCtrl( self, -1, value, size  = wx.Size( 56, 20 ), style = wx.TE_PROCESS_ENTER, validator = PrefValidator(vaFLOAT) )
	self.text = wx.TextCtrl( self, -1, value, size  = wx.Size( 56, 20 ), style = wx.TE_PROCESS_ENTER )
	sizer.Add( self.text, 1,  wx.EXPAND)
	
	sizer.Add( spacer )
	
	self.SetSizer( sizer )
	
        #self.text.Bind(wx.EVT_TEXT_ENTER, self.update_object ) # this crashes on Mac
        #self.text.Bind(wx.EVT_KILL_FOCUS, self.update_object )
        self.text.Bind(wx.EVT_TEXT, self.update_object)
	
    def update_object(self, event):
	for p in self.parameters:
		if p["name"] == self.label:
			p["default"] = self.text.GetValue()
	event.Skip()

class RangeEditPanel(NodePropertyPanel):
    def __init__(self, parent, label, value):
	self.label = label
	self.value = value
	self.parent = parent
	
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
	
	self.SetSizeHints(-1, 24, -1, 24) #minw, minh, maxw, maxh

	sizer  = wx.BoxSizer( wx.HORIZONTAL )
	
	sizer.Add( spacer )

	self._label_lo = wx.StaticText( self, -1, self.label, size = wx.Size(100, 20), style = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE )
	parent.labels.append(self._label_lo)
	sizer.Add( self._label_lo, 0, wx.ALIGN_CENTER_VERTICAL )
	
	sizer.Add( spacer )

	self.slider = wx.Slider( self, -1, float(self.value)*1000, -1000*float(self.value), 2000*float(self.value), size = wx.Size( 120, 20 ), style  = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS )
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
		
		for p in params:
			if p["type"] == "float":
				panel = RangeEditPanel(self, p["name"], p["default"])
			else:
				panel = TextEditPanel(self, p["name"], p["default"])
			panel.AssignParameters(params)
			
			self.bigSizer.Add(wx.Size(-1, 5), 0, wx.EXPAND) # vertical spacer between the editors
			self.bigSizer.Add(panel, 0, wx.EXPAND)
		
		self.Bind(wx.EVT_SIZE, self.OnSize)
		
		self.SetSizer(self.bigSizer)
		
		self.Thaw() # Allow screen updates to occur again
		
	def OnSize(self, event):
		w, h = self.GetClientSizeTuple()
		for l in self.labels:
			l.SetSizeHints(w/3, -1, -1, -1) #minw, minh, maxw, maxh
		event.Skip()
	
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
