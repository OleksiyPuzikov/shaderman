import os
import subprocess

def name():
	return "Unix"
  
def generator(self, filename, code):
	print code
	#code = "bash -c '%s'" % code
	#os.system(code)
	#pipe = subprocess.Popen(code, shell=True, stdout=subprocess.PIPE).stdout
	#buffer = str("".join(pipe.readlines()))
	#print buffer
	#print `pwd`
	p = subprocess.Popen([code], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	sts = os.waitpid(p.pid, 0)
	buffer = str("".join(p.stdout.readlines()+p.stderr.readlines()))
	print buffer