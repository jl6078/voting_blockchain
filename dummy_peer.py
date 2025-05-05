#!/usr/bin/env python3
import socket, json, sys, threading, time

def send(sock, obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    sock.sendall(len(raw).to_bytes(4, "big") + raw)

def listener(sock):
    while True:
        hdr = sock.recv(4)
        if not hdr:
            print("socket closed"); return
        data = sock.recv(int.from_bytes(hdr, "big"))
        print("⇦", data.decode())

node_id = sys.argv[1]
host    = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
port    = int(sys.argv[3]) if len(sys.argv) > 3 else 50000

s = socket.create_connection((host, port))
threading.Thread(target=listener, args=(s,), daemon=True).start()

send(s, {                 # REGISTER
    "type": "REGISTER",
    "src":  node_id,
    "dst":  "tracker",
    "ts":   time.time(),
    "payload": { "node_id": node_id }
})

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:  # graceful LEAVE
    send(s, { "type": "LEAVE",
              "src": node_id,
              "dst": "tracker",
              "ts":  time.time(),
              "payload": {} })
    s.close()