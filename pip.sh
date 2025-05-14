#!/bin/bash
set -e

cd "$(dirname "$0")"
export PYTHONHOME="$(pwd)"
mkdir -p site-packages

./Python -m pip $1 --target "$(pwd)/site-packages" "${@:2}"