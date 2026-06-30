#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"
export BASE_PATH="${BASE_PATH:-/predict}"
export LOG_DIR="${LOG_DIR:-logs}"

python3 app.py
