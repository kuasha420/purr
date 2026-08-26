<div align="center">

# 🐾 purr

### Universal Application Discovery & Priority Installer for Arch Linux & KDE Plasma

[![Arch Linux](https://img.shields.io/badge/Arch%20Linux-Package%20Manager-1793D1?logo=arch-linux&logoColor=white)](https://archlinux.org)
[![KDE Plasma](https://img.shields.io/badge/KDE%20Plasma-Native-3DAEE9?logo=kde&logoColor=white)](https://kde.org/plasma-desktop/)
[![Purrfect Universe](https://img.shields.io/badge/Purrfect%20Universe-Project%20Tuki-FFD166)](https://purrfecthq.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AUR](https://img.shields.io/badge/AUR-purr-blue.svg)](https://aur.archlinux.org)
[![CI](https://github.com/purrfecthq/purr/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

<p align="center">
  <i>"The Calm Before and After All Storms — Delivering serenity to Linux software discovery."</i>
</p>

</div>

---

## 🕊️ Dedicated to Tuki (2019–2024)

> *"In the lore of the Heavenly Council of Fur, Tuki embodies the calm before and after all storms—patience, emotional composure, and deliberate execution under pressure."*

Linux package management has historically been a storm of fragmented ecosystems (*Pacman, AUR, Flatpak, AppImage*), cryptic package names, and prompt fatigue. **`purr` (Project Tuki)** was created by **Purrfect Software Limited (PSL)** to transform that storm into a serene, 1-click experience.

---

## 🌟 The Vision

On consumer operating systems, users simply type `"google chrome"`, `"vs code"`, or `"spotify"`, click install, and they are done.

**`purr`** brings that effortless discovery to **Arch Linux** and **KDE Plasma**:
1. **Understands Human Queries**: Canonical tokenization, brand alias mapping, and AppStream metadata turn `"google chrome"` into the exact official package.
2. **Prioritizes the Best Source**: Always prefers native system binaries first, builds from AUR second, sandboxed Flatpaks third, AppImages fourth, and Git sources as fallback.
3. **Zero-Touch Execution**: Automates all interactive flags (`--noconfirm`, diff bypass, cleanbuild bypass) for a clean, unattended install.
4. **Instant Launch**: Stays open after install and lets you launch newly installed apps right away with `[l]`.

---

## ⚡ Resolution Hierarchy

$$\textbf{[1] System (Pacman / archlinuxcn)} \longrightarrow \textbf{[2] AUR (yay)} \longrightarrow \textbf{[3] Flatpak (Flathub)} \longrightarrow \textbf{[4] AppImage} \longrightarrow \textbf{[5] Git}$$

```text
  User Query: "google chrome"
         │
         ├──► [1] System Repos (core/extra/archlinuxcn) ──► Not found in official base
         ├──► [2] AUR (yay) ──────────────────────────► google-chrome (Votes: 2367) ★ RECOMMENDED
         ├──► [3] Flatpak (Flathub) ──────────────────► com.google.Chrome
         └──► [4] AppImage ───────────────────────────► google-chrome-appimage
```

---

## 🆚 Feature Comparison

| Feature / Capability | **purr** 🐾 | **Pamac** | **Bauh** | **Discover** |
| :--- | :---: | :---: | :---: | :---: |
| **Heuristic Multi-Word Discovery** | ✅ **Advanced** | ⚠️ Substring | ⚠️ Substring | ❌ Limited |
| **Strict Packaging Hierarchy** | ✅ **Built-in** | ❌ Flat list | ❌ Flat list | ❌ Flat list |
| **AUR Popularity & Vote Weighting** | ✅ **Yes ($\log_{10}$)** | ❌ No | ❌ No | ❌ No |
| **Auxiliary / Plugin Suppression** | ✅ **Automatic** | ❌ No | ❌ No | ❌ No |
| **Zero-Touch Silent Installs** | ✅ **Yes** | ⚠️ GUI Confirm | ⚠️ GUI Confirm | ⚠️ GUI Confirm |
| **Post-Install Direct App Launcher** | ✅ **Yes (`[l]`)** | ❌ No | ❌ No | ⚠️ Sometimes |
| **Multi-Source Support** | **Pacman + AUR + Flatpak + AppImage + Git** | Pacman + AUR + Flatpak | Pacman + AUR + Flatpak + AppImage | Flatpak + PK |

---

## 📦 Installation

### Option 1: 1-Click Install (Recommended)

```bash
git clone https://github.com/purrfecthq/purr.git
cd purr
./install.sh
```

### Option 2: Build with PKGBUILD

```bash
cd purr
makepkg -si
```

### Option 3: Full Arch Ecosystem Auto-Setup

To configure `archlinuxcn` CDN mirrors, Flatpak + Flathub, FUSE AppImage compatibility, and companion GUI managers in one step:

```bash
./setup-ecosystem.sh
```

---

## 🚀 Usage

### 1. Direct Search Mode

```bash
purr "google chrome"
purr "vs code"
purr spotify
purr "vlc player"
purr discord
purr blender
```

*(You can also use the alias `tuki` or `app-install` interchangeably!)*

### 2. Interactive Session Mode

```bash
purr
```

### 3. Desktop Application Menu

Press `Super` (Windows Key) and search for **"Purr"**.

---

## 🛠️ CLI Options

```text
usage: purr [-h] [-v] [--dry-run] [--no-loop] [query ...]

🐾 purr (Project Tuki) — Universal Application Discovery & Priority Installer.

positional arguments:
  query          Application name or search keyword

options:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
  --dry-run      search and resolve without executing installation
  --no-loop      exit immediately after single installation without session loop
```

---

## 📂 Project Structure

```text
purr/
├── .github/
│   ├── workflows/ci.yml           # Automated CI syntax & packaging tests
│   └── ISSUE_TEMPLATE/            # GitHub bug & feature templates
├── bin/
│   └── purr                       # Core heuristic installer engine (v1.0.0)
├── completions/
│   ├── purr.bash                  # Bash completion script
│   └── _purr.zsh                  # Zsh completion script
├── data/
│   ├── purr.desktop               # Desktop menu launcher
│   └── icons/purr.svg             # Custom Tuki vector application icon
├── docs/
│   ├── ARCHITECTURE.md            # Discovery math & scoring engine details
│   └── ROADMAP.md                 # Development roadmap (TUI, GUI, updates)
├── CHANGELOG.md                   # Release notes
├── CONTRIBUTING.md                # Contribution guide
├── install.sh                     # System installer script
├── uninstall.sh                   # Clean uninstaller script
├── setup-ecosystem.sh             # 1-click Arch ecosystem configurator
├── PKGBUILD                       # Arch package specification
├── .SRCINFO                       # Generated AUR source info
├── LICENSE                        # MIT License
└── README.md                      # Project documentation
```

---

## 🗺️ Roadmap

* **v1.1.0**: Rich curses/TUI interface with real-time fuzzy search and package inspection drawer.
* **v1.2.0**: Universal uninstaller (`purr remove`) and upgrade runner (`purr update`).
* **v2.0.0**: Native modern Qt/QML desktop software center frontend (**Purr Plasma Center**).

See [docs/ROADMAP.md](docs/ROADMAP.md) for full details.

---

## 🏛️ About Purrfect Software Limited & Purrfect Universe

Purr is engineered and maintained by **Purrfect Software Limited (PSL)**, an operating technology core of the **Purrfect Universe** parent ecosystem.

* **Core Ethos**: *"Functioning program > Functional program"*
* **Website**: [www.purrfecthq.com](https://www.purrfecthq.com)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) © 2026 Purrfect Software Limited.
