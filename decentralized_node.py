import sys, socket, time, json, threading, webbrowser
from LinkedList import Blockchain, Block

# Flask imports
from flask import Flask, request, redirect, url_for, render_template_string

# Local blockchain instance and live peer list
blockchain = Blockchain(difficulty=1)
peer_ids: list[str] = []
# Blocks mined locally but not yet broadcast
pending_broadcast: list[Block] = []

# ────────────────────────────── NODE ID ──────────────────────────────
NODE_ID = None     # will be set in __main__

# ────────────────────────────── Flask app ──────────────────────────────
app = Flask(__name__)

# -------------------------------------------------------------------------
PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Node {{ node }}</title>
<style>
  body            { font-family: system-ui, sans-serif; background:#f5f7fa;
                    margin:0; padding:2rem; color:#333;}
  h1,h2           { margin-top:0; color:#2a2a2a;}
  .card           { background:#fff; border-radius:8px; padding:1.5rem;
                    box-shadow:0 2px 6px rgba(0,0,0,.08); max-width:620px;}
  label           { display:block; margin:.5rem 0 .25rem; font-weight:500;}
  input,select    { width:100%; padding:.5rem .6rem; font-size:1rem;
                    border:1px solid #ccc; border-radius:4px;}
  button          { margin-top:1rem; padding:.6rem 1.2rem; font-size:1rem;
                    background:#0077ff; color:#fff; border:none;
                    border-radius:4px; cursor:pointer;}
  button:hover    { background:#005fe0;}
  nav a           { color:#0077ff; text-decoration:none; margin-right:1rem;}
  nav a:hover     { text-decoration:underline;}
  .meta           { font-size:.9rem; color:#555; margin-bottom:1rem;}
</style>
</head>
<body>
  <div class="card">
    <h2>Node {{ node }}</h2>
    <p class="meta">Blockchain length: <strong>{{ length }}</strong></p>

    <form method="post" action="{{ url_for('submit_vote') }}">
      <label for="a">Votes for A</label>
      <input id="a" name="a" type="number" min="0" required>

      <label for="b">Votes for B</label>
      <input id="b" name="b" type="number" min="0" required>

      <label for="broadcast">Broadcast now?</label>
      <select id="broadcast" name="broadcast">
         <option value="y" selected>Yes</option>
         <option value="n">No (queue)</option>
      </select>

      <button type="submit">Submit Vote</button>
    </form>

    <nav style="margin-top:1.5rem;">
      <a href="{{ url_for('view_chain') }}">🔗 View chain</a>
      <a href="{{ url_for('view_tally') }}">🗳️ Vote tally</a>
      <a href="{{ url_for('do_broadcast') }}">📡 Broadcast queued blocks</a>
    </nav>
  </div>
</body>
</html>
"""

# -------------------------------------------------------------------------
# Additional template strings for chain and tally pages
CHAIN_PAGE = """
<!doctype html>
<html><head><meta charset="utf-8">
<title>Chain – Node {{ node }}</title>
<style>
 body{font-family:system-ui,sans-serif;background:#f5f7fa;margin:0;padding:2rem;color:#333;}
 table{border-collapse:collapse;width:100%;max-width:900px;background:#fff;
       box-shadow:0 2px 6px rgba(0,0,0,.08);border-radius:8px;overflow:hidden;}
 th,td{padding:.75rem 1rem;text-align:left;border-bottom:1px solid #eee;font-size:.9rem;}
 th{background:#0077ff;color:#fff;font-weight:600;border:none;}
 tr:last-child td{border-bottom:none;}
 code{font-family:monospace;}
 a{color:#0077ff;text-decoration:none;margin-top:1rem;display:inline-block;}
 a:hover{text-decoration:underline;}
</style></head><body>
<h2>Blockchain – Node {{ node }}</h2>
<table>
<thead><tr><th>#</th><th>Hash&nbsp;(first&nbsp;12)</th><th>Txs</th><th>Time</th></tr></thead>
<tbody>
{% for b in chain %}
<tr>
  <td>{{ b.index }}</td>
  <td><code>{{ b.hash[:12] }}</code></td>
  <td>{{ b.txs }}</td>
  <td>{{ b.time }}</td>
</tr>
{% endfor %}
</tbody>
</table>
<a href="{{ url_for('index') }}">← back</a>
</body></html>
"""

TALLY_PAGE = """
<!doctype html>
<html><head><meta charset="utf-8">
<title>Tally – Node {{ node }}</title>
<style>
 body{font-family:system-ui,sans-serif;background:#f5f7fa;margin:0;padding:2rem;color:#333;}
 .card{background:#fff;max-width:400px;padding:1.5rem;border-radius:8px;
       box-shadow:0 2px 6px rgba(0,0,0,.08);}
 h2{margin-top:0;}
 table{width:100%;border-collapse:collapse;margin-top:1rem;}
 th,td{padding:.6rem .8rem;text-align:left;border-bottom:1px solid #eee;font-size:.9rem;}
 th{background:#0077ff;color:#fff;font-weight:600;border:none;}
 tr:last-child td{border-bottom:none;}
 a{color:#0077ff;text-decoration:none;margin-top:1.2rem;display:inline-block;}
 a:hover{text-decoration:underline;}
</style></head><body>
<div class="card">
 <h2>Vote tally – Node {{ node }}</h2>
 <table>
   <thead><tr><th>Candidate</th><th>Votes</th></tr></thead>
   <tbody>
     {% for cand,n in tally.items() %}
       <tr><td>{{ cand }}</td><td>{{ n }}</td></tr>
     {% endfor %}
   </tbody>
 </table>
 <a href="{{ url_for('index') }}">← back</a>
</div>
</body></html>
"""
# -------------------------------------------------------------------------

# ────────────────────────── Helper to broadcast a mined block ──────────────────────────
def _broadcast_block(blk: Block):
    head_msg = {
        "type": "HEADERS",
        "src":  NODE_ID,
        "dst":  "*",
        "ts":   time.time(),
        "headers": [block_to_header(blk)]
    }
    net_interface.send(json.dumps(head_msg).encode())

    msg = {
        "type":  "BLOCK_MINED",
        "src":   NODE_ID,
        "dst":   "*",
        "ts":    time.time(),
        "length": blk.index + 1,
        "block": block_to_dict(blk)
    }
    net_interface.send(json.dumps(msg).encode())
    print(f"[INFO] broadcast block #{blk.index}")

# ────────────────────────── Flask route functions ──────────────────────────
@app.route("/")
def index():
    return render_template_string(PAGE,
                                  node=NODE_ID,
                                  length=len(blockchain.chain))

@app.route("/vote", methods=["POST"])
def submit_vote():
    votesA = int(request.form["a"])
    votesB = int(request.form["b"])
    broadcast_now = request.form["broadcast"] == "y"

    tx = {"vote": {"A": votesA, "B": votesB}, "timestamp": time.time()}
    try:
        blockchain.add_transaction(tx)
    except ValueError as e:
        return f"Transaction rejected: {e}", 400

    blk = blockchain.add_block(nodes=peer_ids)
    if blk is None:
        return "Mining failed", 500

    if broadcast_now:
        _broadcast_block(blk)
    else:
        pending_broadcast.append(blk)

    return redirect(url_for('index'))

@app.route("/broadcast")
def do_broadcast():
    """
    Broadcast every queued block in the order it was mined.
    """
    for blk in list(pending_broadcast):   # iterate over a snapshot
        _broadcast_block(blk)
    pending_broadcast.clear()
    return redirect(url_for('index'))

@app.route("/chain")
def view_chain():
    chain_rows = [
        {
            "index": b.index,
            "hash":  b.hash,
            "txs":   len(b.transactions),
            "time":  time.strftime('%H:%M:%S', time.localtime(b.timestamp))
        }
        for b in blockchain.chain
    ]
    return render_template_string(CHAIN_PAGE,
                                  node=NODE_ID,
                                  chain=chain_rows)

@app.route("/tally")
def view_tally():
    return render_template_string(TALLY_PAGE,
                                  node=NODE_ID,
                                  tally=blockchain.get_votes_tally())

# ────────────────────────────── Chain reorg helper ──────────────────────────────
def reorganize_chain(new_blk: Block):
    """
    Reorganize local chain so that `new_blk` can be appended.
    Any local blocks beyond the fork point are moved to pending_broadcast.
    Returns True if reorg done, False if no common ancestor.
    """
    # --- DEBUG: before any changes ---
    with blockchain.lock:
        # 1️⃣ find common ancestor (fork point)
        fork_idx = None
        for i in range(len(blockchain.chain) - 1, -1, -1):
            if blockchain.chain[i].hash == new_blk.previous_hash:
                fork_idx = i
                break
        if fork_idx is None:
            fork_idx = 0

        # 2️⃣ detach local tail (blocks after fork point) in-place so other references see the change
        local_tail = blockchain.chain[fork_idx + 1:]
        del blockchain.chain[fork_idx + 1:]

        # 3️⃣ insert the incoming block
        blockchain.chain.append(new_blk)

        # 4️⃣ re‑mine and append orphaned blocks so they follow the new tip
        reattached = 0
        for old_blk in local_tail:
            # assign new sequential index to avoid duplicates
            old_blk.index = blockchain.get_latest_block().index + 1
            old_blk.previous_hash = blockchain.get_latest_block().hash
            old_blk.nonce = 0
            old_blk.hash = old_blk.calculate_hash()
            try:
                old_blk.mine_block(blockchain.difficulty)
                blockchain.chain.append(old_blk)
                reattached += 1
            except TimeoutError:
                print(f"[WARN] re‑mining block #{old_blk.index} timed out; queued")
                pending_broadcast.append(old_blk)

        if reattached:
            print(f"[INFO] Re‑attached {reattached} orphaned blocks on new tip")

        print("[INFO] Reorg complete: chain now matches broadcasting peer plus re‑attached blocks")
        print("[DEBUG] Chain FINAL after re‑attach:")
        show_chain()
        return True

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
                    # --- Auto‑sync for fresh nodes -------------------
                    # If we have only the genesis block, request headers
                    if len(blockchain.chain) == 1 and peer_ids:
                        target_peer = peer_ids[0]
                        req = {
                            "type": "GET_HEADERS",
                            "src":  NODE_ID,
                            "dst":  target_peer,
                            "ts":   time.time(),
                            "payload": { "from_index": 0 }
                        }
                        self.send(json.dumps(req).encode())
                        print(f"[INFO] Requested full headers from {target_peer} for initial sync")

                elif mtype == "BLOCK_MINED":
                    try:
                        blk = dict_to_block(msg["block"])
                        remote_len = msg.get("length", blk.index + 1)  # sender’s chain length
                        if blk.is_valid(blockchain.difficulty):
                            with blockchain.lock:
                                expected = blockchain.get_latest_block().index + 1
                                if blk.index == expected and blk.previous_hash == blockchain.get_latest_block().hash:
                                    blockchain.chain.append(blk)
                                    print(f"[INFO] added block #{blk.index} from peer")
                                else:
                                    if remote_len > len(blockchain.chain):
                                        # Attempt reorg only if their chain is longer
                                        if reorganize_chain(blk):
                                            print(f"[INFO] reorganized chain; added block #{blk.index}")
                                        else:
                                            print("[WARN] fork with unknown ancestor; waiting for headers")
                                    else:
                                        print(f"[INFO] ignored shorter chain from {msg['src']} "
                                              f"(len {remote_len} vs {len(blockchain.chain)})")
                                        # Send polite rejection
                                        rej = {
                                            "type":   "REJECT_BLOCK",
                                            "src":    NODE_ID,
                                            "dst":    msg["src"],
                                            "ts":     time.time(),
                                            "reason": "shorter_chain",
                                            "your_length": remote_len,
                                            "my_length":   len(blockchain.chain)
                                        }
                                        self.send(json.dumps(rej).encode())
                        else:
                            print("[WARN] invalid PoW in block")
                    except Exception as e:
                        print("[ERR]", e)

                elif mtype == "GET_HEADERS":
                    # Peer wants headers starting from a given index
                    if msg["dst"] in ("*", NODE_ID):
                        loc_index = msg["payload"]["from_index"]
                        with blockchain.lock:
                            headers = [
                                block_to_header(b)
                                for b in blockchain.chain
                                if b.index >= loc_index
                            ]
                        reply = {
                            "type": "HEADERS",
                            "src":  NODE_ID,
                            "dst":  msg["src"],
                            "ts":   time.time(),
                            "headers": headers
                        }
                        self.send(json.dumps(reply).encode())

                elif mtype == "HEADERS":
                    if msg["dst"] in ("*", NODE_ID):
                        last = msg["headers"][-1]
                        remote_tip = last["index"]
                        if remote_tip > blockchain.get_latest_block().index:
                            # ask for full blocks we are missing
                            need_from = blockchain.get_latest_block().index + 1
                            req = {
                                "type": "GET_BLOCKS",
                                "src":  NODE_ID,
                                "dst":  msg["src"],
                                "ts":   time.time(),
                                "from_index": need_from
                            }
                            self.send(json.dumps(req).encode())

                elif mtype == "GET_BLOCKS":
                    if msg["dst"] in ("*", NODE_ID):
                        start = msg["from_index"]
                        with blockchain.lock:
                            blks = [
                                block_to_dict(b)
                                for b in blockchain.chain
                                if b.index >= start
                            ]
                        reply = {
                            "type": "BLOCKS",
                            "src":  NODE_ID,
                            "dst":  msg["src"],
                            "ts":   time.time(),
                            "blocks": blks
                        }
                        self.send(json.dumps(reply).encode())

                elif mtype == "BLOCKS":
                    if msg["dst"] in ("*", NODE_ID):
                        try:
                            new_blks = [dict_to_block(bd) for bd in msg["blocks"]]
                            with blockchain.lock:
                                if new_blks[0].index == blockchain.get_latest_block().index + 1:
                                    blockchain.chain.extend(new_blks)
                                    print(f"[INFO] extended chain by {len(new_blks)} blocks")
                        except Exception as e:
                            print("[ERR] importing blocks:", e)
                elif mtype == "REQ_CHAIN":
                    if msg["dst"] in ("*", NODE_ID):
                        send_full_chain(self, msg["src"], NODE_ID)

                elif mtype == "CHAIN":
                    if msg["dst"] in ("*", NODE_ID):
                        try:
                            new_chain = Blockchain.deserialize_chain(msg["chain"])
                            if blockchain.replace_chain(new_chain):
                                print("[INFO] Replaced local chain with longer one")
                        except Exception as e:
                            print("[ERR] failed to import chain:", e)
                elif mtype == "REJECT_BLOCK":
                    if msg["dst"] in ("*", NODE_ID):
                        print(f"[INFO] block rejected by {msg['src']} – reason: {msg.get('reason')}")
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

def block_to_header(block: Block) -> dict:
    """Lightweight dict for HEADERS messages."""
    return block.header()

def send_full_chain(net_if: 'NetworkInterface', dst_id: str, node_id: str):
    """Send entire chain to a peer that asked for it."""
    msg = {
        "type":  "CHAIN",
        "src":   node_id,
        "dst":   dst_id,
        "ts":    time.time(),
        "chain": blockchain.serialize_chain()
    }
    net_if.send(json.dumps(msg).encode())

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
            rawA = input("> Votes for party A "
                         "(commands: show | broadcast): ").strip()
            if rawA.lower() == "show":
                show_chain()
                continue
            if rawA.lower() == "broadcast":
                # send all queued blocks
                while pending_broadcast:
                    blk = pending_broadcast.pop(0)
                    head_msg = {
                        "type": "HEADERS",
                        "src":  node_id,
                        "dst":  "*",
                        "ts":   time.time(),
                        "headers": [block_to_header(blk)]
                    }
                    net_if.send(json.dumps(head_msg).encode())

                    msg = {
                        "type":  "BLOCK_MINED",
                        "src":   node_id,
                        "dst":   "*",
                        "ts":    time.time(),
                        "length": len(blockchain.chain),
                        "block": block_to_dict(blk)
                    }
                    net_if.send(json.dumps(msg).encode())
                    print(f"[INFO] broadcast stored block #{blk.index}")
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

        # Ask user if they want to broadcast right now
        choice = input("Broadcast this block now? (y/n): ").strip().lower()
        if choice != "y":
            pending_broadcast.append(new_blk)
            print(f"[INFO] queued block #{new_blk.index} for later broadcast")
            continue

        head_msg = {
            "type":  "HEADERS",
            "src":   node_id,
            "dst":   "*",
            "ts":    time.time(),
            "headers": [block_to_header(new_blk)]
        }
        net_if.send(json.dumps(head_msg).encode())

        msg = {
            "type":  "BLOCK_MINED",
            "src":   node_id,
            "dst":   "*",
            "ts":    time.time(),
            "length": len(blockchain.chain),
            "block": block_to_dict(new_blk)
        }
        net_if.send(json.dumps(msg).encode())
        print(f"[INFO] broadcast block #{new_blk.index}")

    
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 decentralized_node.py <tracker_ip> <tracker_port> <node_id> [flask_port]")
        sys.exit(1)

    tracker_ip   = sys.argv[1]
    tracker_port = int(sys.argv[2])
    NODE_ID      = sys.argv[3]
    flask_port   = int(sys.argv[4]) if len(sys.argv) > 4 else 7000

    net_interface = NetworkInterface(tracker_port, tracker_ip, NODE_ID)
    threading.Thread(target=net_interface.listen_for_messages, daemon=True).start()

    # optional: open browser automatically
    threading.Timer(1.0, lambda:
        webbrowser.open(f"http://127.0.0.1:{flask_port}/")).start()

    app.run(host="0.0.0.0", port=flask_port, debug=False)
