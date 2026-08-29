#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Clean up legacy residual files if any
sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg /usr/share/bash-completion/completions/smart-install /usr/share/zsh/site-functions/_smart-install

DEV_MODE=false
OPT_ALL=false
OPT_FAVORITE=false
OPT_PIN=false
OPT_TRAY=false
OPT_AUTOSTART=false

for arg in "$@"; do
    case "$arg" in
        --dev|-d) DEV_MODE=true ;;
        --all|-a) OPT_ALL=true ;;
        --favorite) OPT_FAVORITE=true ;;
        --pin) OPT_PIN=true ;;
        --tray) OPT_TRAY=true ;;
        --autostart) OPT_AUTOSTART=true ;;
    esac
done

# Check optional Python GUI dependencies for Tray & Icon generation
PYTHON_BIN=$(command -v /usr/bin/python3 || command -v python3 || echo "python3")
if ! "$PYTHON_BIN" -c "import PyQt6" 2>/dev/null; then
    if command -v pacman >/dev/null 2>&1; then
        echo "==> [i] Installing recommended Qt6 Python bindings (python-pyqt6)..."
        sudo pacman -S --needed --noconfirm python-pyqt6 2>/dev/null || echo "==> [!] Note: python-pyqt6 could not be auto-installed. You can install it manually: sudo pacman -S python-pyqt6"
    fi
fi

if [ "$DEV_MODE" = true ]; then
    echo "==> 🐾 Installing Purr in LIVE Development Mode..."
    sudo rm -f /usr/local/bin/purr /usr/local/bin/purr-tray /usr/local/bin/purr-integrate /usr/local/bin/tuki /usr/local/bin/purr-install /usr/local/bin/purr-universal-app-engine /usr/local/bin/smart-install /usr/local/bin/app-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr
    sudo ln -sf "${SCRIPT_DIR}/bin/purr-tray" /usr/local/bin/purr-tray
    sudo ln -sf "${SCRIPT_DIR}/bin/purr-integrate" /usr/local/bin/purr-integrate
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/tuki
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr-universal-app-engine
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/smart-install
    sudo ln -sf "${SCRIPT_DIR}/bin/purr" /usr/local/bin/app-install

    sudo install -Dm644 "${SCRIPT_DIR}/data/purr.desktop" /usr/local/share/applications/purr.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/purr-tray.desktop" /usr/local/share/applications/purr-tray.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/icons/purr.svg" /usr/local/share/icons/hicolor/scalable/apps/purr.svg

    if [ -d "/usr/share/bash-completion/completions" ]; then
        sudo ln -sf "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/purr
        sudo ln -sf "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/tuki
    fi
    if [ -d "/usr/share/zsh/site-functions" ]; then
        sudo ln -sf "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_purr
        sudo ln -sf "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_tuki
    fi

    # Install Manpages
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr.1" /usr/local/share/man/man1/purr.1
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr-tray.1" /usr/local/share/man/man1/purr-tray.1
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr-integrate.1" /usr/local/share/man/man1/purr-integrate.1
    sudo ln -sf /usr/local/share/man/man1/purr.1 /usr/local/share/man/man1/tuki.1

    # Install Recipes (Live symlink)
    sudo mkdir -p /usr/local/share/purr
    sudo ln -sfn "${SCRIPT_DIR}/recipes" /usr/local/share/purr/recipes

    echo "==> 🐾 Live Development Mode Active! Edits to ${SCRIPT_DIR}/bin/ and ${SCRIPT_DIR}/recipes/ are instantly live."
else
    echo "==> 🐾 Installing Purr (Production Copy)..."
    sudo install -Dm755 "${SCRIPT_DIR}/bin/purr" /usr/local/bin/purr
    sudo install -Dm755 "${SCRIPT_DIR}/bin/purr-tray" /usr/local/bin/purr-tray
    sudo install -Dm755 "${SCRIPT_DIR}/bin/purr-integrate" /usr/local/bin/purr-integrate
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/tuki
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/purr-install
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/purr-universal-app-engine
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/smart-install
    sudo ln -sf /usr/local/bin/purr /usr/local/bin/app-install

    # Install Recipes (Copy)
    sudo mkdir -p /usr/local/share/purr
    sudo rm -rf /usr/local/share/purr/recipes
    sudo cp -r "${SCRIPT_DIR}/recipes" /usr/local/share/purr/recipes

    sudo install -Dm644 "${SCRIPT_DIR}/data/purr.desktop" /usr/local/share/applications/purr.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/purr-tray.desktop" /usr/local/share/applications/purr-tray.desktop
    sudo install -Dm644 "${SCRIPT_DIR}/data/icons/purr.svg" /usr/local/share/icons/hicolor/scalable/apps/purr.svg

    if [ -d "/usr/share/bash-completion/completions" ]; then
        sudo install -Dm644 "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/purr
        sudo install -Dm644 "${SCRIPT_DIR}/completions/purr.bash" /usr/share/bash-completion/completions/tuki
    fi
    if [ -d "/usr/share/zsh/site-functions" ]; then
        sudo install -Dm644 "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_purr
        sudo install -Dm644 "${SCRIPT_DIR}/completions/_purr.zsh" /usr/share/zsh/site-functions/_tuki
    fi

    # Install Manpages
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr.1" /usr/local/share/man/man1/purr.1
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr-tray.1" /usr/local/share/man/man1/purr-tray.1
    sudo install -Dm644 "${SCRIPT_DIR}/man/man1/purr-integrate.1" /usr/local/share/man/man1/purr-integrate.1
    sudo ln -sf /usr/local/share/man/man1/purr.1 /usr/local/share/man/man1/tuki.1

    echo "==> 🐾 Purr (v1.0.0 — Project Tuki) installed successfully!"
fi

sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true

# Apply Desktop Integrations if requested
if [ "$OPT_ALL" = true ]; then
    "${SCRIPT_DIR}/bin/purr-integrate" --all
else
    if [ "$OPT_FAVORITE" = true ]; then "${SCRIPT_DIR}/bin/purr-integrate" --favorite; fi
    if [ "$OPT_PIN" = true ]; then "${SCRIPT_DIR}/bin/purr-integrate" --pin; fi
    if [ "$OPT_AUTOSTART" = true ]; then "${SCRIPT_DIR}/bin/purr-integrate" --autostart; fi
    if [ "$OPT_TRAY" = true ]; then "${SCRIPT_DIR}/bin/purr-integrate" --tray; fi
fi
