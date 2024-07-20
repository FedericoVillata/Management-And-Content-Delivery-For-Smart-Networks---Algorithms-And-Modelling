#!/usr/bin/python3

import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = 4.5 # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 5.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
LOAD=(SERVICE/ARRIVAL) # This relationship holds for M/M/1

TYPE1 = 1 

SIM_TIME = 500000

arrivals=0
users1=0
users2=0
BusyServer=False # True: server is currently busy; False: server is currently idle

queue1=[]
queue2=[]


# ******************************************************************************
# To take the measurements
# ******************************************************************************
class Measure:
    def __init__(self,Narr,Ndep,NAveraegUser,OldTimeEvent,AverageDelay):
        self.arr = Narr
        self.dep = Ndep
        self.ut = NAveraegUser
        self.oldT = OldTimeEvent
        self.delay = AverageDelay
        
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
def arrival(time, FES, queue1, queue2):
    global users1
    global users2
    queueChoosen = random.randint(1,2)
    if queueChoosen > 1:
        queueChoosen = 1
    else:
        queueChoosen = 0
    #print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )
    if queueChoosen == 0:
        
        # cumulate statistics
        data1.arr += 1
        data1.ut += users1*(time-data1.oldT)
        data1.oldT = time

        # sample the time until the next event
        inter_arrival = random.expovariate(lambd=1.0/ARRIVAL)
        
        # schedule the next arrival
        FES.put((time + inter_arrival, "arrival", "d"))

        users1 += 1
        
        # create a record for the client
        client = Client(TYPE1,time)

        # insert the record in the queue
        queue1.append(client)

        # if the server is idle start the service
        if users1==1:
            
            # sample the service time
            service_time = random.expovariate(1.0/SERVICE)
            #service_time = 1 + random.uniform(0, SEVICE_TIME)

            # schedule when the client will finish the server
            FES.put((time + service_time, "departure", queueChoosen))
    else:
    
        # cumulate statistics
        data2.arr += 1
        data2.ut += users2*(time-data2.oldT)
        data2.oldT = time

        # sample the time until the next event
        inter_arrival = random.expovariate(lambd=1.0/ARRIVAL)
        
        # schedule the next arrival
        FES.put((time + inter_arrival, "arrival", "d"))

        users2 += 1
        
        # create a record for the client
        client = Client(TYPE1,time)

        # insert the record in the queue
        queue2.append(client)

        # if the server is idle start the service
        if users2==1:
            
            # sample the service time
            service_time = random.expovariate(1.0/SERVICE)
            #service_time = 1 + random.uniform(0, SEVICE_TIME)

            # schedule when the client will finish the server
            FES.put((time + service_time, "departure", queueChoosen))

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue1, queue2, choosen):
    global users1
    global users2

    #print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )
    if choosen == 0:    
        # cumulate statistics
        data1.dep += 1
        data1.ut += users1*(time-data1.oldT)
        data1.oldT = time
        
        # get the first element from the queue
        client = queue1.pop(0)
        
        # do whatever we need to do when clients go away
        
        data1.delay += (time-client.arrival_time)
        users1 -= 1
        
        # see whether there are more clients to in the line
        if users1 >0:
            # sample the service time
            service_time = random.expovariate(1.0/SERVICE)

            # schedule when the client will finish the server
            FES.put((time + service_time, "departure", choosen))
    else:    
        # cumulate statistics
        data2.dep += 1
        data2.ut += users2*(time-data2.oldT)
        data2.oldT = time
        
        # get the first element from the queue
        client = queue2.pop(0)
        
        # do whatever we need to do when clients go away
        
        data2.delay += (time-client.arrival_time)
        users2 -= 1
        
        # see whether there are more clients to in the line
        if users2 >0:
            # sample the service time
            service_time = random.expovariate(1.0/SERVICE)

            # schedule when the client will finish the server
            FES.put((time + service_time, "departure", choosen))

        
# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************

random.seed(42)

data1 = Measure(0,0,0,0,0)
data2 = Measure(0,0,0,0,0)

# the simulation time 
time = 0

# the list of events in the form: (time, type)
FES = PriorityQueue()


# schedule the first arrival at t=0
FES.put((0, "arrival", "d"))

# simulate until the simulated time reaches a constant
while time < SIM_TIME:
    (time, event_type, choosen) = FES.get()

    if event_type == "arrival":
        arrival(time, FES, queue1, queue2)

    elif event_type == "departure":
        departure(time, FES, queue1, queue2, choosen)

# print output data
print("================================QUEUE1================================")
print("MEASUREMENTS \n\nNo. of users in the queue:",users1,"\nNo. of arrivals =",
      data1.arr,"- No. of departures =",data1.dep)

print("Load: ",(SERVICE/ARRIVAL))
print("\nArrival rate: ",data1.arr/time," - Departure rate: ",data1.dep/time)

print("\nAverage number of users: ",data1.ut/time)

print("Average delay: ",data1.delay/data1.dep)
print("Actual queue size: ",len(queue1))

if len(queue1)>0:
    print("Arrival time of the last element in the queue:",queue1[len(queue1)-1].arrival_time)

print("================================QUEUE2================================")    
print("MEASUREMENTS \n\nNo. of users in the queue:",users2,"\nNo. of arrivals =",
      data2.arr,"- No. of departures =",data2.dep)

print("Load: ",SERVICE/ARRIVAL)
print("\nArrival rate: ",data2.arr/time," - Departure rate: ",data2.dep/time)

print("\nAverage number of users: ",data2.ut/time)

print("Average delay: ",data2.delay/data2.dep)
print("Actual queue size: ",len(queue2))

if len(queue2)>0:
    print("Arrival time of the last element in the queue:",queue2[len(queue2)-1].arrival_time)
    
