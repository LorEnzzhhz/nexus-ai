#!/data/data/com.termux/files/usr/bin/bash
# Nexus AI launcher for Termux: starts the backend (if needed) and opens the app.
set -e

APP_DIR="${NEXUS_DIR:-$HOME/nexus-ai}"
URL="http://localhost:${PORT:-8000}"

cd "$APP_DIR"

if ! curl -fsS "$URL/health" >/dev/null 2>&1; then
    echo "[*] Starting Nexus AI backend..."
    nohup ./start.sh >/dev/null 2>&1 &
    for i in $(seq 1 30); do
        curl -fsS "$URL/health" >/dev/null 2>&1 && break
        sleep 1
    done
fi

echo "[*] Opening $URL"
termux-open-url "$URL" 2>/dev/null || am start -a android.intent.action.VIEW -d "$URL" 2>/dev/null || echo "Open $URL in your browser"
