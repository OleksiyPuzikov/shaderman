import os
import wx

try:
	set = __import__("settings", globals(), locals(), ("settings"))
	# Actually, storing the settings inside the application source code seems like a bad idea.
	# Just think of all those SVN submissions people will be making, overriding the default rendering settings...
	# Well...
	# We'll fix that later.
except:
	set = None

def name():
	return "Renderman SL"

def preferences():
	if set != None:
		import core.prefs_window as prefs
		dlg = prefs.PropertiesFrame(None, set.settings, title = "Renderman SL mode preferences")
		dlg.Bind(wx.EVT_CLOSE, SaveSettings)
		dlg.Show()
	else:
		wx.MessageBox("Preferences file is corrupted.\nPlease restore from original redistributive or backup.", "Nothing to do",  wx.ICON_ERROR);
	
def SaveSettings(event):
	f = open("%s/settings.py" % __path__[0], 'w') # write down the new settings...
	print >>f, "settings = %s" % set.settings
	f.flush()
	f.close()
	event.Skip()
  
def generator(self, filename, code):
	try:
		os.unlink("%s.sl*" % filename) # delete previous version and compiled shader
	except:
		pass	
	
	outf = open(filename+".sl", "w")
	print >>outf, code
	outf.close()
	
	# default values
	shader = "shader"
	prman = "prman"
	
	# now load from the settings...
	for s in set.settings:
		if s["name"] == "ShaderCompiler":
			shader = s["default"]
		if s["name"] == "Renderer":
			prman = s["default"]
	
	os.system("%s %s.sl" % (shader, filename))
	
	from mako.template import Template
	results = {}
	previewtemplate = Template("".join(open("modes/Renderman SL/preview.rib").readlines()))
	results["shadername"] = self.factory.getName() # this will be refactored
	preview = previewtemplate.render(**results)
	
	#outf = open(filename+".rib", "w")
	#print >>outf, preview
	#outf.close()
	
	#os.system("prman -progress %s.rib" % filename)
	
	import subprocess
	pipe = subprocess.Popen("%s -progress" % prman, shell=True, stdin=subprocess.PIPE).stdin
	print >>pipe, preview
	pipe.close()