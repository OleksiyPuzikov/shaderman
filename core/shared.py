""" 
A couple of global variables and functions shared by main application and some of the core modules.

"""

panels = []
arrows = []

nodes = []
connections = []

settings = {}

def GetNextNodeID():
	try:
		return max([int(node.id) for node in nodes])+1
	except:
		return 1

def GetNextConnectionID():
	try:
		return max([int(connection.id) for connection in connections])+1
	except:
		return 1
