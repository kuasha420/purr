# 🐾 Purr Roadmap (Project Tuki)

> *"The Calm Before and After All Storms — Delivering serenity to Linux application management."*

---

## 🎯 The Vision
Engineered by **Purrfect Software Limited (PSL)** under the **Purrfect Universe** parent ecosystem.
Purr exists to eliminate software discovery and packaging friction on Linux, unapologetically tailored for **Arch Linux** and **KDE Plasma**.

---

## 🗺️ Release Phases

### Phase 1: MVP, Automation & Native Integration (v1.0.0 — *Tuki Edition*) — *Completed*
- [x] Multi-source resolution: `System (Pacman/archlinuxcn)` $\rightarrow$ `AUR` $\rightarrow$ `Flatpak` $\rightarrow$ `AppImage` $\rightarrow$ `Git`.
- [x] Advanced heuristic discovery (multi-word expansion, canonical slugs, brand-to-package alias dictionary).
- [x] Community popularity weighting ($\log_{10}(\text{Votes})$ for AUR).
- [x] Noise & auxiliary package suppression (filtering `-plugin`, `-languageserver`, `-driver`).
- [x] Zero-touch / silent automated installs across `pacman`, `yay`, and `flatpak`.
- [x] Persistent interactive session loop with direct 1-click app launcher (`[l]`).
- [x] Native KDE Plasma 6 Desktop Integration (Kickoff favorites, dynamic Task Manager pin/unpin via DBus, XDG Autostart).
- [x] Background System Tray Indicator (`purr-tray`) with color-coded urgency halos & adaptive network backoff.
- [x] Universal System Upgrade (`purr upgrade`) with automated conflict resolution, stale lock cleanup, and keyring auto-recovery.
- [x] Automated Flatpak EOL & unsupported runtime pruning (`flatpak uninstall --unused -y`).
- [x] Instant IPC tray indicator refresh via `QFileSystemWatcher` and `SIGUSR1`.
- [x] Full UNIX manpages (`purr.1`, `purr-tray.1`, `purr-integrate.1`, `tuki.1`).
- [x] Comprehensive shell completions (Bash & Zsh for `purr` and `tuki`).

---

### Phase 2: Purr Recipes, Android Native Subsystem & Interactive Curation (v1.1.0)
- [x] **Modular Recipe Framework (`purr recipe`)**: Declarative lifecycle management for complex subsystems (`list`, `info`, `apply`, `doctor`, `prune`, `teardown`).
- [x] **Waydroid Native Android Subsystem (`waydroid-native`)**:
  - [x] Field work pruning of legacy 2025 Waydroid state and old images.
  - [x] Auto-provisioning of `libndk` ARM translation for AMD Ryzen CPUs and Mesa GPU gralloc acceleration.
  - [x] Multi-window freeform mode (`persist.waydroid.multi_windows=true`).
  - [x] KDE Plasma 6 KWin window rules for seamless decorations, smart placement, and taskbar grouping.
  - [x] Bidirectional folder bind mounts (`~/Downloads`, `~/Pictures`, `~/Documents` $\leftrightarrow$ `/sdcard/`).
  - [x] Google Play Protect Android ID device certification helper (`purr apk certify`).
- [x] **Purr APK CLI Integration (`purr apk`)**: Direct APK installer, app launcher, and session controls.
- [ ] Interactive curses / textual TUI interface with arrow-key navigation and category filtering.
- [ ] Direct AppImageHub catalog crawler for 1-click AppImage downloads & integration via Gear Lever.
- [ ] Offline SQLite AppStream & pacman index cache for instant `< 10ms` search results.

---

### Phase 3: Unified Management & Standalone GUI (v2.0.0 — *Purr Plasma Center*)
- [ ] `purr remove <app>` / unified uninstaller across all formats.
- [ ] Isolated rollback / backup transaction hooks.
- [ ] Lightweight, modern native Qt/QML desktop GUI frontend built directly on the `purr` heuristic engine.
- [ ] Cross-distribution backend adapters (Fedora/DNF, Ubuntu/APT, openSUSE/Zypper).
