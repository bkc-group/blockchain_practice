import json
import time

from flask import Flask, request
from flask_mqtt import Mqtt

from block import Block
from blockchain import Blockchain

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection

mqtt = Mqtt(app)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("Connect to broker")
    mqtt.subscribe('blockchain/consensus')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    block_data = json.loads(message.payload.decode('utf-8'))
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"])
    block.hash = block.compute_hash()
    added = blockchain.add_block(block)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


@app.route('/new_block', methods=['POST'])
def create_new_block():
    if not blockchain.unconfirmed_transactions:
        return False

    last_block = blockchain.last_block

    new_block = Block(index=last_block.index + 1,
                      transactions=blockchain.unconfirmed_transactions,
                      timestamp=time.time(),
                      previous_hash=last_block.hash)
    mqtt.publish('blockchain/consensus', json.dumps(new_block.__dict__))
    blockchain.unconfirmed_transactions = []
    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)
