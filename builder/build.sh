#!/bin/bash
set -e
cd "$(dirname "$0")"

read -p "将会自动清除原有的文件，是否确定？按回车继续，按Ctrl+C取消"

rm -rf ../lib || true
rm -rf ../dylib || true
rm -f ../python || true

# 用macOS自带的python来运行这个构建脚本就可以了
/usr/bin/python3 main.py