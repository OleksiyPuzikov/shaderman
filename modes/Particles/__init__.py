import os

def name():
	return "Particles"

def generator(self, filename, code):
	from core.utils import good_path

	outf = open("%s/%s.py" % (__path__[0], filename), "w")
	print >>outf, code
	outf.close()
	
	os.system("python %s/%s.py" % (__path__[0], filename))