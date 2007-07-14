import PIL.Image
#import PIL.ImageDraw2
import inspect

tpl = """<?xml version="1.0"?>
<node name="Image.%s" author="Alexei Puzikov, http://www.dream.com.ua">
 <help>%s</help>
 <in>
  <param name="inp" type="variant" />%s
 </in>
 <out>
  <param type="variant" name="outp">${inp}.%s(%s)</param>
</out>
</node>
"""


in_tpl = """  <param name="%s" type="variant" default="%s" />"""
f_tpl = "${%s}"

placeholder = None

#for name, mm in inspect.getmembers(PIL.Image.Image):
id2 = __import__("PIL.ImageDraw2", globals(), locals(), ("Draw"))
for name, mm in inspect.getmembers(PIL.ImageDraw2.Draw):
    #print name
    if inspect.ismethod(mm):
	if name.startswith("_"):
		continue
        print name
	in_params = ""
	in_fparams = ""
	params, varargs, varkw, defaults = inspect.getargspec(mm.im_func)
	params.pop(0)
	
	# By filling up the default tuple, we now have equal indeces for args and default.
	if defaults is not None:
		defaults = (placeholder,)*(len(params)-len(defaults)) + defaults
	else:
		defaults = (placeholder,)*len(params)
		
	#print defaults	
		
	in_params = "\n".join([in_tpl % (p, d.__repr__()) for p,d in zip(params, defaults)])
	in_fparams = ", ".join([f_tpl % (p) for p in params])
	
	if len(in_params):
		in_params = "\n"+in_params
	
	template = tpl % (name, mm.__doc__, in_params, name, in_fparams)
	
	f = open("nodes/ImageDraw2/%s.br" % name, 'w')
	
	print >>f, template
		
	f.flush()
	f.close()

	
	#print template