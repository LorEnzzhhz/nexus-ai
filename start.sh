#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")"

# Load env
if [ -f .env ]; then
    set -a
    source <(grep -v '^#' .env | grep -v '^$')
    set +a
fi

PORT="${PORT:-8000}"
LOCAL_IP=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
LOCAL_IP=${LOCAL_IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}

clear
echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       ⚡ N E X U S   A I          ║"
echo "  ╠══════════════════════════════════╣"
echo "  ║                                  ║"
echo "  ║  Open in browser:                ║"
echo "  ║  → http://localhost:${PORT}         ║"
if [ -n "$LOCAL_IP" ]; then
printf  "  ║  → http://%s\n" "${LOCAL_IP}:${PORT}"
fi
echo "  ║                                  ║"
echo "  ║  Press Ctrl+C to stop            ║"
echo "  ╚══════════════════════════════════╝"
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
