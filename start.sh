#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

PORT="${PORT:-8000}"
LOCAL_IP=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)

clear
echo ""
echo "  ╔══════════════════════════╗"
echo "  ║      ⚡ NEXUS AI          ║"
echo "  ╠══════════════════════════╣"
echo "  ║                          ║"
echo "  ║  http://localhost:${PORT}   ║"
[ -n "$LOCAL_IP" ] && echo "  http://${LOCAL_IP}:${PORT}"
echo "  ║                          ║"
echo "  ║  Ctrl+C to stop          ║"
echo "  ╚══════════════════════════╝"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
