#!/bin/bash
# RVN Revenue - one-click start script (Linux)
set -e

cd "$(dirname "$0")/.."
REPO=$(pwd)
UV="/home/user1/.local/bin/uv"

echo "=== RVN Revenue - Start Services ==="

# Clean up old processes
echo "[0/2] Cleaning up existing services on ports 8765, 3000..."
fuser -k 8765/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 2

echo "[1/2] Starting backend (port 8765)..."
rm -f /tmp/rvn_backend.log
nohup "$UV" run python demo_web.py > /tmp/rvn_backend.log 2>&1 &
sleep 8

if grep -q "Demo server started" /tmp/rvn_backend.log 2>/dev/null; then
    echo "  OK - Backend running"
else
    echo "  WARN - Backend may not have started. Check: tail -20 /tmp/rvn_backend.log"
fi

echo "[2/2] Starting frontend (port 3000)..."
cd "$REPO/frontend"
rm -f /tmp/rvn_frontend.log
nohup env PYTHON_API_BASE=http://127.0.0.1:8765 npm run dev -- --hostname 0.0.0.0 --port 3000 > /tmp/rvn_frontend.log 2>&1 &
sleep 8

if grep -q "Ready in" /tmp/rvn_frontend.log 2>/dev/null; then
    echo "  OK - Frontend running"
else
    echo "  WARN - Frontend may not have started. Check: tail -20 /tmp/rvn_frontend.log"
fi

echo ""
echo "=== Status ==="
ss -tlnp | grep -E "8765|3000"
echo ""
echo "Desktop UI: http://10.8.35.35:3000"
