import sys
import socket
import time

class NetworkInterface():
    """
    DO NOT EDIT.
    
    Provided interface to the network. In addition to typical send/recv methods,
    it also provides a method to receive an initial message from the network, which
    contains the costs to neighbors. 
    """
    def __init__(self, network_port, network_ip):
        """
        Constructor for the NetworkInterface class.

        Parameters:
            network_port : int
                The port the network is listening on.
            network_ip : str
                The IP address of the network.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((network_ip, network_port))
        self.init_msg = self.sock.recv(4096).decode() # receive the initial message from the network
        
    def initial_costs(self): 
        """
        Return the initial message received from the network in following format:
        <node_id>. <neighbor_1>:<cost_1>,...,<neighbor_n>:<cost_n>

        node_id is the unique identifier for this node, i.e., dvr.py instance. 
        Neighbor_i is the unique identifier for direct neighbor nodes. All identifiers
        and costs are specified in the topology file.
        """
        return self.init_msg
    
    def send(self, message):
        """
        Send a message to all direct neigbors.

        Parameters:
            message : bytes
                The message to send.
        
        Returns:
            None
        """
        message_len = len(message)
        packet = message_len.to_bytes(4, byteorder='big') + message
        self.sock.sendall(packet)
    
    def recv(self, length):
        """
        Receive a message from neighbors. Behaves exactly like socket.recv()

        Parameters:
            length : int
                The length of the message to receive.
        
        Returns:
            bytes
                The received message.
        """
        return self.sock.recv(length)
    
    def close(self):
        """
        Close the socket connection with the network.
        """
        self.sock.close()

def get_distance_vector(dv_table):
    """
    Get distance vector from the dv_table.
    """
    dest_to_neighbors = {}
    for neighbor_id, dest_tuples_list in dv_table.items():
        for dest_id, cost in dest_tuples_list:
            dest_to_neighbors.setdefault(dest_id, []).append((neighbor_id, cost))
    
    distance_vector = {
        dest: min(neighbor_pairs, key=lambda x: x[1])[1]
        for dest, neighbor_pairs in dest_to_neighbors.items()
    }
        
    return distance_vector

def parse_message(message):
    """
    Parse the message to extract node_id and distance vector.
    """
    node_id = message.split(".")[0] 
    neighbors_pairs = message.split(". ")[1].split(",") 
    dv = {}

    for pair in neighbors_pairs:
        dest_id, cost = pair.split(":")
        if dest_id in dv:
            print("Duplicate destination id found in message")
        dv[dest_id] = int(cost) 

    return node_id, dv


def update_dv(local_node_id, recv_node_id, local_dv_table, recv_dv, direct_link_costs):
    """
    Update the distance vector table with the new distance vector.
    Returns updated DV table and DV
    """
    
    recv_dests = recv_dv.keys()
    recv_neighbor = recv_node_id



    new_dv = {}
    dests_list = []
    """Only need to update local_dv_table values for the (neighbor, neighbor_dest) pairs in recv_dv"""
    for recv_dest in recv_dests:
        """Don't add destination if it's the local node"""
        if recv_dest != local_node_id:
            new_cost = direct_link_costs[recv_neighbor] + recv_dv[recv_dest]
            dests_list.append((recv_dest, new_cost))
    
    new_dest_ids = [dest[0] for dest in dests_list]
    original_dest_pairs = local_dv_table[recv_neighbor]

    """Make sure we don't eliminate destinations which aren't featured in recv_dv"""
    for pair in original_dest_pairs:
        if pair[0] not in new_dest_ids:
            dests_list.append(pair)
            new_dest_ids.append(pair[0])

    """Add new values"""
    new_local_dv_table = local_dv_table.copy()
    new_local_dv_table[recv_neighbor] = dests_list 
    new_dv = get_distance_vector(new_local_dv_table)

    return new_local_dv_table, new_dv

def dv_to_message(node_id, dv):
    """
    Send the distance vector to neighbors.
    """
    message = f"{node_id}. "
    for dest_id, cost in dv.items():
        message += f"{dest_id}:{cost},"

    message = message[:-1] # remove the last comma
    message += "\n"
    return message.encode()

def write_log(node_id, dv_table):
    """
    Write the distance vector table to a log file.
    """
    log_file = open(f"log_{node_id}.txt", "a") 
    dest_to_neighbors = {}
    for neighbor_id, dest_tuples_list in dv_table.items():
        for dest_id, cost in dest_tuples_list:
            dest_to_neighbors.setdefault(dest_id, []).append((neighbor_id, cost))
    
    distance_vector = {
        dest: min(neighbor_pairs, key=lambda x: x[1])
        for dest, neighbor_pairs in dest_to_neighbors.items()
    }

    log_string = ""
    for dest_id, neighbor_pair in distance_vector.items():
        neighbor = neighbor_pair[0]
        cost = neighbor_pair[1]
        log_string += f"{dest_id}:{cost}:{neighbor} "

    log_string+= "\n"
    log_file.write(log_string)
    log_file.flush() # IMPORTANT







    

if __name__ == '__main__':
    network_ip = sys.argv[1] # the IP address of the network
    network_port = int(sys.argv[2]) # the port the network is listening on
 
    net_interface = NetworkInterface(network_port, network_ip) # initialize the network interface

    init_costs = net_interface.initial_costs() 
    print(init_costs)

    """Below is an example of how to use the network interface and log. Replace it with your distance vector routing protocol"""

    neighbors = []

    direct_link_costs = {}

    """Initialize DV table and DV"""
    dv_table = {} 
    node_id = init_costs.split(".")[0] 
    neighbors_pairs = init_costs.split(". ")[1].split(",") 

    """Initialize dv table with the costs of direct neighbors"""
    for pair in neighbors_pairs:
        neighbor_id, cost = pair.split(":") 
        if neighbor_id not in neighbors:
            neighbors.append(neighbor_id)
            direct_link_costs[neighbor_id] = int(cost) 

        dv_table.setdefault(neighbor_id, []).append((neighbor_id, int(cost)))

    """Log initial distance vector"""
    log_file = open(f"log_{node_id}.txt", "w") 
    write_log(node_id, dv_table)
    
    """Extract DV from DV table"""
    distance_vector = get_distance_vector(dv_table) 

    """Send the initial distance vector to neighbors"""
    message = dv_to_message(node_id, distance_vector)
    net_interface.send(message)

    while True:
        message = net_interface.recv(4096) 

        messages = message.decode().strip().split("\n")  

        all_node_dvs = {}  

        for msg in messages:
            if msg.strip():  
                recv_node_id, recv_dv = parse_message(msg)
                all_node_dvs[recv_node_id] = recv_dv

        for recv_node_id, recv_dv in all_node_dvs.items():
            new_dv_table, new_dv = update_dv(node_id, recv_node_id, dv_table, recv_dv, direct_link_costs)

            dv_table = new_dv_table
            print("DV table updated")

            if new_dv != distance_vector:
                print(f"Updated distance vector: {new_dv}")
                distance_vector = new_dv
                message = dv_to_message(node_id, new_dv)
                net_interface.send(message)
                write_log(node_id, dv_table)  


