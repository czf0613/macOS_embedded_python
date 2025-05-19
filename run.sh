#!/bin/bash
set -e

cd "$(dirname "$0")"
export PYTHONHOME="$(pwd)"
export PYTHONPATH="$(pwd)/lib/site-packages"

./python "$@"