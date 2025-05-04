# CSEE 4119 Spring 2025, Final Project

To run this project, execute (see below for file descriptions):
- python3 network.py <network_port>
- python3 decentralized_node.py <network_ip> <network_port> <node_id> (call for each node in the network)

File descriptions:
- network.py: implements a centralized Tracker server for managing nodes in a peer-to-peer network. Each node, represented by the Node class, registers with the Tracker, maintains a list of neighbors, and can send or receive broadcast or direct messages. The Tracker manages peer registration, connection handling via threads, and broadcasts updated peer lists upon changes in the network.
- decentralized_node.py: peer in a blockchain network that supports block mining, peer-to-peer synchronization, and fork resolution. Implements a NetworkInterface class for interacting with network. Deals with sending and receiving blocks, parsing them, and validating them. Implements longest-fork resolution
- LinkedList.py: implements Block and Blockchain classes that support the linked-list implementation of a blockchain that is stored on each node. Implements an API that supports proof-of-work/mining, adding transactions to blocks, and validating new blocks.


Assumptions:
- code tested with python version >= 3.10
- assume normal network conditions
- assume a reasonable amount of nodes in the network