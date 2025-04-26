import socket
import threading
import sys
import time

LOG_LEVEL  = "INFO"

class Node:
    """
    Node in a network. Each node has a unique ID, a port number, a connection to the network,
    a lock for thread safety, and a dictionary of neighbors with their respective costs.
    """
 
    def __init__(self, node_id):
        """
        Constructor for the Node class.
        
        Parameters:
            node_id : str
                Unique identifier for the node in the network.
        """
        self.node_id = node_id
        self.port = None
        self.connection = None
        self.connection_lock = None
        self.neighbors = dict()  # key: neighbor_id, value: cost

    def add_neighbor(self, neighbor_id, cost):
        """
        Add a neighbor and its associated cost to the node's list of neighbors, 
        if it doesn't already exist.

        Parameters:
            neighbor_id : str
                Unique identifier for the neighbor node.
            cost : int
                Cost to reach the neighbor node.
        """
        if neighbor_id not in self.neighbors:
            self.neighbors[neighbor_id] = cost

    def __repr__(self):
        return f"Node {self.node_id}. Neighbors: {self.neighbors}. Port: {self.port}."

def check_topology_format(filename):
    """
    Validate the format of the topology file. Each line should contain two node IDs and a cost,
    separated by spaces. The node IDs should be different, and the cost should be a positive integer.
    The topology file may not contain lines with the same node pair more than once, as this creates 
    ambiguity in the network.

    Parameters:
        filename : str
            Path to the topology file.
    
    Returns:
        None. Raises AssertionError if the format is incorrect.
    """
    with open(filename, 'r') as f:
        node_pairs = set()
        for line in f:
            if line.strip():
                parts = line.split()
                assert len(parts) == 3, f"Should be three space-separated elements in line, got {len(parts)}: {parts}"
                assert parts[0] != parts[1], f"Node IDs should be different, got {parts[0]} and {parts[1]}"
                assert parts[2].isdigit(), f"Cost should be a number, got {parts[2]}"
                assert int(parts[2]) > 0, f"Cost should be positive, got {parts[2]}"
                # choose node that is first lexicographically
                node_pair = tuple(sorted([parts[0], parts[1]]))
                node_pair = f"{node_pair[0]}-{node_pair[1]}"
                assert node_pair not in node_pairs, f"Duplicate node pair found in {filename}: {node_pair}"
                node_pairs.add(node_pair)
    

def parse_topology(filename):
    """
    Parse topology file to create a dictionary of Node objects.

    Parameters:
        filename : str
            Path to the topology file.

    Returns:
        nodes : dict
            Dictionary where key is node_id and value is Node object.
    """
    nodes = {} # key: node_id, value: Node object
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():  # skip empty lines
                node_id_a = line.split()[0]
                node_id_b = line.split()[1]
                cost = line.split()[2]
                if node_id_a not in nodes:
                    new_node = Node(node_id_a)
                    new_node.add_neighbor(node_id_b, cost)
                    nodes[node_id_a] = new_node
                else:
                    nodes[node_id_a].add_neighbor(node_id_b, cost)
                if node_id_b not in nodes:
                    new_node = Node(node_id_b)
                    new_node.add_neighbor(node_id_a, cost)
                    nodes[node_id_b] = new_node
                else:
                    nodes[node_id_b].add_neighbor(node_id_a, cost)
    return nodes


def network_log(message, level = "INFO"):
    """
    Log messages to the console. The log level determines the verbosity of the output.

    Parameters:
        message : str
            The message to log.
        level : str
            The log level. Can be "DEBUG" or "INFO".
    """
    if level == "DEBUG" and LOG_LEVEL == "DEBUG":
        print(f"[{level}] {message}")
    elif level == "INFO" and LOG_LEVEL in ["INFO", "DEBUG"]:
        print(f"[network] {message}")

def node_thread(node):
    """
    Receive and respond to messages from/to nodes in the network.

    Parameters:
        node : Node
            The Node object representing this thread's node.
    """
    # send message to node with its immediate neighbors and their hop costs
    welcome_message = f"{node.node_id}. "
    for n, c in node.neighbors.items():
        welcome_message += f"{n}:{c},"
    welcome_message = welcome_message[:-1]  # remove the last comma
    node.connection.sendall(welcome_message.encode()) 
    
    while True:
        try:
            # catch issue of connection being reset by peer, which can happen
            # if students call close in dvr.py before the network sends data to it below
            # also return if the node connection is gracefully closed
            header = node.connection.recv(4)
            if not header :
                network_log(f"Node {node.node_id} closed socket")
                return
            data_len = int.from_bytes(header , byteorder='big')
            data = node.connection.recv(data_len)
            if not data:
                network_log(f"Node {node.node_id} closed socket")
                return
        except ConnectionResetError:
            network_log(f"Connection reset by peer for node {node.node_id}. Likely means dvr.py closed the socket or crashed.")
            return 
           
        if data:
            network_log(f"Received data from node {node.node_id}", level  = "DEBUG")
            # for each neighbor, obtain lock and send the message
            for neighbor_id, _ in node.neighbors.items():
                # get the Node obj for the neighbor and send the message using the lock
                neighbor_node = nodes[neighbor_id]
                with neighbor_node.connection_lock:
                    network_log(f"Sending data to neighbor {neighbor_id}", level = "DEBUG")
                    neighbor_node.connection.sendall(data)
          
        time.sleep(0.1)

if __name__ == '__main__':
    NETWORK_PORT = sys.argv[1]
    try:
        NETWORK_PORT = int(NETWORK_PORT)
        assert 1024 <= NETWORK_PORT <= 65535
    except (ValueError, AssertionError):
        print(f"Invalid network port: {NETWORK_PORT}. Must be between 1024 and 65535.")
        sys.exit(1)
    NETWORK_PORT = NETWORK_PORT

    topology_filename = sys.argv[2]

    check_topology_format(topology_filename)
    nodes = parse_topology(topology_filename)
    num_nodes = len(nodes)

    # create listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', NETWORK_PORT))
    server_socket.listen(num_nodes)
    network_log(f"Listening on port {NETWORK_PORT} for {num_nodes} nodes...")

    # wait for incoming connections from nodes until all nodes are connected
    conn_num = 0
    node_threads = []
    while conn_num < num_nodes:
        conn, addr = server_socket.accept()
        port = addr[1]
        node_key = list(nodes.keys())[conn_num]
        nodes[node_key].connection = conn
        nodes[node_key].port = port
        conn_num += 1
        network_log(f"Connected to {addr}")

        # create thread for each node. Note: won't start until all prepped with their locks
        nodes[node_key].connection_lock = threading.Lock()
        t = threading.Thread(target=node_thread, args=(nodes[node_key],))
        node_threads.append(t)
    
    # start all threads
    for t in node_threads:
        t.start()
    
    network_log(f"All {num_nodes} nodes connected.")
    
    for t in node_threads:
        t.join()