""" A couple of simple tools I'm using everywhere. """

import os
import inspect
import sys

def good_path(filename, remove=os.path.sep+"core"):
	"""This will return the path to related filename"""
	#print os.path.dirname(inspect.getfile(sys._getframe(1))).replace(remove, "")
	return os.path.join(os.path.dirname(inspect.getfile(sys._getframe(1))).replace(remove, ""), filename)
	
def good_node_filename(filename):
	"""This should be probably moved to node class... We'll see"""
	parts = filename.split(os.path.sep)
	if parts.index("modes") == -1:
		return filename
	else:
		return os.path.sep.join(parts[parts.index("modes"):])

def uniq(alist):
    """ Fastest order preserving doublicates removal from arrays. """
    set = {}
    return [set.setdefault(e,e) for e in alist if e not in set]

def opj(path):
    """Convert paths to the platform-specific separator"""
    str = apply(os.path.join, tuple(path.split('/')))
    if path.startswith('/'):     # HACK: on Linux, a leading / gets lost...
        str = '/' + str
    return str

def SafelyDelete(array, topic):
    """  Safe removal of item from array """
    try:
	array.remove(topic)
    except:
	pass

def RGBtoHSV(rgb):
    hsv = [0,0,0]
    trgb = list(rgb)
    trgb.sort()

    min = trgb[0]
    max = trgb[2]

    delta = float(max - min)
    hsv[2] = max

    if delta == 0:
        # r = g = b = 0        # s = 0, v is undefined
        hsv[1] = 0
        hsv[0] = -1
    else:
        hsv[1]=delta / max

        if rgb[0] == max:
            hsv[0] = (rgb[1] - rgb[2]) / delta        # between yellow & magenta
        elif rgb[1] == max:
            hsv[0] = 2 + (rgb[2] - rgb[0] ) / delta    # between cyan & yellow
        else:
            hsv[0] = 4 + (rgb[0] - rgb[1] ) / delta    # between magenta & cyan

    hsv[0] *= 60                # degrees
    if hsv[0] < 0:
        hsv[0] += 360

    return hsv

def HSVtoRGB(hsv):
    rgb=[0,0,0] # pass through alpha channel

    hsv[0]/=60

    if hsv[1] == 0:
        return tuple([hsv[2],hsv[2],hsv[2]])

    i = int(hsv[0])
    f = hsv[0] - i                            #Decimal bit of hue
    p = hsv[2] * (1 - hsv[1])
    q = hsv[2] * (1 - hsv[1] * f)
    t = hsv[2] * (1 - hsv[1] * (1 - f))

    if i == 0:
        rgb[0] = hsv[2]
        rgb[1] = t
        rgb[2] = p
    elif i == 1:
        rgb[0] = q
        rgb[1] = hsv[2]
        rgb[2] = p
    elif i == 2:
        rgb[0] = p
        rgb[1] = hsv[2]
        rgb[2] = t
    elif i == 3:
        rgb[0] = p
        rgb[1] = q
        rgb[2] = hsv[2]
    elif i == 4:
        rgb[0] = t
        rgb[1] = p
        rgb[2] = hsv[2]
    elif i == 5:
        rgb[0] = hsv[2]
        rgb[1] = p
        rgb[2] = q

    return tuple(rgb)