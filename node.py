from argparse import ArgumentParser
from flask import Flask, jsonify, request
from uuid import uuid4
from finaldesign.blockchain import Blockchain
# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain1 = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain1.last_block
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain1.new_transaction(
        sender="0",
        recipient=node_identifier,
        msg="mine one coin!",
    )
    # Forge the new Block by adding it to the chain
    nonce, previous_hash = blockchain1.proof_of_work(last_block)

    block = blockchain1.new_block(nonce, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'msg']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain1.new_transaction(
        values['sender'], values['recipient'], values['msg'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/transactions', methods=['GET'])
def transactions():
    tx = blockchain1.get_transactions()
    response = {
        "transactions": list(tx),
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain1.chain,
        'length': len(blockchain1.chain),
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain1.nodes),
        'length': len(list(blockchain1.nodes))
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain1.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain1.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain1.resolve_conflict()

    if replaced:
        response = {
            'message': 'Our chain has synchronized',
            'new_chain': blockchain1.chain
        }
    else:
        response = {
            'message': 'Our chain is the newest',
            'chain': blockchain1.chain
        }

    return jsonify(response), 200


parser = ArgumentParser()
parser.add_argument(
    '-p',
    '--port',
    default=5000,
    type=int,
    help='port to listen on')
args = parser.parse_args()
port = args.port
app.run(host='0.0.0.0', port=port)
