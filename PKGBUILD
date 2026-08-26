# Maintainer: PSL <psl@users.noreply.github.com>
pkgname=smart-install
pkgver=1.0.0
pkgrel=1
pkgdesc="Smart Multi-Source Priority Application Installer and Discovery Engine for Arch Linux"
arch=('any')
url="https://github.com/psl/smart-install"
license=('MIT')
depends=('python' 'pacman' 'yay' 'flatpak' 'fuse2' 'fuse3')
optdepends=(
    'libnotify: Desktop notification support upon installation'
    'bauh: Universal multi-format GUI package manager'
    'pamac-aur: Modern AppStream graphical software center'
    'gearlever: Standalone AppImage desktop integration'
    'konsole: Default terminal launcher'
)
source=(
    "bin/smart-install"
    "data/smart-install.desktop"
    "data/icons/smart-install.svg"
    "completions/smart-install.bash"
    "completions/_smart-install.zsh"
)
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
    # Binaries
    install -Dm755 "${srcdir}/bin/smart-install" "${pkgdir}/usr/bin/smart-install"
    ln -sf /usr/bin/smart-install "${pkgdir}/usr/bin/app-install"

    # Desktop & Icon
    install -Dm644 "${srcdir}/data/smart-install.desktop" "${pkgdir}/usr/share/applications/smart-install.desktop"
    install -Dm644 "${srcdir}/data/icons/smart-install.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/smart-install.svg"

    # Shell Completions
    install -Dm644 "${srcdir}/completions/smart-install.bash" "${pkgdir}/usr/share/bash-completion/completions/smart-install"
    install -Dm644 "${srcdir}/completions/_smart-install.zsh" "${pkgdir}/usr/share/zsh/site-functions/_smart-install"
}
