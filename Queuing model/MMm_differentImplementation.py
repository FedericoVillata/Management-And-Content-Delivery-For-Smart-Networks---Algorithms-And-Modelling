#!/usr/bin/python3

import random
from queue import Queue, PriorityQueue

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = 10.0 # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 5.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
LOAD=SERVICE/ARRIVAL # This relationship holds for M/M/1

TYPE1 = 1 

SIM_TIME = 500000

arrivals=0
users=0
BusyServer=False # True: server is currently busy; False: server is currently idle

MM1=[]
QUEUE_SIZE = 0


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
        self.server = -1
    def setServer(self, id):
        self.server = id

# ******************************************************************************
# Server
# ******************************************************************************
class Server(object):

    # constructor
    def __init__(self, num_servers):

        # whether the server is idle or not
        self.servers = []
        self.num_servers = num_servers
        for i in range(num_servers):
            self.servers.append(0)
        
    def getIdleID(self): #if server busy return 2
        for i in range(self.num_servers):
            if self.servers[i] == 0:
                return i
        return -1

    def changeState(self, id):
        if self.servers[id] == 0:
            self.servers[id] = 1
        else:
            self.servers[id] = 0


# ******************************************************************************

# arrivals *********************************************************************
def arrival(time, FES, queue, server):
    global users
    global QUEUE_SIZE
    
    #print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )
    
    # cumulate statistics
    data.arr += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time

    # sample the time until the next event
    inter_arrival = random.expovariate(lambd=1.0/ARRIVAL)
    
    # schedule the next arrival
    FES.put((time + inter_arrival, "arrival", "d", "d"))

    users += 1
    
    # create a record for the client
    client = Client(TYPE1,time)

    

    # if the server is idle start the service
    idleID = server.getIdleID()
    if idleID != -1:
        client.setServer(idleID)
        server.changeState(idleID)
        # sample the service time
        service_time = random.expovariate(1.0/SERVICE)
        #service_time = 1 + random.uniform(0, SEVICE_TIME)

        # schedule when the client will finish the server
        FES.put((time + service_time, "departure", client,idleID))
        print(f"departure set for{client}, {idleID}")
    else:
        queue.append(client)
    # insert the record in the queue
    QUEUE_SIZE += 1
    print(f"arrival{len(queue)}")
    print(server.servers)

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue, client, serverId, server):
    global users
    global QUEUE_SIZE
    
    #print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )
        
    # cumulate statistics
    data.dep += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time
    # get the first element from the queue
    QUEUE_SIZE -= 1
    
    # do whatever we need to do when clients go away
    
    data.delay += (time-client.arrival_time)
    users -= 1
    userServer = client.server
    print(len(queue))
    # see whether there are more clients to in the line
    if len(queue) > 0:
        # sample the service time
        service_time = random.expovariate(1.0/SERVICE)

        # schedule when the client will finish the server
        client = queue.pop(0)
        FES.put((time + service_time, "departure", client, serverId))
        print(f"departure{client}, {userServer}")
    else: 
        server.changeState(serverId)
    print(f"departure{len(queue)}")
    print(server.servers)
    
    

        
# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************

random.seed(42)

data = Measure(0,0,0,0,0)

# the simulation time 
time = 0

# the list of events in the form: (time, type, client, server)
FES = PriorityQueue()


# schedule the first arrival at t=0
FES.put((0, "arrival", "d", "d"))
num_servers = 2
server = Server(num_servers)

# simulate until the simulated time reaches a constant
while time < SIM_TIME:
    (time, event_type, client, serverId) = FES.get()

    if event_type == "arrival":
        arrival(time, FES, MM1,server)

    elif event_type == "departure":
        departure(time, FES, MM1, client, serverId, server)

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
    
