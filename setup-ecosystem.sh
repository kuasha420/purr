#!/usr/bin/env bash
set -e

echo "================================================================="
echo "  Arch Linux Unified Application Ecosystem Auto-Configuration   "
echo "================================================================="

# 1. archlinuxcn Repository Setup
echo "==> [1/4] Configuring archlinuxcn repository..."

# Ensure keyring directory is initialized
if [ ! -d /etc/pacman.d/gnupg ]; then
    sudo pacman-key --init
    sudo pacman-key --populate archlinux
fi

# Ensure /etc/pacman.d/archlinuxcn-mirrorlist exists before pacman.conf includes it
if [ ! -f /etc/pacman.d/archlinuxcn-mirrorlist ]; then
    echo 'Server = https://repo.archlinuxcn.org/$arch' | sudo tee /etc/pacman.d/archlinuxcn-mirrorlist > /dev/null
fi

if ! grep -q "\[archlinuxcn\]" /etc/pacman.conf; then
    echo -e "\n[archlinuxcn]\nInclude = /etc/pacman.d/archlinuxcn-mirrorlist" | sudo tee -a /etc/pacman.conf
fi

# Bootstrap archlinuxcn-keyring if missing to resolve untrusted signature errors
if ! pacman -Qq archlinuxcn-keyring &>/dev/null; then
    sudo sed -i '/\[archlinuxcn\]/a SigLevel = Optional TrustAll' /etc/pacman.conf
    sudo pacman -Sy --needed --noconfirm --ask 4 --overwrite "*" archlinuxcn-keyring || true
    sudo pacman-key --populate archlinuxcn || true
    sudo sed -i '/SigLevel = Optional TrustAll/d' /etc/pacman.conf
fi

sudo pacman -Sy --needed --noconfirm --ask 4 --overwrite "*" archlinuxcn-keyring archlinuxcn-mirrorlist-git


# 2. Flatpak + Flathub + Desktop UI Setup
echo "==> [2/4] Configuring Flatpak, Flathub & Qt6 dependencies..."
sudo pacman -S --needed --noconfirm --ask 4 --overwrite "*" flatpak xdg-desktop-portal xdg-desktop-portal-kde python-pyqt6 pacman-contrib
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# 3. AppImage & FUSE Runtime
echo "==> [3/4] Ensuring AppImage FUSE compatibility..."
sudo pacman -S --needed --noconfirm --ask 4 --overwrite "*" fuse2 fuse3 libappimage

# 4. GUI Stores (Bauh, Pamac, Gear Lever)
echo "==> [4/4] Installing GUI Managers..."
sudo pacman -S --needed --noconfirm --ask 4 --overwrite "*" pamac-aur || true
yay -S --needed --noconfirm --answerclean All --answerdiff None --answeredit None --answerupgrade None --removemake --cleanafter --overwrite "*" bauh gearlever || true

echo "==> Ecosystem setup completed successfully!"

