#!/usr/bin/python3

import random
from queue import PriorityQueue
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

# Constants
SERVICE = [9, 9]  # Average service time for each server
ARRIVAL = 5.0  # Average inter-arrival time
SIM_TIME = 500000
NUM_SERVERS = 2

# Classes
class Measure:
    def __init__(self, num_servers):
        self.arr = 0
        self.dep = [0] * num_servers
        self.ut = 0
        self.oldT = 0
        self.delay = [0] * num_servers
        self.time_delays = [[] for _ in range(num_servers)]
        self.delays = [[] for _ in range(num_servers)]
        self.usageTime = [0] * num_servers

class Client:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time
        self.server = -1

class Server:
    def __init__(self, num_servers):
        self.servers = [False] * num_servers

    def getIdleID(self):
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

    client = Client(time)

    idleID = server.getIdleID()
    if idleID != -1:
        client.server = idleID
        server.setServerBusy(idleID)
        service_time = random.expovariate(1.0 / SERVICE[idleID])
        FES.put((time + service_time, "departure", client, idleID))
    else:
        queue.append(client)
    return users + 1

def departure(time, FES, queue, client, serverId, server, data, users):
    data.dep[serverId] += 1
    current_delay = time - client.arrival_time
    data.delay[serverId] += current_delay
    data.time_delays[serverId].append(time)
    data.delays[serverId].append(current_delay)
    data.usageTime[serverId] += time - data.oldT

    if users > 1:
        data.ut += (users - 1) * (time - data.oldT)
    data.oldT = time

    server.setServerIdle(serverId)
    if queue:
        next_client = queue.pop(0)
        next_client.server = serverId
        server.setServerBusy(serverId)
        service_time = random.expovariate(1.0 / SERVICE[serverId])
        FES.put((time + service_time, "departure", next_client, serverId))

    return users - 1

# Main simulation
def main():
    random.seed(42)
    data = Measure(NUM_SERVERS)
    queue = []
    users = 0
    server = Server(NUM_SERVERS)
    FES = PriorityQueue()
    FES.put((0, "arrival", None, None))

    time = 0
    while time < SIM_TIME:
        time, event_type, client, serverId = FES.get()
        if event_type == "arrival":
            users = arrival(time, FES, queue, server, data, users)
        elif event_type == "departure":
            users = departure(time, FES, queue, client, serverId, server, data, users)

    for i in range(NUM_SERVERS):
        print(f"-----------------Data measurements for server: {i}-------------------")
        print("MEASUREMENTS \n\nNo. of users in the queue:", len(queue), "\nNo. of arrivals =",
              data.arr, "- No. of departures =", data.dep[i])

        print("Load: ", SERVICE[i] / (2*ARRIVAL))
        print("\nArrival rate: ", data.arr / time, " - Departure rate: ", data.dep[i] / time)

        print("\nAverage number of users: ", data.ut / time)

        print("Average delay: ", data.delay[i] / data.dep[i])
        print("Actual queue size: ", len(queue))

        if queue:
            print("Arrival time of the last element in the queue:", queue[-1].arrival_time)

        print(f"Percentage of usage of server {i}: {data.usageTime[i] / SIM_TIME * 100}%")

if __name__ == "__main__":
    main()