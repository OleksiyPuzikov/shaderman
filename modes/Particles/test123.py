
import random
import la
import zoe






PARTICLES9 = 100

class FountainParticle9(zoe.NewtonianParticle):
    trailLength = 5

    def update(self):
        self.impulse(-0.002*la.Vector.K)
        zoe.NewtonianParticle.update(self)

    def ok(self):
        return self.pos[2] >= 0.0

class FountainSystem9(zoe.System):
    def new(self):
        theta = random.uniform(0, zoe.twoPi)
        phi = random.uniform(0, zoe.pi)
        vel = la.PolarVector(0.1, theta, phi)
        return FountainParticle9(la.Vector.ZERO, vel)



engine = zoe.Engine()
engine.add(zoe.AxesObject())
engine.add(zoe.GridObject())
engine.add(FountainSystem9(PARTICLES9))
engine.add(zoe.FrameRateCounter(engine))
engine.go()


