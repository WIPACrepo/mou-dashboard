<!--- Top of README Badges (automated) --->
[![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/mou-dashboard)](https://app.circleci.com/pipelines/github/WIPACrepo/mou-dashboard?branch=master&filter=all) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/mou-dashboard?include_prereleases)](https://github.com/WIPACrepo/mou-dashboard/) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) 
<!--- End of README Badges (automated) --->
# mou-dashboard

[![CircleCI](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master.svg?style=shield)](https://circleci.com/gh/WIPACrepo/mou-dashboard/tree/master)

A front-end to allow PIs to easily report to the ICC their
Statements of Work in accordance with MOUs:
[mou.icecube.aq](https://mou.icecube.aq/)

*Active MOUs:*
- IceCube M&O
- IceCube Upgrade


## How to Run Locally
You will need to launch four servers:
- MongoDB Server
- Token Server
- REST Server
- Web Server
- *Optional:* Telemetry Service (see [WIPAC Telemetry Repo](https://github.com/WIPACrepo/wipac-telemetry-prototype#wipac-telemetry-prototype))

### Launch Local MongoDB Server via Docker
1. *(Optional)* Kill All Active MongoDB Daemons
1. `./rest_server/resources/mongo_test_server.sh`

### Launch Local Token Server via Docker
1. `./rest_server/resources/token_test_server.sh`

### REST Server
A REST server that interfaces with a local MongoDB server

#### 1. Set Up Environment
    <activate virtual env with python 3.10+>
    pip install .
    export KEYCLOAK_CLIENT_SECRET=[...]
    . resources/keycloak-test-env-vars.sh

#### 2. Start the Server
    python -m rest_server

##### 2a. or with telemetry, instead:
    ./resources/start-rest-server-wipactel-local.sh

### Web App
A dashboard for managing & reporting MOU tasks

#### 1. Set Up Environment
    <activate virtual env with python 3.10+>
    pip install .
    export KEYCLOAK_CLIENT_SECRET=[...]
    . resources/keycloak-test-env-vars.sh
    python resources/client_secrets_json.py  # this will make a client_secrets.json file at $PWD

#### 2. Start the Server
    python -m web_app

##### 2a. or with telemetry, instead:
    ./resources/start-web-app-wipactel-local.sh

#### 3. View Webpage
Go to http://localhost:8050/
