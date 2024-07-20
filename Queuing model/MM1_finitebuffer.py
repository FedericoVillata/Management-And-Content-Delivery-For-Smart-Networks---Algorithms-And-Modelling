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
sim_per_conf = 1

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
        self.loss = 0 #Initialize loss count
        self.busy_time = BusyTime  # Variabile per tracciare il tempo totale in cui il server è occupato

        
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
def arrival(time, FES, queue, service, buffer_size):
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

    elif users > buffer_size:
        users -=1
        packet_loss += 1
        queue.pop()

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue, service, delays):
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
    data.delay += current_delay
    users -= 1
    
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
# Lista per raccogliere i dati: numero di utenti considerati e pacchetti persi corrispondenti
buffer_size_list = []
packet_loss_list = []
avg_delay_list = []
inf_interval_list = []
sup_interval_list = []
results = []
loads = []

for service in SERVICE:
    load = service / ARRIVAL
    loads.append(load)
    all_delays = []  # Accumula i delay di tutte le simulazioni per questo carico

    for buffer_size in range(0,30,2):
        mean_delay = [] #delay medio per simulazione

        for _ in range(sim_per_conf):
            data = Measure(0,0,0,0,0,0)
            MM1 = []  # Reinizializza la coda
            users = 0  # Reinizializza il numero di utenti nel sistema
            packet_loss = 0  # Reinizializza il conteggio dei pacchetti persi
            delays = []

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
                    arrival(time, FES, MM1, service, buffer_size)

                elif event_type == "departure":
                    departure(time, FES, MM1, service, delays)
                
            mean_delay.append(data.delay/data.dep)
            mean_delay_per_service = np.mean(delays)
            all_delays.append(mean_delay_per_service)
        
        if buffer_size == 2:
            mean, lower_bound, upper_bound = confidence_interval(all_delays)
            results.append((mean, lower_bound, upper_bound))
        
        if service == 4.5:
            # Calcolo dell'intervallo di confidenza per il ritardo medio di questa configurazione del buffer size
            media, inf_bound, sup_bound = confidence_interval(mean_delay)
            
            
            buffer_size_list.append(buffer_size)
            packet_loss_list.append(packet_loss)
            avg_delay_list.append(data.delay/data.dep)
            inf_interval_list.append(inf_bound)
            sup_interval_list.append(sup_bound)

        # print output data
        if buffer_size == 4:
            print("MEASUREMENTS \n\nNo. of users in the queue:",users,"\nNo. of arrivals =",
                data.arr,"- No. of departures =",data.dep)

            print("Load: ",service/ARRIVAL)
            print("\nArrival rate: ",data.arr/time," - Departure rate: ",data.dep/time)

            print("\nAverage number of users: ",data.ut/time)

            print("Average delay: ",data.delay/data.dep)
            print("Actual queue size: ",len(MM1))

            print("Busy time:", data.busy_time)  

            print("packet losses:", packet_loss)

# Creazione dei grafici

mean, lower_bounds, upper_bounds = zip(*results)
plt.figure(figsize=(10, 5))
plt.plot(SERVICE, mean)
plt.fill_between(SERVICE, lower_bounds, upper_bounds, color='b', alpha=0.2)
plt.xlabel("service time")
plt.ylabel("Delay (ms)")
plt.legend()
plt.show()

print(load)
plt.figure(figsize=(10, 6))
plt.plot(buffer_size_list, packet_loss_list, marker='o', linestyle='-', color='b')
plt.xlabel('Buffer size')
plt.ylabel('Packet losses')
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(buffer_size_list, avg_delay_list, marker='o', linestyle='-', color='b')
plt.xlabel('Buffer size')
plt.ylabel('avg delay')
plt.grid(True)
plt.show()

# Creazione del grafico per il ritardo medio
plt.figure(figsize=(10, 6))
plt.plot(buffer_size_list, avg_delay_list, marker='o', linestyle='-', color='b')
# Aggiunta dell'intervallo di confidenza
plt.fill_between(buffer_size_list, inf_interval_list, sup_interval_list, color='b', alpha=0.2, label='confidence interval')
plt.xlabel('buffer size')
plt.ylabel('average delay (with confidence interval)')
plt.legend()
plt.grid(True)
plt.show()

if len(MM1)>0:
    print("Arrival time of the last element in the queue:",MM1[len(MM1)-1].arrival_time)
