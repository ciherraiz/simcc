from simcc.callcenter import Simulation
import pandas as pd
import matplotlib


NUM_INTERCALL_MINUTES_HOUR = [10, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 20, 10, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 20]

if __name__ == '__main__':

    sim = Simulation(num_telemarketers=1,
                    num_intercall_minutes=NUM_INTERCALL_MINUTES_HOUR,
                    simulation_time=2880)
    sim.run()
    sim.stats(verbose=True)

    data, summary = sim.stats(verbose=True)

    data['start_h'] = ((data['start'] / 60) % 24).astype(int)
    data['start_d'] = ((data['start'] / (24 * 60))+1).astype(int)

    print(data.head(10))

    print(data[data['start_d']==1][['start_h', 'start']].groupby(['start_h']).agg(['count']))