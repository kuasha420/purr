# Changelog

All notable changes to `purr` will be documented in this file.

## [n.e.x.t] - YYYY-MM-DD (Purr Recipes & Android Native Subsystem)

### ✨ Features & Subsystem Architecture

* **🐾 Modular Recipe Engine (`purr recipe`)**:
  * Extensible, declarative framework for defining, distributing, and executing complex subsystem architectures.
  * Standardized lifecycle interface: `check_prerequisites`, `prune`, `provision`, `integrate_desktop`, `doctor`, and `teardown`.
  * Comprehensive CLI commands: `purr recipe list`, `info`, `apply`, `doctor`, `prune`, and `teardown`.

* **📱 Flagship `waydroid-native` Subsystem**:
  * **Turnkey Provisioning & Maintenance**: Complete field cleanup of legacy 2025 Waydroid containers, stale images, and abandoned desktop entries.
  * **Dynamic Hardware Probing**: Universal hardware detection engine configuring CPU architecture (AMD Ryzen, Intel Core, ARM) and GPU acceleration (`minigbm_gbm_mesa`) with `libndk` ARM translation.
  * **Multi-Window Freeform Mode**: Android applications run as native, floating, resizable desktop windows (`persist.waydroid.multi_windows=true`).
  * **Window Geometry & Position Memory**:
    * Dynamic window coordinate persistence across all resolutions and aspect ratios (`window_memory.py`).
    * Real-time position tracking via `purr-tray` with automatic geometry restoration on cold launch and Kickoff menu clicks.
    * Opt-in configurable state toggle in tray menu and `~/.config/purr/config.json`.
  * **Non-Destructive KDE Plasma 6 Integration**:
    * Custom KWin window rules for seamless decorations, smart window placement, and taskbar grouping without crashing `plasmashell`.
    * Native `.desktop` application launchers generated directly into KDE Kickoff Application Menu with high-resolution icons.
  * **Real-Time Bidirectional Clipboard Sharing**:
    * Native API 33 companion (`PurrClipHelper.apk`) installed in `/system/priv-app/` and container runtime to overcome Android 13 multi-window background focus restrictions.
    * Zero-CPU `wl-paste --watch` event bridge in `purr-tray` continuously streaming Linux host clipboard updates to Android in real time.
    * CLI clipboard injector (`purr apk paste [text]`) and tray menu action for instant text typing into active input fields.
  * **Desktop Keyboard & Touch Optimization**:
    * Physical NumPad direct character mapping in `Virtual.kcm` without requiring host NumLock state synchronization.
    * KeyCharacterMap desktop shortcuts for <kbd>Ctrl</kbd>+<kbd>V</kbd> (Paste), <kbd>Ctrl</kbd>+<kbd>C</kbd> (Copy), <kbd>Ctrl</kbd>+<kbd>A</kbd> (Select All), <kbd>Ctrl</kbd>+<kbd>X</kbd> (Cut), and <kbd>Ctrl</kbd>+<kbd>Z</kbd> (Undo).
    * `persist.waydroid.fake_touch=true` mapping for touch-and-hold gestures, text selection handles, and long-press context menus.
    * On-screen soft keyboards automatically suppressed when physical keyboards are attached.
  * **Audio & Storage Integration**:
    * Low-latency PipeWire Pulse audio routing and microphone integration.
    * Bidirectional media folder bind mounts (`~/Downloads`, `~/Pictures`, `~/Documents` $\leftrightarrow$ `/sdcard/`).
    * Google Play Protect Android ID device certification helper (`purr apk certify`).

* **⚡ Purr APK Management CLI (`purr apk`)**:
  * Direct terminal APK installation (`purr apk install /path/to/app.apk`).
  * Instant application launcher with geometry restoration (`purr apk launch <package>`).
  * Application listing (`purr apk list`), desktop launcher synchronization (`purr apk sync`), and container session control (`purr apk session start|stop|restart`).

* **🔔 Purr System Tray Indicator Refinements (`purr-tray`)**:
  * Fixed antialiased urgency badge icon rendering in Qt6.
  * Color-coded update urgency halos (Cyan $\rightarrow$ Amber $\rightarrow$ Crimson Coral) with network backoff recovery.
  * Android subsystem controls and quick application launchers accessible from tray context menu.

* **🔒 In-Lockstep Maintainability**:
  * Built-in CLI help, UNIX manual pages (`purr.1`), and Bash/Zsh shell completions updated in lockstep.
  * Clean installation (`install.sh`) and complete uninstaller (`uninstall.sh`) updated with recipe assets.
  * Packaging definitions (`PKGBUILD`, `.SRCINFO`) updated with `python-gbinder` and `wl-clipboard` optdepends.

## [1.0.0] - 2026-08-27 (Project Tuki Universal Edition)

### ✨ Features
* **🐾 Official Rebrand to Purr**: The universal app discovery engine, dedicated to Tuki (2019–2024).
* **Universal Discovery Engine**: Searches System (Pacman / archlinuxcn), AUR, Flatpak (Flathub), and AppImage simultaneously.
* **Strict Priority Hierarchy**: System (1) $\rightarrow$ AUR (2) $\rightarrow$ Flatpak (3) $\rightarrow$ AppImage (4) $\rightarrow$ Git (5).
* **Heuristic Query Expansion**: Multi-term parsing, canonical slugs, and brand-to-package alias dictionary.
* **AUR Popularity Weighting**: Community vote scaling ($\log_{10}(\text{Votes})$) prevents obscure packages from outranking popular ones.
* **Auxiliary Noise Filter**: Automatically detects and suppresses plugins, extensions, drivers, and language servers.
* **Zero-Touch Unattended Installation**: Silent flag automation for `yay`, `pacman`, and `flatpak`.
* **Persistent Session Loop**: Window stays open after install, offering instant `[l]` launch or further searches.
* **Universal System Upgrade Engine (`purr upgrade`)**: Multi-tiered unattended upgrades with automated conflict resolution, stale database lock recovery, keyring auto-synchronization, `--ask 4` package replacement, and `--overwrite "*"` conflict bypassing.
* **Automated Flatpak Runtime Pruning**: Auto-detects and purges unsupported, unreferenced, and End-of-Life (EOL) SDKs and runtimes (`flatpak uninstall --unused -y`).
* **Native KDE Plasma 6 Desktop Integration**: Non-destructive Task Manager pin/unpin via in-memory DBus scripts, Kickoff favorites injection, and XDG Autostart.
* **Qt6 StatusNotifierItem Tray Indicator (`purr-tray`)**: Background update monitor with color-coded urgency halos, network outage backoff retry, and an interactive GUI check frequency dialog.
* **Instant IPC Indicator Refresh**: Dual-channel IPC (`QFileSystemWatcher` trigger + `SIGUSR1`) forces the tray indicator to immediately refresh after any CLI upgrade or package installation.
* **Complete UNIX Manual Pages**: Manpages for `purr.1`, `purr-tray.1`, `purr-integrate.1`, and `tuki.1`.
* **Shell Completions**: Comprehensive Bash & Zsh auto-completions for `purr` and `tuki`.
* **Complete Uninstaller (`uninstall.sh`)**: 9-step clean teardown of all binaries, integrations, desktop files, icons, completions, manpages, and config caches.
