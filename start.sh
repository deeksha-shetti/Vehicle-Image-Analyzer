#!/bin/bash
set -e

echo "=========================================="
echo " Starting Unified Vehicle Analyzer Stack"
echo "=========================================="

# Start Python Worker in background
echo "[Worker] Starting Python OCR & Quality Analysis Worker..."
cd /app/worker
python src/main.py &
WORKER_PID=$!

# Start Node.js Express API & Static Frontend in background
echo "[API] Starting Express API Server on port ${PORT:-3000}..."
cd /app/api
node src/index.js &
API_PID=$!

# Trap shutdown signals
terminate() {
  echo "[Shutdown] Stopping Worker ($WORKER_PID) and API ($API_PID)..."
  kill -TERM "$WORKER_PID" "$API_PID" 2>/dev/null
  wait "$WORKER_PID" "$API_PID" 2>/dev/null
  exit 0
}

trap terminate SIGINT SIGTERM

# Wait for background processes
wait -n $WORKER_PID $API_PID
