# Changelog

All notable changes to `purr` will be documented in this file.

## [n.e.x.t] - YYYY-MM-DD

### 🌟 What's New For You

* **Turnkey Arch Linux CN Application Ecosystem Bootstrap**: Automatically initializes keyrings and provisions archlinuxcn repositories with fail-safe signature bootstrapping, ensuring zero broken dependencies or unverified key prompts on fresh setups.
* **Frictionless APK Mode Switching**: Toggling between multi-window freeform mode and fullscreen tablet mode now automatically restarts container sessions smoothly without hanging or command line scope errors.
* **Rock-Solid Stability & Transparent Diagnostics**: When an unexpected glitch happens in background tasks, store searches, or desktop integrations, Purr no longer fails silently or mysteriously swallows the problem. Errors are now traced and reported clearly with actionable diagnostics, making fixes immediate and dependable.
* **Cleaner, Safer Desktop Uninstallation**: Running `uninstall.sh` cleanly validates desktop and system services before stopping them, ensuring KDE Plasma stays silky smooth without leftover warnings or hidden error masking.

### 🔧 Under the Hood

#### 🌐 Ecosystem & Recipe Engine Enhancements
* **Ecosystem Keyring & Mirrorlist Bootstrap (`setup-ecosystem.sh`)**: Added keyring pre-initialization (`pacman-key --init` and `--populate archlinux`), auto-generated default `archlinuxcn-mirrorlist`, and automated transient `SigLevel = Optional TrustAll` bootstrapping for `archlinuxcn-keyring` to resolve unresolvable signature errors on cold systems.
* **Package Conflict & Replacement Automation**: Standardized `--ask 4 --overwrite "*"` pacman automation flags and silent non-interactive AUR `yay` flags across ecosystem GUI manager installations.
* **Waydroid Native Prerequisite Auto-Provisioning (`recipe.py`)**: Enhanced `check_prerequisites()` to install missing dependencies automatically before validating kernel BinderFS.
* **APK Session Mode CLI Binary Scope (`bin/purr`)**: Resolved `UnboundLocalError: local variable 'waydroid_bin'` in `purr apk session mode` and integrated session restarts through `WaydroidNativeRecipe.restart_session()`.
* **Developer & Space-Safe Build Tooling (`install.sh`, `Makefile`)**: Linked live `recipes/` in `--dev` mode to `/usr/local/share/purr/recipes` and fully quoted `$(REPO_DIR)` across Makefile targets to ensure robust execution within directory paths containing spaces.

#### 🐾 In-Lockstep Maintainability & Zero Silent Failures
* **Step 7 Invariant Enforcement ("No error swallowing in committed code")**: Codified Step 7 of the In-Lockstep Maintainability Invariant across `AGENTS.md`, `docs/CODING_STANDARDS.md`, `docs/ARCHITECTURE.md`, and skills runbooks.
* **AST Error Swallowing Auditor (`scripts/audit_errors.py`)**: Built an automated AST static analysis engine that checks all Python files and Shell scripts for bare `except:`, `except ...: pass`, unlogged broad catches, and subprocess `stderr=subprocess.DEVNULL` blackholing.
* **DevOps, Test & Release Gates**:
  * Wired `make audit-errors` into `Makefile` and integrated it as the primary verification step of `make test`.
  * Added mandatory error audit execution to `scripts/release.py` pre-flights and `.github/workflows/ci.yml` CI validation.
* **Codebase Remediation**: Remediated all legacy `except Exception: pass` and unlogged exception clauses across `bin/purr` (package discovery and clipboard fallback), `bin/purr-tray` (configuration, update polling, watcher triggers, keyguard checks), `bin/purr-integrate` (DBus script execution), and `recipes/base.py` (manifest state reading/writing).
* **Elimination of Operational Stderr Masking**: Removed blind `2>/dev/null || true` blackholing across `uninstall.sh`, introducing explicit service state checks (`systemctl is-active --quiet`) and transparent error handling.

## [1.1.0] - 2026-09-11 — *Prionailurus bengalensis* (Purr Recipes & Android Native Subsystem)

### 🌟 What's New For You

* **Android on Your Desktop, Made Effortless**: Run phone and tablet applications (such as WhatsApp, Messenger, Aurora Store, and games) directly on your Arch Linux desktop alongside your native apps. They launch from your KDE Kickoff Application Menu, respect your dark/light themes, and run in smooth, floating, resizable multi-windows.
* **Smart Window Geometry & Position Memory**: Android windows now remember exactly where you left them and what size you preferred. Whether on a laptop screen, multi-monitor setup, HiDPI display, or ultrawide monitor, apps restore cleanly within visible bounds without spawning off-screen.
* **One-Click Headless Recovery for Crashing Apps**: When Android apps crash due to complex translation bugs (like Facebook Messenger turning completely black), Purr headlessly diagnoses the issue, installs a verified compatible 32-bit build, and immunizes the app from breaking auto-updates—all while keeping your chats, messages, and login sessions 100% intact.
* **Frictionless Copy, Paste & Typing**: Copy text on your Linux desktop with <kbd>Ctrl</kbd>+<kbd>C</kbd> and paste it straight into Android with <kbd>Ctrl</kbd>+<kbd>V</kbd>. Typing is effortless with physical NumPad support, hardware <kbd>Esc</kbd> back navigation, and <kbd>Enter</kbd> to send messages in chat apps.
* **Plug-and-Play Gamepads & Webcams**: Connect your PlayStation 5 DualSense, DualShock 4, Xbox Wireless Controller, or external webcam—it connects directly to Android with full analog stick, trigger, vibration, and video call support.
* **Safe, Zero-Data-Loss Subsystem Maintenance**: Running `purr upgrade` now automatically converges Android companion apps, KWin window rules, and framework patches to the newest versions without ever wiping your containers or user databases.

### 🔧 Under the Hood

#### 🐾 Modular Recipe Engine & Subsystem Architecture
* **Extensible Subsystem Framework (`purr recipe`)**: Standardized declarative interface featuring `check_prerequisites`, `provision`, `integrate_desktop`, `sync`, `doctor`, `prune`, and `teardown`.
* **State Convergence Engine (`is_deployed()` & `sync()`)**: Non-destructive state alignment engine that updates companion APKs, KWin window rules, and framework patches on already-deployed systems without invoking destructive `waydroid init -f` re-initialization.
* **Automated Upgrade Lifecycle (Step 4)**: Integrated `sync_all_deployed()` into `purr upgrade`, automatically bringing all active subsystems up to date during routine system package upgrades.
* **Direct Self-Update Engine (`purr self-update`)**: Instant host updating from git checkouts or system packages with automatic manpage and shell completion reinstallation.

#### 📱 Waydroid Native Android Subsystem (`waydroid-native`)
* **Scale-Aware Display Normalization**: Real-time display geometry probing via `kscreen-doctor` with ANSI stripping (`window_memory.py`), dynamically converting physical Android coordinates to KWin logical desktop points.
* **Universal Freeform Window Caption Visibility Patcher**:
  * Fixed Google Material Components `<Button>` tag collision in `framework-res.apk`'s `res/layout/decor_caption.xml` by declaring `<View>` elements to bypass solid purple `MaterialButton` tinting.
  * Binary-patched `framework-res.apk` and `SystemUI.apk` color selectors (`decor_button_dark_color`, `decor_button_light_color`) to 100% solid white for active windows and 50% dimmed white for inactive windows.
  * Replaced black vector path fill colors (`decor_close_button_dark`, `decor_back_button_dark`) with `@android:color/white` in `SystemUI.apk` with byte-aligned 4-byte `zipalign` and AOSP platform key signing.
* **Chromium & Android System WebView Opaque Surface Rendering**: Automated provisioning of Chromium command-line override files (`chrome-command-line`, `webview-command-line`, `brave-command-line`, `chromium-command-line`, `edge-command-line`) with `--disable-features=AndroidSurfaceControl,SurfaceControl` across `/data/local/tmp/` and OverlayFS persistence.
* **Two-Way Synchronous IPC Bridge (`PurrBridgeHelper`)**: Built-in system companion APK (`PurrBridgeHelper.apk`) deployed to `/system/priv-app/PurrBridgeHelper/` enabling synchronous two-way IPC between Linux CLI and Android via `am broadcast -W` returning structured JSON in `resultData`.
* **Headless Android App Repair Engine (`app_repair.py`)**: Preserves user data via `pm uninstall -k`, enforces verified 32-bit ARM (`armeabi-v7a`) builds, purges auto-update records from Google Play Store SQLite databases (`library.db`, `localappstate.db`, `auto_update.db`), and blacklists packages in Aurora Store.
* **Curated Architecture Profiles in Aurora Store**: Automated build and signing engine (`aurora_patcher.py`) embedding genuine Google-certified hardware presets (`! [Purr: ...]`) pinned to the top of Aurora Store's device spoofing menu for guaranteed 32-bit ARM, 64-bit ARM, and x86_64 APK delivery.
* **Hardware Gamepad & Low-Latency Webcam Passthrough**: Hotplug bridge in `purr-tray` dynamically passing gamepads (DualSense, DualShock, Xbox) and V4L2 webcams into the container via LXC cgroup2 device allowances, while isolating host keyboards and mice to prevent keystroke leakage.
* **Zero-Latency Clipboard Bridge**: `PurrClipHelper.apk` priv-app companion combined with zero-CPU `wl-paste --watch` event bridge streaming host clipboard updates to Android in real time.
* **Android 13 APEX Dynamic Linker Multi-Layered Boot Self-Healing**: Deployed system overlay init hook (`/system/etc/init/purr_linkerconfig.rc`), container post-start watchdog (`waydroid-container-post-start.sh`), and upstream LXC startup patch (`patch_waydroid_lxc_helper()`) permanently eliminating bootstrap linkerconfig freezes.
* **Zero Silent Failures Doctrine**: Full compliance across all recipe scripts, release tooling, and background monitors (`docs/CODING_STANDARDS.md`).

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
