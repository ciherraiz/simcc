import random
import simpy
import pandas as pd

class Simulation:
    def __init__ (self,
                num_queue_slots=1, 
                num_telemarketers=1,
                num_costumers_start=0,
                num_intercall_minutes=1,
                ivr_max_time=3,
                telemarketer_max_time=10,

                simulation_time=60):
        self.env = simpy.Environment()

        self.callcenter = CallCenter(self.env,
                                     num_queue_slots,
                                     num_telemarketers,
                                     ivr_max_time,
                                     telemarketer_max_time)
        
        self.demand = Demand(self.env,
                            num_intercall_minutes)


        self.num_costumers_start = num_costumers_start
        self.simulation_time = simulation_time

        random.seed(23)
    
    def start(self):
        for _ in range(self.num_costumers_start):
            customer = self.demand.new_customer()
            self.env.process(customer.call(self.callcenter))

        while True:
            customer = self.demand.new_customer()
            yield self.env.timeout(self.demand.intercall_minutes())
            self.env.process(customer.call(self.callcenter))

    def run(self):
        self.env.process(self.start())
        self.env.run(until=self.simulation_time)


    def stats(self, verbose=False):
        summary={}
        calls = []

        for customer in self.demand.customers:
            for c in customer.calls:
                calls.append(c)

        df = pd.DataFrame(calls)
        df['total'] = df['end'] - df['start']
        
        summary['customers'] = len(df)
        summary['total_avg'] = df.total.mean()
        summary['total_std'] = df.total.std()

        if verbose:
            print(f'\n[TM={self.callcenter.num_telemarketers} ({self.simulation_time} min)]')
            print(f'Customers {summary["customers"]}')
            print(f'Total time average {summary["total_avg"]:.2f} min')
            print(f'Total time standard deviation {summary["total_std"]:.2f} min')
        
        return df, summary


class Demand:
    def __init__(self, env, num_intercall_minutes):
        self.env = env
        self.customers = []
        self.id_customer = 0

        self.num_intercall_minutes = num_intercall_minutes
        self.request = random.choices(['P1', 'P2', 'P3', 'P4', 'P5'], [5, 10, 20, 30, 35])

    def new_customer(self):
        self.id_customer += 1
        customer = Customer(self.env, self.id_customer)
        self.customers.append(customer)
        return customer

    def intercall_minutes(self):
        return self.num_intercall_minutes        

class Customer:
    def __init__(self, env, identifier):
        self.env = env
        self.id = identifier
        self.calls = []

    def call(self, callcenter):
        start_time = self.env.now

        yield self.env.process(callcenter.interact_IVR(self))
        ivr_time = self.env.now

        with callcenter.queue_slot.request() as request:
            yield request
            yield self.env.process(callcenter.asign_telemarketer(self))
        queue_time = self.env.now
        with callcenter.telemarketer.request() as request:
            yield request
            yield self.env.process(callcenter.ask_telemarketer(self))
        ask_time = self.env.now
        end_time = self.env.now

        self._log_call(start_time,
                        ivr_time,
                        queue_time,
                        ask_time,
                        end_time)
        
    def _log_call(self,
                  start_time,
                  ivr_time,
                  queue_time,
                  ask_time,
                  end_time):
        

        l = {}
        l['id'] = self.id
        l['start'] = start_time
        l['ivr'] = ivr_time
        l['queue'] = queue_time
        l['ask'] = ask_time
        l['end'] = end_time

        self.calls.append(l)


class CallCenter:
    def __init__(self,
                 env, 
                 num_queue_slots, 
                 num_telemarketers,
                 ivr_max_time,
                 telemarketer_max_time):
        self.env = env
        self.num_queue_slots = num_queue_slots
        self.num_telemarketers = num_telemarketers
        self.ivr_max_time = ivr_max_time
        self.telemarketer_max_time = telemarketer_max_time
        # Resources
        self.queue_slot = simpy.Resource(env, num_queue_slots)
        self.telemarketer = simpy.Resource(env, num_telemarketers)   

    # Processes
    def interact_IVR(self, customer):
        yield self.env.timeout(random.randint(1, self.ivr_max_time))

    def asign_telemarketer(self, customer):
        yield self.env.timeout(1/60)

    def ask_telemarketer(self, customer):
        yield self.env.timeout(random.randint(1, self.telemarketer_max_time))