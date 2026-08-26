# Smart App Installer Roadmap

This roadmap outlines the planned evolution of `smart-install` from MVP to a full-featured universal packaging platform.

---

## 🎯 The Core Vision
Deliver a consumer-grade, friction-free app discovery and management experience on Linux without sacrificing Arch Linux's packaging depth.

---

## 🗺️ Phases

### Phase 1: MVP & Core Engine (v1.0.0) — *Current*
- [x] Multi-source resolution: `System (Pacman/archlinuxcn)` $\rightarrow$ `AUR` $\rightarrow$ `Flatpak` $\rightarrow$ `AppImage` $\rightarrow$ `Git`.
- [x] Advanced heuristic discovery (multi-word expansion, canonical slugs, brand-to-package alias dictionary).
- [x] Community popularity weighting ($\log_{10}(\text{Votes})$ for AUR).
- [x] Noise & auxiliary package suppression (filtering `-plugin`, `-languageserver`, `-driver`).
- [x] Zero-touch / silent automated installs across `pacman`, `yay`, and `flatpak`.
- [x] Persistent interactive session loop with direct 1-click app launcher (`[l]`).
- [x] Desktop integration (menu launcher, `.desktop`, custom SVG icon).
- [x] Shell completions (Bash & Zsh).

---

### Phase 2: Rich TUI & Interactive Curation (v1.1.0)
- [ ] Interactive curses / textual TUI interface with arrow-key navigation and category filtering.
- [ ] Real-time search-as-you-type fuzzy filtering.
- [ ] Package details drawer (view screenshots, upstream URL, package maintainer, licensing, permissions).
- [ ] Direct AppImageHub catalog crawler for 1-click AppImage downloads & integration via Gear Lever.

---

### Phase 3: Unified Management & Updates (v1.2.0)
- [ ] `smart-install remove <app>` / unified uninstaller across all formats.
- [ ] `smart-install update` / universal multi-backend upgrade runner.
- [ ] Isolated rollback / backup transaction hooks.
- [ ] Offline SQLite AppStream & pacman index cache for instant `< 10ms` search results.

---

### Phase 4: Standalone GUI Store (v2.0.0)
- [ ] Lightweight, modern native Qt/QML or GTK4/Adwaita desktop GUI frontend built directly on the `smart-install` heuristic engine.
- [ ] System tray update indicator.
- [ ] Cross-distribution backend adapters (Fedora/DNF, Ubuntu/APT, openSUSE/Zypper).
