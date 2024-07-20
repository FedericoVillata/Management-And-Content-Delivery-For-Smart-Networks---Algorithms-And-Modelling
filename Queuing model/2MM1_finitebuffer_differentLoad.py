#!/usr/bin/python3

import random
from queue import PriorityQueue

# ******************************************************************************
# Constants
# ******************************************************************************
SERVICE = 2.5  # Average service time; service rate = 1/SERVICE
ARRIVAL = 5.0  # Average inter-arrival time; arrival rate = 1/ARRIVAL
LOAD = SERVICE / ARRIVAL  # This relationship holds for M/M/1

TYPE1 = 1

SIM_TIME = 500000

# ******************************************************************************
# Measurement Structures
# ******************************************************************************
class Measure:
    def __init__(self):
        self.arr = 0
        self.dep = 0
        self.ut = 0
        self.oldT = 0
        self.delay = 0
        self.lost = 0  

# ******************************************************************************
# Client
# ******************************************************************************
class Client:
    def __init__(self, type, arrival_time):
        self.type = type
        self.arrival_time = arrival_time

# ******************************************************************************
# Main simulation
# ******************************************************************************
def simulate(buffer_size):
    time = 0
    FES = PriorityQueue()
    FES.put((0, "arrival"))
    queue1, queue2 = [], []
    data1, data2 = Measure(), Measure()

    while time < SIM_TIME:
        (time, event_type) = FES.get()

        if event_type == "arrival":
            arrival(time, FES, queue1, queue2, buffer_size, data1, data2)

        elif event_type == "departure":
            departure(time, FES, queue1, queue2, data1, data2)

    print_results("QUEUE1", data1, queue1)
    print_results("QUEUE2", data2, queue2)

def arrival(time, FES, queue1, queue2, buffer_size, data1, data2):
    choosen = random.randint(1, 2)
    target_queue = queue1 if choosen == 1 else queue2
    data = data1 if choosen == 1 else data2

    # Always schedule the next arrival
    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival"))

    if len(target_queue) < buffer_size:
        data.arr += 1
        users = len(target_queue)
        data.ut += users * (time - data.oldT)
        data.oldT = time

        client = Client(TYPE1, time)
        target_queue.append(client)

        if users == 0:
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure"))
    else:
        data.lost += 1  # Incremento del contatore di pacchetti persi

def departure(time, FES, queue1, queue2, data1, data2):
    choosen = 1 if (queue1 and (not queue2 or random.random() < 0.5)) else 2
    target_queue = queue1 if choosen == 1 else queue2
    data = data1 if choosen == 1 else data2

    if target_queue:
        data.dep += 1
        users = len(target_queue)
        data.ut += users * (time - data.oldT)
        data.oldT = time

        client = target_queue.pop(0)
        data.delay += (time - client.arrival_time)

        if len(target_queue) > 0:
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure"))

def print_results(queue_name, data, queue):
    print(f"================================{queue_name}================================")
    print(f"MEASUREMENTS\n\nNumber of users in the queue: {len(queue)}\nNumber of arrivals =",
          f"{data.arr} - Number of departures = {data.dep}")

    print("Load: ", SERVICE / ARRIVAL)
    print("\nArrival rate: ", data.arr / SIM_TIME, "- Departure rate: ", data.dep / SIM_TIME)
    print("\nAverage number of users: ", data.ut / SIM_TIME)
    print("Average delay: ", data.delay / data.dep if data.dep > 0 else "N/A")
    print("Actual queue size: ", len(queue))
    print("Lost packets: ", data.lost)  # Stampa del numero di pacchetti persi
    if queue:
        print("Arrival time of the last element in the queue:", queue[-1].arrival_time)

# ******************************************************************************
# Main
# ******************************************************************************
random.seed(42)

buffer_size = 2
simulate(buffer_size)
