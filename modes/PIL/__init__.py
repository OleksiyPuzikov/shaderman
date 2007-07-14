import os
def name():
	return "PIL"
  
def generator(self, filename, code):
	outf = open(filename+".py", "w")
	print >>outf, code
	outf.close()
	
	os.system("python %s.py" % filename)
	print "successful"