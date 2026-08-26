<div align="center">

# 🚀 Smart App Installer (`smart-install`)

**Universal Application Discovery & Priority Installer for Arch Linux & EndeavourOS**

[![Arch Linux](https://img.shields.io/badge/Arch%20Linux-Package%20Manager-1793D1?logo=arch-linux&logoColor=white)](https://archlinux.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AUR](https://img.shields.io/badge/AUR-smart--install-blue.svg)](https://aur.archlinux.org)
[![CI](https://github.com/psl/smart-install/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

<p align="center">
  <i>Bringing the effortless discovery of consumer app stores to Linux without sacrificing Arch Linux's packaging power.</i>
</p>

</div>

---

## 🌟 The Vision

On Windows or macOS, users simply search `"google chrome"`, `"vs code"`, or `"spotify"`, click install, and they are done. 

On Linux, new users often face packaging fragmentation, cryptic package names (e.g. `visual-studio-code-bin` vs `code`), prompt fatigue (cleanbuild menus, diff prompts, confirmation questions), or irrelevant search hits (random plugins outranking official apps).

**Smart App Installer** bridges this gap:
1. **Understands Human Queries**: Intelligent tokenization, alias mapping, and canonical slugs turn `"google chrome"` into the exact official package.
2. **Prioritizes the Best Source**: Always prefers native system binaries first, builds from AUR second, sandboxed Flatpaks third, AppImages fourth, and Git sources as fallback.
3. **Zero-Touch Execution**: Automates all interactive flags (`--noconfirm`, diff bypass, cleanbuild bypass) for a clean, unattended 1-click install.
4. **App Launch Ready**: Stays open and lets you launch newly installed apps right away with a single keystroke.

---

## ⚡ Resolution Hierarchy

$$\textbf{[1] System (Pacman / archlinuxcn)} \longrightarrow \textbf{[2] AUR (yay)} \longrightarrow \textbf{[3] Flatpak (Flathub)} \longrightarrow \textbf{[4] AppImage} \longrightarrow \textbf{[5] Git}$$

```text
  User Query: "google chrome"
         │
         ├──► [1] System Repos (core/extra/archlinuxcn) ──► Not found in official base
         ├──► [2] AUR (yay) ──────────────────────────► google-chrome (Votes: 2367) ★ BEST
         ├──► [3] Flatpak (Flathub) ──────────────────► com.google.Chrome
         └──► [4] AppImage ───────────────────────────► google-chrome-appimage
```

---

## 🆚 Feature Comparison

| Feature / Capability | **Smart App Installer** | **Pamac** | **Bauh** | **Discover** |
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

### Option 1: 1-Click Git Install (Recommended)

```bash
git clone https://github.com/psl/smart-install.git
cd smart-install
./install.sh
```

### Option 2: Build with PKGBUILD

```bash
cd smart-install
makepkg -si
```

### Option 3: Full Ecosystem Auto-Setup

To configure `archlinuxcn` CDN mirrors, Flatpak + Flathub, FUSE AppImage compatibility, and companion GUI managers in one step:

```bash
./setup-ecosystem.sh
```

---

## 🚀 Usage

### 1. Interactive Session Mode

Simply run `smart-install` or `app-install`:

```bash
smart-install
```

### 2. Direct Search Mode

```bash
smart-install "google chrome"
smart-install "vs code"
smart-install spotify
smart-install "vlc player"
smart-install discord
smart-install blender
```

### 3. Desktop Application Menu

Press `Super` (Windows Key) and search for **"Smart App Installer"**.

---

## 🛠️ CLI Options

```text
usage: smart-install [-h] [-v] [--dry-run] [--no-loop] [query ...]

Smart Multi-Source Priority Application Installer and Discovery Engine.

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
smart-install/
├── .github/
│   ├── workflows/ci.yml           # Automated CI syntax & packaging tests
│   └── ISSUE_TEMPLATE/            # GitHub bug & feature templates
├── bin/
│   └── smart-install              # Core heuristic installer engine
├── completions/
│   ├── smart-install.bash         # Bash completion script
│   └── _smart-install.zsh         # Zsh completion script
├── data/
│   ├── smart-install.desktop      # Desktop menu launcher
│   └── icons/smart-install.svg    # Custom SVG application icon
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

## 🗺️ Roadmap & Vision

* **v1.1.0**: Rich curses/TUI interface with real-time fuzzy search and package inspection drawer.
* **v1.2.0**: Universal uninstaller (`smart-install remove`) and upgrade runner (`smart-install update`).
* **v2.0.0**: Native modern GUI software center frontend built directly on the discovery engine.

See [docs/ROADMAP.md](docs/ROADMAP.md) for full details.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) © 2026 PSL.
