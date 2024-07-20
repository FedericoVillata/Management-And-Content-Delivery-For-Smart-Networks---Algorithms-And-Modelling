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

#BusyServer=False # True: server is currently busy; False: server is currently idle

#MM1=[]
#MM2 = []
#QUEUE_SIZE = 0

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


SERVICE_BASE = 10.0
SERVICE_DRONE = 20.0
ARRIVAL = arrivalGauss(SIM_TIME+1) #ARRIVAL between 10 and 20
COEFF = 1
NUM_DRONES = []
DEPARTURES = 0
#LOAD=SERVICE/ARRIVAL
#NUM_QUEUE = 2
PACKET_DEP_TIME = []
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

class BaseStation:
    def __init__(self, baseID, serviceTime, numServers):
        self.id = baseID
        self.serviceTime = serviceTime
        self.numServers = numServers
        self.servers = Server(numServers)
        self.queue = []
        self.data =  Measure(0,0,0,0,0)
        self.users = 0

class Drone:
    def __init__(self,droneID, service_time, num_servers, battery_capacity, recharge_time, buffer_size, pv_capacity):
        self.id = droneID
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
        self.flag_charge = 0
        self.buffer_size = buffer_size
        self.losses = 0
        self.losses_battery = 0
        self.num_takeoff = 0
        self.service_time = service_time
        self.isUp = False
        self.num_servers = num_servers
        self.servers = Server(num_servers)
        self.queue = []
        self.data =  Measure(0,0,0,0,0)
        self.users = 0
        self.load = []
        self.actual_load = []
    def send2recharge(self, time, FES, index, test):
        # Set the drone's active time to zero
        #print(test)
        self.flag_charge = 1   
        self.isUp = False
        packetsLost = self.servers.resetServers()
        self.users -= packetsLost
        # Schedule the recharge time
        FES.put((time + self.recharge_time, "drone_charged", "null", index, "null"))
        print(f"{self.id} sent for recharge at time: {time}, landing time: {self.landing_time}")
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
    def resetServers(self):
        count = 0
        for i in range(self.num_servers):
            if self.servers[i] == 1:
                count += 1
            self.servers[i] = 0
        return count
    def changeState(self, id):
        if self.servers[id] == 0:
            self.servers[id] = 1
        else:
            self.servers[id] = 0


# ******************************************************************************

# arrivals *********************************************************************
def arrival(time, FES, baseStation, drones):   
    active_drones_indexes = []
    index = 0
    for d in drones:
        if d.isUp:
            if d.landing_time < int(time):
                #print(f"Landing number {d.num_takeoff} at time {int(time)}")
                d.num_takeoff += 1
                d.send2recharge(time, FES, index, "arr")
                for c in d.queue:
                    baseStation.queue.append(c)
                    d.losses_battery += 1
                    d.users -= 1
                    baseStation.users += 1
                d.queue = []
                
            else:
                if d.landing_time - d.battery_capacity < 8*60*60 and int(time) >= 8*60*60:
                    d.landing_time -= d.pv_recharge_seconds*(d.landing_time-int(time))
                active_drones_indexes.append(index)
            index += 1            
        elif d.flag_charge == 0 and ARRIVAL[int(time)] < 18/(1+len(active_drones_indexes)/5): #and condition
            #drone sent -> modify the condition such that the next drone doesnt take off
            d.isUp = True
            print(f"{d.id} takeOff number: {d.num_takeoff} at time {int(time)}")
            if int(time) > 8*60*60:
                d.battery_capacity = 25*60
            d.landing_time = int(time)+d.battery_capacity
            active_drones_indexes.append(index)
            index += 1
        else:
            index += 1
    NUM_DRONES.append((len(active_drones_indexes), int(time)))
    queueChoosen = random.randint(0,len(active_drones_indexes))
    inter_arrival = ARRIVAL[int(time)]
    FES.put((time + inter_arrival, "arrival", "null" , "null", "null"))
    for d in drones:
        if d.isUp:
            d.load.append(((d.service_time/d.num_servers)/ARRIVAL[int(time)]/(len(active_drones_indexes)+1),int(time)))
        else:
            d.load.append((0, int(time)))
    if queueChoosen != 0:
        droneChoosen = active_drones_indexes[queueChoosen-1]
    if queueChoosen != 0:
        droneChoosen = active_drones_indexes[queueChoosen-1]
        service_time = random.expovariate(1.0/drones[droneChoosen].service_time)
        idleID = drones[droneChoosen].servers.getIdleID()
        if idleID != -1 and drones[droneChoosen].landing_time >= int(time) + service_time:
            drones[droneChoosen].data.arr += 1
            drones[droneChoosen].data.ut += drones[droneChoosen].users*(time-drones[droneChoosen].data.oldT)
            drones[droneChoosen].data.oldT = time
            drones[droneChoosen].users += 1
            client = Client(TYPE1,time)
            client.setServer(idleID)
            drones[droneChoosen].servers.changeState(idleID)
            FES.put((time + service_time, "departure", client, droneChoosen,idleID))
        elif idleID != -1 and drones[droneChoosen].landing_time < int(time) + service_time:
            drones[droneChoosen].num_takeoff += 1
            drones[droneChoosen].send2recharge(time, FES, droneChoosen, "arr2") 
            for c in drones[droneChoosen].queue:
                    baseStation.queue.append(c)
                    drones[droneChoosen].losses_battery += 1
                    drones[droneChoosen].users -= 1
                    baseStation.users += 1
            drones[droneChoosen].queue = []
            drones[droneChoosen].losses += 1
            queueChoosen = 0            
        elif idleID == -1 and len(drones[droneChoosen].queue) < drones[droneChoosen].buffer_size:
            drones[droneChoosen].data.arr += 1
            drones[droneChoosen].data.ut += drones[droneChoosen].users*(time-drones[droneChoosen].data.oldT)
            drones[droneChoosen].data.oldT = time
            drones[droneChoosen].users += 1
            client = Client(TYPE1,time)
            drones[droneChoosen].queue.append(client)
        elif len(drones[droneChoosen].queue) >= drones[droneChoosen].buffer_size:
            #print(f"loss for {droneChoosen} for buffer size")
            drones[droneChoosen].losses += 1
            queueChoosen = 0
    if queueChoosen == 0:   
    # Cumulate statistics
        baseStation.data.arr += 1
        baseStation.data.ut += baseStation.users*(time-baseStation.data.oldT)
        baseStation.data.oldT = time

        # Sample the time until the next even
        baseStation.users += 1
    
        # Create a record for the client
        client = Client(TYPE1,time)

    # If the server is idle start the service
        idleID = baseStation.servers.getIdleID()
        if idleID != -1:
            client.setServer(idleID)
            baseStation.servers.changeState(idleID)
            # Sample the service time
            service_time = random.expovariate(1.0/SERVICE_BASE)

            # Schedule when the client will finish the server
            FES.put((time + service_time, "departure", client, -1,idleID))
            #print(f"Departure set for {client}, {idleID}")
        else:
            baseStation.queue.append(client)
            
    PACKET_DEP_TIME.append((drones[0].data.dep,drones[1].data.dep,drones[2].data.dep, baseStation.data.dep, drones[0].data.dep + drones[1].data.dep + drones[2].data.dep + baseStation.data.dep ))
    
    # Insert the record in the queue
    #QUEUE_SIZE += 1
    #print(f"Arrival {len(queue)}")
    #print(server.servers)
    
        

# departures *******************************************************************
def departure(time, FES, client, queueChoosen, serverId, drones, baseStation):
    global DEPARTURES
    if queueChoosen == -1:
        # Cumulate statistics
        baseStation.data.dep += 1
        DEPARTURES += 1
        baseStation.data.ut += baseStation.users*(time-baseStation.data.oldT)
        baseStation.data.oldT = time
        # Get the first element from the queue
        
        # Do whatever we need to do when clients go away
        
        baseStation.data.delay += (time-client.arrival_time)
        baseStation.users -= 1
        userServer = client.server
        #print(len(queue))
        # See whether there are more clients to in the line
        if len(baseStation.queue) > 0:
            # Sample the service time
            service_time = random.expovariate(1.0/SERVICE_BASE)

            # Schedule when the client will finish the server
            client = baseStation.queue.pop(0)
            client.setServer(userServer)
            FES.put((time + service_time, "departure", client, queueChoosen, serverId))
            #print(f"Departure {client}, {userServer}")
        else: 
            baseStation.servers.changeState(serverId)
        #print(f"Departure {len(queue)}")
        #print(server.servers)
    else:
        # Cumulate statistics
        
        drones[queueChoosen].data.dep += 1
        DEPARTURES += 1
        drones[queueChoosen].data.ut += drones[queueChoosen].users*(time-drones[queueChoosen].data.oldT)
        drones[queueChoosen].data.oldT = time
        # Get the first element from the queue
        
        # Do whatever we need to do when clients go away
        
        drones[queueChoosen].data.delay += (time-client.arrival_time)
        drones[queueChoosen].users -= 1
        userServer = client.server
        #print(len(queue))
        # See whether there are more clients to in the line
        if len(drones[queueChoosen].queue) > 0:
            # Sample the service time
            service_time = random.expovariate(1.0/drones[queueChoosen].service_time)
            
            if drones[queueChoosen].landing_time > int(time) + service_time:
                # Schedule when the client will finish the server
                client = drones[queueChoosen].queue.pop(0)
                client.setServer(userServer)
                FES.put((time + service_time, "departure", client, queueChoosen, serverId))
                #print(f"Departure {client}, {userServer}")
            else:
                print(f"Landing number {drones[queueChoosen].num_takeoff} at time {drones[queueChoosen].landing_time}")
                drones[queueChoosen].num_takeoff += 1
                drones[queueChoosen].send2recharge(time, FES, queueChoosen, "dep")
                for i in range(len(drones[queueChoosen].queue)):
                    drones[queueChoosen].queue.append(drones[queueChoosen].queue.pop(0))
                    drones[queueChoosen].users += 1        
        else: 
            drones[queueChoosen].servers.changeState(serverId)
        

# ******************************************************************************
# the "main" of the simulation
# ******************************************************************************
random.seed(19)

# The simulation time 
time = 0
#time_r =0
# The list of events in the form: (time, type, client, server)
FES = PriorityQueue()

# Initialize the drone
#Possible PV capacities = [0,45,65,75]
baseStation = BaseStation("Base1", SERVICE_BASE, numServers= 1)
drones = []
drones.append(Drone("Drone1", SERVICE_DRONE, num_servers= 1,battery_capacity=ACTIVE_TIME, recharge_time=RECHARGE_TIME, buffer_size=20, pv_capacity=45))
drones.append(Drone("Drone2", SERVICE_DRONE, num_servers= 1,battery_capacity=ACTIVE_TIME, recharge_time=RECHARGE_TIME, buffer_size=20, pv_capacity=45))
drones.append(Drone("Drone3", SERVICE_DRONE, num_servers= 1,battery_capacity=ACTIVE_TIME, recharge_time=RECHARGE_TIME, buffer_size=20, pv_capacity=45))
# Schedule the first arrival at t=0
FES.put((0, "arrival","null", "null", "null"))

# Simulate until the simulated time reaches a constant
while time < SIM_TIME:
    (time, event_type, client, queueChoosen, serverId) = FES.get()
    if time > SIM_TIME:
        break

    if event_type == "arrival":
        arrival(time, FES, baseStation, drones)

    elif event_type == "departure":
        departure(time, FES, client, queueChoosen, serverId, drones, baseStation)
    elif event_type == "drone_charged":
        #drone_recharge(time, FES, drone)
        drones[queueChoosen].flag_charge = 0

sumPercentage = 0.0
for drone in drones:
    # Print output data
    print(f"================================{drone.id}================================")
    print("MEASUREMENTS \n\nNo. of users in the queue:",drone.users,"\nNo. of arrivals =",
        drone.data.arr,"- No. of departures =",drone.data.dep)

    #print("Load: ",SERVICE/ARRIVAL)
    print("\nArrival rate: ",drone.data.arr/time," - Departure rate: ",drone.data.dep/time)

    print("\nAverage number of users: ",drone.data.ut/time)

    print("Average delay: ",drone.data.delay/drone.data.dep)
    print("Actual queue size: ",len(drone.queue))

    if len(drone.queue)>0:
        print("Arrival time of the last element in the queue:",drone.queue[len(drone.queue)-1].arrival_time)
    
    print(f"Drone losses: {drone.losses}")
    print(f"Drone losses for empty battery: {drone.losses_battery}")

    print(f"Percentage of packets served by the: {drone.data.dep/(DEPARTURES)*100}%")
    sumPercentage += (drone.data.dep/(DEPARTURES)*100)
    
    #plt.figure()
    #plt.plot(np.linspace(8, 20, len(loadBase)), loadBase)
    #plt.plot(np.linspace(8, 20, len(loadDrone)), loadDrone)
    #plt.show()

print("================================BASESTATION================================")    
print("MEASUREMENTS \n\nNo. of users in the queue:",baseStation.users,"\nNo. of arrivals =",
    baseStation.data.arr,"- No. of departures =",baseStation.data.dep)

#print("Load: ",SERVICE/ARRIVAL)

print("\nArrival rate: ",baseStation.data.arr/time," - Departure rate: ",baseStation.data.dep/time)

print("\nAverage number of users: ",baseStation.data.ut/time)

print("Average delay: ",baseStation.data.delay/baseStation.data.dep)
print("Actual queue size: ",len(baseStation.queue))

if len(baseStation.queue)>0:
    print("Arrival time of the last element in the queue:",baseStation.queue[len(baseStation.queue)-1].arrival_time)

print(f"Percentage of traffic hendled by drones: {sumPercentage}%")

    
plt.figure()
plt.plot(range(len(ARRIVAL)), ARRIVAL)
plt.show()

for d in drones:
    prev_val = 0
    abs_time = 0
    for val, time in d.load:
        for t in range(abs_time, time):
            d.actual_load.append(prev_val)
        prev_val = val
        abs_time = time
plt.figure()
legend = []
plt.title("Loads of each drone")
plt.xlabel("Time")
plt.ylabel("Load")
for d in drones:
    plt.plot(np.linspace(8, 20, len(d.actual_load)), d.actual_load)
    legend.append(d.id)
plt.legend(legend)
#plt.savefig("4_CBA_Load.png")
plt.show()

num_drones = []
prev_num = 0
abs_time = 0
for val, time in NUM_DRONES:
    for t in range(abs_time, time):
        num_drones.append(prev_num)
    prev_num = val
    abs_time = time
    
plt.figure()
plt.title("Drones on service")
plt.xlabel("Time")
plt.ylabel("n° service drones")
plt.plot(np.linspace(8, 20, len(num_drones)), num_drones)
#plt.savefig("4_CBA_NDrones.png")
plt.show()

packets1 = []
packets2 = [] 
packets3 = []
packetsBase = []
packetsAll = []
for i in PACKET_DEP_TIME:
    packets1.append(i[0])
    packets2.append(i[1])
    packets3.append(i[2])
    packetsBase.append(i[3])
    packetsAll.append(i[4])
plt.figure()
plt.title("Packets departure of all the system")
plt.xlabel("Time")
plt.ylabel("packets departure")
legend = ["Drone1", "Drone2", "Drone3","BaseStation", "All packets"]

plt.plot(np.linspace(8, 20, len(packets1)), packets1)
plt.plot(np.linspace(8, 20, len(packets2)), packets2)
plt.plot(np.linspace(8, 20, len(packets3)), packets3)
plt.plot(np.linspace(8, 20, len(packetsBase)), packetsBase)
plt.plot(np.linspace(8, 20, len(packetsAll)), packetsAll)
plt.legend(legend)
plt.savefig("4_BBB_PacketDep.png")
plt.show()
