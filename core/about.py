""" Implements the about box. """

import sys
import wx
import wx.html
from core.utils import good_path

class AboutBox(wx.Dialog):
	text = """
<html>
<body bgcolor="#EFEFEF" border="0" style="padding: 0; margin: 0;">
<center>
<img src="%s" />
<br>
<font size="-2">
&copy; Alexei Puzikov, http://www.dream.com.ua<br>
Released under BSD license in 2007. http://code.google.com/p/shaderman<br>&nbsp;<br>
wxPython %s (%s), running on Python %s</font></center></body></html>"""

	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'About ShaderMan.Next',)
		html = wx.html.HtmlWindow(self, -1, size=(420, -1))
		html.SetPage(self.text % (good_path("core/logo.gif"), wx.VERSION_STRING, wx.PlatformInfo[1], sys.version.split()[0]))
		
		ir = html.GetInternalRepresentation()
		html.SetSize( (ir.GetWidth()+20, ir.GetHeight()+20) )
		self.SetClientSize(html.GetSize())
		self.CentreOnParent(wx.BOTH)
		
		html.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
	
	def OnClick(self, event):
		self.Close()
	
if __name__ == '__main__':
	app = wx.PySimpleApp()
	dlg = AboutBox(None)
	dlg.ShowModal()
	dlg.Destroy()
	app.MainLoop()
