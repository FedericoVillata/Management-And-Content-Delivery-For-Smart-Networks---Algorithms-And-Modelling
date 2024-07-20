import random
from queue import PriorityQueue
import matplotlib.pyplot as plt
import numpy as np

# Constants
SERVICE = [10, 8, 12]  # average service time for each server
ARRIVAL = 5.0  # average time between arrivals
SIM_TIME = 500000  # simulation time in units

# Classes and Functions
class Measure:
    def __init__(self, num_servers):
        self.arr = 0
        self.dep = [0] * num_servers
        self.ut = 0
        self.oldT = 0
        self.delay = [0] * num_servers

class Client:
    def __init__(self, type, arrival_time):
        self.type = type
        self.arrival_time = arrival_time
        self.server = -1

    def setServer(self, id):
        self.server = id

class Server:
    def __init__(self, num_servers):
        self.servers = [0] * num_servers
        self.usageTime = [0] * num_servers
        self.num_servers = num_servers
        self.roundRobin = 0

    def getIdleID(self):
        for i in range(self.num_servers):
            if self.servers[i] == 0:
                return i
        return -1

    def getFasterIdleID(self):
        sorted_indexes = sorted(range(len(SERVICE)), key=lambda k: SERVICE[k])
        for i in sorted_indexes:
            if self.servers[i] == 0:
                return i
        return -1

    def getRandomIdleID(self):
        free_servers = [i for i in range(self.num_servers) if self.servers[i] == 0]
        if free_servers:
            return random.choice(free_servers)
        return -1

    def getRoundRobinIdleID(self):
        start = self.roundRobin
        for _ in range(self.num_servers):
            idx = (start + self.roundRobin) % self.num_servers
            self.roundRobin = (self.roundRobin + 1) % self.num_servers
            if self.servers[idx] == 0:
                return idx
        return -1

    def changeState(self, id):
        if self.servers[id] == 0:
            self.servers[id] = 1
        else:
            self.servers[id] = 0

def arrival(time, FES, queue, server, server_selection_func):
    global data, users
    data.arr += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time

    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", None, None))
    users += 1

    client = Client(1, time)
    idleID = server_selection_func(server)
    if idleID != -1:
        client.setServer(idleID)
        server.changeState(idleID)
        service_time = random.expovariate(1.0 / SERVICE[idleID])
        FES.put((time + service_time, "departure", client, idleID))
        server.usageTime[idleID] += service_time
    else:
        queue.append(client)

def departure(time, FES, queue, client, serverId, server):
    global data, users
    data.dep[serverId] += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time
    data.delay[serverId] += (time - client.arrival_time)
    users -= 1

    if queue:
        new_client = queue.pop(0)
        service_time = random.expovariate(1.0 / SERVICE[serverId])
        FES.put((time + service_time, "departure", new_client, serverId))
        server.usageTime[serverId] += service_time
        new_client.setServer(serverId)
    else:
        server.changeState(serverId)

def run_simulation(server_selection_func):
    global data, users, MM1
    random.seed(42)
    num_servers = 3
    data = Measure(num_servers)
    time = 0
    FES = PriorityQueue()
    FES.put((0, "arrival", None, None))
    server = Server(num_servers)
    MM1 = []
    users = 0

    while time < SIM_TIME:
        (time, event_type, client, serverId) = FES.get()

        if event_type == "arrival":
            arrival(time, FES, MM1, server, server_selection_func)
        elif event_type == "departure":
            departure(time, FES, MM1, client, serverId, server)
    
     # Calcolo dei tempi di attesa medi
    avg_delays = [data.delay[i] / data.dep[i] if data.dep[i] > 0 else 0 for i in range(num_servers)]

    # Output results
    print(f"\nResults for method: {server_selection_func}")
    for i in range(num_servers):
        print(f"-----------------Data measurements for server: {i}-------------------")
        print("MEASUREMENTS \nNo. of users in the queue:", users, "\nNo. of arrivals =", data.arr, "- No. of departures =", data.dep[i])
        print("Load:", 10 / (ARRIVAL*3))
        print("Arrival rate:", data.arr / time, "- Departure rate:", data.dep[i] / time)
        print("Average number of users:", data.ut / time)
        print("Average delay:", data.delay[i] / data.dep[i])
        print("Actual queue size:", len(MM1))
        if MM1:
            print("Arrival time of the last element in the queue:", MM1[-1].arrival_time)
        print(f"Percentage of usage of server {i}: {server.usageTime[i] / SIM_TIME * 100}%")

    return [server.usageTime[i] / SIM_TIME * 100 for i in range(num_servers)], avg_delays

def plot_results(results, methods):
    num_servers = len(results[0])
    num_methods = len(methods)
    bar_width = 0.2  # Width of bars in the bar chart
    index = np.arange(num_servers)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i in range(num_methods):
        ax.bar(index + i * bar_width, results[i], bar_width, label=methods[i])
    
    ax.set_xlabel('Server ID', fontsize=14)
    ax.set_ylabel('Utilization %', fontsize=14)
    ax.set_xticks(index + bar_width * (num_methods - 1) / 2)
    ax.set_xticklabels(['Server ' + str(i) for i in range(num_servers)])
    ax.legend()
    ax.grid(True)
    
    plt.show()

def plot_avg_delays(results, methods):
    num_servers = len(results[0])
    num_methods = len(methods)
    bar_width = 0.2  # Width of bars in the bar chart
    index = np.arange(num_servers)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i in range(num_methods):
        ax.bar(index + i * bar_width, results[i], bar_width, label=methods[i])
    
    ax.set_xlabel('Server ID', fontsize=14)
    ax.set_ylabel('Average Waiting Time', fontsize=14)
    ax.set_xticks(index + bar_width * (num_methods - 1) / 2)
    ax.set_xticklabels(['Server ' + str(i) for i in range(num_servers)])
    ax.legend()
    ax.grid(True)
    
    plt.show()

# Main simulation loop for each method
methods = [Server.getIdleID, Server.getFasterIdleID, Server.getRandomIdleID, Server.getRoundRobinIdleID]
# Esegue la simulazione per ciascun metodo e raccoglie i risultati
all_results = [run_simulation(method) for method in methods]

# Separa i risultati in due liste distinte per l'utilizzo dei server e i tempi di attesa medi
results = [result[0] for result in all_results]  # Utilizzo dei server
avg_delay_results = [result[1] for result in all_results]  # Tempi di attesa medi

plot_results(results, ["getIdleID", "getFasterIdleID", "getRandomIdleID", "getRoundRobinIdleID"])
plot_avg_delays(avg_delay_results, ["getIdleID", "getFasterIdleID", "getRandomIdleID", "getRoundRobinIdleID"])
