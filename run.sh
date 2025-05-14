#!/bin/bash
set -e

cd "$(dirname "$0")"
export PYTHONHOME="$(pwd)"
export PYTHONPATH="$(pwd)/site-packages"

./Python "$@"