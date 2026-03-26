#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install python3-venv

python3.12 -m venv env
source env/bin/activate
pip install -r requirements.txt