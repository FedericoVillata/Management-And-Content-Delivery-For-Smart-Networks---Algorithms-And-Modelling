import random
from queue import Queue, PriorityQueue

from matplotlib import pyplot as plt
import numpy as np

# ******************************************************************************
# Constants
# ******************************************************************************

#SERVICE = 10.0 # SERVICE is the average service time; service rate = 1/SERVICE
#ARRIVAL = 5.0 # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
#LOAD=SERVICE/ARRIVAL # This relationship holds for M/M/1

TYPE1 = 1 

SIM_TIME = 43199 #seconds in 12 hours
ACTIVE_TIME = 25*60 #seconds of active flight od drone
RECHARGE_TIME = 60*60 #seconds of recharging drone

BusyServer=False # True: server is currently busy; False: server is currently idle

MM1=[]
MM2 = []
QUEUE_SIZE = 0

def gaussian(x, mu, sig):
    return (
        1.0 / (np.sqrt(2.0 * np.pi) * sig) * np.exp(-np.power((x - mu) / sig, 2.0) / 2)
    )
    
def arrivalGauss(index):
    x = np.linspace(8, 20, index)

    y1 = gaussian(x, 10, 1)
    y2 = gaussian(x, 15, 1)
    y3 = gaussian(x, 12, 1)
    sum = 1*10/(y1 + y2 + y3 + 0.5)
    return sum

SERVICE0 = 10.0
SERVICE1 = 10.0
ARRIVAL = arrivalGauss(SIM_TIME+1) #ARRIVAL between 10 and 20
#LOAD=SERVICE/ARRIVAL
NUM_QUEUE = 2
users0 = 0
users1 = 0
queue0 = []
queue1 = []
loadBase = []
loadDrone = []
load = []

isUp = False 

times = 0 
timesQueue1 = 0

    

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

class Drone:
    def __init__(self, service_time, battery_capacity, recharge_time, buffer_size, pv_capacity):
        self.pv_capacity = pv_capacity
        self.landing_time = 0
        if pv_capacity == 45:
            self.pv_recharge_seconds = 10/35
            self.battery_capacity = battery_capacity+10*60
        elif pv_capacity == 65:
            self.pv_recharge_seconds = 15/40
            self.battery_capacity = battery_capacity+15*60
        elif pv_capacity == 75:
            self.pv_recharge_seconds = 20/45
            self.battery_capacity = battery_capacity+20*60
        elif pv_capacity == 0:
            self.pv_recharge_seconds = 0
            self.battery_capacity = battery_capacity              
        self.recharge_time = recharge_time
        self.battery_level = battery_capacity
        self.flag_charge = 0
        self.buffer_size = buffer_size
        self.losses = 0
        self.num_takeoff = 0
        self.service_time = service_time
        self.already_reduced = 0
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
def arrival(time, FES, queue0,queue1, server0,server1, drone):
    global users0
    global users1
    global isUp
    global times
    global timesQueue1
    if isUp:
        if drone.landing_time < int(time):
            print(f"Landing number {drone.num_takeoff} at time {int(time)}")
            drone.num_takeoff += 1
            isUp = False
            send_drone2recharge(time, FES, drone)
            queueChoosen = 0
        else:
            #print(f"landing time > 16------- {drone.landing_time - drone.battery_capacity}")    
            if drone.landing_time - drone.battery_capacity < 8*60*60 and int(time) >= 8*60*60 and drone.pv_capacity != 0 and drone.already_reduced == 0:
                print("reducing time")
                drone.already_reduced = 1
                drone.landing_time -= drone.pv_recharge_seconds*(drone.landing_time-int(time))
        #print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )
        #test = (ARRIVAL[int(time)]- ARRIVAL[int(time)-10])/60
    elif drone.flag_charge == 0 and ARRIVAL[int(time)]<18: #and (ARRIVAL[int(time)]<11 or ((ARRIVAL[int(time)]- ARRIVAL[int(time)-60])/60 < 0 and ARRIVAL[int(time)]<12)):
        isUp = True
        print(f"TakeOff number {drone.num_takeoff} at time {int(time)}")
        if int(time) > 8*60*60:
            drone.battery_capacity = 25*60
            drone.battery_level = 25*60
        drone.landing_time = int(time)+drone.battery_capacity          
    else:
        queueChoosen = 0
    if isUp:
        load.append((SERVICE1/server1.num_servers/ARRIVAL[int(time)]/2, int(time)))
        loadBase.append(SERVICE0/server0.num_servers/ARRIVAL[int(time)]/2)
        loadDrone.append(SERVICE1/server1.num_servers/ARRIVAL[int(time)]/2)
        times += 1
        queueChoosen = random.randint(0,10)
        if queueChoosen > 4:
            queueChoosen = 1
            timesQueue1 += 1
        else:
            queueChoosen = 0 
    else:
        load.append((0, int(time)))
        loadDrone.append(0)
        loadBase.append(SERVICE0/server0.num_servers/ARRIVAL[int(time)])

    
    inter_arrival = ARRIVAL[int(time)]    
    # Schedule the next arrival
    FES.put((time + inter_arrival, "arrival", "d" , "d", "d"))
    if queueChoosen == 1:
        service_time = random.expovariate(1.0/SERVICE1)
        idleID = server1.getIdleID()
        if idleID != -1 and drone.landing_time >= int(time) + service_time:
            client = Client(TYPE1,time)
            client.setServer(idleID)
            server1.changeState(idleID)
            data1.arr += 1
            data1.ut += users1*(time-data1.oldT)
            data1.oldT = time
            users1 += 1
            #print(f"Departure set for {client}, {idleID}")
            # Check if the drone needs to be sent        
            FES.put((time + service_time, "departure", client, queueChoosen,idleID))
        elif drone.landing_time < int(time) + service_time:
            print(f"Landing number {drone.num_takeoff} at time {int(time)}")
            drone.num_takeoff += 1
            drone.losses += 1
            queueChoosen = 0
            isUp = False
            send_drone2recharge(time, FES, drone)
        elif idleID == -1 and len(queue1) < drone.buffer_size:
            data1.arr += 1
            data1.ut += users1*(time-data1.oldT)
            data1.oldT = time
            users1 += 1
            client = Client(TYPE1,time)
            queue1.append(client)
        if len(queue1) >= drone.buffer_size:
            drone.losses += 1
            queueChoosen = 0
    if queueChoosen == 0:    
    # Cumulate statistics
        data0.arr += 1
        data0.ut += users0*(time-data0.oldT)
        data0.oldT = time
        users0 += 1    
        # Create a record for the client
        client = Client(TYPE1,time)
    # If the server is idle start the service
        idleID = server0.getIdleID()
        if idleID != -1:
            client.setServer(idleID)
            server0.changeState(idleID)
            # Sample the service time
            service_time = random.expovariate(1.0/SERVICE0)

            # Schedule when the client will finish the server
            FES.put((time + service_time, "departure", client, queueChoosen,idleID))
            #print(f"Departure set for {client}, {idleID}")
        else:
            queue0.append(client)
    
    # Insert the record in the queue
    #QUEUE_SIZE += 1
    #print(f"Arrival {len(queue)}")
    #print(server.servers)
    
        

# departures *******************************************************************
def departure(time, FES, queue, client, queueChoosen, serverId):
    global users0
    global users1
    global queue0
    
    
    if queueChoosen == 0:
        # Cumulate statistics
        data0.dep += 1
        data0.ut += users0*(time-data0.oldT)
        data0.oldT = time
        # Get the first element from the queue
        
        # Do whatever we need to do when clients go away
        
        data0.delay += (time-client.arrival_time)
        users0 -= 1
        userServer = client.server
        #print(len(queue))
        # See whether there are more clients to in the line
        if len(queue) > 0:
            # Sample the service time
            service_time = random.expovariate(1.0/SERVICE0)

            # Schedule when the client will finish the server
            client = queue.pop(0)
            FES.put((time + service_time, "departure", client, queueChoosen, serverId))
            #print(f"Departure {client}, {userServer}")
        else: 
            server0.changeState(serverId)
        #print(f"Departure {len(queue)}")
        #print(server.servers)
    else:
        # Cumulate statistics
        data1.dep += 1
        data1.ut += users1*(time-data1.oldT)
        data1.oldT = time
        # Get the first element from the queue
        
        # Do whatever we need to do when clients go away
        
        data1.delay += (time-client.arrival_time)
        users1 -= 1
        userServer = client.server
        #print(len(queue))
        # See whether there are more clients to in the line
        if len(queue) > 0:
            # Sample the service time
            service_time = random.expovariate(1.0/SERVICE1)
            
            if drone.landing_time > int(time) + service_time:
                # Schedule when the client will finish the server
                client = queue.pop(0)
                FES.put((time + service_time, "departure", client, queueChoosen, serverId))
                #print(f"Departure {client}, {userServer}")
            else:
                print(f"Landing number {drone.num_takeoff} at time {drone.landing_time}")
                drone.num_takeoff += 1
                isUp = False
                send_drone2recharge(time, FES, drone)
                for i in range(len(queue)):
                    queue0.append(queue.pop(0))
                    users0 += 1        
        else: 
            server1.changeState(serverId)
        


# ******************************************************************************
# Function to send the drone
# ******************************************************************************
def send_drone2recharge(time, FES, drone):
    
    # Set the drone's active time to zero
    drone.flag_charge = 1
    drone.battery_level = drone.battery_capacity
    # Check if the battery is empty
    
    # Schedule the recharge time
    FES.put((time + drone.recharge_time, "drone_charged", "d","d", "d"))
    print(f"Drone sent for recharge at time: {time}, landing time: {drone.landing_time}")
    #drone_recharge(time,FES,drone)
    # if drone.flag_charge==0:
    #     # Schedule the next time to send the drone
    #     FES.put((time + drone.recharge_time, "drone_send", "d", "d"))
    #     print("Drone sent for service")


# ******************************************************************************
# Function to recharge the drone
# ******************************************************************************
def drone_recharge(time, FES, drone):
    i=0
    while i<drone.recharge_time:
        i+=1
    drone.flag_charge=0
    drone.battery_level = drone.battery_capacity
    print("Drone fully recharged")


# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************
random.seed(19)

data0 = Measure(0,0,0,0,0)
data1 = Measure(0,0,0,0,0)

# The simulation time 
time = 0
time_r =0
# The list of events in the form: (time, type, client, server)
FES = PriorityQueue()

# Initialize the drone
#Possible PV capacities = [0,45,65,75]
drone = Drone(SERVICE1,battery_capacity=ACTIVE_TIME, recharge_time=RECHARGE_TIME, buffer_size=10, pv_capacity=75)

# Schedule the first arrival at t=0
FES.put((0, "arrival","d", "d", "d"))
num_servers0 = 1
num_servers1 = 1
server0 = Server(num_servers0)
server1 = Server(num_servers1)

# Simulate until the simulated time reaches a constant
while time < SIM_TIME:
    (time, event_type, client, queueChoosen, serverId) = FES.get()
    if time > SIM_TIME:
        break

    if event_type == "arrival":
        arrival(time, FES, queue0 ,queue1, server0, server1, drone)

    elif event_type == "departure":
        if queueChoosen == 0:
            departure(time, FES, queue0, client, queueChoosen, serverId)
        else:
            departure(time, FES, queue1, client, queueChoosen, serverId)

    elif event_type == "drone_charged":
        #drone_recharge(time, FES, drone)
        drone.flag_charge = 0
        

# Print output data
print("================================DRONE================================")
print("MEASUREMENTS \n\nNo. of users in the queue:",users1,"\nNo. of arrivals =",
    data1.arr,"- No. of departures =",data1.dep)

#print("Load: ",SERVICE/ARRIVAL)
print("\nArrival rate: ",data1.arr/time," - Departure rate: ",data1.dep/time)

print("\nAverage number of users: ",data1.ut/time)

print("Average delay: ",data1.delay/data1.dep)
print("Actual queue size: ",len(queue1))

if len(queue1)>0:
    print("Arrival time of the last element in the queue:",queue1[len(queue1)-1].arrival_time)

print("================================BASESTATION================================")    
print("MEASUREMENTS \n\nNo. of users in the queue:",users0,"\nNo. of arrivals =",
    data0.arr,"- No. of departures =",data0.dep)

#print("Load: ",SERVICE/ARRIVAL)

prev_val = 0
abs_time = 0
actual_load = []
for val, time in load:
    for t in range(abs_time, time):
        actual_load.append(prev_val)
    prev_val = val
    abs_time = time

plt.figure()
#plt.plot(np.linspace(8, 20, len(loadBase)), loadBase)
#plt.plot(np.linspace(8, 20, len(loadDrone)), loadDrone)
plt.plot(np.linspace(8, 20, len(actual_load)), actual_load)
plt.title("LOAD DRONE")
plt.xlabel("Working hours")
plt.ylabel("load")
plt.savefig("load3SecondSchedulePV75.png")
plt.show()
#plt.figure()
#plt.plot(np.linspace(8, 20, len(ARRIVAL)), 1/ARRIVAL)
#plt.title("ARRIVAL RATE")
#plt.xlabel("Working hours")
#plt.ylabel("Arrival rate")
#plt.savefig("ArrivalRate2.png")
#plt.show()

print("\nArrival rate: ",data0.arr/time," - Departure rate: ",data0.dep/time)

print("\nAverage number of users: ",data0.ut/time)

print("Average delay: ",data0.delay/data0.dep)
print("Actual queue size: ",len(queue0))

if len(queue0)>0:
    print("Arrival time of the last element in the queue:",queue0[len(queue0)-1].arrival_time)
    
print(f"Drone losses: {drone.losses}")

print(f"Percentage of packets served by the: {data1.dep/(data0.dep+data1.dep)*100}%")

print(f"Drone choosen {timesQueue1} times in {times}")