#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing Smart App Installer..."

# Executables
sudo install -Dm755 "${SCRIPT_DIR}/bin/smart-install" /usr/local/bin/smart-install
sudo ln -sf /usr/local/bin/smart-install /usr/local/bin/app-install

# Desktop Entry & Icon
sudo install -Dm644 "${SCRIPT_DIR}/data/smart-install.desktop" /usr/local/share/applications/smart-install.desktop
sudo install -Dm644 "${SCRIPT_DIR}/data/icons/smart-install.svg" /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg

# Shell Completions
if [ -d "/usr/share/bash-completion/completions" ]; then
    sudo install -Dm644 "${SCRIPT_DIR}/completions/smart-install.bash" /usr/share/bash-completion/completions/smart-install
fi
if [ -d "/usr/share/zsh/site-functions" ]; then
    sudo install -Dm644 "${SCRIPT_DIR}/completions/_smart-install.zsh" /usr/share/zsh/site-functions/_smart-install
fi

# Update system databases
sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true

echo "==> Smart App Installer (v1.0.0) installed successfully!"
echo "    Run 'smart-install <query>' in your terminal or search 'Smart App Installer' in your app menu."
