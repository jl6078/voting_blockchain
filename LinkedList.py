# Blockchain Implementation in Python
# This is the linked list implementation of a simple blockchain
# It includes basic functionalities like adding blocks, mining, and validating the chain.
# Author: Roni Herschmann

# Blockchain Implementation in Python
# This is the linked list implementation of a simple blockchain
# It includes basic functionalities like adding blocks, mining, and validating the chain.
# Author: Roni Herschmann

import hashlib
import time
import json
import logging
from typing import List, Dict, Any
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("blockchain")

# Constants
GENESIS_PREVIOUS_HASH = "0"
MINING_TIMEOUT_SECONDS = 60
MAX_MINING_ITERATIONS = 10000000  # 10 million iterations max

class BlockValidationError(Exception):
    """Exception raised for validation errors in blocks or the blockchain."""
    pass

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float,
                 transactions: List[Dict], nodes: List[str], nonce: int = 0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions  # List of vote transactions
        self.nodes = nodes  # Current nodes in network
        self.nonce = nonce
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        """Calculate the hash of this block."""
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nodes": self.nodes,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
        
    def mine_block(self, difficulty: int) -> None:
        """
        Proof of work: Find a hash that starts with 'difficulty' number of zeros
        
        Args:
            difficulty: Number of leading zeros required in the hash
            
        Raises:
            TimeoutError: If mining takes too long
        """
        target = '0' * difficulty
        start_time = time.time()
        iterations = 0
        
        logger.info(f"Started mining block {self.index} with difficulty {difficulty}")
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            iterations += 1
            
            # Check for timeout or excessive iterations
            if time.time() - start_time > MINING_TIMEOUT_SECONDS:
                logger.warning(f"Mining timeout after {MINING_TIMEOUT_SECONDS} seconds")
                raise TimeoutError(f"Mining took longer than {MINING_TIMEOUT_SECONDS} seconds")
                
            if iterations > MAX_MINING_ITERATIONS:
                logger.warning(f"Exceeded max mining iterations ({MAX_MINING_ITERATIONS})")
                raise TimeoutError(f"Mining exceeded {MAX_MINING_ITERATIONS} iterations")
        
        logger.info(f"Successfully mined block {self.index} with nonce {self.nonce} in {iterations} iterations")
            
    def is_valid(self, difficulty: int) -> bool:
        """
        Validate the block's hash
        
        Args:
            difficulty: Number of leading zeros required in the hash
            
        Returns:
            bool: True if the block is valid, False otherwise
        """
        return (self.hash == self.calculate_hash() and
                self.hash[:difficulty] == '0' * difficulty)


class Blockchain:
    def __init__(self, difficulty: int = 3):
        """
        Initialize a new blockchain with genesis block
        
        Args:
            difficulty: Number of leading zeros required in block hashes
        """
        logger.info(f"Initializing blockchain with difficulty {difficulty}")
        
        self.chain = []
        self.difficulty = difficulty
        
        # Thread‑safe access to the chain (allow re‑entrant acquisition)
        self.lock = threading.RLock()
        
        # Pending transactions
        self.pending_transactions = []
        self.transaction_lock = threading.Lock()
        
        # Create the genesis block
        self.create_genesis_block()
        
        # Track time to mine blocks for potential difficulty adjustments
        self.last_block_time = time.time()
        self.target_block_time = 10  # Target 10 seconds per block
        
    def create_genesis_block(self) -> None:
        """Create the first block in the chain"""
        logger.info("Creating genesis block")
        
        genesis_block = Block(0, GENESIS_PREVIOUS_HASH, time.time(), [], [], 0)
        genesis_block.mine_block(self.difficulty)
        
        with self.lock:
            self.chain.append(genesis_block)
        
    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain
        
        Returns:
            Block: The most recent block
            
        Raises:
            ValueError: If the chain is empty
        """
        with self.lock:
            if not self.chain:
                logger.error("Attempted to get latest block from empty chain")
                raise ValueError("Blockchain is empty")
            return self.chain[-1]
    
    def validate_transaction(self, transaction: Dict) -> bool:
        """
        Validate a transaction before adding it to the pending transactions
        
        Args:
            transaction: The transaction to validate
            
        Returns:
            bool: True if the transaction is valid, False otherwise
        """
        # Check transaction format
        if not isinstance(transaction, dict):
            logger.warning(f"Invalid transaction format: {transaction}")
            return False
            
        # Check required fields for a vote transaction
        if 'vote' not in transaction:
            logger.warning(f"Transaction missing 'vote' field: {transaction}")
            return False
            
        # Check for timestamp
        if 'timestamp' not in transaction:
            logger.warning(f"Transaction missing 'timestamp' field: {transaction}")
            return False
            
        # Additional validation can be added here
        
        return True
        
    def is_duplicate_transaction(self, transaction: Dict) -> bool:
        """
        Check if a transaction is already in the pending list
        
        Args:
            transaction: The transaction to check
            
        Returns:
            bool: True if it's a duplicate, False otherwise
        """
        with self.transaction_lock:
            # Create a serialized version of the transaction for comparison
            tx_string = json.dumps(transaction, sort_keys=True)
            
            # Check against all pending transactions
            for pending_tx in self.pending_transactions:
                pending_tx_string = json.dumps(pending_tx, sort_keys=True)
                if pending_tx_string == tx_string:
                    return True
                    
        return False
        
    def add_transaction(self, transaction: Dict) -> int:
        """
        Add a transaction to the pending transactions list
        
        Args:
            transaction: The transaction to add
            
        Returns:
            int: The index of the block this transaction will be added to
            
        Raises:
            ValueError: If the transaction is invalid or a duplicate
        """
        # Validate the transaction
        if not self.validate_transaction(transaction):
            logger.warning(f"Rejected invalid transaction: {transaction}")
            raise ValueError("Invalid transaction format")
            
        # Check for duplicates
        if self.is_duplicate_transaction(transaction):
            logger.warning(f"Rejected duplicate transaction: {transaction}")
            raise ValueError("Duplicate transaction")
            
        # Add the transaction
        with self.transaction_lock:
            self.pending_transactions.append(transaction)
            logger.info(f"Added transaction: {transaction}")
            
            # Return the index of the next block
            return self.get_latest_block().index + 1
        
    def add_block(self, nodes: List[str]) -> Block:
        """
        Add a new block to the chain with pending transactions
        
        Args:
            nodes: List of nodes in the network
            
        Returns:
            Block: The newly created and mined block
        """
        logger.info("Creating new block with pending transactions")
        
        # Get pending transactions with the lock
        with self.transaction_lock:
            if not self.pending_transactions:
                logger.warning("No pending transactions to include in block")
                return None
                
            transactions = self.pending_transactions.copy()
            self.pending_transactions = []
            
        # Create and mine the new block
        with self.lock:
            latest_block = self.get_latest_block()
            new_block = Block(
                latest_block.index + 1,
                latest_block.hash,
                time.time(),
                transactions,
                nodes
            )
            
            try:
                # Mine the block
                new_block.mine_block(self.difficulty)
                
                # Add to chain
                self.chain.append(new_block)
                
                # Update timing information for difficulty adjustment
                current_time = time.time()
                block_time = current_time - self.last_block_time
                self.last_block_time = current_time
                
                # Adjust difficulty if needed
                self._adjust_difficulty(block_time)
                
                logger.info(f"Added new block #{new_block.index} with {len(transactions)} transactions")
                return new_block
                
            except TimeoutError as e:
                logger.error(f"Mining failed: {str(e)}")
                
                # Return pending transactions to the pool
                with self.transaction_lock:
                    self.pending_transactions.extend(transactions)
                    
                return None
    
    def _adjust_difficulty(self, block_time: float) -> None:
        """
        Adjust mining difficulty based on the time taken to mine the last block
        
        Args:
            block_time: Time taken to mine the last block in seconds
        """
        # Only adjust after we have some blocks
        if len(self.chain) < 10:
            return
            
        # If blocks are taking too long, decrease difficulty
        if block_time > self.target_block_time * 2:
            if self.difficulty > 1:
                self.difficulty -= 1
                logger.info(f"Decreased difficulty to {self.difficulty} (block time: {block_time:.2f}s)")
                
        # If blocks are being mined too quickly, increase difficulty
        elif block_time < self.target_block_time / 2:
            self.difficulty += 1
            logger.info(f"Increased difficulty to {self.difficulty} (block time: {block_time:.2f}s)")
    
    def get_votes_tally(self) -> Dict:
        """
        Calculate the vote tally across the entire blockchain
        
        Returns:
            Dict: Dictionary with candidate names as keys and vote counts as values
        """
        tally = {}
        
        with self.lock:
            for block in self.chain:
                for transaction in block.transactions:
                    if 'vote' in transaction:
                        candidate = transaction['vote']
                        if candidate in tally:
                            tally[candidate] += 1
                        else:
                            tally[candidate] = 1
        
        logger.info(f"Current vote tally: {tally}")            
        return tally
        
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        logger.info("Validating blockchain integrity")
        
        with self.lock:
            # Check if chain is empty
            if not self.chain:
                logger.warning("Chain is empty")
                return False
                
            # Check genesis block
            if self.chain[0].previous_hash != GENESIS_PREVIOUS_HASH:
                logger.error("Invalid genesis block")
                return False
                
            # Validate each block
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i-1]
                
                # Check hash integrity
                if current.hash != current.calculate_hash():
                    logger.error(f"Block #{current.index} has invalid hash")
                    return False
                    
                # Check link integrity
                if current.previous_hash != previous.hash:
                    logger.error(f"Block #{current.index} has invalid previous hash")
                    return False
                    
                # Check proof of work
                if current.hash[:self.difficulty] != '0' * self.difficulty:
                    logger.error(f"Block #{current.index} has invalid proof of work")
                    return False
            
            logger.info("Blockchain is valid")        
            return True
        
    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Replace current chain with a longer valid chain (Fork resolution mechanism)
        
        Args:
            new_chain: The new chain to replace the current one
            
        Returns:
            bool: True if the chain was replaced, False otherwise
            
        Raises:
            TypeError: If new_chain is not a list of Block objects
            BlockValidationError: If new_chain is invalid
        """
        logger.info(f"Evaluating chain replacement with new chain of length {len(new_chain)}")
        
        # Validate new_chain type
        if not isinstance(new_chain, list):
            logger.error("new_chain is not a list")
            raise TypeError("new_chain must be a list")
            
        # Check if all items are Block instances
        if not all(isinstance(block, Block) for block in new_chain):
            logger.error("new_chain contains non-Block objects")
            raise TypeError("All items in new_chain must be Block instances")
            
        # Chain validation
        with self.lock:
            # Check if new chain is longer
            if len(new_chain) <= len(self.chain):
                logger.info("Rejecting new chain - not longer than current chain")
                return False
                
            # Validate new chain
            if not new_chain:
                logger.error("New chain is empty")
                raise BlockValidationError("New chain is empty")
                
            # Check genesis block
            if new_chain[0].previous_hash != GENESIS_PREVIOUS_HASH:
                logger.error("Invalid genesis block in new chain")
                raise BlockValidationError("Invalid genesis block in new chain")
                
            # Validate each block in the new chain
            for i in range(1, len(new_chain)):
                current = new_chain[i]
                previous = new_chain[i-1]
                
                if (current.previous_hash != previous.hash or
                    current.hash != current.calculate_hash() or
                    current.hash[:self.difficulty] != '0' * self.difficulty):
                    logger.error(f"Invalid block at index {i} in new chain")
                    raise BlockValidationError(f"Invalid block at index {i} in new chain")
                    
            # Collect transactions that need to be retransmitted
            current_transactions = set()
            for block in self.chain:
                for tx in block.transactions:
                    # Create a hashable representation of the transaction
                    tx_string = json.dumps(tx, sort_keys=True)
                    current_transactions.add(tx_string)
                    
            new_transactions = set()
            for block in new_chain:
                for tx in block.transactions:
                    tx_string = json.dumps(tx, sort_keys=True)
                    new_transactions.add(tx_string)
                    
            # Find orphaned transactions (in old chain but not in new chain)
            orphaned = current_transactions - new_transactions
            
            # Replace chain
            old_chain = self.chain
            self.chain = new_chain
            
            logger.info(f"Chain replaced with new chain of length {len(new_chain)}")
            logger.info(f"Found {len(orphaned)} orphaned transactions to reprocess")
            
            # Re-add orphaned transactions to pending
            with self.transaction_lock:
                for tx_string in orphaned:
                    try:
                        tx = json.loads(tx_string)
                        if not self.is_duplicate_transaction(tx):
                            self.pending_transactions.append(tx)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse orphaned transaction: {tx_string}")
                    
            return True
    
    def serialize_chain(self) -> str:
        """
        Serialize the blockchain to a JSON string for transmission over the network
        
        Returns:
            str: JSON string representation of the blockchain
            
        Raises:
            json.JSONEncodeError: If serialization fails
        """
        logger.info("Serializing blockchain")
        
        serialized_chain = []
        with self.lock:
            for block in self.chain:
                serialized_block = {
                    "index": block.index,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "transactions": block.transactions,
                    "nodes": block.nodes,
                    "nonce": block.nonce,
                    "hash": block.hash
                }
                serialized_chain.append(serialized_block)
        
        try:
            json_data = json.dumps(serialized_chain)
            logger.info(f"Blockchain serialized to {len(json_data)} bytes")
            return json_data
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise
    
    @staticmethod
    def deserialize_chain(chain_json: str) -> List[Block]:
        """
        Deserialize a JSON string back into a list of Block objects
        
        Args:
            chain_json: JSON string representation of the blockchain
            
        Returns:
            List[Block]: List of Block objects
            
        Raises:
            json.JSONDecodeError: If deserialization fails
            ValueError: If deserialized data is invalid
        """
        logger.info("Deserializing blockchain")
        
        try:
            chain_data = json.loads(chain_json)
        except json.JSONDecodeError as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise
            
        if not isinstance(chain_data, list):
            logger.error("Deserialized data is not a list")
            raise ValueError("Deserialized data must be a list")
            
        deserialized_chain = []
        
        for block_data in chain_data:
            # Validate required fields
            required_fields = ["index", "previous_hash", "timestamp", "transactions", 
                               "nodes", "nonce", "hash"]
            for field in required_fields:
                if field not in block_data:
                    logger.error(f"Missing required field '{field}' in block data")
                    raise ValueError(f"Missing required field '{field}' in block data")
                    
            # Create the block
            block = Block(
                block_data["index"],
                block_data["previous_hash"],
                block_data["timestamp"],
                block_data["transactions"],
                block_data["nodes"],
                block_data["nonce"]
            )
            
            # Recalculate and validate the hash
            calculated_hash = block.calculate_hash()
            if calculated_hash != block_data["hash"]:
                logger.warning(
                    f"Block #{block.index} hash mismatch: "
                    f"expected {block_data['hash']}, calculated {calculated_hash}"
                )
                # Set the hash to the calculated value to ensure integrity
                block.hash = calculated_hash
            else:
                # Hash matches, use the provided one
                block.hash = block_data["hash"]
                
            deserialized_chain.append(block)
            
        logger.info(f"Deserialized chain with {len(deserialized_chain)} blocks")
        return deserialized_chain