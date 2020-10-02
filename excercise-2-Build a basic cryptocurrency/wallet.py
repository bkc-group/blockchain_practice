import argparse
import json

import ecdsa
import requests

node_url = 'http://localhost:8000'


def generate_key_pair():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    message = {"user_public_key": public_key.to_string().hex()}
    requests.post(node_url+"/user", json=message)
    print("PRIVATE_KEY: {}".format(private_key.to_string().hex()))
    print("PUBLIC_KEY: {}".format(public_key.to_string().hex()))


def send_money(private_key, from_wallet, to_wallet, amount):
    tx_data = {
        "from_wallet": from_wallet,
        "to_wallet": to_wallet,
        "amount": amount
    }
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    # print(json.dumps(tx_data).encode())
    sign = sk.sign(json.dumps(tx_data).encode()).hex()
    message = {
        "tx_data": tx_data,
        "signature": sign
    }
    requests.post(node_url+"/new_transaction", json=message)
    print("send transaction: {}".format(message))


parser = argparse.ArgumentParser()
parser.add_argument("--command", "-c")
parser.add_argument("--private_key", "-p")
parser.add_argument("--from_wallet", "-f")
parser.add_argument("--to_wallet", "-t")
parser.add_argument("--amount", "-a")

args = parser.parse_args()

if args.command == "generate_key_pair":
    generate_key_pair()
elif args.command == "send_money":
    if args.private_key and args.from_wallet and args.to_wallet and args.amount:
        send_money(args.private_key, args.from_wallet, args.to_wallet, args.amount)
    else:
        print("The command need more arguments")
else:
    print("Does not support the command")
