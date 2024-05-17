#!/bin/bash
set -e

current_version=$(poetry version | awk '{print $2}')
registry_version=$(pip show sabogaapi | grep "Version: " | awk '{print $2}')

if [[ "$current_version" == "$registry_version" ]];
then
  echo "Version is not bumped!"
  exit 1
fi
