#!/bin/bash
set -e

current_version=$(uv pip show sabogaapi | grep "Version: " | awk '{print $2}')
registry_version=$(docker image inspect ghcr.io/ruberhauptmann/saboga-api:latest | jq -r '.[0].Config.Labels."org.opencontainers.image.version"')

if [[ "$current_version" != "$registry_version" ]];
then
  echo "Version is bumped!"
  exit 0
else
  echo "Bump package version!"
  exit 1
fi
