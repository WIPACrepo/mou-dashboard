#!/bin/bash
set -x  # turn on debugging
set -e  # exit on fail

# Setup Keycloak environment variables for a test environment

# make sure we're sourcing
(return 0 2>/dev/null) && sourced=1 || sourced=0
if [ "$sourced" -eq "0" ]; then
   echo "You need to source this script"
   exit 1
fi

export KEYCLOAK_REALM=IceCube-FullTest
export KEYCLOAK_URL=https://keycloak.icecube.wisc.edu
export KEYCLOAK_CLIENT_ID=mou
# export KEYCLOAK_CLIENT_SECRET=""
export KEYCLOAK_CLIENT_REALM=IceCube-FullTest

if [ -z "$KEYCLOAK_CLIENT_SECRET" ]; then
      echo "\$KEYCLOAK_CLIENT_SECRET is not set. (Hint: export KEYCLOAK_CLIENT_SECRET=...)"
      return 1
fi