#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

APP_DIR="$HOME/nexus-ai"
REPO="https://github.com/LorEnzzhhz/nexus-ai.git"

clear
echo ""
echo "  ⚡ NEXUS AI INSTALLER"
echo "  ────────────────────"

wait_for_package_manager() {
    waited=0
    while pgrep -x apt >/dev/null 2>&1 || pgrep -x apt-get >/dev/null 2>&1 || pgrep -x dpkg >/dev/null 2>&1; do
        if (( waited == 0 )); then
            echo "[*] Waiting up to 2 minutes for Termux package manager..."
        fi
        sleep 5
        waited=$((waited + 5))
        if (( waited >= 120 )); then
            pgrep -ax apt || true
            pgrep -ax apt-get || true
            pgrep -ax dpkg || true
            echo "[!] Close every other Termux session, force-stop Termux, reopen it, then retry." >&2
            exit 1
        fi
    done
}

repair_package_manager() {
    wait_for_package_manager
    rm -f \
        "$PREFIX/var/lib/dpkg/lock-frontend" \
        "$PREFIX/var/lib/dpkg/lock" \
        "$PREFIX/var/lib/apt/lists/lock" \
        "$PREFIX/var/cache/apt/archives/lock"
    dpkg --configure -a
}

install_package() {
    local package="$1"
    if ! command -v "$package" >/dev/null 2>&1; then
        repair_package_manager
        pkg install -y "$package"
    fi
}

install_package curl
install_package git

if ! command -v python3 >/dev/null 2>&1; then
    repair_package_manager
    pkg install -y python
fi
if ! python3 -m pip --version >/dev/null 2>&1; then
    repair_package_manager
    pkg install -y python-pip
fi

umask 077
saved_env=""
if [[ -d "$APP_DIR" && ! -d "$APP_DIR/.git" ]]; then
    backup="${APP_DIR}-old-$(date +%s)"
    saved_env="$backup"
    echo "[*] Backing up old installation to $backup"
    mkdir -p "$backup"
    [[ -f "$APP_DIR/.env" ]] && cp "$APP_DIR/.env" "$backup/.env"
    [[ -d "$APP_DIR/workspace" ]] && cp -a "$APP_DIR/workspace" "$backup/workspace"
    rm -rf "$APP_DIR"
fi

if [[ -d "$APP_DIR/.git" ]]; then
    echo "[*] Updating Nexus AI..."
    git -C "$APP_DIR" fetch --depth=1 origin main
    git -C "$APP_DIR" reset --hard origin/main
else
    echo "[*] Downloading Nexus AI..."
    git clone --depth=1 "$REPO" "$APP_DIR"
fi

if [[ -n "${saved_env:-}" ]]; then
    [[ -f "$saved_env/.env" ]] && cp "$saved_env/.env" "$APP_DIR/.env"
    if [[ -d "$saved_env/workspace" ]]; then
        mkdir -p "$APP_DIR/workspace"
        cp -a "$saved_env/workspace/." "$APP_DIR/workspace/"
    fi
fi

cd "$APP_DIR"
[[ -f .env ]] || cp .env.example .env

for variable in OPENROUTER_API_KEY NVIDIA_API_KEY OPENCODE_ZEN_API_KEY OPENCODE_ZEN_BASE_URL; do
    if [[ -n "${!variable:-}" ]]; then
        export "__NEXUS_SET_${variable}"="${!variable}"
        python3 - "$variable" <<'PY'
import pathlib
import re
import os
import sys
path = pathlib.Path(".env")
name = sys.argv[1]
value = os.environ[f"__NEXUS_SET_{name}"]
lines = path.read_text().splitlines()
pattern = re.compile(rf"^{re.escape(name)}=")
replacement = f"{name}={value}"
if any(pattern.match(line) for line in lines):
    lines = [replacement if pattern.match(line) else line for line in lines]
else:
    lines.append(replacement)
path.write_text("\n".join(lines) + "\n")
PY
    fi
done

echo "[*] Installing Python packages..."
python3 -m pip install --upgrade --break-system-packages -r requirements-termux.txt

chmod +x start.sh
if [ -d "$PREFIX/bin" ]; then
    cp nexus-launch.sh "$PREFIX/bin/nexus"
    chmod +x "$PREFIX/bin/nexus"
    echo "[*] Created 'nexus' launcher command."
fi
echo "[*] Installation complete. Starting Nexus AI..."
exec ./start.sh
