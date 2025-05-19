#!/bin/bash
set -e
cd "$(dirname "$0")"

../../run.sh test_tk.py
echo "tkinter测试成功"

../../run.sh test_asyncio.py

../../run.sh test_ssl.py

../../run.sh test_sqlite.py