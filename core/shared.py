""" 
A couple of global variables and functions shared by main application and some of the core modules.

"""

panels = []
arrows = []

nodes = []
connections = []

groups = []

settings = {}

import warnings

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

@deprecated
def GetNextNodeID(): # those are deprecated
	pass

@deprecated
def GetNextConnectionID():
	pass
