# CSEE 4119 Spring 2025, Final Project

Test Case 1: 3 node network, 1 transaction per node

Nodes:
- Node A
- Node B
- Node C

Transactions:
- Node A votes 10, 20 (for A and B respectively)
- Node B votes 15, 15
- Node C votes 5, 25

Test Case 2: 5 node network, scattered transactions, demonstrate resilience in a larger network 

Nodes:
- Node A
- Node B
- Node C
- Node D
- Node E

Transactions:
- Node A votes 10, 20 (for A and B respectively)
- Node B votes 15, 15
- Node A votes 30, 10
- Node C votes 5, 25
- Node B votes 20, 25
- Node E votes 10, 0

Test Case 3: 3 node network, one node joins late
Nodes:
- Node A
- Node B
- Node C (joins after 2 transactions)

Transactions: 
- Node A votes 10, 20
- Node B votes 35, 8
- Node C joins
- Node C votes 30, 12
- Node A votes 10, 0


Test Case 4: 3 node network, demonstrate fork
Nodes:
- Node A (will be fork causer)
- Node B 
- Node C

Transactions: 
- Node A votes 10, 10
- Node B votes 5, 10
- Node A votes 20, 10 and doesn't broadcast
- Node A votes 5, 15 and doesn't broadcast
- Node B votes 5, 10 and doesn't broadcast
- Node A broadcasts (B should remove its unbroadcasted block, adopt the longer chain, and place it in the broadcasting queue)
- Node B broadcasts the transactions it removed and queued


Test Case 5: Ensure that longest chain rejects shorter chain broadcast
Nodes:
- Node A (will be longest chain)
- Node B (shorter chain broadcasting)

Transactions:
- Node A votes 10, 10
- Node A votes 21, 23 and doesn't broadcast
- Node A votes 31, 2 and doesn't broadcast
- Node B votes 32, 10, and broadcasts
- Node A rejects block from Node B (shorter blockchain) and retains its current chain

Test Case 6: Ensure that new node joining network updates to the longest chain is requested
Nodes:
- Node A
- Node B
- Node C (will join after 2 transactions)

- Node A votes 10, 20
- Node B votes 21, 33
- Node C joins (receives votes 31, 53)






All above test cases output blockchains as expected.