import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = 10.0 # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 12.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
LOAD=SERVICE/ARRIVAL # This relationship holds for M/M/1

TYPE1 = 1 

SIM_TIME = 500000

arrivals=0
users=0
BusyServer=False # True: server is currently busy; False: server is currently idle
serviceTime =0
delays = []
MG1=[]

def RTPservice():
    packetChoosen = random.randint(0,10)
    if packetChoosen > 3:
        packetChoosen = 1
    else:
        packetChoosen = 0
    if packetChoosen==1:
        out = random.gauss((SERVICE/10)*7,SERVICE/10)
        #out = random.gauss((SERVICE/11.63)*7,SERVICE/10)
        while out<0:
            out = random.gauss((SERVICE/10)*7,SERVICE/10)
            #out = random.gauss((SERVICE/11.63)*7,SERVICE/10)
        return out
    else:
        out = random.gauss((SERVICE/10)*3,SERVICE/5)
        while out<0:
            out = random.gauss((SERVICE/10)*3,SERVICE/5)
        return out
    
def UniformServiceTime():
    out = random.uniform(0,SERVICE)
    return out

def GaussianServiceTime():
    while True:
        out = random.gauss(SERVICE/2,SERVICE/5)
        if out > 0:
            return out

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
    global serviceTime
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

        #service_time = RTPservice()
        #service_time = UniformServiceTime()
        service_time = GaussianServiceTime()

        serviceTime += service_time

        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

# ******************************************************************************

# departures *******************************************************************
def departure(time, FES, queue):
    global users
    global serviceTime
    global delays
    #print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )
        
    # cumulate statistics
    data.dep += 1
    data.ut += users*(time-data.oldT)
    data.oldT = time
    
    # get the first element from the queue
    client = queue.pop(0)
    
    # do whatever we need to do when clients go away
    
    packet_delay = abs(time-client.arrival_time)
    data.delay += packet_delay
    # if packet_delay < 0:
    #     packet_delay = 0 #solve a precision problem for few packets
    delays.append(packet_delay)
    users -= 1
    
    # see whether there are more clients to in the line
    if users >0:
        # sample the service time

        #service_time = RTPservice()
        #service_time = UniformServiceTime()
        service_time = GaussianServiceTime()

        serviceTime += service_time

        # schedule when the client will finish the server
        FES.put((time + service_time, "departure"))

        
# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************

random.seed(42)

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
        arrival(time, FES, MG1)

    elif event_type == "departure":
        departure(time, FES, MG1)

# print output data
print("MEASUREMENTS \n\nNo. of users in the queue:",users,"\nNo. of arrivals =",
      data.arr,"- No. of departures =",data.dep)

print("Load: ",SERVICE/ARRIVAL)
print("\nArrival rate: ",data.arr/time," - Departure rate: ",data.dep/time)

print("\nAverage number of users: ",data.ut/time)

print("Average delay: ",data.delay/data.dep)
print("Actual queue size: ",len(MG1))

if len(MG1)>0:
    print("Arrival time of the last element in the queue:",MG1[len(MG1)-1].arrival_time)
print(f"Avarage service time: {serviceTime/data.dep}")

#service_times = [RTPservice() for _ in range(10000)]
#service_times = [UniformServiceTime() for _ in range(10000)]
service_times = [GaussianServiceTime() for _ in range(10000)]
plt.figure(figsize=(10, 6))
plt.hist(service_times, bins=30, alpha=0.50, color='blue', edgecolor='black')
plt.xlabel('Service time')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

plt.hist(delays, bins=30, alpha=0.75)
plt.xlabel('Time in the system') #tempo che un pacchetto trascorre nel sistema, include sia il tempo trascorso in coda in attesa che il tempo di servizio effettivo  
plt.ylabel('frequency')
plt.grid(True)
plt.show()
    
