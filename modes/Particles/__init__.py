import os

def name():
	return "Particles"

def generator(self, filename, code):
	from core.utils import good_path

	outf = open("%s/%s.py" % (__path__[0], filename), "w")
	print >>outf, code
	outf.close()
	
	import subprocess
	p = subprocess.Popen("python %s/%s.py" % (__path__[0], filename), shell=True)