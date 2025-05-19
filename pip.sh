#!/bin/bash
set -e

cd "$(dirname "$0")"
export PYTHONHOME="$(pwd)"
mkdir -p lib/site-packages

./Python -m pip $1 --target "$(pwd)/lib/site-packages" "${@:2}"