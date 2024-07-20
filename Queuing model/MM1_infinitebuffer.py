#!/usr/bin/python3

import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = [2.5, 3.0, 3.5, 4.0, 4.5] # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 5.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL

TYPE1 = 1 

SIM_TIME = 500000

arrivals=0
BusyServer=False # True: server is currently busy; False: server is currently idle

# Numero di simulazioni per calcolare l'intervallo di confidenza
sim_per_conf = 2

# Funzione per calcolare l'intervallo di confidenza
def confidence_interval(data, conf=0.95):
    mean = np.mean(data)
    std_err = st.sem(data)  # Errore standard della media
    interval = std_err * st.t.ppf((1 + conf) / 2., len(data)-1)
    return mean, mean - interval, mean + interval


# ******************************************************************************
# To take the measurements
# ******************************************************************************

class Measure:
    def __init__(self,Narr,Ndep,NAveraegUser,OldTimeEvent,AverageDelay, BusyTime):
        self.arr = Narr
        self.dep = Ndep
        self.ut = NAveraegUser
        self.oldT = OldTimeEvent
        self.delay = AverageDelay
        self.busy_time = BusyTime  # New attribute to measure busy time

        
# ******************************************************************************
# Client
# ******************************************************************************
        
class Client:
    def __init__(self,type,arrival_time):
        self.type = type
        self.arrival_time = arrival_time

# ******************************************************************************
# Server
# ******************************************************************************
        
class Server(object):

    # constructor
    def __init__(self):

        # whether the server is idle or not
        self.idle = True


# ******************************************************************************

# arrivals *********************************************************************
def arrival(time, FES, queue, service, times_user, users_over_time):
    global users
    global packet_loss
    
    #print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )
    
    # cumulate statistics
    data.arr += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time

    # sample the time until the next event
    inter_arrival = random.expovariate(lambd=1.0/ARRIVAL)
    
    # schedule the next arrival
    FES.put((time + inter_arrival, "arrival"))

    users += 1
    users_over_time.append(users)
    times_user.append(time)
    
    # create a record for the client
    client = Client(TYPE1,time)

    # insert the record in the queue
    queue.append(client)

    # if the server is idle start the service
    if users==1:
        
        # sample the service time
        service_time = random.expovariate(1.0/service)
        #service_time = 1 + random.uniform(0, SEVICE_TIME)

        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

        # Update busy time when server starts serving
        data.busy_time += service_time

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue, service, delays, times, times_user, users_over_time):
    global users

    #print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )
        
    # cumulate statistics
    data.dep += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time
    
    # get the first element from the queue
    client = queue.pop(0)
    
    # do whatever we need to do when clients go away
    
    current_delay = (time - client.arrival_time)
    delays.append(current_delay)
    times.append(time)  # Track time of departure
    data.delay += current_delay
    users -= 1

    users_over_time.append(users)
    times_user.append(time)
    
    # see whether there are more clients to in the line
    if users >0:
        # sample the service time
        service_time = random.expovariate(1.0/service)

        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

        # Update busy time when server continues serving
        data.busy_time += service_time

        
# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************

random.seed(42)
results = []
loads = []

for service in SERVICE:
    load = service / ARRIVAL
    loads.append(load)
    all_delays = []  # Accumula i delay di tutte le simulazioni per questo carico
    

    for _ in range(sim_per_conf):
        data = Measure(0,0,0,0,0,0)  # Include busy_time initialization
        MM1 = []  # Reinizializza la coda
        users = 0  # Reinizializza il numero di utenti nel sistema
        packet_loss = 0  # Reinizializza il conteggio dei pacchetti persi
        delays = []
        times = []
        times_user = []
        users_over_time = []

        # the simulation time 
        time = 0

        # the list of events in the form: (time, type)
        FES = PriorityQueue()

        # schedule the first arrival at t=0
        FES.put((0, "arrival"))

        # Reimposta il tempo dell'ultimo evento per evitare discrepanze nel calcolo delle metriche
        data.oldT = 0

        # simulate until the simulated time reaches a constant
        #print(cons_users)
        while time < SIM_TIME:
            (time, event_type) = FES.get()

            if event_type == "arrival":
                arrival(time, FES, MM1, service, times_user, users_over_time)

            elif event_type == "departure":
                departure(time, FES, MM1, service, delays, times, times_user, users_over_time)
        
        mean_delay = np.mean(delays)
        all_delays.append(mean_delay)
    
    mean_delay, lower_bound, upper_bound = confidence_interval(all_delays)
    results.append((mean_delay, lower_bound, upper_bound))

    #print output data

    print("MEASUREMENTS \n\nNo. of users in the queue:",users,"\nNo. of arrivals =",
        data.arr,"- No. of departures =",data.dep)

    print("Load: ", service/ARRIVAL)
    print("\nArrival rate: ",data.arr/time," - Departure rate: ",data.dep/time)

    print("\nAverage number of users: ",data.ut/time)

    print("Average delay: ",data.delay/data.dep)
    print("Actual queue size: ",len(MM1))

    print("Busy time:", data.busy_time)  # Print busy time

    print("packet losses:", packet_loss)

    if load == 0.5 or load == 0.9:
        plt.figure(figsize=(10, 5))
        plt.plot(times, delays)
        plt.xlabel("Time (ms)")
        plt.ylabel("Delay (ms)")
        plt.show()
        # delay istantaneo di ogni pacchetto al momento della sua partenza.
        # Ogni punto sul grafico corrisponde al tempo impiegato da un singolo pacchetto per attraversare il sistema, dall'arrivo alla partenza

        plt.figure(figsize=(12, 6))
        plt.plot(times_user, users_over_time)
        plt.xlabel('Time (ms)')
        plt.ylabel('Average number of users')
        plt.show()

mean_delays, lower_bounds, upper_bounds = zip(*results)
plt.figure(figsize=(10, 5))
plt.plot(SERVICE, mean_delays)
plt.fill_between(SERVICE, lower_bounds, upper_bounds, color='b', alpha=0.2)
plt.xlabel("service")
plt.ylabel("Average delay (ms)")
plt.show()

if len(MM1)>0:
    print("Arrival time of the last element in the queue:",MM1[len(MM1)-1].arrival_time)
