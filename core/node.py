""" Defines the non-visual part of core: Node and Connection classes, as well as all the code generation and Factory class (now disfunctional).
"""

import os
from mako.template import Template
import logging
from core.utils import *

#logging.basicConfig(level=logging.DEBUG)

class Factory:
	""" Some time in the future I'll refactor all the Factory code to something more useful. It's mostly a stub now, left from my early experiments. """
	def __init__(self):
		self._name = ""
		self.values = []
		
	def getName(self):
		return self._name
	
	def setName(self, value):
		self._name = value
		
	def getValue(self, name, default):
		return default
	
	def setValue(self, name, value):
		self.values[name] = value
		
	def clearValues(self):
		del self.values
		self.values = []
		
	def get(self, what):
		return ""
	

class Connection:
	""" Non-visual connection between the Nodes/Bricks. """
	def __init__(self, id):
		self.id = str(id)
	
		self.inputNode = None
		self.inputName = ""
		self.outputNode = None
		self.outputName = ""
		self.arrow = None
		
	def assignInput(self, inputNode, inputName):
		self.inputNode = inputNode
		self.inputName = inputName
		if self.inputNode.out_connections.get(self.inputName, None) == None:
			self.inputNode.out_connections[self.inputName] = []
		self.inputNode.out_connections[self.inputName].append(self)

	def assignOutput(self, outputNode, outputName):
		self.outputNode = outputNode
		self.outputName = outputName
		prev = self.outputNode.in_connections.get(self.outputName, None)
		self.outputNode.in_connections[self.outputName] = self
		return prev
		
	def SaveState(self):
		return """connection%s = node.Connection(GetNextConnectionID())\nconnections.append(connection%s)\nconnection%s.assignInput(node%s, "%s")\nconnection%s.assignOutput(node%s, "%s")\n""" % (self.id, self.id, self.id, self.inputNode.id, self.inputName, self.id, self.outputNode.id, self.outputName)


class Node:
	""" The main code for everything you'll see in this project. """
	def __init__(self, id, filename="", factory = None):
		self.id = str(id)
		
		self.filename = filename
		self.smallfilename = self.filename.replace(opj(os.getcwd()+"/"), "")
		self.name = ""
		self.author = ""
		self.help = ""
		
		self.code = ""
		self.precode = ""
		self.header = ""
		
		self.codebackup = "" # this one for the case when somebody will edit the code using UI
		self.precodebackup = ""
		
		self.factory = factory
		
		self.panel = None
		
		self.in_params = []
		self.in_connections = {} # dict of input connections
		self.out_params = []
		self.out_connections = {} # given there might be multiple outputs from single slot, this one is dict of arrays of output connections
		if ("" != filename):
			self.LoadFromFile(filename)

	def LoadFromFile(self, filename):
		logging.info(filename)
		self.filename = filename
		self.smallfilename = self.filename.replace(opj(os.getcwd()+"/"), "")
		self.ParseLoadedCode()
		
	def SaveState(self): # serialize the state into file
		s = """node%s = node.Node(GetNextNodeID(), "%s", factory = self.factory)\nnodes.append(node%s)\n""" % (self.id, self.smallfilename.replace("\\", "/"), self.id)
		for i in self.in_params:
			if i["backup"] != i["default"]:
				s += """node%s.setInputDefault("%s", "%s")\n""" % (self.id, i["name"], i["default"])
		if self.code != self.codebackup:
			s += "node%s.code = \"\"\"%s\"\"\"\n" % (self.id, self.code)
		if self.precode != self.precodebackup:
			s += "node%s.precode = \"\"\"%s\"\"\"\n" % (self.id, self.precode)
		return s
	
	def GenerateCodeAsRoot(self, slot=""):
		self.GenerateCode(slot)
		
	def setInputDefault(self, name, newvalue):
		for i in self.in_params:
			if i["name"] == name:
				i["default"] = newvalue
	
	def GenerateCode(self, slot=""):
		# code generation parameters initialization
		if slot != "": # non-root node
			for i in self.out_params:
				if i["name"] == slot:
					code = i["code"]
		else:
			code = self.code
		
		gatherheader = []
		gatherprecode = []
		
		# pass over all the connections
		results = {}
		for inp in self.in_params:
			pname = str(inp["name"])
			connection = self.in_connections.get(pname, None)
			if (connection != None): # there's connection
				(results[pname], h, p) = connection.inputNode.GenerateCode(connection.inputName)
				gatherheader = gatherheader+h
				gatherprecode = gatherprecode+p
			else:
				if self.factory:
					results[pname] = self.factory.getValue(pname, str(inp["default"])) # might return something different in the future
				else:
					results[pname] = str(inp["default"])
		
		codetemplate = Template(code.replace("#", self.id))
		
		if slot != "": # non-root node
			headertemplate = Template(self.header.replace("#", "\#"))
			precodetemplate = Template(self.precode.replace("#", self.id))
			
			return (codetemplate.render(**results), 
				gatherheader+[headertemplate.render(**results).replace("\#", "#")], 
				gatherprecode+[precodetemplate.render(**results)])
			
		else:
			# cleanup gather arrays from dublicates
			gatherheader = uniq(gatherheader)
			gatherprecode = uniq(gatherprecode)
			
			results["header"] = "\n".join(gatherheader)
			results["precode"] = "\n".join(gatherprecode)
			
			if self.factory:
				results["shadername"] = self.factory.getName()
			else:
				results["shadername"] = ""
				
			if self.factory:
				results["shaderparams"] = self.factory.get("shaderparams")
			else:
				results["shaderparams"] = ""
			
			return (codetemplate.render(**results), '', '')
			
	def SafeGetXMLData(self, node, what):
		temp = node.getElementsByTagName(what)
		if len(temp)>0:
			return temp[0].childNodes[0].data
			logging.info(what)
		else:
			return ""
	
	def ParseLoadedCode(self):
		import xml.dom.minidom as mdom
		parsed = mdom.parse(self.filename) # TODO: exception handling
		node = parsed.getElementsByTagName("node")[0]
		
		self.name = node.attributes.get("name").value.strip()
		logging.info(self.name)
		
		self.author = node.attributes.get("author").value.strip()
		logging.info(self.author)
		
		self.help = self.SafeGetXMLData(node, "help")
		
		ins = node.getElementsByTagName("in")
		if len(ins)>0:
			params = ins[0].getElementsByTagName("param")
			attributes = ["name", "type", "default", "hint"]
			for i in params:
				t = {}
				for attr in attributes:
					a = i.attributes.get(attr)
					if a:
						t[attr] = a.value.strip()
					else:
						t[attr] = "" # TODO should be type-dependable, like, "color(0)" or "float(0)" etc
							     # if there's no type == abort
				t["backup"] = t["default"] # we need this to be able to see whenever the default value is changed
				self.in_params.append( t )
		logging.info(self.in_params)
		
		outs = node.getElementsByTagName("out")
		if len(outs)>0:
			params = outs[0].getElementsByTagName("param")
			attributes = ["name", "type", "default"]
			for i in params:
				t = {}
				for attr in attributes:
					a = i.attributes.get(attr)
					if a:
						t[attr] = a.value.strip()
					else:
						t[attr] = ""
				t["code"] = i.childNodes[0].data
			self.out_params.append( t )
		logging.info(self.out_params)
		
		self.code = self.SafeGetXMLData(node, "code")
		self.precode = self.SafeGetXMLData(node, "precode")
		self.header = self.SafeGetXMLData(node, "header")
		
		self.codebackup = self.code
		self.precodebackup = self.precode
		
if __name__ == '__main__':
		pass # move the test code here?
