#!/usr/bin/env bash
set -e

echo "==> 🐾 Uninstalling Purr..."

sudo rm -f /usr/local/bin/purr
sudo rm -f /usr/local/bin/tuki
sudo rm -f /usr/local/bin/purr-install
sudo rm -f /usr/local/bin/smart-install
sudo rm -f /usr/local/bin/app-install
sudo rm -f /usr/local/share/applications/purr.desktop
sudo rm -f /usr/local/share/applications/smart-install.desktop
sudo rm -f /usr/local/share/icons/hicolor/scalable/apps/purr.svg
sudo rm -f /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg
sudo rm -f /usr/share/bash-completion/completions/purr
sudo rm -f /usr/share/bash-completion/completions/smart-install
sudo rm -f /usr/share/zsh/site-functions/_purr
sudo rm -f /usr/share/zsh/site-functions/_smart-install

sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true

echo "==> 🐾 Purr has been completely uninstalled."
