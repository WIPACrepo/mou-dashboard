<!--- Top of README Badges (automated) --->
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/mou-dashboard?include_prereleases)](https://github.com/WIPACrepo/mou-dashboard/) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/mou-dashboard)](https://github.com/WIPACrepo/mou-dashboard/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) 
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
You will need to launch servers:
- MongoDB Server
- REST Server
- Web Server
- *Optional:* Telemetry Service (see [WIPAC Telemetry Repo](https://github.com/WIPACrepo/wipac-telemetry-prototype#wipac-telemetry-prototype))

### 1. Launch Local MongoDB Server via Docker
1. *(Optional)* Kill All Active MongoDB Daemons
1. `docker run -p 27017:27017 --rm -i --name mou-mongo mongo:VERSION`
1. *(Optional)* Ingest data to create a realistic start-up state
```
TEST_JSON_DIR=tests/resources
mongoimport -d mo-supplemental -c LIVE_COLLECTION --type json --file $TEST_JSON_DIR/v2-mo-supplemental.json
mongoimport -d mo -c LIVE_COLLECTION --jsonArray --type json --file $TEST_JSON_DIR/v2-mo.json
```

### 2. Build Local Docker Image
```
docker build -t moudash:local --no-cache .
```

### 3. Launch REST Server
A REST server that interfaces with a local MongoDB server
```
docker run --network="host" --rm -i --name mou-rest \
    --env CI_TEST=true \
    moudash:local \
    python -m rest_server --override-krs-insts ./resources/dummy-krs-data.json
```

### 4. Launch Web App
A dashboard for managing & reporting MOU tasks
```
docker run --network="host" --rm -i --name mou-web \
    --env CI_TEST=true \
    --env DEBUG=yes \
    --env OIDC_CLIENT_SECRETS=resources/dummy_client_secrets_for_web_app.json \
    moudash:local \
    python -m web_app
```

#### 4a. Launch from Source
This is most useful for debugging and editing CSS live, since it requires no docker rebuilding.
```
<create virtual environment>
pip install .
pip uninstall UNKNOWN  # this uninstalls the mou source code so it can be ran/changed live
export CI_TEST=true
export DEBUG=yes
export OIDC_CLIENT_SECRETS=resources/dummy_client_secrets_for_web_app.json
python -m web_app
```

### 5. View Webpage
Go to http://localhost:8050/
