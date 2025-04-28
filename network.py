import socket
import threading
import sys
import time
import json

# ───────────────────────── Tracker globals & helpers ─────────────────────────

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
        self.node_id = None     # assigned after REGISTER
        self.neighbors: list[str] = []   # list of current peer IDs (no costs)

    def add_neighbor(self, neighbor_id, cost=None):
        """
        Add a neighbor ID to this node’s neighbor list (ignores self &
        avoids duplicates). `cost` is unused and kept for signature
        compatibility.
        """
        if neighbor_id != self.node_id and neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)

    def __repr__(self):
        return f"Node {self.node_id}. Neighbors: {self.neighbors}. Port: {self.port}."

# ────────────────────────────── Tracker class ──────────────────────────────
class Tracker:
    """
    Single‑instance tracker that maintains the live roster of peers and
    broadcasts updates. It wraps all previous global state in one place.
    """
    def __init__(self, port: int, difficulty: int = 3, genesis_hash: str | None = None):
        self.port           = port
        self.difficulty     = difficulty
        self.genesis_hash   = genesis_hash or ("0" * 64)
        self.peers: dict[str, Node] = {}          # node_id ➜ Node
        self.lock = threading.Lock()              # protects self.peers
        self.server_socket: socket.socket | None = None

    # ── helper -------------------------------------------------------------
    @staticmethod
    def send_msg(sock: socket.socket, msg: dict) -> None:
        raw = json.dumps(msg, separators=(",", ":")).encode()
        sock.sendall(len(raw).to_bytes(4, "big") + raw)

    # ── roster maintenance -------------------------------------------------
    def _refresh_neighbor_lists(self):
        ids = list(self.peers.keys())
        for nid, peer in self.peers.items():
            peer.neighbors = [other for other in ids
                              if other != nid and other not in peer.neighbors]
            # de‑duplicate in case topology + refresh overlap
            peer.neighbors = list(dict.fromkeys(peer.neighbors))

    def _broadcast_peer_list(self):
        self._refresh_neighbor_lists()
        roster_msg = {
            "type": "PEER_LIST",
            "src":  "tracker",
            "dst":  "*",
            "ts":   time.time(),
            "payload": { "nodes": list(self.peers.keys()) }
        }
        for peer in self.peers.values():
            self.send_msg(peer.connection, roster_msg)

    # ── message forwarding -------------------------------------------------
    def _forward(self, msg: dict, sender: str) -> None:
        dst = msg.get("dst", "*")
        if dst in ("*", "broadcast"):
            for nid, peer in self.peers.items():
                if nid != sender:
                    self.send_msg(peer.connection, msg)
        elif dst in self.peers:
            self.send_msg(self.peers[dst].connection, msg)

    def _drop_peer(self, node: Node):
        """Remove peer on disconnect and broadcast new roster."""
        with self.lock:
            if node.node_id and node.node_id in self.peers:
                del self.peers[node.node_id]
        self._broadcast_peer_list()

    # ── per‑connection thread --------------------------------------------
    def _node_thread(self, node: Node):
        while True:
            try:
                hdr = node.connection.recv(4)
                if not hdr:
                    break
                data = node.connection.recv(int.from_bytes(hdr, "big"))
                if not data:
                    break
                msg = json.loads(data)
            except (ConnectionResetError, json.JSONDecodeError):
                break

            # first packet must be REGISTER
            if node.node_id is None:
                if msg.get("type") != "REGISTER":
                    break
                nid = msg["payload"]["node_id"]
                with self.lock:
                    if nid in self.peers:
                        break  # duplicate ID
                    node.node_id = nid
                    self.peers[nid] = node
                self._broadcast_peer_list()
                continue

            # graceful leave
            if msg.get("type") == "LEAVE":
                self._drop_peer(node)
                return

            # all other traffic
            self._forward(msg, sender=node.node_id)

        self._drop_peer(node)

    # ── main accept loop ---------------------------------------------------
    def serve_forever(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen()
        print(f"[tracker] Listening on 0.0.0.0:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                node = Node("temp")
                node.connection = conn
                node.connection_lock = threading.Lock()
                threading.Thread(target=self._node_thread,
                                 args=(node,),
                                 daemon=True).start()
        finally:
            self.server_socket.close()

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
                    new_node.add_neighbor(node_id_b)
                    nodes[node_id_a] = new_node
                else:
                    nodes[node_id_a].add_neighbor(node_id_b)
                if node_id_b not in nodes:
                    new_node = Node(node_id_b)
                    new_node.add_neighbor(node_id_a)
                    nodes[node_id_b] = new_node
                else:
                    nodes[node_id_b].add_neighbor(node_id_a)
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

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 network.py <PORT>")
        sys.exit(1)

    try:
        PORT = int(sys.argv[1])
        assert 1024 <= PORT <= 65535
    except (ValueError, AssertionError):
        print("Port must be an int between 1024 and 65535")
        sys.exit(1)

    Tracker(PORT).serve_forever()