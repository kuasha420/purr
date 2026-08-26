# Maintainer: PSL <psl@local>
pkgname=smart-install
pkgver=1.0.0
pkgrel=1
pkgdesc="Smart Multi-Source Priority Application Installer and Discovery Engine for Arch Linux"
arch=('any')
url="https://github.com/psl/smart-install"
license=('MIT')
depends=('python' 'pacman' 'yay' 'flatpak' 'fuse2' 'fuse3')
optdepends=(
    'bauh: Universal multi-format GUI manager'
    'pamac-aur: Modern AppStream software center'
    'gearlever: Standalone AppImage desktop integration'
    'konsole: Default terminal launcher'
)
source=("bin/smart-install" "data/smart-install.desktop")
sha256sums=('SKIP' 'SKIP')

package() {
    install -Dm755 "${srcdir}/bin/smart-install" "${pkgdir}/usr/bin/smart-install"
    ln -sf /usr/bin/smart-install "${pkgdir}/usr/bin/app-install"
    install -Dm644 "${srcdir}/data/smart-install.desktop" "${pkgdir}/usr/share/applications/smart-install.desktop"
}
