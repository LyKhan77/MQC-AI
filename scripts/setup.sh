#!/usr/bin/env bash
#
# MQC-AI — one-shot environment setup (Linux).
# Creates the backend Python venv, installs backend + frontend deps,
# and runs the backend test suite as a sanity check.
#
# Usage:   bash scripts/setup.sh
# Env:     PYTHON=python3.11   (override interpreter)
#          SKIP_TESTS=1        (skip the pytest sanity check)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BE_DIR="$ROOT/qc_server"
FE_DIR="$ROOT/qc_frontend"
PYTHON="${PYTHON:-python3}"

echo "============================================================"
echo " MQC-AI setup"
echo " backend : $BE_DIR"
echo " frontend: $FE_DIR"
echo " python  : $($PYTHON --version 2>&1)"
echo "============================================================"

echo ""
echo ">>> [1/3] Backend virtualenv + dependencies"
cd "$BE_DIR"
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
  echo "    created .venv"
else
  echo "    .venv already exists — reusing"
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if [ "${SKIP_TESTS:-0}" != "1" ]; then
  echo ""
  echo ">>> [2/3] Backend test suite (sanity check)"
  .venv/bin/python -m pytest -q
else
  echo ""
  echo ">>> [2/3] Backend tests skipped (SKIP_TESTS=1)"
fi

echo ""
echo ">>> [3/3] Frontend dependencies"
cd "$FE_DIR"
npm install

echo ""
echo "============================================================"
echo " Setup complete. Start both servers with:"
echo "     bash scripts/dev.sh"
echo "============================================================"
