Jonathan Liu, Roni Herschmann, Ron Zimmermann


Voting Blockchain System - Design.MD

We want to implement a voting application built on top of a blockchain. Users will vote from different nodes in a P2P network, where each node represents a sort of "voting booth". The blockchain will treat each vote as a transaction, and broadcast it to the remainder of the network. 

Blockchain Specifications:
Linked list
Data will be transactions with a timestamp+voting tally
State/data stored in each block:
Current nodes in network
Votes (each vote is a transaction)
Vote
Timestamp

P2P network/application specifications:
Implement a dense network with 1 tracker and multiple nodes
Have broadcasting of new nodes handled by something like HW3. As each node amends the blockchain, it will broadcast the entire new blockchain to the whole network, and nodes will validate/update their own state accordingly
See "State/data stored in each block" for structure of blocks. Blocks will form a linked list, implemented in python
Nodes will need to handle validation by proof of work, where nodes will need to find a nonce such that the header hash starts with enough zeros
Our initial threshold of zeroes will be 3
This blockchain will back a voting application, where each node will have a frontend that can cast votes for one of two candidates


Other features/notes:
We'll implement a graphical user interface for each decentralized node, and allow the nodes to vote 
We'll implement a solution to forking issues
This will first resolve to choose the longest chain, and then make the removed transactions retransmitted
For us these edge cases will be created by a rogue node manually



# Blockchain Linked List Design
# Author: Roni Herschmann
## Overview
This document outlines the enhanced linked list implementation for our blockchain-based voting system. The blockchain is designed as a sequential chain of blocks, where each block contains voting transactions, network information, and cryptographic links to maintain the chain's integrity. This implementation focuses on robustness, security, and concurrency management for distributed deployment.

## Constants and Configuration
- **GENESIS_PREVIOUS_HASH**: A constant value ("0") for the genesis block's previous hash
- **MINING_TIMEOUT_SECONDS**: Maximum time allowed for mining a block (60 seconds)
- **MAX_MINING_ITERATIONS**: Maximum iterations allowed for mining (10 million)
- **TARGET_BLOCK_TIME**: Target time for mining blocks (10 seconds) used for difficulty adjustment

## Block Structure
Each block in our blockchain linked list contains:

- **Index**: Sequential position in the blockchain
- **Previous Hash**: Cryptographic hash of the previous block (the "link")
- **Timestamp**: When the block was created
- **Transactions**: List of voting transactions (vote + timestamp)
- **Nodes**: Current nodes in the network
- **Nonce**: Value used in proof-of-work mining
- **Hash**: Cryptographic hash of the entire block

## Core Features

### Thread Safety
- **Chain Lock**: Ensures thread-safe access to the blockchain
- **Transaction Lock**: Ensures thread-safe access to pending transactions
- **All operations are properly synchronized** to prevent race conditions in multi-threaded environments

### Transaction Management
- **Transaction Validation**: Validates transaction format and required fields
- **Duplicate Detection**: Prevents duplicate transactions from being added
- **Pending Transaction Pool**: Stores valid transactions before they're added to a block
- **Transaction Reprocessing**: Handles orphaned transactions during chain replacements

### Mining and Proof of Work
- **Block Mining**: Finding a nonce that produces a hash with leading zeros
- **Hash Validation**: Verifying hash integrity and proof of work
- **Timeout Protection**: Prevents infinite loops during mining
- **Dynamic Difficulty Adjustment**: Automatically adjusts mining difficulty based on block times

### Chain Integrity
- **Block Linking**: Each block contains the hash of the previous block
- **Hash Verification**: Validation of block hashes and chain integrity
- **Genesis Block**: Special first block with predefined parameters
- **Full Chain Validation**: Methods to validate the entire blockchain

### Error Handling
- **Custom Exceptions**: BlockValidationError for validation issues
- **JSON Error Handling**: Error handling for serialization/deserialization
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Error Recovery**: Recovery mechanisms for mining failures

### Fork Resolution
- **Longest Chain Rule**: Accepts the longest valid chain as canonical
- **Orphaned Transaction Handling**: Reprocesses transactions that aren't in the new chain
- **Chain Replacement**: Mechanism to replace the current chain with a valid longer chain
- **Validation Before Replacement**: Ensures the new chain is valid before replacing

### Serialization and Networking
- **Blockchain Serialization**: Converts the blockchain to JSON for network transmission
- **Deserialization with Validation**: Reconstructs blockchain with hash verification
- **Type Safety**: Ensures deserialized data is validated properly

## Advanced Features

### Vote Tallying
- **Real-time Vote Counting**: Aggregates votes across all blocks
- **Candidate Tracking**: Maintains counts for each candidate
- **Threadsafe Results**: Results are protected during concurrent operations

### Dynamic Difficulty Adjustment
- **Automatic Difficulty Management**: Adjusts based on mining speed
- **Target Block Time Maintenance**: Aims to keep blocks generated at consistent intervals
- **Minimum Difficulty Safeguard**: Prevents difficulty from dropping below 1

### Extensive Validation
- **Empty Chain Protection**: Prevents operations on empty chains
- **Chain Structure Validation**: Ensures proper blockchain structure
- **Type Checking**: Verifies correct data types throughout the implementation

## Implementation Guidelines

### Thread-Safety Best Practices
- Always acquire locks before modifying shared data
- Use with-statements for locks to ensure they're properly released
- Minimize the duration of lock holding
- Avoid nested locks when possible to prevent deadlocks

### Error Handling Strategy
- Use try-except blocks for operations that may fail
- Log all errors with appropriate context
- Return error status or raise exceptions as appropriate
- Handle all possible exceptions during critical operations

### Logging Requirements
- Log all significant operations (block creation, mining, chain replacement)
- Include timestamp and operation details
- Use appropriate log levels (INFO, WARNING, ERROR)
- Log validation failures and security-related events

### Performance Considerations
- Implement timeouts for long-running operations
- Optimize hash calculations and validations
- Use efficient data structures for transaction management
- Avoid unnecessary blockchain traversals

## Security Considerations
- Validate all incoming data from the network
- Verify block hashes after deserialization
- Check transaction integrity before adding to the blockchain
- Protect against mining attacks with timeouts and difficulty adjustments
- Ensure proper concurrency controls to prevent race conditions
