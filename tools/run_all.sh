#!/usr/bin/env bash
# Run with `./tools/run_all.sh`

set -e  # Exit if anything fails

ROOT_PATH=$(dirname $(dirname "$(readlink -f "$0")"))  # Root directory path

${ROOT_PATH}/tools/run_formatting.sh

${ROOT_PATH}/tools/run_linters.sh
