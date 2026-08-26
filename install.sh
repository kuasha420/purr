#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Clean up legacy residual files if any
sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg /usr/share/bash-completion/completions/smart-install /usr/share/zsh/site-functions/_smart-install

if [ "$1" == "--dev" ] || [ "$1" == "-d" ]; then
    echo "==> 🐾 Installing Purr in LIVE Development Mode..."
    sudo rm -f /usr/local/bin/purr /usr/local/bin/tuki /usr/local/bin/purr-install /usr/local/bin/purr-universal-app-engine /usr/local/bin/smart-install /usr/local/bin/app-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/tuki
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr-universal-app-engine
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/smart-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/app-install

    sudo install -Dm644 "${SCRIPT_DIR}/data/purr.desktop" /usr/local/share/applications/purr.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/icons/purr.svg" /usr/local/share/icons/hicolor/scalable/apps/purr.svg

    if [ -d "/usr/share/bash-completion/completions" ]; then
        sudo ln -sf "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/purr
    fi
    if [ -d "/usr/share/zsh/site-functions" ]; then
        sudo ln -sf "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_purr
    fi
    echo "==> 🐾 Live Development Mode Active! Edits to ${SCRIPT_DIR}/bin/purr are instantly live."
else
    echo "==> 🐾 Installing Purr (Production Copy)..."
    sudo install -Dm755 "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/tuki
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/purr-install
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/purr-universal-app-engine
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/smart-install
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/app-install

    sudo install -Dm644 "${SCRIPT_DIR}/data/purr.desktop" /usr/local/share/applications/purr.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/icons/purr.svg" /usr/local/share/icons/hicolor/scalable/apps/purr.svg

    if [ -d "/usr/share/bash-completion/completions" ]; then
        sudo install -Dm644 "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/purr
    fi
    if [ -d "/usr/share/zsh/site-functions" ]; then
        sudo install -Dm644 "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_purr
    fi
    echo "==> 🐾 Purr (v1.0.0 — Project Tuki) installed successfully!"
fi

sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true
