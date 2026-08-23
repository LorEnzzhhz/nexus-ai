#!/data/data/com.termux/files/usr/bin/bash
set -e

echo ""
echo "  ⚡ Nexus AI — Termux Setup"
echo "  ────────────────────────────"
echo ""

# Install system packages
echo "[*] Installing system packages..."
pkg update -y && pkg upgrade -y
pkg install -y python git libxml2 libxslt

# Upgrade pip
echo "[*] Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies (no C-extension extras)
echo "[*] Installing Python dependencies..."
pip install fastapi uvicorn httpx beautifulsoup4 aiofiles python-dotenv soupsieve lxml

# Copy env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[*] Created .env from template"
    echo "    → Edit .env and add your API keys"
fi

# Create workspace
mkdir -p workspace

chmod +x start-termux.sh

echo ""
echo "  ✅ Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. nano .env        ← add your API keys"
echo "  2. ./start-termux.sh"
echo ""
