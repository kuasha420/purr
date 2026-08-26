#!/usr/bin/env bash
set -e

echo "==> Installing Smart App Installer..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo install -Dm755 "${SCRIPT_DIR}/bin/smart-install" /usr/local/bin/smart-install
sudo ln -sf /usr/local/bin/smart-install /usr/local/bin/app-install
sudo install -Dm644 "${SCRIPT_DIR}/data/smart-install.desktop" /usr/local/share/applications/smart-install.desktop
sudo update-desktop-database /usr/local/share/applications || true

echo "==> Smart App Installer installed successfully!"
echo "    Run 'smart-install <app-name>' in your terminal or search in your app menu."
