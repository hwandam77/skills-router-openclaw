#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
exec python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8091
