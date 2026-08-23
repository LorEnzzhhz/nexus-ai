#!/data/data/com.termux/files/usr/bin/bash
set -e

clear
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║      ⚡ NEXUS AI — INSTALLER          ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

echo "[1/5] Updating Termux packages..."
pkg update -y && pkg upgrade -y 2>/dev/null | tail -1

echo "[2/5] Installing system dependencies..."
pkg install -y python git libxml2 libxslt openssl 2>/dev/null | tail -1

echo "[3/5] Installing Python packages..."
pip install --upgrade pip setuptools wheel -q
pip install fastapi uvicorn httpx beautifulsoup4 aiofiles python-dotenv lxml -q

echo "[4/5] Setting up workspace..."
mkdir -p workspace data

if [ ! -f .env ]; then
    cp .env.example .env
fi

echo "[5/5] Configuring..."
echo ""
echo "  ── API Keys ──"
echo ""

# Prompt for keys
read -p "  OpenRouter key (or Enter to skip): " OR_KEY
if [ -n "$OR_KEY" ]; then
    sed -i "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=${OR_KEY}|" .env
    echo "  ✓ OpenRouter set"
else
    echo "  ○ Skipped"
fi

read -p "  NVIDIA NIM key (or Enter to skip): " NV_KEY
if [ -n "$NV_KEY" ]; then
    sed -i "s|NVIDIA_API_KEY=.*|NVIDIA_API_KEY=${NV_KEY}|" .env
    echo "  ✓ NVIDIA set"
else
    echo "  ○ Skipped"
fi

chmod +x start.sh

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║           ✅ READY!                   ║"
echo "  ╠══════════════════════════════════════╣"
echo "  ║                                      ║"
echo "  ║  Start now? Type:                    ║"
echo "  ║    ./start.sh                        ║"
echo "  ║                                      ║"
echo "  ║  Then open in browser:               ║"
echo "  ║    http://localhost:8000             ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
