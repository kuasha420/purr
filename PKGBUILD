# Maintainer: Arafat Zahan <arafat@purrfecthq.com>
# Contributor: Purrfect Software Limited <team@purrfecthq.com>
pkgname=purr
pkgver=1.0.0
pkgrel=1
pkgdesc="Purr Universal App Engine — Smart Multi-Source Discovery & Priority Installer for Arch Linux & KDE Plasma (Project Tuki, CSP-IP)"
arch=('any')
url="https://github.com/kuasha420/purr"
license=('MIT')
provides=('purr' 'tuki' 'purr-universal-app-engine' 'smart-install' 'app-install')
conflicts=('smart-install')
depends=('python' 'pacman' 'yay' 'flatpak' 'fuse2' 'fuse3')
optdepends=(
    'libnotify: Desktop notification support upon installation'
    'bauh: Universal multi-format GUI package manager'
    'pamac-aur: Modern AppStream graphical software center'
    'gearlever: Standalone AppImage desktop integration'
    'konsole: Default terminal launcher'
)
source=(
    "bin/purr"
    "data/purr.desktop"
    "data/icons/purr.svg"
    "completions/purr.bash"
    "completions/_purr.zsh"
)
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
    # Binaries & Compatibility Symlinks
    install -Dm755 "${srcdir}/bin/purr" "${pkgdir}/usr/bin/purr"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/tuki"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/purr-install"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/purr-universal-app-engine"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/smart-install"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/app-install"

    # Desktop Entry & Icon
    install -Dm644 "${srcdir}/data/purr.desktop" "${pkgdir}/usr/share/applications/purr.desktop"
    install -Dm644 "${srcdir}/data/icons/purr.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/purr.svg"

    # Shell Completions
    install -Dm644 "${srcdir}/completions/purr.bash" "${pkgdir}/usr/share/bash-completion/completions/purr"
    install -Dm644 "${srcdir}/completions/_purr.zsh" "${pkgdir}/usr/share/zsh/site-functions/_purr"
}
