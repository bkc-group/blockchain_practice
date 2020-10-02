import json
import time
from hashlib import sha256

from flask import Flask, request
import requests
import ecdsa

from block import Block
from blockchain import Blockchain

app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    print(request.get_json())
    tx_data = request.get_json()["tx_data"]
    signature = request.get_json()["signature"]
    required_fields = ["from_wallet", "to_wallet", "amount"]
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(tx_data["from_wallet"]), curve=ecdsa.SECP256k1)
        vk.verify(bytes.fromhex(signature), json.dumps(tx_data).encode())
        tx_data["timestamp"] = time.time()
        blockchain.add_new_transaction(tx_data)
        return "Success", 201
    except:
        return "Wrong Signature", 400


@app.route('/user', methods=['POST'])
def create_new_user():
    user_info = request.get_json()
    required_fields = ["user_public_key"]
    for field in required_fields:
        if not user_info.get(field):
            return "Invalid transaction data", 404

    tx_data = {"from_wallet": "system",
               "to_wallet": user_info["user_public_key"],
               "amount": "50",
               "timestamp": time.time()}

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    print(block)
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


@app.route('/balance', methods=['POST'])
def get_balance():
    body = request.get_json()
    wallet_address = body['wallet_address']
    return {
               "balance": blockchain.get_balance(wallet_address)
           }, 200


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)

