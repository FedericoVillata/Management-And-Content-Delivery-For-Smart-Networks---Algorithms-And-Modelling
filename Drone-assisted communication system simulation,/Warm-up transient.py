#!/usr/bin/python3

import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt
import numpy as np

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = 9.9 # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 10.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
LOAD=SERVICE/ARRIVAL # This relationship holds for M/M/1

TYPE1 = 1 

SIM_TIME = 500000

arrivals=0
users=0
BusyServer=False # True: server is currently busy; False: server is currently idle
delayVector = []
allDiffs = []
singleDepDelay = []
singleBufferTime = []
lastDelay = 0
firstCycle = 0
steadyStateIndex = 0
steadyStateFlag = 0
MM1=[]


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
def arrival(time, FES, queue):
    global users
    global singleDepDelay
    
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
        service_time = random.expovariate(1.0/SERVICE)
        #service_time = 1 + random.uniform(0, SEVICE_TIME)
        
        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue):
    global users
    global delayVector
    global singleDepDelay
    global singleBufferTime
    #print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )
        
    # cumulate statistics
    data.dep += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time
    
    # get the first element from the queue
    client = queue.pop(0)
    # do whatever we need to do when clients go away
    
    data.delay += (time-client.arrival_time)
    delayVector.append(data.delay/data.dep)
    singleDepDelay.append(time-client.arrival_time)
    users -= 1
    
    # see whether there are more clients to in the line
    if users >0:
        # sample the service time
        service_time = random.expovariate(1.0/SERVICE)
        singleBufferTime.append(time-client.arrival_time)
        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

        
# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************

random.seed(27)

data = Measure(0,0,0,0,0)

# the simulation time 
time = 0

# the list of events in the form: (time, type)
FES = PriorityQueue()


# schedule the first arrival at t=0
FES.put((0, "arrival"))

# simulate until the simulated time reaches a constant
while time < SIM_TIME:
    (time, event_type) = FES.get()

    if event_type == "arrival":
        arrival(time, FES, MM1)

    elif event_type == "departure":
        departure(time, FES, MM1)

# print output data
print("MEASUREMENTS \n\nNo. of users in the queue:",users,"\nNo. of arrivals =",
      data.arr,"- No. of departures =",data.dep)

print("Load: ",SERVICE/ARRIVAL)
print("\nArrival rate: ",data.arr/time," - Departure rate: ",data.dep/time)

print("\nAverage number of users: ",data.ut/time)

print("Average delay: ",data.delay/data.dep)
print("Actual queue size: ",len(MM1))

if len(MM1)>0:
    print("Arrival time of the last element in the queue:",MM1[len(MM1)-1].arrival_time)
    
print(f"Steady state index: {steadyStateIndex}")
plt.figure()
plt.plot(np.arange(0, data.dep), delayVector)
plt.title("Avarage Delay")
plt.xlabel("Departures")
plt.ylabel("Delay")
plt.savefig("avgDelay1a.png")
plt.show()

plt.figure()
plt.plot(np.arange(0, data.dep), singleDepDelay)
plt.title("Single Departure Delay")
plt.xlabel("Departures")
plt.ylabel("Delay")
plt.savefig("singleDelay1a.png")
plt.show()




meanDelayVec = np.mean(delayVector)
meanAvgDelay = data.delay/data.dep
print(meanAvgDelay-meanDelayVec)


avgDelayVec = []
relativeVariation = []
relativeVariation1 = []
n = int(20000)
index = 0
smallest = 1
for i in range(n):
    avgDelayVec.append(sum(delayVector[i+1:n])/(n-i))
    #print(avgDelayVec[i])
    relativeVariation.append(abs(avgDelayVec[i] - meanAvgDelay)/meanAvgDelay)
    relativeVariation1.append(abs(avgDelayVec[i] - meanDelayVec)/meanDelayVec)
    if relativeVariation[i] < smallest:
        index = i
        smallest = relativeVariation[i]
        
print(f"index: {index}")
#plt.plot(np.arange(0, int(n)), avgDelayVec[0:int(n)])
x = np.arange(0, index+3000)
y1 = avgDelayVec[0:index+3000]
y2 = relativeVariation[0:index+3000]

fig, ax1 = plt.subplots()

ax1.plot(x,y1, "r", label = "Average Delay")
ax1.set_xlabel("Index of canceled observations")
ax1.set_ylabel("Delay")

ax2 = ax1.twinx()
ax2.plot(x,y2, label = "Relative Variation")
ax2.set_ylabel("Variation")
fig.legend()
plt.savefig("1b.png")
plt.show()
