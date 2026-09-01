# Maintainer: Arafat Zahan <arafat@purrfecthq.com>
# Contributor: Purrfect Software Limited <team@purrfecthq.com>
pkgname=purr
pkgver=1.0.0
pkgrel=1
pkgdesc="Purr Universal App Engine — Smart Multi-Source Discovery & Priority Installer for Arch Linux & KDE Plasma (Project Tuki, CSP-IP)"
arch=('any')
url="https://github.com/kuasha420/purr"
license=('MIT')
provides=('purr' 'purr-tray' 'purr-integrate' 'tuki' 'purr-universal-app-engine' 'smart-install' 'app-install')
conflicts=('smart-install')
depends=('python' 'pacman' 'yay' 'flatpak' 'fuse2' 'fuse3' 'python-pyqt6')
optdepends=(
    'libnotify: Desktop notification support upon installation'
    'pacman-contrib: Fast checkupdates background update checker'
    'bauh: Universal multi-format GUI package manager'
    'pamac-aur: Modern AppStream graphical software center'
    'gearlever: Standalone AppImage desktop integration'
    'konsole: Default terminal launcher'
    'python-gbinder: Direct IPC integration with Android container HAL'
    'wl-clipboard: Seamless host-to-container clipboard synchronization on Wayland'
)
source=(
    "bin/purr"
    "bin/purr-tray"
    "bin/purr-integrate"
    "data/purr.desktop"
    "data/purr-tray.desktop"
    "data/icons/purr.svg"
    "completions/purr.bash"
    "completions/_purr.zsh"
    "man/man1/purr.1"
    "man/man1/purr-tray.1"
    "man/man1/purr-integrate.1"
    "recipes/__init__.py"
    "recipes/base.py"
    "recipes/manager.py"
    "recipes/waydroid_native/__init__.py"
    "recipes/waydroid_native/recipe.json"
    "recipes/waydroid_native/recipe.py"
    "recipes/waydroid_native/system_tuning.py"
    "recipes/waydroid_native/kwin_rules.py"
    "recipes/waydroid_native/fileshare.py"
    "recipes/waydroid_native/desktop_sync.py"
    "recipes/waydroid_native/window_memory.py"
    "recipes/waydroid_native/aurora_patcher.py"
    "recipes/waydroid_native/assets/Generic.kcm"
    "recipes/waydroid_native/assets/PurrClipHelper.apk"
    "recipes/waydroid_native/assets/PurrNullIME.apk"
    "recipes/waydroid_native/assets/GamepadTester.apk"
    "recipes/waydroid_native/assets/PurrWindowDecorOverlay.apk"
    "recipes/waydroid_native/assets/services.jar"
)
sha256sums=(
    'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP'
    'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP'
    'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP'
)

package() {
    # Binaries & Compatibility Symlinks
    install -Dm755 "${srcdir}/bin/purr" "${pkgdir}/usr/bin/purr"
    install -Dm755 "${srcdir}/bin/purr-tray" "${pkgdir}/usr/bin/purr-tray"
    install -Dm755 "${srcdir}/bin/purr-integrate" "${pkgdir}/usr/bin/purr-integrate"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/tuki"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/purr-install"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/purr-universal-app-engine"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/smart-install"
    ln -sf /usr/bin/purr "${pkgdir}/usr/bin/app-install"

    # Desktop Entries & Icon
    install -Dm644 "${srcdir}/data/purr.desktop" "${pkgdir}/usr/share/applications/purr.desktop"
    install -Dm644 "${srcdir}/data/purr-tray.desktop" "${pkgdir}/usr/share/applications/purr-tray.desktop"
    install -Dm644 "${srcdir}/data/icons/purr.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/purr.svg"

    # Shell Completions
    install -Dm644 "${srcdir}/completions/purr.bash" "${pkgdir}/usr/share/bash-completion/completions/purr"
    ln -sf /usr/share/bash-completion/completions/purr "${pkgdir}/usr/share/bash-completion/completions/tuki"
    install -Dm644 "${srcdir}/completions/_purr.zsh" "${pkgdir}/usr/share/zsh/site-functions/_purr"
    ln -sf /usr/share/zsh/site-functions/_purr "${pkgdir}/usr/share/zsh/site-functions/_tuki"

    # UNIX Manual Pages
    install -Dm644 "${srcdir}/man/man1/purr.1" "${pkgdir}/usr/share/man/man1/purr.1"
    install -Dm644 "${srcdir}/man/man1/purr-tray.1" "${pkgdir}/usr/share/man/man1/purr-tray.1"
    install -Dm644 "${srcdir}/man/man1/purr-integrate.1" "${pkgdir}/usr/share/man/man1/purr-integrate.1"
    ln -sf /usr/share/man/man1/purr.1 "${pkgdir}/usr/share/man/man1/tuki.1"

    # Purr Recipes Engine
    local _recipe_dir="${pkgdir}/usr/share/purr/recipes"
    install -Dm644 "${srcdir}/recipes/__init__.py" "${_recipe_dir}/__init__.py"
    install -Dm644 "${srcdir}/recipes/base.py" "${_recipe_dir}/base.py"
    install -Dm644 "${srcdir}/recipes/manager.py" "${_recipe_dir}/manager.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/__init__.py" "${_recipe_dir}/waydroid_native/__init__.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/recipe.json" "${_recipe_dir}/waydroid_native/recipe.json"
    install -Dm644 "${srcdir}/recipes/waydroid_native/recipe.py" "${_recipe_dir}/waydroid_native/recipe.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/system_tuning.py" "${_recipe_dir}/waydroid_native/system_tuning.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/kwin_rules.py" "${_recipe_dir}/waydroid_native/kwin_rules.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/fileshare.py" "${_recipe_dir}/waydroid_native/fileshare.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/desktop_sync.py" "${_recipe_dir}/waydroid_native/desktop_sync.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/window_memory.py" "${_recipe_dir}/waydroid_native/window_memory.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/aurora_patcher.py" "${_recipe_dir}/waydroid_native/aurora_patcher.py"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/Generic.kcm" "${_recipe_dir}/waydroid_native/assets/Generic.kcm"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/PurrClipHelper.apk" "${_recipe_dir}/waydroid_native/assets/PurrClipHelper.apk"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/PurrNullIME.apk" "${_recipe_dir}/waydroid_native/assets/PurrNullIME.apk"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/GamepadTester.apk" "${_recipe_dir}/waydroid_native/assets/GamepadTester.apk"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/PurrWindowDecorOverlay.apk" "${_recipe_dir}/waydroid_native/assets/PurrWindowDecorOverlay.apk"
    install -Dm644 "${srcdir}/recipes/waydroid_native/assets/services.jar" "${_recipe_dir}/waydroid_native/assets/services.jar"
}
