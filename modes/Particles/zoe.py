#!/usr/local/bin/python
#
# $Id: //projects/zoe/zoe.py#1 $ $Date$

"""
A simple OpenGL rendering engine.
"""

__program__ = 'zoe'
__version__ = '1.0a'
__url__ = 'http://www.alcyone.com/pyos/zoe/'
__author__ = 'Erik Max Francis <max@alcyone.com>'
__copyright__ = 'Copyright (C) 2000-2002 Erik Max Francis'
__license__ = 'LGPL'


import math
import sys
import time
import types

from OpenGL.GL   import * # strange, but canonical PyOpenGL import
from OpenGL.GLU  import *
from OpenGL.GLUT import *


# Some mathematical constants for convenience.
pi = math.pi
twoPi = 2*pi
piOverTwo = pi/2
piOverOneEighty = pi/180
radiansToDegrees = 1/piOverOneEighty
degreesToRadians = piOverOneEighty
sqrtTwo = math.sqrt(2)


# Object ######################################################################

class Object:

    """The fundamental object."""
    
    def __init__(self):
        if self.__class__ is Object:
            raise NotImplementedError
    
    def display(self):
        """Display the object.  This method must be overridden."""
        raise NotImplementedError
    
    def update(self):
        """Update the object.  This should update the internal state of
        the object, if relevant."""
        pass
    
    def commit(self):
        """Commit any pending changes to the object.  This method is only
        called for objects in an engine which has the committing attribute
        set."""
        pass


class AxesObject(Object):

    """Shows a set of axes, with stippling in the negative direction."""
    
    xColor = 1.0, 0.0, 0.0
    yColor = 0.0, 1.0, 0.0
    zColor = 0.0, 0.0, 1.0
    stipple = 0x0f0f

    def __init__(self, expanse=20):
        Object.__init__(self)
        self.expanse = expanse

    def display(self):
        glLineStipple(1, self.stipple)
	glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glColor3d(*self.xColor)
        glVertex3d(0, 0, 0)
        glVertex3d(self.expanse, 0, 0)
        glEnd()
	glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex3d(0, 0, 0)
        glVertex3d(-self.expanse, 0, 0)
        glEnd()
	glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glColor3d(*self.yColor)
        glVertex3d(0, 0, 0)
        glVertex3d(0, self.expanse, 0)
	glEnd()
	glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex3d(0, 0, 0)
        glVertex3d(0, -self.expanse, 0)
        glEnd()
	glDisable(GL_LINE_STIPPLE)
	glBegin(GL_LINES)
        glColor3d(*self.zColor)
        glVertex3d(0, 0, 0)
        glVertex3d(0, 0, self.expanse)
	glEnd()
	glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex3d(0, 0, 0)
        glVertex3d(0, 0, -self.expanse)
        glEnd()
	glDisable(GL_LINE_STIPPLE)


class GridObject(Object):

    """Shows a grid on the x-y plane."""

    gridColor = 0.25, 0.25, 0.25
    
    def __init__(self, resolution=1, expanse=20, skipZero=1):
        Object.__init__(self)
        self.resolution = resolution
        self.expanse = expanse
        self.skipZero = skipZero

    def display(self):
	glColor3d(*self.gridColor)
	glBegin(GL_LINES)
        i = -self.expanse
        while i <= +self.expanse:
            if i == 0 and self.skipZero:
                i += self.resolution
                continue
	    glVertex3d(i, -self.expanse, 0)
	    glVertex3d(i, +self.expanse, 0)
	    glVertex3d(-self.expanse, i, 0)
	    glVertex3d(+self.expanse, i, 0)
            i += self.resolution
	glEnd()


class ReplayingObject(Object):

    """An object which can be given a series of PostScript-like
    commands, finished with the 'done' method, and then can replay
    them back."""
    
    def __init__(self):
        self.paths = []
        self.current = None

    def setColor(self, triple):
        self.endPath()
        self.paths.append(tuple(triple))

    def startPath(self):
        if self.current is not None:
            self.endPath()
        self.current = []

    def vertex(self, point):
        assert self.current is not None
        self.current.append(point)

    def endPath(self):
        if self.current is not None:
            self.paths.append(self.current)
            self.current = None

    def closePath(self):
        assert self.current is not None
        self.current.append(self.current[0])
        self.endPath()

    def done(self):
        self.endPath()

    def display(self):
        for path in self.paths:
            if type(path) is types.TupleType:
                glColor3d(*path)
            else:
                if len(path) == 1:
                    glBegin(GL_POINTS)
                elif len(path) == 2:
                    glBegin(GL_LINES)
                else:
                    glBegin(GL_LINE_STRIP)
                for point in path:
                    glVertex3d(*point)
                glEnd()


class Plotter(ReplayingObject):

    """A plotter which, given a function taking two arguments, will
    play out its behavior drawing a surface."""
    
    def __init__(self, func, startT=-10.0, deltaT=0.2, endT=+10.0):
        ReplayingObject.__init__(self)
        x = startT
        while x <= endT:
            self.startPath()
            y = startT
            while y <= endT:
                try:
                    z = func(x, y)
                except (ZeroDivisionError, OverflowError):
                    y += deltaT
                    continue
                self.vertex((x, y, z))
                y += deltaT
            self.endPath()
            x += deltaT
        y = startT
        while y <= endT:
            self.startPath()
            x = startT
            while x <= endT:
                try:
                    z = func(x, y)
                except (ZeroDivisionError, OverflowError):
                    x += deltaT
                    continue
                self.vertex((x, y, z))
                x += deltaT
            self.endPath()
            y += deltaT


class StatusObject(Object):

    """A status object is one that can render itself as text on the
    main screen."""

    textColor = 1.0, 1.0, 1.0
    
    def __init__(self, engine):
        Object.__init__(self)
        self.engine = engine

    def displayText(self, x, y, style, message):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.engine.width, 0, self.engine.height, -1, 1)
        glColor3d(*self.textColor)
        glRasterPos2i(x, y)
        for char in message:
            glutBitmapCharacter(style, ord(char))
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


class FrameRateCounter(StatusObject):

    """A frame rate counter, which displays the current frame number
    and the current frame rate."""
    
    def __init__(self, engine, x=10, y=10, style=GLUT_BITMAP_HELVETICA_12):
        StatusObject.__init__(self, engine)
        self.x, self.y = x, y
        self.style = style

    def display(self):
        self.displayText(self.x, self.y, self.style,
                         "frame %d rate %.2f" % \
                         (self.engine.frame, self.engine.frameRate))



# Transform ###################################################################

class Transform:

    """An encapsulation of a transformation."""
    
    def __init__(self):
        pass

    def apply(self):
        """Apply the transformation."""
        pass


class TranslateTransform(Transform):

    """A translation transformation."""
    
    def __init__(self, vec):
        self.vec = vec

    def apply(self):
        glTranslated(self.vec[0], self.vec[1], self.vec[2])


class RotateTransform(Transform):

    """A rotation transformation."""
    
    def __init__(self, angle, ray=(0, 0, 1)):
        self.angle = angle
        self.ray = ray

    def apply(self):
        glRotated(self.angle*radiansToDegrees, \
                  self.ray[0], self.ray[1], self.ray[2])


class ScaleTransform(Transform):

    """A scale transformation."""
    
    def __init__(self, vecOrScalar):
        if type(vecOrScalar) is types.FloatType:
            self.vec = (vecOrScalar,) * 3
        else:
            self.vec = vecOrScalar

    def apply(self):
        glScaled(self.vec[0], self.vec[1], self.vec[2])



# Group #######################################################################

class Group(Object):

    """A group is an object which holds a collection of other objects.
    It displays, updates, and commits all its contained objects in
    sequence."""
    
    def __init__(self, objects=None):
        Object.__init__(self)
        if objects is None:
            objects = []
        self.objects = objects

    def append(self, object):
        self.objects.append(object)

    def extend(self, objects):
        self.objects.extend(objects)

    def remove(self, object):
        self.objects.remove(object)

    def before(self):
        pass

    def after(self):
        pass

    def display(self):
        self.before()
        for object in self.objects:
            object.display()
        self.after()

    def update(self):
        for object in self.objects:
            object.update()

    def commit(self):
        for object in self.objects:
            object.commit()


class TransformGroup(Group):

    """A group that implements a series of transforms."""
    
    def __init__(self, transforms, objects=None):
        Group.__init__(self, objects)
        self.transforms = transforms

    def before(self):
        glPushMatrix()
        for transform in self.transforms:
            transform.apply()

    def after(self):
        glPopMatrix()


class RotatingGroup(TransformGroup):

    """A group that slowly rotates."""
    
    def __init__(self, angularSpeed, ray=(0, 0, 1), objects=None):
        self.transform = RotateTransform(0.0, ray)
        TransformGroup.__init__(self, [self.transform], objects)
        self.angularSpeed = angularSpeed

    def update(self):
        self.transform.angle += self.angularSpeed
        if self.transform.angle >= twoPi:
            self.transform.angle -= twoPi



# Particle, System ############################################################

class Particle(Object):

    """A particle is an object with a position, and an optional
    trail."""

    trailLength = 0
    particleColor = 1.0, 1.0, 1.0
    trailColor = 0.5, 0.5, 0.5
    
    def __init__(self, pos=(0, 0, 0)):
        Object.__init__(self)
        self.pos = pos
        self.trail = []

    def display(self):
        if self.trailLength:
            glColor3d(*self.trailColor)
            glBegin(GL_LINE_STRIP)
            for point in self.trail:
                glVertex3d(*point)
            glVertex3d(*self.pos)
            glEnd()
	glColor3d(*self.particleColor)
        glBegin(GL_POINTS)
        glVertex3d(*self.pos)
        glEnd()

    def update(self):
        if self.trailLength:
            self.trail.append(self.pos)
            if len(self.trail) > self.trailLength:
                self.trail = self.trail[-self.trailLength:]

    def ok(self):
        """Does this particle need to be reclaimed?  Only applicable for
        particles in systems."""
        return 1


class NewtonianParticle(Particle):

    """A Newtonian particle has a position and a velocity, and every
    turn updates its position according to the velocity (which
    actually acts as a change in position."""
    
    def __init__(self, pos=(0, 0, 0), vel=(0, 0, 0)):
        Particle.__init__(self, pos)
        self.vel = vel

    def update(self):
        Particle.update(self)
        self.pos = self.pos[0] + self.vel[0], \
                   self.pos[1] + self.vel[1], \
                   self.pos[2] + self.vel[2]

    def impulse(self, deltavee):
        """Apply an impulse to the particle, with the change in velocity."""
        self.vel = self.vel[0] + deltavee[0], \
                   self.vel[1] + deltavee[1], \
                   self.vel[2] + deltavee[2]


class System(Group):

    """A system is a group that maintains a list of objects with a
    maximum number, all of the same type.  Each object is excepted to
    have an 'ok' method that returns whether or not it should be
    reclaimed."""

    def __init__(self, max):
        Group.__init__(self)
        self.max = max

    def new(self):
        """Construct a new particle."""
        raise NotImplementedError

    def reset(self, index):
        """Reset the nth particle."""
        self.objects[index] = self.new()

    def update(self):
        Group.update(self)
        # Look for expired particles.
        for i in range(len(self.objects)):
            if not self.objects[i].ok():
                self.reset(i)
        # Inject new particles.
        count = len(self.objects)
        if count < self.max:
            self.objects.append(None)
            self.reset(count)



# Camera ######################################################################

class Camera:

    """A camera, which applies the viewing transformations in order to
    get the desired view."""

    defaultZoom = 0.2
    
    def __init__(self, engine):
        self.engine = engine
        engine.camera = self
        self.zoom = self.defaultZoom

    def zoomIn(self, factor=sqrtTwo):
        """Zoom in."""
        self.zoom *= factor

    def zoomOut(self, factor=sqrtTwo):
        """Zoom out."""
        self.zoom /= factor

    def view(self):
        """Apply the relevant viewing transformations."""
        pass

    def refresh(self):
        """Refresh the position of the camera."""
        pass


class OverheadCamera(Camera):

    """An overhead camera views the x-y plane."""
    
    def __init__(self, engine, left=0, right=None, bottom=0, top=None):
        Camera.__init__(self, engine)
        if right is None:
            right = engine.width
        if top is None:
            top = engine.height
        self.left = left
        self.right = right
        self.bottom = bottom
        self.top = top
    
    def view(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.left, self.right, self.bottom, self.top, -1, 1)
        glScalef(self.zoom, self.zoom, self.zoom)


class BasicCamera(Camera):

    """A basic camera views a center point from an eye position, with
    a reference up vector that points to the top of the screen."""
    
    def __init__(self, engine, eye, center=(0, 0, 0), up=(0, 0, 1)):
        Camera.__init__(self, engine)
        self.center = center
        self.eye = eye
        self.up = up

    def view(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluLookAt(self.center[0], self.center[1], self.center[2],
                  self.eye[0], self.eye[1], self.eye[2],
                  self.up[0], self.up[1], self.up[2])
        glScalef(self.zoom, self.zoom, self.zoom)


class PrecessingCamera(BasicCamera):

    """A precessing camera orbits around the z axis at a given
    distance from it and height above the x-y plane."""
    
    def __init__(self, engine, distance, height, rate, \
                 center=(0, 0, 0), up=(0, 0, 1)):
        BasicCamera.__init__(self, engine, None, center, up)
        self.distance = distance
        self.height = height
        self.rate = rate
        self.angle = 0.0
        self.calc()

    def calc(self):
        self.eye = self.distance*math.cos(self.angle), \
                   self.distance*math.sin(self.angle), \
                   self.height

    def refresh(self):
        self.angle += self.rate
        if self.angle < 0:
            self.angle += twoPi
        elif self.angle >= twoPi:
            self.angle -= twoPi
        self.calc()


class MobileCamera(BasicCamera):

    """A mobile camera maintains a certain distance (rho) from the
    origin, but is user controllable."""
    
    def __init__(self, engine, rho, center=(0, 0, 0), up=(0, 0, 1)):
        BasicCamera.__init__(self, engine, None, center, up)
        self.x, self.y, self.z = center
        self.rho = rho
        self.theta = 0
        self.phi = 0
        self.calc()

    def calc(self):
        self.center = self.x, self.y, self.z
        r = self.rho*math.cos(self.phi)
        z = self.rho*math.sin(self.phi)
        self.eye = (r*math.cos(self.theta), r*math.sin(self.theta), z)
    
    def refresh(self):
        self.calc()



# Interface ###################################################################

class Interface:

    """The interface encapsulates all the user interface behavior that
    an engine can exhibit."""
    
    def __init__(self, engine):
        self.engine = engine
        assert self.engine.camera is not None
        engine.interface = self
        self.keyMap = {} # mapping for keys and special keys
        self.buttons = [] # list of buttons currently pressed
        self.lastButton = None # last button pressed
        self.mouseMark = None # last mouse down location
        self.visible = 0 # is window currently visible

    def _mouse(self, button, state, loc):
        """The mouse event wrapper."""
        if state == GLUT_DOWN:
            assert button not in self.buttons
            self.buttons.append(button)
            self.lastButton = button
            self.mouseMark = loc
            self.mouseDown(button, loc)
        else:
            self.buttons.remove(button)
            self.lastButton = None
            self.mouseMark = None
            self.mouseUp(button, loc)

    def _motion(self, loc):
        """The mouse motion wrapper."""
        self.mouseDrag(self.lastButton, loc)

    def _visibility(self, visibility):
        """The visibility wrapper."""
        visible = visibility == GLUT_VISIBLE
        if visible != self.visible:
            self.visibilityChange(visible)
            self.visible = visible

    def _entry(self, entry):
        """The window entry wrapper."""
        self.entryChange(entry == GLUT_ENTERED)

    # The following should be overridden by subclasses.

    def keyPressed(self, key, loc):
        """A key was pressed while the mouse was at the specified
        location."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'keyPressed', (key, loc)
        if self.keyMap.has_key(key):
            self.keyMap[key](loc)

    def mouseMove(self, loc):
        """The mouse moved with no buttons pressed."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'mouseMove', loc
        
    def mouseDown(self, button, loc):
        """The specified mouse button was clicked while the mouse was at
        the given location."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'mouseDown', (button, loc)
    
    def mouseUp(self, button, loc):
        """The specified mouse button was released while the mouse was at
        the given location."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'mouseUp', (button, loc)

    def mouseDrag(self, button, loc):
        """The mouse was dragged to the specified location while the given
        mouse button was held down."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'mouseDrag', (button, loc)

    def entryChange(self, entered):
        """The mouse moved into or out of the window."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'entryChange', entered

    def visibilityChange(self, visible):
        """The window had a visibility chnage."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'visibilityChange', visible

    def reshapeWindow(self, size):
        """The window was reshaped."""
        if self.engine.debug >= 2:
            print >> sys.stderr, 'reshapeWindow', size


class BasicInterface(Interface):

    """A basic interface supports quitting, pausing, stepping,
    zooming, and resizing."""
    
    def __init__(self, engine):
        Interface.__init__(self, engine)
        self.keyMap['q'] = self.shutdown
        self.keyMap['\033'] = self.shutdown
        self.keyMap[GLUT_KEY_F12] = self.shutdown
        self.keyMap[' '] = self.toggle
        self.keyMap['z'] = self.zoomIn
        self.keyMap['Z'] = self.zoomOut
        self.keyMap['\r'] = self.step
        self.keyMap['>'] = self.sizeUp
        self.keyMap['<'] = self.sizeDown
        
    def toggle(self, loc): self.engine.toggle()
    def shutdown(self, loc): self.engine.shutdown()
    def step(self, loc): self.engine.step()
    
    def zoomIn(self, loc):
        self.engine.camera.zoomIn()
        self.engine.redisplay()
        
    def zoomOut(self, loc):
        self.engine.camera.zoomOut()
        self.engine.redisplay()

    def sizeUp(self, factor=2):
        self.engine.reshape(self.engine.width*2, self.engine.height*2)

    def sizeDown(self, factor=2):
        self.engine.reshape(self.engine.width/2, self.engine.height/2)


class PivotingInterface(BasicInterface):

    """A pivoting interface supports the basic interfaces and can be
    pivoted around the center point with the mouse."""
    
    sensitivity = 0.005
    
    def __init__(self, engine):
        BasicInterface.__init__(self, engine)
        self.keyMap['r'] = self.resetEye

    def mouseDrag(self, button, loc):
        if button == GLUT_LEFT_BUTTON:
            delta = loc[0] - self.mouseMark[0], loc[1] - self.mouseMark[1]
            self.engine.camera.theta += delta[0]*self.sensitivity
            self.engine.camera.phi += delta[1]*self.sensitivity
            self.mouseMark = loc
            self.engine.camera.refresh()
            self.engine.redisplay()

    def resetEye(self, loc):
        self.engine.camera.theta = self.engine.camera.phi = 0


class PanningInterface(PivotingInterface):

    """A panning interface supports all the pivoting and basic
    behavior, but the pivoting point can be moved with the
    keyboard."""
    
    increment = 0.1
    
    def __init__(self, engine):
        PivotingInterface.__init__(self, engine)
        self.keyMap['d'] = self.panPositiveX
        self.keyMap['a'] = self.panNegativeX
        self.keyMap['w'] = self.panPositiveY
        self.keyMap['x'] = self.panNegativeY
        self.keyMap['e'] = self.panPositiveZ
        self.keyMap['c'] = self.panNegativeZ
        self.keyMap['s'] = self.resetPan

    def panPositiveX(self, loc): self.engine.camera.x += self.increment
    def panNegativeX(self, loc): self.engine.camera.x -= self.increment
    def panPositiveY(self, loc): self.engine.camera.y += self.increment
    def panNegativeY(self, loc): self.engine.camera.y -= self.increment
    def panPositiveZ(self, loc): self.engine.camera.z += self.increment
    def panNegativeZ(self, loc): self.engine.camera.z -= self.increment

    def resetPan(self, loc):
        self.engine.camera.x = self.engine.camera.y = self.engine.camera.z = \
                               0.0



# Engine ######################################################################

class Engine:

    """The engine manages the window, handles high-level displaying
    and updating."""

    defaultCamera = MobileCamera, (5.0,)
    defaultInterface = PanningInterface, ()

    def __init__(self):
        self.debug = 0
        self.title = 'ZOE'
        self.width, self.height = 320, 320
        self.mode = GLUT_RGBA | GLUT_DOUBLE
        self.background = (0, 0, 0, 0)
        self.every = 1 # display how many updates
        self.objects = [] # list of objects
        self.running = 1 # is running?
        self.play = 1 # positive = play, 0 = paused, negative = update count
        self.frame = 0l # frame count
        self.timePeriod = 2 # period (s) to update frame rate
        self.frameMark, self.timeMark = 0l, time.time() # marks for updating
        self.frameRate = 0.0 # current frame rate
        self.committing = 0 # is the Engine a committing one?
        self.camera = None
        self.interface = None
        self.error = None
        
    def clear(self):
        """Clear the display."""
        glClear(GL_COLOR_BUFFER_BIT)

    def add(self, object):
        """Add an object."""
        self.objects.append(object)

    def extend(self, objects):
        """Add a sequence of objects."""
        self.objects.extend(objects)

    def remove(self, object):
        """Remove an object."""
        self.objects.remove(object)

    def display(self):
        """Display."""
        self.clear()
        self.camera.view()
        glMatrixMode(GL_MODELVIEW)
        for object in self.objects:
            object.display()
        self.flush()
        self.measure()
        
    def redisplay(self):
        """Register a redisplay."""
        glutPostRedisplay()

    def flush(self):
        """Flush all pending drawing and show the result."""
        glFlush()
        glutSwapBuffers()

    def update(self):
        """Update."""
        i = 0
        while i < self.every:
            self.camera.refresh() ### what to do with dirty?
            for object in self.objects:
                object.update()
            if self.committing:
                self.commit()
            i += 1
        self.redisplay()

    def commit(self):
        """Commit pending changes.  This only gets called if the committing
        attribute is set to true."""
        for object in self.objects:
            object.commit()

    def idle(self):
        """Idle the engine."""
        if not self.running:
            self.terminate()
        if self.play:
            self.update()
            if self.play < 0:
                self.play += 1

    def step(self, count=1):
        """Set to only step the engine one frame."""
        self.play = -count

    def toggle(self):
        """Toggle the engine between playing and pausing."""
        self.play = not self.play

    def reshape(self, width, height):
        """Resize the window."""
        glutSetWindow(self.window)
        glutReshapeWindow(width, height)
        glViewport(0, 0, width, height)
        self.width, self.height = width, height
        self.interface.reshapeWindow((width, height))

    def measure(self):
        """Update frame measure."""
        self.frame += 1
        now = time.time()
        elapsed = now - self.timeMark
        if elapsed >= self.timePeriod:
            self.frameRate = (self.frame - self.frameMark)/elapsed
            self.frameMark = self.frame
            self.timeMark = now
            
    def setup(self):
        """Setup the camera and interface if they're unspecified.  """
        if self.camera is None:
            functor, args = self.defaultCamera
            self.camera = functor(*((self,) + args))
        if self.interface is None:
            functor, args = self.defaultInterface
            self.interface = functor(*((self,) + args))

    def callbacks(self):
        """Register the GLUT  callbacks."""
        glutDisplayFunc(self.__display)
        glutIdleFunc(self.__idle)
        glutReshapeFunc(self.__reshape)
        glutKeyboardFunc(self.__keyboard)
        glutSpecialFunc(self.__special)
        glutMouseFunc(self.__mouse)
        glutMotionFunc(self.__motion)
        glutPassiveMotionFunc(self.__passive)
        glutVisibilityFunc(self.__visibility)
        glutEntryFunc(self.__entry)

    def go(self):
        """Set everything up and then execute the main loop."""
        self.setup()
	glutInit(sys.argv)
        glutInitDisplayMode(self.mode)
        glutInitWindowSize(self.width, self.height)
        self.window = glutCreateWindow(self.title)
        glutSetWindow(self.window)
        glClearColor(*self.background)
        self.callbacks()
        glutMainLoop()

    def shutdown(self, *args):
        """Mark the engine as shutting down."""
        self.running = 0

    def terminate(self):
        """Actually terminate the process."""
        sys.exit()

    # The GLUT callbacks follow.

    def __display(self):
        if self.debug >= 10:
            print >> sys.stderr, 'display'
        self.display()
        
    def __idle(self):
        if self.debug >= 10:
            print >> sys.stderr, 'idle'
        self.idle()

    def __reshape(self, width, height):
        if self.debug >= 5:
            print >> sys.stderr, 'reshape', (width, height)
        self.reshape(width, height)
        
    def __keyboard(self, key, x, y):
        assert type(key) == types.StringType
        if self.debug >= 5:
            print >> sys.stderr, 'keyboard', (key, (x, y))
        self.interface.keyPressed(key, (x, y))

    def __special(self, key, x, y):
        assert type(key) == types.IntType
        if self.debug >= 5:
            print >> sys.stderr, 'special', (key, (x, y))
        self.interface.keyPressed(key, (x, y))

    def __mouse(self, button, state, x, y):
        assert button in \
               (GLUT_LEFT_BUTTON, GLUT_MIDDLE_BUTTON, GLUT_RIGHT_BUTTON)
        if self.debug >= 5:
            print >> sys.stderr, 'mouse', (button, state, (x, y))
        self.interface._mouse(button, state, (x, y))
    
    def __motion(self, x, y):
        if self.debug >= 5:
            print >> sys.stderr, 'motion', (x, y)
        self.interface._motion((x, y))
    
    def __passive(self, x, y):
        if self.debug >= 5:
            print >> sys.stderr, 'passive', (x, y)
        self.interface.mouseMove((x, y))

    def __visibility(self, visibility):
        if self.debug >= 5:
            print >> sys.stderr, 'visibility', visibility
        self.interface._visibility(visibility)

    def __entry(self, entry):
        if self.debug >= 5:
            print >> sys.stderr, 'entry', entry
        self.interface._entry(entry)
