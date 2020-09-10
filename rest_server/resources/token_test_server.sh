#!/bin/bash
docker run --name test-mou-token --rm \
  --network=host \
  --env auth_secret=secret wipac/token-service:latest python test_server.py # &