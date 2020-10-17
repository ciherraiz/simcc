from simcc.callcenter import Simulation
import pandas as pd


if __name__ == '__main__':

    sim = Simulation()
    sim.run()
    sim.stats(verbose=True)