import sys, socket, time, json, threading
from LinkedList import Blockchain, Block

# Local blockchain instance and live peer list
blockchain = Blockchain(difficulty=1)
peer_ids: list[str] = []

class NetworkInterface():
    """
    DO NOT EDIT.
    
    Provided interface to the network. In addition to typical send/recv methods,
    it also provides a method to receive an initial message from the network, which
    contains the costs to neighbors. 
    """
    def __init__(self, network_port, network_ip, node_id):
        """
        Constructor for the NetworkInterface class.

        Parameters:
            network_port : int
                The port the network is listening on.
            network_ip : str
                The IP address of the network.
            node_id : str
                The unique identifier for this peer.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((network_ip, network_port))

        # Immediately self‑register with the tracker
        register_msg = {
            "type": "REGISTER",
            "src":  node_id,
            "dst":  "tracker",
            "ts":   time.time(),
            "payload": { "node_id": node_id }
        }
        self.send(json.dumps(register_msg).encode())

        # Tracker will answer with PEER_LIST soon; no blocking read here
        
    def initial_message(self): 
        return ""
    
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
                # ---- framed read: 4-byte length prefix ----
                hdr = self.recv(4)
                if not hdr:
                    break
                msg_len = int.from_bytes(hdr, "big")
                data = self.recv(msg_len)
                if not data:
                    break

                # ---- decode JSON ----
                try:
                    msg = json.loads(data.decode())
                except json.JSONDecodeError:
                    print("[WARN] received non-JSON payload")
                    continue

                mtype = msg.get("type")
                if mtype == "PEER_LIST":
                    global peer_ids
                    peer_ids = msg["payload"]["nodes"]
                    print(f"[INFO] peers → {peer_ids}")

                elif mtype == "BLOCK_MINED":
                    try:
                        blk = dict_to_block(msg["block"])
                        if blk.is_valid(blockchain.difficulty):
                            with blockchain.lock:
                                if blk.index == blockchain.get_latest_block().index + 1:
                                    blockchain.chain.append(blk)
                                    print(f"[INFO] added block #{blk.index} from peer")
                                else:
                                    print("[WARN] out-of-order block ignored")
                        else:
                            print("[WARN] invalid PoW in block")
                    except Exception as e:
                        print("[ERR]", e)
                else:
                    print("[RECV]", msg)

            except Exception as e:
                print("listener error:", e)
                break

    def close(self):
        """
        Close the socket connection with the network.
        """
        self.sock.close()

# ───────────────── Block <-> JSON helpers ─────────────────
def block_to_dict(block: Block) -> dict:
    """Convert Block to a plain dict ready for json.dumps()."""
    return {
        "index": block.index,
        "previous_hash": block.previous_hash,
        "timestamp": block.timestamp,
        "transactions": block.transactions,
        "nodes": block.nodes,
        "nonce": block.nonce,
        "hash": block.hash
    }

def dict_to_block(d: dict) -> Block:
    """Convert dict to Block and verify its hash integrity."""
    blk = Block(
        d["index"], d["previous_hash"], d["timestamp"],
        d["transactions"], d["nodes"], d["nonce"]
    )
    if blk.calculate_hash() != d["hash"]:
        raise ValueError("Hash mismatch in received block")
    blk.hash = d["hash"]
    return blk

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

# -------------------------------------------------------------------------
def show_chain():
    print(f"\n––– Local blockchain ({len(blockchain.chain)} blocks) –––")
    for blk in blockchain.chain:
        print(f"#{blk.index}  {blk.hash[:10]}…  txs={len(blk.transactions)}")
    print("––––––––––––––––––––––––––––––––––––––––––––––\n")
# -------------------------------------------------------------------------

def send_user_blocks(net_if: 'NetworkInterface', node_id: str):
    """Prompt user for votes, mine a block, broadcast it."""
    while True:
        try:
            rawA = input("> Votes for party A (or 'show'): ").strip()
            if rawA.lower() == "show":
                show_chain()
                continue
            votesA = int(rawA)

            rawB = input("> Votes for party B (or 'show'): ").strip()
            if rawB.lower() == "show":
                show_chain()
                continue          # restart loop so you’re re-prompted for votes A again
            votesB = int(rawB)
        except ValueError:
            print("Please enter integers.")
            continue
        except KeyboardInterrupt:
            print("\nExiting…")
            net_if.close()
            sys.exit(0)

        tx = {"vote": {"A": votesA, "B": votesB},
              "timestamp": time.time()}

        try:
            blockchain.add_transaction(tx)
        except ValueError as e:
            print("Tx rejected:", e)
            continue

        new_blk = blockchain.add_block(nodes=peer_ids)
        if not new_blk:
            print("[WARN] mining failed")
            continue

        msg = {
            "type": "BLOCK_MINED",
            "src":  node_id,
            "dst":  "*",
            "ts":   time.time(),
            "block": block_to_dict(new_blk)
        }
        net_if.send(json.dumps(msg).encode())
        print(f"[INFO] broadcast block #{new_blk.index}")

    


if __name__ == '__main__':
    network_ip   = sys.argv[1]          # tracker IP
    network_port = int(sys.argv[2])     # tracker port
    node_id      = sys.argv[3]          # unique ID for this peer

    net_interface = NetworkInterface(network_port, network_ip, node_id)

    listener_thread = threading.Thread(target=net_interface.listen_for_messages,
                                    daemon=True)
    listener_thread.start()

    send_user_blocks(net_interface, node_id)










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

