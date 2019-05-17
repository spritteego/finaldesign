import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
from finaldesign.util.merkle import MerkleTools


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.chain2 = []
        self.nodes = set()
        self.merkle=MerkleTools()
        # Create the genesis block
        self.new_block(previous_hash='1', nonce=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def   resolve_conflict(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, nonce, previous_hash):
        """
        Create a new Block in the Blockchain

        :param nonce: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        self.merkle.make_tree()
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'tx_root':self.merkle.get_merkle_root()
        }

        # Reset the current list of transactions
        self.current_transactions = []
        self.merkle.reset_tree()

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, msg):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param msg: The data of msg
        :return: The index of the Block that will hold this transaction
        """
        tx_data={
            'sender': sender,
            'recipient': recipient,
            'msg': msg,
            'timestamp':time()
        }
        self.current_transactions.append(tx_data)
        self.merkle.add_leaf(str(tx_data),do_hash=True)
        self.merkle.make_tree()
        return self.last_block['index'] + 1
    def get_transactions(self):
        return self.current_transactions

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):

        # make the transaction  proofed
        # Done
        last_block_header = {
            'index': last_block['index'],
            'timestamp': last_block['timestamp'],
            'previous_hash': last_block['previous_hash'],
            'tx_root': last_block['tx_root']
        }
        nonce = 0
        while self.valid_proof(nonce,last_block_header) is False:
            nonce += 1
        guess = f'{nonce}{last_block_header}'.encode()
        return nonce,hashlib.sha256(guess).hexdigest()

    @staticmethod
    def valid_proof( nonce, blockheader):


        guess = f'{nonce}{blockheader}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"




