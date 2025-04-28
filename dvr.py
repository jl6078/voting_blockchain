import sys
import socket
import time

import threading

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
        
    def initial_message(self): 
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
    
    def listen_for_messages(self):
        while True:
            try:
                data = self.recv(4096)
                if data:
                    print(f"\n[Received] {data.decode()}\n> ", end="", flush=True)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def close(self):
        """
        Close the socket connection with the network.
        """
        self.sock.close()


def parse_message(message):
    """
    Parse the message to extract a Block object from a string representation of that object
    """
    return
    
def block_to_message(block):
    return

# def write_log(node_id, dv_table):
#     """
#     Write the distance vector table to a log file.
#     """
#     log_file = open(f"log_{node_id}.txt", "a") 
#     dest_to_neighbors = {}
#     for neighbor_id, dest_tuples_list in dv_table.items():
#         for dest_id, cost in dest_tuples_list:
#             dest_to_neighbors.setdefault(dest_id, []).append((neighbor_id, cost))
    
#     distance_vector = {
#         dest: min(neighbor_pairs, key=lambda x: x[1])
#         for dest, neighbor_pairs in dest_to_neighbors.items()
#     }

#     log_string = ""
#     for dest_id, neighbor_pair in distance_vector.items():
#         neighbor = neighbor_pair[0]
#         cost = neighbor_pair[1]
#         log_string += f"{dest_id}:{cost}:{neighbor} "

#     log_string+= "\n"
#     log_file.write(log_string)
#     log_file.flush() # IMPORTANT

def send_user_blocks():
    while True:
        try:
            votesA = input("> Enter votes for party A:")
            votesB = input("> Enter votes for party B:")

            voteTransaction = {"votesA": votesA, "votesB": votesB}

            # Initialize new block (including mining)
            # Add depth of each block

            if block:

                sock.sendall(block.encode())
        except Exception as e:
            print(f"Error sending data: {e}")
            break

    


if __name__ == '__main__':
    network_ip = sys.argv[1] # the IP address of the network
    network_port = int(sys.argv[2]) # the port the network is listening on
 
    net_interface = NetworkInterface(network_port, network_ip) # initialize the network interface

    # init_costs = net_interface.initial_costs() 
    init_message = net_interface.initial_message() 
    # print(init_costs)

    """Below is an example of how to use the network interface and log. Replace it with your distance vector routing protocol"""

    # neighbors = []

    """Initialize node_id and neighbors"""
    # dv_table = {} 
    node_id = init_message.split(".")[0] 
    neighbors = init_message.split(". ")[1].split(",") 


    # Start the listener thread
    listener_thread = threading.Thread(target=net_interface.listen_for_messages, daemon=True)
    listener_thread.start()




    # Main thread handles user input
    send_user_blocks()










    # """Initialize dv table with the costs of direct neighbors"""
    # for pair in neighbors_pairs:
    #     neighbor_id, cost = pair.split(":") 
    #     if neighbor_id not in neighbors:
    #         neighbors.append(neighbor_id)
    #         direct_link_costs[neighbor_id] = int(cost) 

    #     dv_table.setdefault(neighbor_id, []).append((neighbor_id, int(cost)))

    # """Log initial distance vector"""
    # log_file = open(f"log_{node_id}.txt", "w") 
    # write_log(node_id, dv_table)
    
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


