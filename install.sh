#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 🐾 Installing Purr (Project Tuki)..."

# Binaries & Symlinks
sudo install -Dm755 "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr
sudo ln -sf /usr/local/bin/purr /usr/local/bin/tuki
sudo ln -sf /usr/local/bin/purr /usr/local/bin/purr-install
sudo ln -sf /usr/local/bin/purr /usr/local/bin/smart-install
sudo ln -sf /usr/local/bin/purr /usr/local/bin/app-install

# Desktop Entry & Icon
sudo install -Dm644 "${SCRIPT_DIR}/data/purr.desktop" /usr/local/share/applications/purr.desktop
sudo install -Dm644 "${SCRIPT_DIR}/data/icons/purr.svg" /usr/local/share/icons/hicolor/scalable/apps/purr.svg

# Shell Completions
if [ -d "/usr/share/bash-completion/completions" ]; then
    sudo install -Dm644 "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/purr
fi
if [ -d "/usr/share/zsh/site-functions" ]; then
    sudo install -Dm644 "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_purr
fi

# Update system databases
sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true

echo "==> 🐾 Purr (v1.0.0 — Project Tuki) installed successfully!"
echo "    Run 'purr <query>' or 'tuki <query>' in your terminal or search 'Purr' in your app menu."
