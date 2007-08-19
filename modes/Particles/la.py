#!/usr/local/bin/python

"""
A very simple 3D vector, matrix, and linear algebra library.
"""

import math
import types


class Vector:

    """A 3 element vector."""

    ZERO = None
    I = None
    J = None
    K = None
    
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def normSquared(self):
        """Return the squared vector norm.  If it is not necessary to
        actually calculate the norm, this is more efficient since it
        does not involve a square root."""
        return self.x**2 + self.y**2 + self.z**2

    def norm(self):
        """Return the vector norm."""
        return math.sqrt(self.normSquared())

    def __len__(self): return 3

    def __getitem__(self, index):
        return (self.x, self.y, self.z)[index]

    def dot(self, other):
        """Return the dot product, u dot v."""
        return self.x*other.x + self.y*other.y + self.z*other.z

    def cross(self, other):
        """Return the cross product, u cross v."""
        return Vector(self.y*other.z - self.z*other.y, \
                      self.z*other.x - self.x*other.z, \
                      self.x*other.y - self.y*other.x)

    def unit(self):
        """Return a vector in the same direction but whose length is
        unity."""
        norm = self.norm()
        return Vector(self.x/norm, self.y/norm, self.z/norm)

    def bound(self, norm):
        """Return a vector in the same direction, but whose length is no
        greater than norm."""
        if self.normSquared() > norm**2:
            return norm*self.unit()
        else:
            return self

    def __neg__(self):
        """Return -v."""
        return Vector(-self.x, -self.y, -self.z)

    def __add__(self, other):
        """Return u + v."""
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """Return u - v."""
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        """Return v r."""
        return Vector(self.x*scalar, self.y*scalar, self.z*scalar)
    
    def __rmul__(self, scalar):
        """Return r v."""
        return Vector.__mul__(self, scalar)
    
    def __div__(self, scalar):
        """Return v/r."""
        return Vector(self.x/scalar, self.y/scalar, self.z/scalar)

    def __eq__(self, other):
        """Return u == v."""
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        """Return u != v."""
        return self.x != other.x or self.y != other.y or self.z != other.z

    def __lt__(self, other): raise TypeError, "no ordering on vectors"
    def __gt__(self, other): raise TypeError, "no ordering on vectors"
    def __le__(self, other): raise TypeError, "no ordering on vectors"
    def __ge__(self, other): raise TypeError, "no ordering on vectors"

    def __str__(self):
        return '(%s %s %s)' % (self.x, self.y, self.z)

    def __repr__(self):
        return '<%s @ 0x%x %s>' % (self.__class__, id(self), str(self))

Vector.ZERO = Vector(0.0, 0.0, 0.0)
Vector.I = Vector(1.0, 0.0, 0.0)
Vector.J = Vector(0.0, 1.0, 0.0)
Vector.K = Vector(0.0, 0.0, 1.0)

def PolarVector(rho, theta, phi):
    """Return a polar vector (r, theta, phi)."""
    r = rho*math.cos(phi)
    z = rho*math.sin(phi)
    return Vector(r*math.cos(theta), r*math.sin(theta), z)


class Matrix:

    """A 3x3 square matrix."""
    
    ZERO = None
    IDENTITY = None
    
    def __init__(self, a, b, c, d, e, f, g, h, i):
        self.a, self.b, self.c, \
                 self.d, self.e, self.f, \
                 self.g, self.h, self.i = \
                 float(a), float(b), float(c), \
                 float(d), float(e), float(f), \
                 float(g), float(h), float(i)

    def trace(self):
        """Return the trace of the matrix, tr M."""
        return self.a*self.e*self.i

    def determinant(self):
        """Return the determinant of the matrix, det M."""
        return self.a*self.e*self.i - self.a*self.f*self.h + \
               self.b*self.f*self.g - self.b*self.d*self.i + \
               self.c*self.d*self.h - self.c*self.e*self.g

    def isSingular(self):
        """Is the matrix singular?"""
        return self.determinant() == 0

    def rows(self):
        """Return the rows of the matrix as a sequence of vectors."""
        return [Vector(self.a, self.b, self.c), \
                Vector(self.d, self.e, self.f), \
                Vector(self.g, self.h, self.i)]

    def row(self, index):
        """Get the nth row as a vector."""
        return self.rows()[index]

    def columns(self):
        """Return the columns of the matrix as a sequence of vectors."""
        return [Vector(self.a, self.b, self.g), \
                Vector(self.b, self.e, self.h), \
                Vector(self.c, self.f, self.i)]

    def column(self, index):
        """Get the nth column as a vector."""
        return self.columns()[index]

    def __len__(self): return 3
    def __getitem__(self, index): return self.row(index)

    def transpose(self):
        """Return the transpose of the matrix, M^T."""
        return Matrix(self.a, self.d, self.g, \
                      self.b, self.e, self.h, \
                      self.c, self.f, self.i)

    def __add__(self, other):
        """Return M + N."""
        return Matrix(self.a + other.a, self.b + other.b, self.c + other.c, \
                      self.d + other.d, self.e + other.e, self.f + other.f, \
                      self.g + other.g, self.h + other.h, self.i + other.i)

    def __sub__(self, other):
        """Return M - N."""
        return Matrix(self.a - other.a, self.b - other.b, self.c - other.c, \
                      self.d - other.d, self.e - other.e, self.f - other.f, \
                      self.g - other.g, self.h - other.h, self.i - other.i)

    def __mul__(self, scalar):
        """Return M r."""
        return Matrix(self.a*scalar, self.b*scalar, self.c*scalar, \
                      self.d*scalar, self.e*scalar, self.f*scalar, \
                      self.g*scalar, self.h*scalar, self.i*scalar)
        
    def __rmul__(self, scalar):
        """Return r M."""
        return Matrix.__mul__(self, scalar)

    def __div__(self, scalar):
        """Return M/r."""
        return Matrix(self.a/scalar, self.b/scalar, self.c/scalar, \
                      self.d/scalar, self.e/scalar, self.f/scalar, \
                      self.g/scalar, self.h/scalar, self.i/scalar)

    def __pow__(self, exponent):
        """Return M^n."""
        if type(exponent) != types.IntType and \
           type(exponent) != types.LongType:
            raise TypeError, "exponent must be integral"
        if exponent <= 0:
            raise ValueError, "exponent must be positive"
        result = self
        for i in range(exponent - 1):
            result = result.concatenate(self)
        return result

    def concatenate(self, other):
        """Return M1 M2."""
        return Matrix(self.a*other.a + self.b*other.d + self.c*other.g, \
                      self.a*other.b + self.b*other.e + self.c*other.h, \
                      self.a*other.c + self.b*other.f + self.c*other.i, \
                      self.d*other.a + self.e*other.d + self.f*other.g, \
                      self.d*other.b + self.e*other.e + self.f*other.h, \
                      self.d*other.c + self.e*other.f + self.f*other.i, \
                      self.g*other.a + self.h*other.d + self.i*other.g, \
                      self.g*other.b + self.h*other.e + self.i*other.h, \
                      self.g*other.c + self.h*other.f + self.i*other.i)

    def transform(self, vector):
        """Return v M."""
        return Vector(self.a*vector.x + self.b*vector.y + self.c*vector.z, \
                      self.d*vector.x + self.e*vector.y + self.f*vector.z, \
                      self.g*vector.x + self.h*vector.y + self.i*vector.z)

    def __cofactorSign(self, i, j):
        """Compute (-1)^(i + j) to help in determining cofactors."""
        if (i + j + 2) % 2 == 0:
            return 1
        else:
            return -1

    def __minorDeterminant(self, minor):
        """Find the determinant of a 2x2 matrix represented as [a b c d]."""
        a, b, c, d = minor
        return a*d - b*c

    def __cofactor(self, i, j):
        """Return the cofactor for the (i, j)-th element."""
        minor = []
        for y in range(3):
            for x in range(3):
                if x == i or y == j:
                    continue
                minor.append(self[y][x])
        return self.__cofactorSign(i, j)*self.__minorDeterminant(minor)

    def adjoint(self):
        """Return adj M."""
        coefficients = []
        for j in range(3):
            for i in range(3):
                coefficients.append(self.__cofactor(j, i)) # built-n transpose
        return Matrix(*coefficients)
                
    def inverse(self):
        """Return M^-1 where M M^-1 = M^-1 M = I."""
        return self.adjoint()/self.determinant()

    def __eq__(self, other):
        """Return M == N."""
        return \
            self.a == other.a and self.b == other.b and self.c == other.c and \
            self.d == other.d and self.e == other.e and self.f == other.f and \
            self.g == other.g and self.h == other.h and self.i == other.i

    def __ne__(self, other):
        """Return M != N."""
        return \
            self.a != other.a or self.b != other.b or self.c != other.c or \
            self.d != other.d or self.e != other.e or self.f != other.f or \
            self.g != other.g or self.h != other.h or self.i != other.i

    def __str__(self):
        return '[%s %s %s; %s %s %s; %s %s %s]' % \
               (self.a, self.b, self.c, \
                self.d, self.e, self.f, \
                self.g, self.h, self.i)

    def __repr__(self):
        return '<%s @ 0x%x %s>' % (self.__class__, id(self), str(self))

Matrix.ZERO = Matrix(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
Matrix.IDENTITY = Matrix(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

def ScaleMatrix(sx, sy=None, sz=None):
    """Return a scaling matrix."""
    if sy is None:
        sy = sx
    if sz is None:
        sz = sy
    return Matrix(sx, 0, 0, 0, sy, 0, 0, 0, sz)

### more matrix creators
### __hash__ methods for vectors and matrices
