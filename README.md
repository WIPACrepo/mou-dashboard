# mou-dashboard

[![CircleCI](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master.svg?style=shield)](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master)

A front-end to allow PIs to easily report to the ICC their
Statements of Work in accordance with MoUs:
[mou.icecube.aq](https://mou.icecube.aq/)

*Active MoUs:*
- IceCube M&O
- IceCube Upgrade


## How to Run Locally
You will need to launch four servers:
- MongoDB Server
- Token Server
- REST Server
- Web Server

### Launch Local MongoDB Server via Docker
1. *(Optional)* Kill All Active MongoDB Daemons
1. `./rest_server/resources/mongo_test_server.sh`

### Launch Local Token Server via Docker
1. `./rest_server/resources/token_test_server.sh`

### REST Server
A REST server that interfaces with a local MongoDB server *(future: also Smartsheet)*

#### 1. Set Up Enivornment
    python3 -m virtualenv -p python3 mou-dash-rest
    . mou-dash-rest/bin/activate
    pip install -r rest_server/requirements.txt

#### 2. Start the Server
    python -m rest_server [-x PATH_TO_XLSX_FILE]


### Web App
A dashboard for managing & reporting MoU tasks

#### 1. Set Up Enivornment
    python3.8 -m virtualenv -p python3.8 mou-dash-web
    . mou-dash-web/bin/activate
    pip install -r web_app/requirements.txt

#### 2. Start the Server
    python -m web_app

#### 3. View Webpage
Go to http://localhost:8050/


## Testing

### Local / Manual Testing
#### Unit
1. `pytest tests/unit`
#### Integration
1. Set up and start servers (see above)
1. `pytest tests/integration`

### Automated Testing
[![CircleCI](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master.svg?style=shield)](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master)


