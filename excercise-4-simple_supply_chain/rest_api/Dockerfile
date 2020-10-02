FROM ubuntu:bionic

RUN \
 apt-get update --fix-missing \
 && apt-get install -y -q curl gnupg \
 && curl -sSL 'http://p80.pool.sks-keyservers.net/pks/lookup?op=get&search=0x8AA7AF1F1091A5FD' | apt-key add -  \
 && echo 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' >> /etc/apt/sources.list \
 && apt-get update --fix-missing

RUN apt-get install -y --allow-unauthenticated -q python3-grpcio-tools \
    python3-pip \
    python3-sawtooth-rest-api \
    python3-sawtooth-sdk

RUN pip3 install \
    aiohttp \
    aiopg \
    bcrypt \
    itsdangerous \
    pycrypto \
    psycopg2-binary \
    jsonschema \
    ipfsapi \
    ipfshttpclient \
    aiohttp_cors


WORKDIR /project/sawtooth-supply

ENV PATH $PATH:/project/sawtooth-supply/bin

COPY . .

EXPOSE 8080

# ENTRYPOINT [ "python3", "main.py" ]