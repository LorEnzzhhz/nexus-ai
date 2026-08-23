#!/data/data/com.termux/files/usr/bin/bash
# Nexus AI - Termux installer
set -e

echo ""
echo "  ⚡ NEXUS AI INSTALLER"
echo "  ─────────────────────"
echo ""

echo "[1/4] Installing packages..."
apt update -y 2>/dev/null || pkg update -y 2>/dev/null || true
apt install -y python 2>/dev/null || pkg install -y python 2>/dev/null || true

echo "[2/4] Installing Python packages..."
pip install --upgrade pip -q 2>/dev/null || pip3 install --upgrade pip -q 2>/dev/null || true

for PKG in fastapi uvicorn httpx beautifulsoup4 aiofiles python-dotenv; do
    echo "  → $PKG"
    pip install "$PKG" -q 2>&1 | tail -1
done

echo "[3/4] Creating workspace..."
mkdir -p workspace data

if [ ! -f .env ]; then
cat > .env << 'ENVEOF'
OPENROUTER_API_KEY=
NVIDIA_API_KEY=
OPENCODE_ZEN_API_KEY=
OPENCODE_ZEN_BASE_URL=https://opencode.ai/zen/v1
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
HOST=0.0.0.0
PORT=8000
WORKSPACE_DIR=./workspace
MAX_ITERATIONS=15
MAX_TOKENS=4096
TEMPERATURE=0.7
ENVEOF
fi

echo "[4/4] Configuring API keys..."
echo ""
read -p "  OpenRouter key (Enter to skip): " ORK
[ -n "$ORK" ] && sed -i "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=${ORK}|" .env

read -p "  NVIDIA key (Enter to skip): " NVK
[ -n "$NVK" ] && sed -i "s|NVIDIA_API_KEY=.*|NVIDIA_API_KEY=${NVK}|" .env

read -p "  OpenCode Zen key (Enter to skip): " OCZ
[ -n "$OCZ" ] && sed -i "s|OPENCODE_ZEN_API_KEY=.*|OPENCODE_ZEN_API_KEY=${OCZ}|" .env

chmod +x start.sh 2>/dev/null || true

echo ""
echo "  ✅ Setup complete!"
echo ""
echo "  Type this to start:"
echo "    ./start.sh"
echo ""
