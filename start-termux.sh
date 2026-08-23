#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")"

echo ""
echo "  ⚡ Nexus AI"
echo "  ────────────"
echo ""
echo "  Loading..."

# Load env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

PORT="${PORT:-8000}"

# Get local IP for LAN access
LOCAL_IP=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)

sleep 1
clear
echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║        ⚡ N E X U S   A I         ║"
echo "  ╠══════════════════════════════════╣"
echo "  ║                                  ║"
echo "  ║  Local:    http://localhost:${PORT}  ║"
if [ -n "$LOCAL_IP" ]; then
printf "  ║  Network:  http://%s\n" "$LOCAL_IP:${PORT}"
fi
echo "  ║                                  ║"
echo "  ║  Press Ctrl+C to stop            ║"
echo "  ╚══════════════════════════════════╝"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
