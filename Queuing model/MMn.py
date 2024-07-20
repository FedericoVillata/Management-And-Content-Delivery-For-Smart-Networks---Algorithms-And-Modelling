#!/usr/bin/python3

import random
from queue import PriorityQueue
import numpy as np
import scipy.stats as st

# Constants
SERVICE = 10.0  # Average service time
ARRIVAL = 5.0   # Average inter-arrival time
SIM_TIME = 500000
NUM_SERVERS = 15

# Classes
class Measure:
    def __init__(self):
        self.arr = 0
        self.dep = 0
        self.ut = 0
        self.oldT = 0
        self.delay = 0

class Client:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time
        self.server = -1 # se -1 cliente non servito da nessun server

class Server:
    def __init__(self, num_servers):
        self.servers = [False] * num_servers  # False for idle, True for busy

    def getIdleID(self): # Trova un server libero
        for i, busy in enumerate(self.servers):
            if not busy:
                return i
        return -1

    def setServerBusy(self, id):
        self.servers[id] = True

    def setServerIdle(self, id):
        self.servers[id] = False

# Event handling
def arrival(time, FES, queue, server, data, users):
    data.arr += 1
    if users > 0:
        data.ut += users * (time - data.oldT)
    data.oldT = time

    # Schedule next arrival
    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", None, None))

    client = Client(time) #create new client registering the arrival time

    # Check for an idle server
    idleID = server.getIdleID()
    if idleID != -1:
        client.server = idleID
        server.setServerBusy(idleID)
        service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + service_time, "departure", client, idleID))
    else:
        queue.append(client)
    return users + 1

def departure(time, FES, queue, client, serverId, server, data, users):
    data.dep += 1
    data.delay += (time - client.arrival_time)
    if users > 1:
        data.ut += (users - 1) * (time - data.oldT)
    data.oldT = time

    server.setServerIdle(serverId)
    if queue:
        next_client = queue.pop(0)
        next_client.server = serverId
        server.setServerBusy(serverId)
        service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + service_time, "departure", next_client, serverId))

    return users - 1

# Main simulation
def main():
    random.seed(42)
    data = Measure()
    MMN = []
    users = 0
    server = Server(NUM_SERVERS)
    FES = PriorityQueue()
    FES.put((0, "arrival", None, None))

    time = 0
    while time < SIM_TIME:
        time, event_type, client, serverId = FES.get()
        if event_type == "arrival":
            users = arrival(time, FES, MMN, server, data, users)
        elif event_type == "departure":
            users = departure(time, FES, MMN, client, serverId, server, data, users)

    print(f"Total Arrivals: {data.arr}, Total Departures: {data.dep}")
    print(f"Average Delay: {data.delay / data.dep if data.dep > 0 else 0:.2f}")
    print(f"System Utilization: {data.ut / time:.2f}")
    print(f"Loss Probability: {(data.arr - data.dep) / data.arr if data.arr > 0 else 0:.4f}")

if __name__ == "__main__":
    main()
