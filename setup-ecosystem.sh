#!/usr/bin/env bash
set -e

echo "================================================================="
echo "  Arch Linux Unified Application Ecosystem Auto-Configuration   "
echo "================================================================="

# 1. archlinuxcn Repository Setup
echo "==> [1/4] Configuring archlinuxcn repository..."
if ! grep -q "\[archlinuxcn\]" /etc/pacman.conf; then
    echo -e "\n[archlinuxcn]\nInclude = /etc/pacman.d/archlinuxcn-mirrorlist" | sudo tee -a /etc/pacman.conf
fi

sudo pacman-key --recv-keys farseerfc@archlinux.org || sudo pacman-key --recv-key 4AB8310E || true
sudo pacman-key --lsign-key farseerfc@archlinux.org || sudo pacman-key --lsign-key 4AB8310E || true
sudo pacman -Sy --noconfirm archlinuxcn-keyring archlinuxcn-mirrorlist-git

# 2. Flatpak + Flathub + Desktop UI Setup
echo "==> [2/4] Configuring Flatpak, Flathub & Qt6 dependencies..."
sudo pacman -S --needed --noconfirm flatpak xdg-desktop-portal xdg-desktop-portal-kde python-pyqt6 pacman-contrib
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# 3. AppImage & FUSE Runtime
echo "==> [3/4] Ensuring AppImage FUSE compatibility..."
sudo pacman -S --needed --noconfirm fuse2 fuse3 libappimage

# 4. GUI Stores (Bauh, Pamac, Gear Lever)
echo "==> [4/4] Installing GUI Managers..."
sudo pacman -S --needed --noconfirm pamac-aur
yay -S --needed --noconfirm bauh gearlever || true

echo "==> Ecosystem setup completed successfully!"
