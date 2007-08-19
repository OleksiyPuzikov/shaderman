import random

import la
import zoe


PARTICLES = 1000


class FountainParticle(zoe.NewtonianParticle):

    """Each particle is pulled down by a gravitational force, and is
    reset when it hits the x-y plane."""
    
    G = -0.002*la.Vector.K # 
    Z_MIN = 0.0 # 

    trailLength = 5

    def update(self):
        self.impulse(self.G)
        zoe.NewtonianParticle.update(self)

    def ok(self):
        return self.pos[2] >= self.Z_MIN


class FountainSystem(zoe.System):

    """Manage the fountain particles, creating them at the origin with some
    random upward velocity."""
    
    V0_MAX = 0.1 # maximum initial speed
    
    def new(self):
        theta = random.uniform(0, zoe.twoPi)
        phi = random.uniform(0, zoe.pi)
        vel = la.PolarVector(self.V0_MAX, theta, phi)
        return FountainParticle(la.Vector.ZERO, vel)


def main():
    engine = zoe.Engine()
    engine.add(zoe.AxesObject())
    engine.add(zoe.GridObject())
    engine.add(FountainSystem(PARTICLES))
    engine.add(zoe.FrameRateCounter(engine))
    engine.go()

if __name__ == '__main__': main()
