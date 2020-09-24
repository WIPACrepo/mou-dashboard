# mou-dashboard
Web App and Servers for the MoU Dashboard

A front-end to Smartsheet docs which allows PIs to easily report to the ICC their
Statements of Work in accordance with MoUs.


## REST Server
A REST server that interfaces with a local MongoDB server *(future: also Smartsheet)*

### Getting Started
    python3 -m virtualenv -p python3 mou-dash-rest
    . mou-dash-rest/bin/activate
    pip install -r rest_server/requirements.txt

#### *Optional:*
Kill All Active MongoDB Daemons

#### Launch Local MongoDB Server via Docker
    ./rest_server/resources/mongo_test_server.sh

#### Launch Local Token Server via Docker
    ./rest_server/resources/token_test_server.sh

### Running the Server
    python -m rest_server [-x PATH_TO_XLSX_FILE]


## Web App
A dashboard for managing & reporting MoU tasks

### Getting Started
    python3.8 -m virtualenv -p python3.8 mou-dash-web
    . mou-dash-web/bin/activate
    pip install -r web_app/requirements.txt

### Running the Server
    python -m web_app

### Viewing Webpage
#### Locally
Go to http://localhost:8050/
