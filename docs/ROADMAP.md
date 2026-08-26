# 🐾 Purr Roadmap (Project Tuki)

> *"The Calm Before and After All Storms — Delivering serenity to Linux application management."*

---

## 🎯 The Vision
Engineered by **Purrfect Software Limited (PSL)** under the **Purrfect Universe** parent ecosystem.
Purr exists to eliminate software discovery and packaging friction on Linux, unapologetically tailored for **Arch Linux** and **KDE Plasma**.

---

## 🗺️ Release Phases

### Phase 1: MVP & Discovery Engine (v1.0.0 — *Tuki Edition*) — *Current*
- [x] Multi-source resolution: `System (Pacman/archlinuxcn)` $\rightarrow$ `AUR` $\rightarrow$ `Flatpak` $\rightarrow$ `AppImage` $\rightarrow$ `Git`.
- [x] Advanced heuristic discovery (multi-word expansion, canonical slugs, brand-to-package alias dictionary).
- [x] Community popularity weighting ($\log_{10}(\text{Votes})$ for AUR).
- [x] Noise & auxiliary package suppression (filtering `-plugin`, `-languageserver`, `-driver`).
- [x] Zero-touch / silent automated installs across `pacman`, `yay`, and `flatpak`.
- [x] Persistent interactive session loop with direct 1-click app launcher (`[l]`).
- [x] Desktop integration (menu launcher, `.desktop`, custom Tuki vector icon).
- [x] Shell completions (Bash & Zsh for `purr` and `tuki`).

---

### Phase 2: Rich TUI & Interactive Curation (v1.1.0)
- [ ] Interactive curses / textual TUI interface with arrow-key navigation and category filtering.
- [ ] Real-time search-as-you-type fuzzy filtering.
- [ ] Package details drawer (view screenshots, upstream URL, package maintainer, licensing, permissions).
- [ ] Direct AppImageHub catalog crawler for 1-click AppImage downloads & integration via Gear Lever.

---

### Phase 3: Unified Management & Updates (v1.2.0)
- [ ] `purr remove <app>` / unified uninstaller across all formats.
- [ ] `purr update` / universal multi-backend upgrade runner.
- [ ] Isolated rollback / backup transaction hooks.
- [ ] Offline SQLite AppStream & pacman index cache for instant `< 10ms` search results.

---

### Phase 4: Standalone GUI Store (v2.0.0 — *Purr Plasma Center*)
- [ ] Lightweight, modern native Qt/QML desktop GUI frontend built directly on the `purr` heuristic engine.
- [ ] System tray update indicator.
- [ ] Cross-distribution backend adapters (Fedora/DNF, Ubuntu/APT, openSUSE/Zypper).
