#!/usr/bin/python3

import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt

# ******************************************************************************
# Constants
# ******************************************************************************

SERVICE = 10.0  # Average service time; service rate = 1/SERVICE
ARRIVAL = 5.0   # Average inter-arrival time; arrival rate = 1/ARRIVAL
SIM_TIME = 500000
TYPE1 = 1

# Output results
def print_stats(queue_number, data, queue):
    print(f"================================QUEUE{queue_number}================================")
    print("MEASUREMENTS\n\nNo. of users in the queue:", users[queue_number-1])
    print("No. of arrivals =", data.arr, "- No. of departures =", data.dep)
    print("Load: ", SERVICE / ARRIVAL)
    print("\nArrival rate: ", data.arr / time, " - Departure rate: ", data.dep / time)
    print("\nAverage number of users: ", data.ut / time)
    print("Average delay: ", data.delay / data.dep)
    print("Actual queue size: ", len(queue))
    if len(queue) > 0:
        print("Arrival time of the last element in the queue:", queue[-1].arrival_time)

def plot_delays(data, queue_number, n):
    plt.figure()
    plt.plot(data.delay_times, data.delays, label=f'Queue {n}')
    plt.xlabel('Time')
    plt.ylabel('Delay')
    plt.title(f'Delay over Time for Queue {n}')
    plt.legend()
    plt.show()

# ******************************************************************************
# Measurement class
# ******************************************************************************
class Measure:
    def __init__(self, Narr=0, Ndep=0, NAveraegUser=0, OldTimeEvent=0, AverageDelay=0):
        self.arr = Narr
        self.dep = Ndep
        self.ut = NAveraegUser
        self.oldT = OldTimeEvent
        self.delay = AverageDelay
        self.delay_times = []  # Lista per i tempi degli eventi di partenza
        self.delays = [] # Lista per i ritardi

# ******************************************************************************
# Client class
# ******************************************************************************
class Client:
    def __init__(self, type, arrival_time):
        self.type = type
        self.arrival_time = arrival_time

# ******************************************************************************
# Arrival function
# ******************************************************************************
def arrival(time, FES, queues, users, datas):
    queueChoosen = random.randint(0, 1)
    queue = queues[queueChoosen]
    data = datas[queueChoosen]

    # Cumulate statistics
    data.arr += 1
    data.ut += users[queueChoosen] * (time - data.oldT)
    data.oldT = time

    # Sample the time until the next event
    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", queueChoosen))

    users[queueChoosen] += 1
    client = Client(TYPE1, time)
    queue.append(client)

    # If the server is idle start the service
    if len(queue) == 1:
        service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + service_time, "departure", queueChoosen))

# ******************************************************************************
# Departure function
# ******************************************************************************
def departure(time, FES, queues, users, datas, choosen):
    queue = queues[choosen]
    data = datas[choosen]

    # Cumulate statistics
    data.dep += 1
    data.ut += users[choosen] * (time - data.oldT)
    data.oldT = time
    
    client = queue.pop(0)
    delay = (time - client.arrival_time)
    data.delay += delay

    data.delay_times.append(time)
    data.delays.append(delay)

    users[choosen] -= 1
    
    if len(queue) > 0:
        service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + service_time, "departure", choosen))

# ******************************************************************************
# Main simulation
# ******************************************************************************
random.seed(42)
data1 = Measure()
data2 = Measure()
users = [0, 0]
queues = [[], []]
FES = PriorityQueue()
time = 0

FES.put((0, "arrival", 0))  # Schedule the first arrival at t=0

while time < SIM_TIME:
    (time, event_type, choosen) = FES.get()

    if event_type == "arrival":
        arrival(time, FES, queues, users, datas=[data1, data2])
    elif event_type == "departure":
        departure(time, FES, queues, users, datas=[data1, data2], choosen=choosen)

plt.figure()
plt.plot(data1.delay_times, data1.delays, label='Queue 1', color="b", linewidth=0.75)
plt.plot(data2.delay_times, data2.delays, label='Queue 2', color="r", linewidth=0.75)
plt.xlabel('Time')
plt.ylabel('Delay')
plt.title(f'Delay over Time for Queues')
plt.legend()
plt.show()

print_stats(1, data1, queues[0])
print_stats(2, data2, queues[1])
