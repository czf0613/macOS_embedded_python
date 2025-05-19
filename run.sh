#!/bin/bash
set -e

BASE_DIR="$(dirname "$0")"
export PYTHONHOME="$BASE_DIR"
export PYTHONPATH="$BASE_DIR/lib/site-packages"

"$BASE_DIR/python" "$@"