import random
from queue import PriorityQueue
import matplotlib.pyplot as plt

# ******************************************************************************
# Constants
# ******************************************************************************
SERVICE = 10.0  # Average service time; service rate = 1/SERVICE
ARRIVAL = 5.0   # Average inter-arrival time; arrival rate = 1/ARRIVAL
SIM_TIME = 500000
TYPE1 = 1

# ******************************************************************************
# Measurement class
# ******************************************************************************
class Measure:
    def __init__(self):
        self.arr = 0
        self.dep = 0
        self.ut = 0
        self.oldT = 0
        self.delay = 0
        self.loss = 0  # Clients lost because the queue is full

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
def arrival(time, FES, queues, users, buffer_size, datas):
    queueChoosen = random.randint(0, 1)
    queue = queues[queueChoosen]
    data = datas[queueChoosen]

    # Cumulate statistics
    data.arr += 1
    data.ut += users[queueChoosen] * (time - data.oldT)
    data.oldT = time

    # Check if the buffer is full
    if len(queue) >= buffer_size:
        data.loss += 1  # Increment the count of rejected clients
    else:
        users[queueChoosen] += 1
        client = Client(TYPE1, time)
        queue.append(client)

        # If the server is idle start the service
        if len(queue) == 1:
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", queueChoosen))

    # Schedule the next arrival
    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", queueChoosen))

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
    data.delay += (time - client.arrival_time)
    users[choosen] -= 1
    
    if len(queue) > 0:
        service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + service_time, "departure", choosen))

def print_stats(queue_number, data, queue, users, time):
    print(f"================================QUEUE {queue_number}================================")
    print("MEASUREMENTS\n\nNo. of users in the queue:", users[queue_number-1])
    print("No. of arrivals =", data.arr, "- No. of departures =", data.dep)
    print("Packets lost: ", data.loss)
    print("Load: ", SERVICE / ARRIVAL)
    print("\nArrival rate: ", data.arr / time, " - Departure rate: ", data.dep / time)
    print("\nAverage number of users: ", data.ut / time)
    print("Average delay: ", data.delay / data.dep)
    print("Actual queue size: ", len(queue))
    if len(queue) > 0:
        print("Arrival time of the last element in the queue:", queue[-1].arrival_time)
    print("=============================================================================")


# ******************************************************************************
# Simulation function
# ******************************************************************************
def simulate(buffer_size):
    data1 = Measure()
    data2 = Measure()
    users = [0, 0]
    queues = [[], []]
    FES = PriorityQueue()
    time = 0
    FES.put((0, "arrival", 0))
    
    while time < SIM_TIME:
        (time, event_type, choosen) = FES.get()

        if event_type == "arrival":
            arrival(time, FES, queues, users, buffer_size, datas=[data1, data2])
        elif event_type == "departure":
            departure(time, FES, queues, users, datas=[data1, data2], choosen=choosen)
    
    if buffer_size == 20:
        print_stats(1, data1, queues[0], users, time)
        print_stats(2, data2, queues[1], users, time)

    total_arrivals = data1.arr + data2.arr
    total_losses = data1.loss + data2.loss
    loss_probability = total_losses / total_arrivals if total_arrivals > 0 else 0

    return loss_probability

# ******************************************************************************
# Main loop for different buffer sizes
# ******************************************************************************
buffer_sizes = list(range(1, 21))
loss_probabilities = []

for size in buffer_sizes:
    loss_probability = simulate(size)
    loss_probabilities.append(loss_probability)

plt.figure(figsize=(10, 6))
plt.plot(buffer_sizes, loss_probabilities, marker='o')
plt.title('Loss Probability vs Buffer Size')
plt.xlabel('Buffer Size')
plt.ylabel('Loss Probability')
plt.grid(True)
plt.show()
