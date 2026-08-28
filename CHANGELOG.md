# Changelog

All notable changes to `purr` will be documented in this file.

## [1.1.0] - 2026-08-28 (Purr Recipes & Android Native Subsystem)

### ✨ Features
* **🐾 Modular Recipe Engine (`purr recipe`)**: Extensible framework for defining, distributing, and executing complex subsystem architectures with full lifecycle management (`list`, `info`, `apply`, `doctor`, `prune`, `teardown`).
* **📱 Turnkey Waydroid Native Ecosystem Recipe (`waydroid-native`)**:
  * Complete field work pruning of legacy 2025 Waydroid containers, images, and stale desktop launchers.
  * Hardware-aware auto-tuning with ARM translation (`libndk`) dynamically probing across AMD, Intel, ARM, Radeon, and Intel/NVIDIA Mesa graphics.
  * Multi-window freeform desktop mode with Android task-level window coordinate & dimension persistence (`recipes/waydroid_native/window_memory.py`).
  * Real-time window movement tracker in `purr-tray` with automatic position restoration across cold launches and Kickoff menu clicks.
  * **📋 Real-Time Bidirectional Clipboard Sharing**:
    * Created native SDK 33 companion `PurrClipHelper.apk` installed into `/system/priv-app/` and container runtime to bypass Android 13 multi-window background focus restrictions.
    * Integrated real-time `wl-paste --watch` event bridge inside `purr-tray` to push Linux host copy events directly into Android system clipboard in real time.
    * Added `purr apk paste [text]` CLI command and Purr Tray context menu action for direct text injection.
  * **⌨️ Desktop Keyboard & Touch Enhancements**:
    * Physical NumPad direct character mapping in `Virtual.kcm` without requiring host NumLock synchronization.
    * Desktop keyboard shortcut mappings in KeyCharacterMaps for <kbd>Ctrl</kbd>+<kbd>V</kbd> (Paste), <kbd>Ctrl</kbd>+<kbd>C</kbd> (Copy), <kbd>Ctrl</kbd>+<kbd>A</kbd> (Select All), <kbd>Ctrl</kbd>+<kbd>X</kbd> (Cut), and <kbd>Ctrl</kbd>+<kbd>Z</kbd> (Undo).
    * Enabled `persist.waydroid.fake_touch=true` to support long-press context menus and touch-and-hold text selection gestures.
  * Disabled on-screen soft keyboards when physical keyboards are attached (`secure.show_ime_with_hard_keyboard=0`).
  * KDE Plasma 6 KWin window rules for seamless window placement, decorations, and taskbar grouping without crashes.
  * Low-latency PipeWire Pulse audio routing and microphone integration.
  * Bidirectional folder bind mounts (`~/Downloads`, `~/Pictures`, `~/Documents` $\leftrightarrow$ `/sdcard/`).
  * Google Play Protect Android ID device certification helper (`purr apk certify`).
* **⚡ Purr APK CLI Manager (`purr apk`)**: Direct terminal APK installation (`purr apk install`), app launcher with geometry restore (`purr apk launch`), app listing (`purr apk list`), desktop launcher sync (`purr apk sync`), direct clipboard injection (`purr apk paste`), and session management (`purr apk session`).
* **🔔 Purr Tray Indicator Refinements**: Fixed badged urgency icon generation in Qt6, color-coded update halos, and real-time background update detection.
* **🔒 In-Lockstep Maintainability**: Updated CLI help epilogs, UNIX manual pages (`purr.1`), Bash and Zsh shell completions, and installer/uninstaller scripts.

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
