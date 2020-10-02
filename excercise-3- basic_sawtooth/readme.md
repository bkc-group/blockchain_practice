docker-compose -f sawtooth-default-pbft.yaml up

# Check rest api running
docker exec -it sawtooth-rest-api-default-0 bash
ps --pid 1 fw

# Confirm functionality
docker exec -it sawtooth-shell-default bash
curl http://sawtooth-rest-api-default-0:8008/peers

sawtooth peer list --url http://sawtooth-rest-api-default-0:8008
sawnet peers list http://sawtooth-rest-api-default-0:8008

# Test with intkey
intkey set --url http://sawtooth-rest-api-default-0:8008 key 999
intkey show --url http://sawtooth-rest-api-default-1:8008 key
