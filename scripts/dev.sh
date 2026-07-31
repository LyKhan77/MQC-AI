#!/usr/bin/env bash
#
# MQC-AI — run backend (qc_server) and frontend (qc_frontend) together (Linux).
# Logs are combined into this terminal; every line is prefixed with a coloured
# [BE] or [FE] tag so the two streams stay distinguishable. Ctrl+C stops both.
#
# Usage:   bash scripts/dev.sh
# Env:     BE_PORT=8787   FE_PORT=5757   MQC_TLS_KEY=... MQC_TLS_CERT=...
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BE_DIR="$ROOT/qc_server"
FE_DIR="$ROOT/qc_frontend"
BE_PORT="${BE_PORT:-8787}"
FE_PORT="${FE_PORT:-5757}"
TLS_KEY="${MQC_TLS_KEY:-$FE_DIR/.certs/server-key.pem}"
TLS_CERT="${MQC_TLS_CERT:-$FE_DIR/.certs/server-cert.pem}"

if [[ -f "$TLS_KEY" && -f "$TLS_CERT" ]]; then
  export MQC_TLS_KEY="$TLS_KEY"
  export MQC_TLS_CERT="$TLS_CERT"
  FE_SCHEME="https"
else
  unset MQC_TLS_KEY MQC_TLS_CERT
  FE_SCHEME="http"
fi

C_BE='\033[1;36m'   # cyan
C_FE='\033[1;35m'   # magenta
C_RST='\033[0m'

# Prefix every line of stdin with a coloured [TAG].
prefix() {
  local tag="$1" color="$2"
  while IFS= read -r line; do
    printf "%b[%s]%b %s\n" "$color" "$tag" "$C_RST" "$line"
  done
}

# Kill the whole process group (both servers + their children) on exit/Ctrl+C.
cleanup() {
  trap - INT TERM EXIT
  echo ""
  echo ">>> stopping backend + frontend ..."
  kill 0 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Pre-flight checks.
if [ ! -x "$BE_DIR/.venv/bin/python" ]; then
  echo "ERROR: backend venv missing. Run 'bash scripts/setup.sh' first." >&2
  exit 1
fi
if [ ! -d "$FE_DIR/node_modules" ]; then
  echo "ERROR: frontend deps missing. Run 'bash scripts/setup.sh' first." >&2
  exit 1
fi

echo "============================================================"
echo " MQC-AI dev"
echo "   backend  [BE] -> http://0.0.0.0:$BE_PORT  (docs: /docs)"
echo "   frontend [FE] -> $FE_SCHEME://0.0.0.0:$FE_PORT"
echo "   Ctrl+C to stop both."
echo "============================================================"

# Backend (unbuffered so logs stream live through the pipe).
(
  cd "$BE_DIR"
  PYTHONUNBUFFERED=1 .venv/bin/python -m uvicorn app.main:app \
    --host 0.0.0.0 --port "$BE_PORT" 2>&1 | prefix "BE" "$C_BE"
) &

# Frontend.
(
  cd "$FE_DIR"
  npm run dev -- --host --port "$FE_PORT" 2>&1 | prefix "FE" "$C_FE"
) &

wait
