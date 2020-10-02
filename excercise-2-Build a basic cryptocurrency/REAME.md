- Run a node:
~~~
export FLASK_APP=node_server.py
flask run --port 8000
~~~

- Link PostMan: https://www.getpostman.com/collections/30b54d0d4ef8c5dc4e29. Please choose Exercise 2

- Example for running wallet command: 
~~~
python3 wallet.py --command generate_key_pair

python3 wallet.py --command send_money --private_key {insert_your_private_key} --from_wallet {insert_sender_public_key} --to_wallet {insert_receiver_public_key} --amount {insert_amount_you_want_to_send}
~~~