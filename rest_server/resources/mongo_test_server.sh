#!/bin/bash
docker run --name test-maddash-mongo --rm \
  --network=host circleci/mongo:3.7.9-ram # &