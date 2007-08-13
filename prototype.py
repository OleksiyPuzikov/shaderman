""" Main code for ShaderMan.Next. Still called prototype.py for reasons I don't understand by myself :) """

import os
import glob
import sys
import inspect

curpath = os.path.dirname(inspect.getfile(sys._getframe(0)))
if curpath=="":
	curpath=os.getcwd()
sys.path.append(curpath)

import wx
from wx import glcanvas

productname = "ShaderMan.Next"

try:
	from OpenGL.GL import *
except ImportError:
	print("OpenGL extensions for Python do not appear to be installed.\nThis application cannot run.", "Can't start %s" % productname)
	sys.exit(1)

from core import node # non-visual elements of DAG
from core.panel import * # visual representations of DAG elements and connections

from core.utils import * # some util functions I'm using
from core.shared import * # global variables

from core.properties import PropertiesFrame # window being used to edit properties of nodes; will be replaced with prefs_window.py when ready

from core.edit_window import EditDialog # we're using pretty simple edit window to edit the source code for nodes

from core.node_draw import InitNodeDraw # initialization of node paint code - we need to load the settings for colors, fonts etc
	
class NodeCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
	self.parent = parent
        # initial mouse position
        self.lastx = self.x = self.lasty = self.y = 30
        self.size = None
	self.selected = None
	self.selection = None
	self.temparrow = None
	self.insidePreview = False
	self.SetSize((200, 200))
	
	self.markedPanels = []

	self.panx = self.pany = 0
	self.zoom = 1
	
	self.mx = self.my = self.mlastx = self.mlasty = 0 # for panning the canvas
	
	msz = wx.Display(0).GetGeometry()[2:]
	self.maxsize = (-msz[0], -msz[1], msz[0]*2, msz[1]*2)
	#print self.maxsize
	
	self.tax = self.tay = self.tax2 = self.tay2 = 0
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
	self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel) # Zoom is partially implemented, but I don't like it.

        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleMouseDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleMouseUp)

	self.popupID1 = wx.NewId()
	self.popupID2 = wx.NewId()
	self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def CorrectPosition(self, event): # return the event.GetPosition corrected by panx, pany
	x, y = event.GetPosition()
	return (x+self.panx, y+self.pany)

    def OnMiddleMouseDown(self, event):
	self.CaptureMouse()
	self.mx, self.my = self.mlastx, self.mlasty = event.GetPosition()

    def OnMiddleMouseUp(self, event):
	if self.HasCapture():
		self.ReleaseMouse()
	self.Refresh(False)

    def OnMouseWheel(self, event):
	zoomFactor = event.GetWheelRotation() / event.GetWheelDelta()

	if zoomFactor > 0:
		self.doZoom(1.0/zoomFactor)
	elif zoomFactor < 0:
		self.doZoom(zoomFactor)
		
    def doZoom(self, factor): # TODO check with users if they actually like this implementation...
	#self.zoom += factor*0.05
	z = float(settings.get('fontsize', 10))
	z += factor
	z = min(20.0, max(4.0, z))
	#print z
	settings['fontsize'] = str(z)
	
	InitNodeDraw()
	for obj in panels+arrows:
		obj.refreshFont()
	
	self.Refresh(True)

	#event.Skip()
	
	#self.InitGL()
	#self.Refresh(False)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on Windows

    def OnSize(self, event):
        self.size = self.GetClientSize()
        if self.GetContext():
	    try:
            	self.SetCurrent()
	    except:
	    	pass
	    if self.size.width>0: # <0 happened on Mac sometimes
		try:
			glViewport(0, 0, self.size.width, self.size.height)
		        self.InitGL()
		except:
			pass
        self.Refresh(True)
	self.Update()
	event.Skip()
	
    def OnPaint(self, event):
        dc = wx.ClientDC(self)
        self.SetCurrent()
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()
	
    def OnContextMenu(self, event):
	self.popupID1 = wx.NewId()
	self.popupID2 = wx.NewId()
	self.Bind(wx.EVT_MENU, self.OnMenuDeleteConnection, id=self.popupID1)
	#self.Bind(wx.EVT_MENU, self.OnMenuDoNothing, id=self.popupID2)

	self.popupID3 = wx.NewId()
	self.popupID4 = wx.NewId()
	self.popupID5 = wx.NewId()
	self.popupID6 = wx.NewId()

	self.Bind(wx.EVT_MENU, self.OnMenuSwitchParameters, id=self.popupID3)
	self.Bind(wx.EVT_MENU, self.OnMenuSwitchIcon, id=self.popupID5)
	self.Bind(wx.EVT_MENU, self.OnMenuEditCode, id=self.popupID6)

	# different menus for different places to click
	
	pos = self.CorrectPosition(event)
	pos = self.ScreenToClient(pos)
	x, y = pos
	self.menuConnection = None
	self.menuPanel = None
	
	for e in panels:
		if e.inside(x, y):
			self.menuPanel = e
			# There can be multiple outputs from the single out cell, so we don't support it now. Definitely will in the future, so TODO.
			
			#outtest = node_draw.IsArrowStart(e.node, wx.ClientDC(self), x, y)
			#if -1 != outtest:
				#pname = e.node.out_params[outtest-1]["name"]
				#connection = e.node.out_connections.get(pname, None)
				#if (connection != None): # there's connection
					#self.menuConnection = connection[0]
	
			intest = node_draw.IsArrowEnd(e.node, wx.ClientDC(self), x, y)
			if intest>0: # it's -1 if there's nothing or 0 if it's header - but we don't need header workaround here
				pname = e.node.in_params[intest-1]["name"]
				connection = e.node.in_connections.get(pname, None)
				if (connection != None): # there's connection
					self.menuConnection = connection # we somehow need to pass the information on the selected connection outside...

	menu = wx.Menu()
	if (self.menuConnection != None):
		item = wx.MenuItem(menu, self.popupID1, "Delete connection")
		menu.AppendItem(item)
		item.Enable(True)
		
		menu.AppendSeparator()
		
		item = wx.MenuItem(menu, self.popupID2, "Empty")
		menu.AppendItem(item)
		item.Enable(False)
	
	else: # we right-clicked inside node, but not on the connection end
		if self.menuPanel != None: # we've got the panel selected, so we show it's menu
			item = wx.MenuItem(menu, -1, self.menuPanel.node.name)
			menu.AppendItem(item)
			item.Enable(False)
		
			menu.AppendSeparator()
		
			item = wx.MenuItem(menu, self.popupID3, "Show parameters", kind=wx.ITEM_CHECK)
			menu.AppendItem(item)
			item.Check(self.menuPanel.showParameters)
			item.Enable(True)
		
			item = wx.MenuItem(menu, self.popupID4, "Show preview", kind=wx.ITEM_CHECK)
			menu.AppendItem(item)
			item.Enable(False) # TODO implement preview
	
			menu.AppendSeparator()
		
			item = wx.MenuItem(menu, self.popupID5, "Iconic mode", kind=wx.ITEM_CHECK)
			menu.AppendItem(item)
			item.Check(self.menuPanel.iconicMode)
			item.Enable(self.menuPanel.node.icon != "")
			
			menu.AppendSeparator()
			
			item = wx.MenuItem(menu, self.popupID6, "Edit code")
			menu.AppendItem(item)
			
		else:
			menu = self.parent.brickMenu
				
	self.PopupMenu(menu)
	if menu is not self.parent.brickMenu:
		menu.Destroy()
	self.Refresh(True)
		
    def OnMenuSwitchIcon(self, event):
	if self.menuPanel != None:
		ar = self.markedPanels
		if self.menuPanel not in ar:
			ar.append(self.menuPanel)
	
		for p in ar:
			if p.node.icon != "":
				p.iconicMode = event.Checked()
				p.refreshFont()

				for c in p.node.in_connections.itervalues():
					c.arrow.refreshFont()
		
				for c in p.node.out_connections.itervalues():
					for c2 in c:
						c2.arrow.refreshFont()
			

		self.Refresh(True)
		
		del ar
		
    def OnMenuSwitchParameters(self, event):
	if self.menuPanel != None:
		ar = self.markedPanels
		if self.menuPanel not in ar:
			ar.append(self.menuPanel)
		
		for p in ar:
			p.showParameters = event.Checked()
			p.refreshFont()

			for c in p.node.in_connections.itervalues():
				c.arrow.refreshFont()
		
			for c in p.node.out_connections.itervalues():
				for c2 in c:
					c2.arrow.refreshFont()
			
		self.Refresh(True)
		
		del ar
		
    def OnMenuEditCode(self, event):
	if self.menuPanel != None:
		editCode = True
		dlg = EditDialog(self, "Edit code for %s" % self.menuPanel.node.name)
		c = self.menuPanel.node.code
		pc = self.menuPanel.node.precode
		if c != "":
			ac = c
		else:
			ac = pc
			editCode = False
		dlg.SetValue(ac)
		if dlg.ShowModal() == wx.ID_OK:
			if editCode:
				self.menuPanel.node.code = dlg.GetValue()
			else:
				self.menuPanel.node.precode = dlg.GetValue()
		del dlg
		
		if self.CUpdateMenuItem.IsChecked():
			wx.PostEvent(self.parent, wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED, frm.ID_ACTION))
		
    def ActuallyDeleteConnection(self, connection):
	if connection != None:
		if connection.outputNode != None:
			del connection.outputNode.in_connections[connection.outputName]
		if connection.inputNode != None:
			arr = connection.inputNode.out_connections[connection.inputName]
			SafelyDelete(arr, connection)
		
		a = None
		for b in arrows:
			if b.connection == connection:
				a = b
		
		if a != None:
			SafelyDelete(arrows, a)
			del a
		
		SafelyDelete(connections, connection)
		del connection

		if self.CUpdateMenuItem.IsChecked():
			wx.PostEvent(self.parent, wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED, frm.ID_ACTION))
		
    def OnMenuDeleteConnection(self, event):
	self.ActuallyDeleteConnection(self.menuConnection)
    
    #def OnMenuDoNothing(self, event):
	#pass
	
    def OnLeftDClick(self, event):
        x, y = self.CorrectPosition(event)#event.GetPosition()
	
	for p in panels:
		if p.inside(x, y):
			node = p.node
			
			self.parent.pform.AssignNode(node)
			self.parent.pform.Show(True)
			self.parent.pform.Raise()
			
    def CoordinateInsidePreview(self, x, y):
	offx = self.size.width+self.panx
	offy = self.size.height+self.pany
	
	xw = self.maxsize[2]-self.maxsize[0];
	yw = self.maxsize[3]-self.maxsize[1];

	xw23 = xw*2/3
	yw23 = yw*2/3
	
	x1 = offx+(self.maxsize[0]-xw23)/30
	x2 = offx+(self.maxsize[2]-xw23)/30
	
	y1 = offy+(self.maxsize[1]-yw23)/30
	y2 = offy+(self.maxsize[3]-yw23)/30

	return (x in range(x1, x2)) and ((y in range(y1, y2))) # BTW, this only works with integers :)

    def OnMouseDown(self, event):
		self.CaptureMouse()
		self.x, self.y = self.lastx, self.lasty = self.CorrectPosition(event)#event.GetPosition()
		self.mx, self.my = event.GetPosition()
		
		self.insidePreview = self.CoordinateInsidePreview(self.x, self.y)
		if self.insidePreview: # code duplication alert :) see the OnMouseMove
			offx = self.size.width+self.panx
			offy = self.size.height+self.pany
			
			xw23 = (self.maxsize[2]-self.maxsize[0])*2/3
			yw23 = (self.maxsize[3]-self.maxsize[1])*2/3
			
			dx, dy = self.CorrectPosition(event)
			dx = (dx - offx)*30+xw23
			dy = (dy - offy)*30+yw23
			
			self.panx = dx
			self.pany = dy
			
			self.InitGL()
			self.Refresh(False)
			return
	
		self.selected = None
		self.selection = None
		self.temparrow = None
			
		for e in panels:
			if e.inside(self.x, self.y):
				if -1 == node_draw.IsArrowStart(e.node, wx.ClientDC(self), self.x, self.y):
					self.selected = e
					dx = self.x - e.x
					dy = self.y - e.y
					self.selected.delta = ((dx, dy))
					self.selected.originalClick = (e.x, e.y)
					if e not in self.markedPanels:
						del self.markedPanels[:]
						self.markedPanels.append(e)
						
					self.parent.pform.AssignNode(e.node)
					if self.parent.pform.IsShown():
						self.parent.pform.Raise()
				else:
					self.temparrow = Arrow(self)
					self.tax = self.tax2 = self.x
					self.tay = self.tay2 = self.y
					self.startpanel = e
					
		if (self.selected == None) and (self.temparrow == None):
			self.selection = (self.x, self.y, self.x, self.y)	

		self.Refresh(False)
		
    hatetheglobals = -1
    hatemenu = None
		
    def ManuallyAskCallback(self, event):
	node = self.stoppanel.node
	count = 1
	
	global hatetheglobals
	
	menuItem = hatemenu.FindItemById(event.GetId())
	
	for inp in node.in_params:
		pname = str(inp["name"])
		if pname == menuItem.GetLabel():
			hatetheglobals = count
			return
		count += 1
		
    def ManuallyAskForInput(self, node):
	menu = wx.Menu()
	
	global hatemenu
	hatemenu = menu
	
	item = wx.MenuItem(menu, -1, "Connect to:")
	menu.AppendItem(item)
	item.Enable(False)
		
	menu.AppendSeparator()
		
	for inp in node.in_params:
		pname = str(inp["name"])
		nid = wx.NewId()
		item = wx.MenuItem(menu, nid, pname)
		menu.AppendItem(item)
		self.Bind(wx.EVT_MENU, self.ManuallyAskCallback, id=nid)
		
	global hatetheglobals
	hatetheglobals = -1
		
	self.PopupMenu(menu)
	menu.Destroy()
	
	return hatetheglobals

    def OnMouseUp(self, event):
		self.insidePreview = False
	    
		DropSuccessful = False
		if self.temparrow != None:
			for e in panels:
				if e.inside(self.x, self.y):
					stop = node_draw.IsArrowEnd(e.node, wx.ClientDC(self), self.x, self.y)
					if -1 != stop:
						self.stoppanel = e
						if stop == 0: # ask for the connection using popupMenu and some ugly callback hack...
							stop = self.ManuallyAskForInput(e.node)
							if -1 == stop:
								continue 
						start = node_draw.IsArrowStart(self.startpanel.node, wx.ClientDC(self), self.tax, self.tay)
						
						conn = node.Connection(GetNextConnectionID())
						connections.append(conn)
						
						conn.assignInput(self.startpanel.node, self.startpanel.node.out_params[start-1]["name"])
						prev = self.stoppanel.node.in_connections.get(self.stoppanel.node.in_params[stop-1]["name"], None)
						if prev != None:
							self.ActuallyDeleteConnection(prev)
						
						conn.assignOutput(self.stoppanel.node, self.stoppanel.node.in_params[stop-1]["name"])
						
						arrows.append(self.temparrow)
						self.temparrow.assignConnection(conn)
						
						self.temparrow.refreshFont()
						
						DropSuccessful = True

						if self.CUpdateMenuItem.IsChecked():
							wx.PostEvent(self.parent, wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED, frm.ID_ACTION))
						
		if not DropSuccessful:
			self.temparrow = None
		if self.HasCapture():
			self.ReleaseMouse()
		self.selected = None
		if self.selection != None:
			del self.markedPanels[:]
			for e in panels:
				if (self.selection[0] < e.x) and (self.selection[2] > e.x+e.width) and (self.selection[1] < e.y) and (self.selection[3] > e.y+e.height):
					self.markedPanels.append(e)
			
			self.selection = None
		self.Refresh(False)

    def OnMouseMotion(self, event):
		if event.Dragging() and (event.MiddleIsDown() or (event.LeftIsDown() and event.AltDown())):
			self.mlastx, self.mlasty = self.mx, self.my
			self.mx, self.my = event.GetPosition()
			self.panx += self.mlastx-self.mx
			self.pany += self.mlasty-self.my
			self.InitGL()
			self.Refresh(False)
			return	
	
		if event.Dragging() and event.LeftIsDown():
			self.lastx, self.lasty = self.x, self.y
			self.x, self.y = self.CorrectPosition(event)#event.GetPosition()
			if self.insidePreview:
				
				offx = self.size.width+self.panx
				offy = self.size.height+self.pany
				
				xw23 = (self.maxsize[2]-self.maxsize[0])*2/3
				yw23 = (self.maxsize[3]-self.maxsize[1])*2/3
				
				dx, dy = self.CorrectPosition(event)
				dx = (dx - offx)*30+xw23
				dy = (dy - offy)*30+yw23
				
				self.panx = dx
				self.pany = dy
				
				self.InitGL()
				self.Refresh(False)
				return
			
		if self.selected != None:
			self.selected.x = self.x-self.selected.delta[0]
			self.selected.y = self.y-self.selected.delta[1]
			if self.selected in self.markedPanels: # move all the other panels as well
				for p in self.markedPanels:
					if p != self.selected:
						p.x += (self.selected.x-self.lastx+self.selected.delta[0]) 
						p.y += (self.selected.y-self.lasty+self.selected.delta[1]) 
			self.Refresh(False)
		else:
			if self.selection != None:
				self.selection = (self.selection[0], self.selection[1], self.x, self.y)
				self.Refresh(False)
			else:
				if self.temparrow != None:
					self.tax2 = self.x
					self.tay2 = self.y	
					self.Refresh(False)

class NodeCanvas(NodeCanvasBase):
    def InitGL(self):
	glDisable( GL_DEPTH_TEST )
	glDisable( GL_LIGHTING )
	
	glMatrixMode( GL_PROJECTION )
	glLoadIdentity()
	#glOrtho( 0.0, self.size.width, self.size.height, 0.0,  -1.0, 1.0 )
	glOrtho( 0.0+self.panx, self.size.width+self.panx, self.size.height+self.pany, 0.0+self.pany, -1.0, 1.0 )
	#print self.zoom
	glScalef( self.zoom, self.zoom, 1 )

  	glMatrixMode( GL_MODELVIEW )
	glLoadIdentity()

    def OnDraw(self):
	if wx.Platform == "__WXMAC__":
		bgColor = wx.Color(240, 240, 240)
	else:
		bgColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
		
	glClearColor( bgColor.Red()/255.0, bgColor.Green()/255.0, bgColor.Blue()/255.0, 1.0 )
		
  	glClear( GL_COLOR_BUFFER_BIT ) # | GL_DEPTH_BUFFER_BIT ) ?
  	#glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
	
	glEnable(GL_LINE_SMOOTH)
	glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
	#glEnable(GL_POINT_SMOOTH)
	#glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

	glLineWidth(1.2)
	glPointSize(1)
		
	for a in arrows:
		a.paint()
	
 	glEnable(GL_TEXTURE_2D)
 	glEnable(GL_BLEND)
 	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	
	for p in panels:
		p.paint()
		
	glDisable(GL_TEXTURE_2D)
	
	if self.temparrow != None:
		self.temparrow.paint()
		
	if self.selection != None:
		glColor4f(0.4, 0.4, 0.4, 0.3)        # grey
		glBegin(GL_POLYGON)
		glVertex2i( self.selection[0], self.selection[1] )
		glVertex2i( self.selection[0], self.selection[3] )
		glVertex2i( self.selection[2], self.selection[3] )
		glVertex2i( self.selection[2], self.selection[1] )
		glEnd()
		glColor4f(0.4, 0.4, 0.4, 1.0)
		
	# small preview of bricks
	offx = self.size.width+self.panx
	offy = self.size.height+self.pany
	
	xw = self.maxsize[2]-self.maxsize[0];
	yw = self.maxsize[3]-self.maxsize[1];

	xw23 = xw*2/3
	yw23 = yw*2/3

	glColor4f(0.4, 0.4, 0.4, 0.2)        # total view
	glBegin(GL_POLYGON)
	glVertex2i( offx+(self.maxsize[0]-xw23)/30, offy+(self.maxsize[1]-yw23)/30 )
	glVertex2i( offx+(self.maxsize[0]-xw23)/30, offy+(self.maxsize[3]-yw23)/30 )
	glVertex2i( offx+(self.maxsize[2]-xw23)/30, offy+(self.maxsize[3]-yw23)/30 )
	glVertex2i( offx+(self.maxsize[2]-xw23)/30, offy+(self.maxsize[1]-yw23)/30 )
	glEnd()
	
	glColor4f(0.4, 0.4, 0.4, 0.4) # current view
	glBegin(GL_POLYGON)
	glVertex2i( offx+(self.panx-xw23)/30, offy+(self.pany-yw23)/30 )
	glVertex2i( offx+(self.panx-xw23)/30, offy+(offy-yw23)/30 )
	glVertex2i( offx+(offx-xw23)/30, offy+(offy-yw23)/30 )
	glVertex2i( offx+(offx-xw23)/30, offy+(self.pany-yw23)/30 )
	glEnd()
	
	glColor4f(0.4, 0.4, 0.4, 0.8) # bricks
	for p in panels:
		glBegin(GL_POLYGON)
		glVertex2i( offx+(p.x-xw23)/30, offy+(p.y-yw23)/30 )
		glVertex2i( offx+(p.x-xw23)/30, offy+(p.y+p.height-yw23)/30 )
		glVertex2i( offx+(p.x+p.width-xw23)/30, offy+(p.y+p.height-yw23)/30 )
		glVertex2i( offx+(p.x+p.width-xw23)/30, offy+(p.y-yw23)/30 )
		glEnd()

	glColor4f(0.4, 0.4, 0.4, 1.0)

        self.SwapBuffers()

class CanvasDropTarget(wx.PyDropTarget):
    def __init__(self, window):
        wx.PyDropTarget.__init__(self)
        self.window = window

        self.df = wx.CustomDataFormat("CanvasDropTarget")
        self.data = wx.CustomDataObject(self.df)
        self.SetDataObject(self.data)

    def OnEnter(self, x, y, d):
        return d

    def OnLeave(self):
        pass

    def OnDrop(self, x, y):
        return True

    def OnDragOver(self, x, y, d):
        return d

    def OnData(self, x, y, d):
        if self.GetData():
            data = self.data.GetData()
            if data == "wxTreeCtrl":
                win = self.window.OnTreeLeftDClick(None)
		if win != None:
			win.x = x
			win.y = y
        return d

class MainFrame(wx.Frame):
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)
	
	self.scenename = None
	
	img = wx.Image(os.path.join(curpath, "core/icon.png"))
	self.SetIcon(self.MakeIcon(img))
	
	self.factory = node.Factory() # refactor to scene settings
	self.factory.setName("test123") # should be the scene settings?
	
        self.dividerPanel = wx.Panel(self, -1, style=wx.BORDER_NONE)
	self.dividerPanel.SetSizeHints(6, -1, 6, -1) #minw, minh, maxw, maxh
	
	if wx.Platform == "__WXMAC__": # should be adjustable from the settings...
		bgColor = wx.Color(240, 240, 240)
	else:
		bgColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
	
	lhsv = node_draw.RGBtoHSV(bgColor.Get())
	lhsv[2] -= 20
	lrgb = node_draw.HSVtoRGB(lhsv)
	lcolor = wx.Colour(lrgb[0], lrgb[1], lrgb[2])
	
	self.dividerPanel.SetBackgroundColour(lcolor)	
	
	self.c = NodeCanvas(self)
	
	self.tree = wx.TreeCtrl(self, -1, style = wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_NO_LINES | wx.TR_FULL_ROW_HIGHLIGHT | wx.BORDER_NONE)
	self.tree.SetDimensions(0, 0, 160, -1)
	self.tree.SetSizeHints(160, -1, -1, -1) #minw, minh, maxw, maxh	

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il

	self.tree.SetBackgroundColour(bgColor)
	self.tree.Refresh(True)
	
        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnTreeLeftDClick)
	
	self.ID_ACTION = wx.NewId()
	self.ID_VIEWCODE = wx.NewId()
	self.ID_IMMEDIATEUPDATE = wx.NewId()
	self.ID_MODEPREFERENCES = wx.NewId()
	self.ID_LAYOUTNODES = wx.NewId()
	
	self.modeMenus = {}
	
	self.brickMenu = None
	self.brickMenuArr = {}
	
	self.currentMode = "Renderman SL" # should load from the settings
        self._setMenu()
	self.ActuallySwitchMode()

	aTable = wx.AcceleratorTable([
				(wx.ACCEL_NORMAL, wx.WXK_F9, self.ID_ACTION),
				(wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),
				(wx.ACCEL_CTRL, ord('S'), wx.ID_SAVE),
				(wx.ACCEL_CTRL, ord('N'), wx.ID_NEW),
				(wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN),
				(wx.ACCEL_CTRL, ord('A'), wx.ID_SELECTALL),
				])
				
	self.SetAcceleratorTable(aTable)
	
	self.pform = PropertiesFrame(self)
	
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.tree, 0, wx.EXPAND)
        self.sizer.Add(self.dividerPanel, 0, wx.EXPAND)
        self.sizer.Add(self.c,  1, wx.EXPAND)
        self.SetSizer(self.sizer)
	self.sizer.Layout()
	
	self.sx = 0
	
	self.dividerPanel.Bind(wx.EVT_LEFT_DOWN, self.OnSMouseDown)
        self.dividerPanel.Bind(wx.EVT_LEFT_UP, self.OnSMouseUp)
        self.dividerPanel.Bind(wx.EVT_MOTION, self.OnSMouseMotion)
	
	self.Bind(wx.EVT_SIZE, self.OnSize)
	self.Bind(wx.EVT_SHOW, self.OnSize)
	self.Bind(wx.EVT_MOVE, self.OnMove)
        #self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
	self.Bind(wx.EVT_WINDOW_DESTROY, self.OnCleanup)
	
	self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self._startDrag)
        
	dt = CanvasDropTarget(self)
        self.c.SetDropTarget(dt)
	
    def _startDrag(self, event):
	    
        button = event.GetEventObject()
        item = event.GetItem()
        tree = event.GetEventObject()

        df = wx.CustomDataFormat("CanvasDropTarget")
        ldata = wx.CustomDataObject(df)
        ldata.SetData(str(button.GetName()))
        dropSource = wx.DropSource(self)
        dropSource.SetData(ldata)
        result = dropSource.DoDragDrop(True)
	
    def OnSMouseDown(self, evt):
        self.dividerPanel.CaptureMouse()
        self.sx, y = evt.GetPosition()
	evt.Skip()

    def OnSMouseUp(self, evt):
	if self.dividerPanel.HasCapture():
		self.dividerPanel.ReleaseMouse()
        self.sx, y = evt.GetPosition()
	evt.Skip()

    def OnSMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            x, y = evt.GetPosition()
	    w, h = self.GetClientSizeTuple()
	    cw, ch = self.tree.GetClientSizeTuple()
	    if cw+x-self.sx>120:
		self.tree.SetSizeHints(cw+x-self.sx, -1, -1, -1) #minw, minh, maxw, maxh
	    	self.sizer.Layout()
	evt.Skip()	
	
    def OnCleanup(self, event):
	del self.filehistory
	
    def ActuallySwitchMode(self):
	# check if menu is switched
	for mid, mmenu in self.modeMenus.items():
		if mmenu.GetLabel() == self.currentMode:
			if not (mmenu.IsChecked()):
				mmenu.Check(True)
			
	#root = opj('%s/modes/%s/nodes' % (os.getcwd(), self.currentMode))
	root = opj('%s/modes/%s/nodes' % (curpath, self.currentMode))
	
	if self.brickMenu != None:
		del self.brickMenu
		
	self.brickMenu = wx.Menu()
	item = wx.MenuItem(self.brickMenu, -1, "Insert node:")
	self.brickMenu.AppendItem(item)
	item.Enable(False)
	self.brickMenu.AppendSeparator()
	
	self.tree.Freeze()
	self.tree.DeleteAllItems()
	
	self.brickMenuArr.clear()
	
	self.treeids = {root : self.tree.AddRoot(root)}
	self.root = self.treeids[root]
	self.tree.SetPyData(self.root, root)
	
	for (dirpath, dirnames, filenames) in os.walk(root):
		if dirpath.find(".svn") == -1:
			for dirname in dirnames:
				if dirname.find(".svn") == -1:
					fullpath = os.path.join(dirpath, dirname)
					self.treeids[fullpath] = self.tree.AppendItem(self.treeids[dirpath], dirname)
					self.tree.SetPyData(self.treeids[fullpath], fullpath)
					self.tree.SetItemImage(self.treeids[fullpath], self.fldridx, wx.TreeItemIcon_Normal)
					self.tree.SetItemImage(self.treeids[fullpath], self.fldropenidx, wx.TreeItemIcon_Selected)
			#for filename in sorted(filenames): # removed for Python 2.3 compatibility
			
			fmenu = wx.Menu()
			
			for filename in filenames:
				if filename.endswith(".br"):
					i = self.tree.AppendItem(self.treeids[dirpath], filename.replace(".br", ""))
					self.tree.SetPyData(i, "%s%s%s" % (dirpath, os.path.sep, filename))
					self.tree.SetItemImage(i, self.fileidx, wx.TreeItemIcon_Normal)
					self.tree.SetItemImage(i, self.fileidx, wx.TreeItemIcon_Selected)
					nid = wx.NewId()
					if dirpath==root:
						self.brickMenu.Append(nid, filename.replace(".br", ""))
					else:
						fmenu.Append(nid, filename.replace(".br", ""))
					self.brickMenuArr[nid] = os.path.join(dirpath, filename)
					self.Bind(wx.EVT_MENU, self.OnNewBrickContextMenu, id=nid)
			
			if dirpath!=root:		
				self.brickMenu.AppendMenu(-1, dirpath.replace(root+os.path.sep, ""), fmenu)

        try:
		self.tree.Expand(self.root)
	except:
		pass
		
	self.tree.Thaw()
	self.tree.Refresh(True)

    def OnNewBrickContextMenu(self, event):
	newname = self.brickMenuArr[event.GetId()]
	
	node1 = node.Node(GetNextNodeID(), newname, factory = self.factory)
	nodes.append(node1)
		
	pnl = NodePanel(self, x = 20 + self.c.panx, y = 20 + self.c.pany)
	panels.append(pnl)
		
	pnl.assignNode(node1)
	self.c.Refresh(False)

	#event.Skip()

    def _setMenu(self):
        self.mainmenu = wx.MenuBar()
        menu1 = wx.Menu()
        
        menu1.Append(wx.ID_NEW, "New")
        menu1.AppendSeparator()
	menu1.Append(wx.ID_OPEN, "Open...")
        menu1.Append(wx.ID_SAVE, "Save")
	menu1.Append(wx.ID_SAVEAS, "Save as...")
        if wx.Platform != "__WXMAC__":
	        menu1.AppendSeparator()
        menu1.Append(wx.ID_PREFERENCES, "Preferences...")
        if wx.Platform != "__WXMAC__":
		menu1.AppendSeparator()
	menu1.Append(wx.ID_EXIT, "Exit")
        self.mainmenu.Append(menu1, "&File")
	
	self.filehistory = wx.FileHistory()
        self.filehistory.UseMenu(menu1)
	self.Bind( wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9 )

        menu3 = wx.Menu()
        #menu3.Append(wx.ID_UNDO, "Undo")
        #menu3.Append(wx.ID_REDO, "Redo")
        #menu3.AppendSeparator()
        #menu3.Append(wx.ID_CUT, "Cut")
        #menu3.Append(wx.ID_COPY, "Copy")
        #menu3.Append(wx.ID_PASTE, "Paste")
        menu3.Append(wx.ID_DELETE, "Delete")
        menu3.AppendSeparator()
        menu3.Append(wx.ID_SELECTALL, "Select all")
        #menu3.AppendSeparator()
        #menu3.Append(self.ID_LAYOUTNODES, "Layout nodes")
	
        self.mainmenu.Append(menu3, "&Edit")

        menu4 = wx.Menu()
        menu4.Append(self.ID_ACTION, "Render")
	menu4.Append(self.ID_VIEWCODE, "View generated code")
        menu4.AppendSeparator()
	self.c.CUpdateMenuItem = wx.MenuItem(menu4, self.ID_IMMEDIATEUPDATE, "Continuous update", kind=wx.ITEM_CHECK)
	menu4.AppendItem(self.c.CUpdateMenuItem)
        self.mainmenu.Append(menu4, "&Action!")

	# dynamic menu...
	menud = wx.Menu()
	
	#directories = filter(lambda x: os.path.isdir(x), sorted(glob.glob(opj('%s/modes/*' % os.getcwd()))))
	# removed for Python 2.3 compatibility
	directories = filter(lambda x: os.path.isdir(x), glob.glob(opj('%s/modes/*' % curpath)))
	directories = map(lambda y: os.path.split(y)[1] , directories)
	
	for d in directories:
		nid = wx.NewId()
		#dd = d.replace(opj('%s/modes/' % os.getcwd()), "")
		dd = d
	        item = wx.MenuItem(menud, nid, dd, kind = wx.ITEM_RADIO)
        	menud.AppendItem(item)
		self.modeMenus[nid] = item
		if dd == self.currentMode:
			item.Check(True)
	        self.Bind(wx.EVT_MENU, self.OnSwitchMode, id=nid)
	
        menud.AppendSeparator()
	menud.Append(self.ID_MODEPREFERENCES, "Mode preferences...")
        self.Bind(wx.EVT_MENU, self.OnModePreferences, id=self.ID_MODEPREFERENCES)
	
        self.mainmenu.Append(menud, "&Mode")

	# end

        menu2 = wx.Menu()
        menu2.Append(wx.ID_HELP, "Help")
        #menu2.AppendSeparator()
        menu2.Append(wx.ID_ABOUT, "About...")
        self.mainmenu.Append(menu2, "&Help")
        
        self.SetMenuBar(self.mainmenu)

        if wx.Platform == "__WXMAC__":
            wx.App.SetMacAboutMenuItemId(wx.ID_ABOUT)
            wx.App.SetMacPreferencesMenuItemId(wx.ID_PREFERENCES)

        '''
            add an handler for verify things on
            menu items opening
        '''
        #if wx.Platform in ['__WXMSW__','__WXGTK__']:
            #self.Bind( wx.EVT_MENU_OPEN,  self.onMainMenuOpen )
            #self.Bind( wx.EVT_MENU_CLOSE, self.onMainMenuClose )

        # FILE MENU
        self.Bind(wx.EVT_MENU,  self.OnNewDocument, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU,  self.OnOpenDocument, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU,  self.OnSaveDocument, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU,  self.OnSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU,  self.OnExit, id=wx.ID_EXIT)
	
        self.Bind(wx.EVT_MENU,  self.OnAction, id=self.ID_ACTION)
	self.Bind(wx.EVT_MENU,  self.OnImmediateUpdate, id=self.ID_IMMEDIATEUPDATE)
	self.Bind(wx.EVT_MENU,  self.OnViewGeneratedCode, id=self.ID_VIEWCODE)
	
	self.Bind(wx.EVT_MENU,  self.OnPreferences, id=wx.ID_PREFERENCES)
	#self.Bind(wx.EVT_MENU,  self.OnLayoutNodes, id=self.ID_LAYOUTNODES)
	
	# file history binding
        #self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE1 + 19)

	## EDIT MENU
        #self.Bind(wx.EVT_MENU, self.OnUndo, id=wx.ID_UNDO)
        #self.Bind(wx.EVT_MENU, self.OnRedo, id=wx.ID_REDO)
        self.Bind(wx.EVT_MENU, self.OnDelete, id=wx.ID_DELETE)
	self.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)

        ## HELP MENU
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        #self.Bind(wx.EVT_MENU, self.OnCheckVersion, id=ID_CHECK_VERSION)
	
    def OnLayoutNodes(self, event): # apparently, doesn't work as expected
	import core.topo
	
	#nodes = ['root', 'diff', 'spec', 'op', 'n1', 'n2']
	#route = [('diff', 'root'), ('spec', 'root'), ('n1', 'op'), ('op','diff'), ('n2','root')]
	
	#nodes = [ p.node.id for p in panels ]
	#route = [ (a.connection.inputNode.id, a.connection.outputNode.id) for a in arrows ]
	
	nodes = [ p.node for p in panels ]
	route = [ (a.connection.inputNode, a.connection.outputNode) for a in arrows ]
	
	#print nodes
	#print route
	
	sorted = core.topo.toposort(nodes, route)
	for row in sorted:
		print ">",
		for item in row:
			print item.id,
		print ""
		
	MARGIN = 200
	
	counter = 0
	for row in sorted:
		x = counter*MARGIN
		y = 0
		for item in row:
			item.panel.x = x
			item.panel.y = y
			y += item.panel.height + 20
		counter += 1
	
	self.c.Refresh()
	event.Skip()
	
    def OnPreferences(self, event):
	import core.prefs_window as prefs
	
	if wx.Platform == "__WXMAC__":
		deffontsize = 12
	else:
		deffontsize = 10
	
	curfontsize = settings.get("fontsize", str(deffontsize))
	#self.preferences = [{'default': curfontsize, 'name': u'Font Size'}, {'default': u'prman', 'name': u'Font Name'}]
	self.preferences = [{'default': curfontsize, 'name': u'Font Size'}]
	
	dlg = prefs.PropertiesFrame(None, self.preferences, title = "ShaderMan preferences")
	dlg.Bind(wx.EVT_CLOSE, self.SavePreferences)
	dlg.Show()
	
    def SavePreferences(self, event):
	for s in self.preferences:
		if s["name"] == "Font Size":
			settings['fontsize'] = s["default"]
		#if s["name"] == "Font Name":
			#settings['fontname'] = s["default"]
			
	InitNodeDraw()
	for obj in panels+arrows:
		obj.refreshFont()
	
	self.c.Refresh(True)

	event.Skip()

    def OnViewGeneratedCode(self, event): # code dublicated from OnAction
	imported = __import__("modes.%s" % self.currentMode, globals(), locals(), ("name", "generator"))

	rootnodes = filter(self.findRootNode, nodes) # can be selected mode as well?

	if len(rootnodes):
		cg = rootnodes[0].GenerateCode()
		print cg[0]
	
    def OnModePreferences(self, event):
	imported = __import__("modes.%s" % self.currentMode, globals(), locals(), ("preferences"))
	try:
		imported.preferences()
	except: # module doesn't require preferences or they're not implemented yet
		wx.MessageBox("This module doesn't provide the preferences to edit", "Nothing to do",  wx.ICON_INFORMATION)
	
    def OnFileHistory(self, event):
	temp = self.filehistory.GetHistoryFile(event.GetId() - wx.ID_FILE1)
	if os.path.exists(temp):
		self.scenename = temp
		self.JustLoadTheData()
		self.SetTitle("%s - %s" % (self.scenename, productname))
		self.filehistory.AddFileToHistory(self.scenename)
		self.UpdateFileHistoryArray()
	else:
		wx.MessageBox("Scene file %s not found." % temp, "Nothing to do",  wx.ICON_INFORMATION)

    def OnImmediateUpdate(self, event):
	pass

    def OnSwitchMode(self, event):
	self.currentMode = self.modeMenus[event.GetId()].GetLabel()
	self.ActuallySwitchMode()
	self.OnNewDocument(None)
	event.Skip()
	
    def findRootNode(self, x):
	return (x.code != "")
    
    def OnAction(self, event):
	imported = __import__("modes.%s" % self.currentMode, globals(), locals(), ("name", "generator"))
	
	rootnodes = filter(self.findRootNode, nodes)
	
	filename = self.factory.getName()
	
	if len(rootnodes):
		cg = rootnodes[0].GenerateCode()
		imported.generator(self, filename, cg[0])

    def OnSelectAll(self, event):
	del self.c.markedPanels[:]
	self.c.markedPanels = [p for p in panels]
	self.c.Refresh(True)
	
    def OnDelete(self, event):
	connectedArrows = []
	for pnl in self.c.markedPanels:
		node = pnl.node
		# find connected arrows
		for a in arrows:
			if (a.connection.inputNode == pnl.node) or (a.connection.outputNode == pnl.node):
				try:
					i = connectedArrows.index(a)
				except:
					connectedArrows.append(a)
		SafelyDelete(panels, pnl)
		del pnl
		
		SafelyDelete(nodes, node)
		del node
	del self.c.markedPanels[:]
	#delete connected arrows
	for a in connectedArrows:
		self.c.ActuallyDeleteConnection(a.connection)
	
	self.c.Refresh(False)

    def OnAbout(self, event):
	import core.about as about
	dlg = about.AboutBox(self)
	dlg.ShowModal()
	dlg.Destroy()

    def OnHelp(self, event):
	pass

    def OnNewDocument(self, event):
	self.scenename = None
	del arrows[:]
	del connections[:]
	del panels[:]
	del nodes[:]
	node.Node._instance_count = 0
	node.Connection._instance_count = 0
	self.c.Refresh(False)

    def JustLoadTheData(self):
	del arrows[:]
	del connections[:]
	del panels[:]
	del nodes[:]
	
	res = False
	
	try:
		f = open(self.scenename, 'r')
		
		# simple sandbox protection
		import copy
		
		gg = globals()
		ll = locals()
		
		ng = copy.copy(gg)
		nc = copy.copy(ll)
		
		try:
			del ng['os'] # we're not allowing os module in files we're loading...
		except:
			pass
		
		exec(f, ng, nc)
		f.close()
		
		del ng
		del nc
		
		res = True
	finally:
		self.c.Refresh(False)
		return res
    
    def OnOpenDocument(self, event):
    	wildcard = "ShaderMan scenes|*.smn|All files (*)|*"
	dlg = wx.FileDialog( self, message="Load scene", defaultDir=os.getcwd(), defaultFile="", wildcard=wildcard, style=wx.OPEN )
	
	if dlg.ShowModal() == wx.ID_OK:
		self.scenename = dlg.GetPath()
		self.JustLoadTheData()
		self.SetTitle("%s - %s" % (self.scenename, productname))
		self.filehistory.AddFileToHistory(self.scenename)
		self.UpdateFileHistoryArray()

	dlg.Destroy()
    
    def JustSaveTheData(self):
	f = open(self.scenename, 'w')
	
	print >>f, """self.currentMode = "%s"\nself.ActuallySwitchMode()\n""" % self.currentMode

	print >>f, "\n".join([str(thing) for thing in nodes+panels+connections+arrows])
		
	f.flush()
	f.close()
    
    def OnSaveDocument(self, event):
	if self.scenename == None:
		self.OnSaveAs(event)
	else:
		self.JustSaveTheData()
    
    def OnSaveAs(self, event):
    	wildcard = "ShaderMan scenes|*.smn|All files (*)|*"
	dlg = wx.FileDialog( self, message="Save scene", defaultDir=os.getcwd(), defaultFile="test.smn", wildcard=wildcard, style=wx.SAVE ) 
	# should be factory.name?

	if dlg.ShowModal() == wx.ID_OK:
		self.scenename = dlg.GetPath()
		self.JustSaveTheData()
		self.SetTitle("%s - %s" % (self.scenename, productname))

	dlg.Destroy()
    
    def OnTreeLeftDClick(self, event):
	itemid = self.tree.GetSelection()
	fullpath = self.tree.GetPyData(itemid)
	pnl = None
	if fullpath.endswith(".br"): # isn't directory or something
		node1 = node.Node(GetNextNodeID(), fullpath, factory = self.factory)
		nodes.append(node1)
		
		pnl = NodePanel(self, x = 20 + self.c.panx, y = 20 + self.c.pany)
		panels.append(pnl)
		
		pnl.assignNode(node1)
		self.c.Refresh(False)

	if event != None:
		event.Skip()
	
	return pnl
	
    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnExit(self, event):
	self.pform.Close()
	del self.pform
        self.Close()
	
    def OnSize(self, event):
	ws, hs = self.GetSize()
	settings['width'] = ws
	settings['height'] = hs
	event.Skip()
	
    def OnMove(self, event):
	x, y = self.GetPosition()
	settings['left'] = x
	settings['top'] = y
	event.Skip()

    def MakeIcon(self, img):
        """
        The various platforms have different requirements for the
        icon size...
        """
        if "wxMSW" in wx.PlatformInfo:
            img = img.Scale(16, 16)
        elif "wxGTK" in wx.PlatformInfo:
            img = img.Scale(22, 22)
        # wxMac can be any size upto 128x128, so leave the source img alone....
        icon = wx.IconFromBitmap(img.ConvertToBitmap() )
        return icon
    
    def UpdateFileHistoryArray(self):
	history = []
	for i in range(self.filehistory.GetCount()):
            history.append(self.filehistory.GetHistoryFile(i))
	    
        settings['history'] = ",".join(history)
	
def LoadSettings():
	filename = os.path.expanduser("~/.ShaderMan")
	if os.path.isfile(filename):
		raw_settings = open(filename).readlines()
		for line in raw_settings:
			a = line.strip().split("=")
			settings[a[0]] = a[1]
    
def SaveSettings():
	filename = os.path.expanduser("~/.ShaderMan")
	h = open(filename, 'w')
	
	for key in settings.keys():
		line = "%s=%s\n" % (key, settings[key])
		h.write(line)
	
	h.close()
	
if __name__ == '__main__':
    
    	LoadSettings()
    
	app = wx.PySimpleApp(redirect=False, useBestVisual=True)
        app.SetUseBestVisual(True)
	frm = MainFrame(None, productname)
	
	InitNodeDraw()
	
	w = int(settings.get("width", 600))
	h = int(settings.get("height", 700))
	x = min(int(settings.get("left", 0)), wx.SystemSettings_GetMetric( wx.SYS_SCREEN_X )-w) # because we want to see it on the screen
	y = min(int(settings.get("top", 0)), wx.SystemSettings_GetMetric( wx.SYS_SCREEN_Y )-h)
	
	history = settings.get("history", None)
	if history != None:
		for hh in history.split(","):
			frm.filehistory.AddFileToHistory(hh)
	
	frm.SetSize((w,h))
	frm.SetPosition((x, y))
	frm.Show()
	app.SetTopWindow(frm)
	
	if len(sys.argv)>1:
		frm.scenename = sys.argv[1]
		frm.JustLoadTheData()
		frm.SetTitle("%s - %s" % (frm.scenename, productname))
		frm.filehistory.AddFileToHistory(frm.scenename)
		frm.UpdateFileHistoryArray()
	
	app.MainLoop()

	SaveSettings()
