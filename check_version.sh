#!/bin/bash
set -e

poetry config repositories.gitlab "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi"
pip install saboga-api --extra-index-url "https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/api/v4/projects/${CI_PROJECT_ID}/packages/pypi/simple"

current_version=$(poetry version | awk '{print $2}')
registry_version=$(pip show sabogaapi | grep "Version: " | awk '{print $2}')

if [[ "$current_version" == "$registry_version" ]];
then
  echo "Version is not bumped!"
  exit 1
fi
