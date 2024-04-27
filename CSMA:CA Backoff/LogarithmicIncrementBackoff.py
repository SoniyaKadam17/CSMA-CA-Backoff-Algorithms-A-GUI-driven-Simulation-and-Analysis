import random
import threading
import time
import math
import matplotlib.pyplot as plt

#random.seed(time.time())  # Set the random seed based on the current time

# Constants
DIFS = 0.05  # Distributed Inter-Frame Space (in seconds)
SIFS = 0.01  # Short Inter-Frame Space (in seconds)
SLOT_TIME = 0.02  # Slot time (in seconds)
CW_MIN = 15  # Minimum contention window size
CW_MAX = 1023  # Maximum contention window size
MAX_RETRIES = 7  # Maximum number of retransmission attempts
TRANSMISSION_RANGE = 15  # Transmission range or radiation radius

# Constants for energy consumption in milliwatts
ENERGY_SLEEP = 0.1
ENERGY_IDLE = 1
ENERGY_BACKOFF = 0.5
ENERGY_RTS = 2
ENERGY_CTS = 2
ENERGY_SIFS = 0.2
ENERGY_DIFS = 0.2
ENERGY_TRANSMISSION = 10

# Node classes
class Node:
    def __init__(self, name, x, y):
        self.name = name
        self.neighbors = []
        self.backoff_counter = 0
        self.contention_window = CW_MIN
        self.retries = 0
        self.transmitting = False
        self.nav = 0
        self.x = x
        self.y = y
        self.energy_consumed = 0  # Total energy consumed
        self.cw_history = []  # List to store contention window history
        self.cw_timestamps = []  # List to store timestamps corresponding to contention window changes
        self.rts_received = False

    def find_neighbors(self, nodes):
        for node in nodes:
            if node != self:
                distance = math.sqrt((self.x - node.x) ** 2 + (self.y - node.y) ** 2)
                if distance <= TRANSMISSION_RANGE:
                    self.neighbors.append(node)

    def send_rts(self, receiver):
        self.update_energy_consumption("idle")  # Update energy consumption
        print(f"[RTS] {self.name} sends RTS to {receiver.name}")
        time.sleep(SIFS)
        if not receiver.rts_received:
            receiver.rts_received = True
            receiver.send_cts(self)
        else:
            print(f"{receiver.name} has already received an RTS, ignoring RTS from {self.name}")
            self.retries += 1
            self.backoff()

    def send_cts(self, sender):
        self.update_energy_consumption("RTS")  # Update energy consumption
        print(f"[CTS] {self.name} sends CTS to {sender.name}")
        time.sleep(SIFS)
        for neighbor in self.neighbors:
            if neighbor != sender:
                neighbor.update_nav(SIFS + DIFS + (2 * SLOT_TIME))
        sender.transmit_data()

    def update_nav(self, duration):
        self.nav = duration / SLOT_TIME
        print(f"{self.name} updates NAV for {duration} seconds ({self.nav} slots)")

    def transmit_data(self):
        self.transmitting = True
        self.update_energy_consumption("DIFS")  # Update energy consumption
        print(f"[DATA] {self.name} transmits data")
        time.sleep(DIFS)
        print(f"[DIFS] {self.name} waits for {DIFS} seconds")
        for neighbor in self.neighbors:
            if neighbor.transmitting:
                print(f"Collision detected at {neighbor.name}")
                self.retries += 1
                self.backoff()
                break
        else:
            print(f"{self.name} data transmission successful")
            self.retries = 0
            self.cw_history.append(2 ** self.retries)  # Record contention window
            self.cw_timestamps.append(time.time())  # Record timestamp
        self.transmitting = False

    def backoff(self):
        backoff_slots = random.randint(0, 2 ** self.retries - 1)
        backoff_time = backoff_slots * SLOT_TIME
        print(f"[BACKOFF] {self.name} selected random backoff: {backoff_slots} slots ({backoff_time} seconds)")
        self.backoff_counter = backoff_slots
        self.cw_history.append(2 ** self.retries)  # Record contention window
        self.cw_timestamps.append(time.time())  # Record timestamp
        print(f"[BACKOFF] {self.name} goes into backoff for {backoff_slots} slots ({backoff_time} seconds)")
        time.sleep(backoff_time)
        print(f"[SIFS] {self.name} waits for {SIFS} seconds after backoff")
        if self.retries < MAX_RETRIES:
            if not self.transmitting:  # Only send RTS if not already transmitting
                for receiving_node in receiving_nodes:
                    if receiving_node in self.neighbors:
                        distance = math.sqrt((self.x - receiving_node.x) ** 2 + (self.y - receiving_node.y) ** 2)
                        self.update_energy_consumption("backoff", distance)  # Pass the distance to update_energy_consumption()
                        self.send_rts(receiving_node)
                        break
        else:
            print(f"{self.name} reached maximum number of retries, transmission failed")
            self.retries = 0

    def update_energy_consumption(self, activity, distance=None):
        if activity == "sleep":
            self.energy_consumed += ENERGY_SLEEP
        elif activity == "idle":
            self.energy_consumed += ENERGY_IDLE
        elif activity == "backoff":
            backoff_energy = ENERGY_BACKOFF * (self.backoff_counter / CW_MIN)
            if distance is not None:
                backoff_energy *= distance
            self.energy_consumed += backoff_energy
        elif activity == "RTS":
            self.energy_consumed += ENERGY_RTS
        elif activity == "CTS":
            self.energy_consumed += ENERGY_CTS
        elif activity == "SIFS":
            self.energy_consumed += ENERGY_SIFS
        elif activity == "DIFS":
            self.energy_consumed += ENERGY_DIFS
        elif activity == "transmission":
            self.energy_consumed += ENERGY_TRANSMISSION

    def print_coordinates(self):
        print(f"{self.name}: ({self.x}, {self.y})")

    def print_backoff_table(self):
        print(f"\nBackoff Table for {self.name}:")
        print("Backoff Period\tContention Window\tTime")
        start_time = self.cw_timestamps[0]
        for i in range(len(self.cw_history)):
            backoff_period = self.cw_timestamps[i] - start_time
            current_time = time.strftime("%H:%M:%S", time.localtime(self.cw_timestamps[i]))
            print(f"{backoff_period:.2f}\t\t{self.cw_history[i]}\t\t\t{current_time}")

# Function to create nodes with user input coordinates
def create_nodes_with_coordinates(num_nodes):
    nodes = []
    for i in range(num_nodes):
        print(f"Enter coordinates for Node {i+1}:")
        x = float(input("Enter x-coordinate: "))
        y = float(input("Enter y-coordinate: "))
        node = Node(f"Node {i+1}", x, y)
        nodes.append(node)
    return nodes

# Visualization
def plot_nodes(nodes):
    plt.figure(figsize=(8, 6))
    for node in nodes:
        plt.plot(node.x, node.y, 'ro', markersize=10)
    plt.title("Node Locations")
    plt.xlabel("X-coordinate")
    plt.ylabel("Y-coordinate")
    plt.grid(True)
    plt.show()

# Get the number of nodes from the user
num_nodes = int(input("Enter the number of nodes: "))

# Create nodes with user input coordinates
nodes = create_nodes_with_coordinates(num_nodes)

# Plot node locations
plot_nodes(nodes)

# Print node coordinates
print("Node Coordinates:")
for node in nodes:
    node.print_coordinates()

# Find neighbors for each node
for node in nodes:
    node.find_neighbors(nodes)

# Select the transmitting nodes
transmitting_nodes_indices = []
num_transmitting_nodes = int(input("Enter the number of transmitting nodes: "))
for i in range(num_transmitting_nodes):
    index = int(input(f"Enter the index ({i+1}/{num_transmitting_nodes}) of the transmitting node: "))
    while index < 0 or index >= num_nodes or index in transmitting_nodes_indices:
        print("Invalid index or duplicate index. Please select a valid index.")
        index = int(input(f"Enter the index ({i+1}/{num_transmitting_nodes}) of the transmitting node: "))
    transmitting_nodes_indices.append(index)

# Select the receiving nodes
receiving_nodes_indices = []
num_receiving_nodes = int(input("Enter the number of receiving nodes: "))
for i in range(num_receiving_nodes):
    index = int(input(f"Enter the index ({i+1}/{num_receiving_nodes}) of the receiving node: "))
    while index < 0 or index >= num_nodes or index in transmitting_nodes_indices or index in receiving_nodes_indices:
        print("Invalid index or duplicate index. Please select a valid index.")
        index = int(input(f"Enter the index ({i+1}/{num_receiving_nodes}) of the receiving node: "))
    receiving_nodes_indices.append(index)

# Assign transmitting and receiving nodes
transmitting_nodes = [nodes[index] for index in transmitting_nodes_indices]
receiving_nodes = [nodes[index] for index in receiving_nodes_indices]

# Run the simulation for each transmitting node and the selected receiving nodes
def simulate_transmission(transmitting_node):
    while True:
        if all(not receiving_node.rts_received for receiving_node in receiving_nodes):
            print(f"Simulation for transmitting node {transmitting_node.name} and receiving nodes:")
            for receiving_node in receiving_nodes:
                transmitting_node.backoff()  # Contention window before RTS
                if receiving_node in transmitting_node.neighbors:
                    transmitting_node.send_rts(receiving_node)
                else:
                    print(f"{receiving_node.name} is not within transmission range of {transmitting_node.name}")
            print("Simulation End")
            break
        else:
            print("One or more receiving nodes have already received an RTS, waiting for them to become available...")
            time.sleep(SLOT_TIME)

threads = []
for transmitting_node in transmitting_nodes:
    thread = threading.Thread(target=simulate_transmission, args=(transmitting_node,))
    threads.append(thread)
    thread.start()
for thread in threads:
    thread.join()

# Print total energy consumed by each node
print("\nTotal energy consumed by each node:")
for node in nodes:
    print(f"{node.name}: {node.energy_consumed}")

# Generate contention window vs time graphs for each transmitting node
for transmitting_node in transmitting_nodes:
    plt.figure()
    plt.plot(transmitting_node.cw_timestamps, transmitting_node.cw_history)
    plt.xlabel('Time')
    plt.ylabel('Contention Window')
    plt.title(f'Contention Window vs Time for {transmitting_node.name}')
    plt.show()

# Generate energy consumed vs node bar graph
energy_consumption = {node.name: node.energy_consumed for node in nodes}
plt.bar(energy_consumption.keys(), energy_consumption.values())
plt.xlabel('Node')
plt.ylabel('Energy Consumption')
plt.title('Total Energy Consumption by Node')
plt.show()

# Print backoff table for each transmitting node
for transmitting_node in transmitting_nodes:
    transmitting_node.print_backoff_table()