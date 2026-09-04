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
  * **Scale-Aware Multi-Window Geometry & Position Memory**:
    * Dynamic resolution and scaling factor auto-detection via `kscreen-doctor` with ANSI stripping (`window_memory.py`).
    * Automatic physical-to-logical point normalization across scaled/HiDPI and ultrawide displays, eliminating off-screen spawns and invisible edge drag boundaries.
    * Strict desktop boundary clamping ensuring all windows launch within visible screen viewports.
    * Automated `clean_oversized_kwin_rules()` engine sanitizing legacy unscaled entries from `kwinrulesrc`.
    * Real-time position tracking via `purr-tray` with automatic geometry restoration on cold launch and Kickoff menu clicks.
    * Opt-in configurable state toggle in tray menu and `~/.config/purr/config.json`.
  * **Non-Destructive KDE Plasma 6 Integration**:
    * Custom KWin window rules for seamless decorations, smart window placement, and taskbar grouping without crashing `plasmashell`.
    * Bundled `PurrWindowDecorOverlay.apk` (SystemUI) Runtime Resource Overlay (RRO) providing acrylic titlebar borders and clean multi-window UI theming.
  * **Universal Window Caption Visibility Fix**:
    * Resolved invisible window caption controls (`<`, `—`, `🗗`, `✕`) across all Android freeform windows, including both Google Material Components apps (e.g. Gamepad Tester) and standard apps (e.g. Play Store).
    * Fixed Google Material Components `<Button>` tag interception where `MaterialComponentsViewInflater` replaced caption buttons with `MaterialButton` and tinted the entire button solid purple with `colorPrimary`, by declaring `<View>` in `res/layout/decor_caption.xml` within `framework-res.apk`.
    * Binary-patched both `framework-res.apk` and `SystemUI.apk` color selectors (`decor_button_dark_color` and `decor_button_light_color`) to 100% solid white (`#ffffffff`) for focused windows and 50% dimmed white (`#80ffffff`) for unfocused windows, maintaining active window hierarchy while preserving full legibility.
    * Replaced black vector path fill colors (`decor_close_button_dark`, `decor_back_button_dark`) with `@android:color/white` in `SystemUI.apk`.
    * Automated byte-aligned APK repackaging, 4-byte `zipalign`, and AOSP platform test-key signing (APK Signature Scheme v1/v2/v3).
  * **Chromium & WebView Opaque Surface Rendering Fix**:
    * Automated provisioning of Chromium command-line override files (`chrome-command-line`, `webview-command-line`, `brave-command-line`, `chromium-command-line`, `edge-command-line`) with `--disable-features=AndroidSurfaceControl,SurfaceControl` and `0777` permissions across active container `/data/local/tmp/` and OverlayFS persistence.
    * Eliminates multi-window freeform transparent webpage rendering by forcing Chromium's Blink/Skia GPU compositor to render directly into the primary Activity window canvas rather than punching a translucent hole for a detached `SurfaceControl`.
  * **Real-Time Bidirectional Clipboard Sharing**:
    * Native API 33 companion (`PurrClipHelper.apk`) installed in `/system/priv-app/` and container runtime to overcome Android 13 multi-window background focus restrictions.
    * Zero-CPU `wl-paste --watch` event bridge in `purr-tray` continuously streaming Linux host clipboard updates to Android in real time.
    * CLI clipboard injector (`purr apk paste [text]`) and tray menu action for instant text typing into active input fields.
  * **Desktop Keyboard & Touch Optimization**:
    * Physical NumPad direct character mapping in `Generic.kcm` without requiring host NumLock state synchronization.
    * Hardware <kbd>Esc</kbd> key mapped to Android hardware Back button (`fallback BACK`) for instant modal, popup, and navigation dismissal.
    * Multi-line <kbd>Shift</kbd>+<kbd>Enter</kbd> newline support and <kbd>Ctrl</kbd>+<kbd>Enter</kbd> message dispatch fallback across chat apps (Messenger, WhatsApp, Slack, Discord).
    * Automated `input_enter_send` configuration for WhatsApp enabling direct Enter key message dispatch on physical keyboards.
    * Integrated zero-UI `PurrNullIME.apk` companion completely eliminating LatinIME soft keyboard popup surfaces and ghost windows.
    * Enhanced KWin Plasma 6 window suppression rule matching `title=InputMethod` across all window types.
    * KeyCharacterMap desktop shortcuts for <kbd>Ctrl</kbd>+<kbd>V</kbd> (Paste), <kbd>Ctrl</kbd>+<kbd>C</kbd> (Copy), <kbd>Ctrl</kbd>+<kbd>A</kbd> (Select All), <kbd>Ctrl</kbd>+<kbd>X</kbd> (Cut), and <kbd>Ctrl</kbd>+<kbd>Z</kbd> (Undo).
    * `persist.waydroid.fake_touch=true` mapping for touch-and-hold gestures, text selection handles, and long-press context menus.
    * On-screen soft keyboards automatically suppressed when physical keyboards are attached.
  * **🎮 Hardware Game Controller & Low-Latency Webcam Passthrough**:
    * Full hardware game controller passthrough supporting PlayStation 5 DualSense (`Vendor_054c_Product_0ce6.kl`), DualShock 4, Xbox Wireless Controller (`Vendor_045e_Product_028e.kl`), Nintendo Switch Pro, and generic USB/Bluetooth gamepads.
    * Strict input device isolation filtering (`get_host_gamepad_devices()`) ensuring host Linux keyboards and mice are never bound into container `/dev/input/`, completely preventing background keystroke leakage and phantom search popups.
    * Real-time zero-CPU hotplug bridge in `purr-tray` automatically synchronizing newly plugged/paired controllers into the container with full analog sticks, triggers, D-pad, and vibration support.
    * LXC cgroup2 device allowances for input major 13 (`/dev/input/event*`, `/dev/input/js*`), HIDRAW (`/dev/hidraw*`), `/dev/uinput`, `/dev/uhid`, and media controllers (`/dev/media*`).
    * Low-latency V4L2 external webcam passthrough with front-facing camera HAL mapping for video calling in WhatsApp, Zoom, Google Meet, and native camera apps.
  * **Audio & Storage Integration**:
    * Low-latency PipeWire Pulse audio routing and microphone integration.
    * Bidirectional media folder bind mounts (`~/Downloads`, `~/Pictures`, `~/Documents` $\leftrightarrow$ `/sdcard/`).
    * Google Play Protect Android ID device certification helper (`purr apk certify`).

* **⚡ Purr APK Management CLI (`purr apk`)**:
  * Direct terminal APK installation (`purr apk install /path/to/app.apk`).
  * Instant application launcher with geometry restoration (`purr apk launch <package>`).
  * Application listing (`purr apk list`), desktop launcher synchronization (`purr apk sync`), and container session control (`purr apk session start|stop|restart`).

* **🏪 Aurora Store Architecture Profiles & Automated Patcher**:
  * Automated build, 4-byte zipalign, and signing engine (`aurora_patcher.py`) automatically detecting Android SDK build-tools or falling back gracefully to upstream preloads.
  * Curated, genuine Google-certified hardware profile presets pinned to the top of Aurora Store's device spoofing menu (`! [Purr: ...]`) for guaranteed 32-bit ARM, 64-bit ARM, and x86_64 native APK delivery without Storefront check failures.
  * Clean ASCII profile naming and stock device categorizations (`Stock: ...`).
  * Integrated seamlessly into `install_essential_stores()` during `purr recipe apply waydroid-native`.

* **🔔 Purr System Tray Indicator Refinements (`purr-tray`)**:
  * Fixed antialiased urgency badge icon rendering in Qt6.
  * Color-coded update urgency halos (Cyan $\rightarrow$ Amber $\rightarrow$ Crimson Coral) with network backoff recovery.
  * Android subsystem controls and quick application launchers accessible from tray context menu.

* **🔒 In-Lockstep Maintainability**:
  * Built-in CLI help, UNIX manual pages (`purr.1`), and Bash/Zsh shell completions updated in lockstep.
  * Clean installation (`install.sh`) and complete uninstaller (`uninstall.sh`) updated with recipe assets.
  * Packaging definitions (`PKGBUILD`, `.SRCINFO`) updated with `python-gbinder` and `wl-clipboard` optdepends.

### 🐛 Bug Fixes & Hardware Parity Hardening

* **Android 13 APEX Dynamic Linker Auto-Configuration**:
  * Implemented `ensure_linkerconfig()` in `system_tuning.py` to regenerate full APEX namespaces (`com.android.runtime`, `com.android.art`, `com.android.i18n`) and SPHAL/VNDK graphics libraries (`libEGL_mesa.so`) into `/linkerconfig/ld.config.txt`.
  * Resolves dynamic linker aborts in LXC containers where early bootstrap linker configuration fails to locate APEX bionic libraries.
* **Modern Linux 6.6+ OverlayFS Mount Compatibility**:
  * Added `patch_waydroid_mount_helper()` to patch `/usr/lib/waydroid/tools/helpers/mount.py`, ensuring `readonly=False` is set whenever `upper_dir` is supplied.
  * Prevents kernel `fsconfig() failed: Stale file handle` (`ESTALE`) rejections on modern Arch Linux kernels when mounting system/vendor overlays.
* **LXC 6.0 Device Filter Hardening**:
  * Added standard root device allow classes (`c 1:*`, `c 5:*`, `c 10:*`, `c 226:*`, `c 242:*`) to `tune_game_controller_and_webcam_passthrough()` in `/var/lib/waydroid/lxc/waydroid/config`.
  * Prevents LXC 6.0 from stripping default device permissions (`/dev/null`, `/dev/zero`, `/dev/tty`, DRM render nodes, and BinderFS) when custom gamepad filters are applied.
* **Container Frozen State Auto-Recovery**:
  * Added `ensure_container_unfrozen()` across package query tools, desktop synchronization, and CLI commands.
  * Prevents operations from hanging indefinitely when Waydroid auto-freezes idle containers via cgroup2.
* **Application Listing & Desktop Synchronization**:
  * Fixed multi-line YAML parsing in `list_apps()` (`recipe.py`) and added non-blocking IPC timeouts with package manager fallbacks.
  * Batched `tune_android_keyboard_and_freeform()` commands into a single `lxc-attach` execution, reducing execution time from ~30s to <0.5s.
* **Storage Sharing & Build Tools Fallback**:
  * Resolved `[Errno 13] Permission denied` in `fileshare.py` by ensuring proper permissions and replacing empty default Android media directories with host symlinks.
  * Added graceful fallback in `titlebar_patch.py` to use pre-built `PurrWindowDecorOverlay.apk` when Android SDK build-tools (`zipalign`/`apksigner`) are absent.

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
