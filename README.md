<div align="center">

# 🐾 purr

### Purr Universal App Engine (PUAE)
**Universal Application Discovery & Priority Installer for Arch Linux & KDE Plasma**

[![Arch Linux](https://img.shields.io/badge/Arch%20Linux-Package%20Manager-1793D1?logo=arch-linux&logoColor=white)](https://archlinux.org)
[![KDE Plasma](https://img.shields.io/badge/KDE%20Plasma-Native-3DAEE9?logo=kde&logoColor=white)](https://kde.org/plasma-desktop/)
[![CSP-IP](https://img.shields.io/badge/Licensing-CSP--IP%20(ICARO--42%2Fb)-FFD166)](LICENSE)
[![Purrfect Universe](https://img.shields.io/badge/Purrfect%20Universe-Project%20Tuki-2ECC71)](https://purrfecthq.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AUR](https://img.shields.io/badge/AUR-purr-blue.svg)](https://aur.archlinux.org)
[![CI](https://github.com/kuasha420/purr/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

<p align="center">
  <i>"The Calm Before and After All Storms — Delivering serenity to Linux software discovery."</i>
</p>

</div>

---

## 🕊️ Dedicated to Tuki (2019–2024)

> *"In the constitutional lore of the Heavenly Council of Fur, Tuki embodies the calm before and after all storms—patience, emotional composure, and deliberate execution under pressure."*

Linux package management has historically been a storm of fragmented formats (*Pacman, AUR, Flatpak, AppImage*), cryptic package names, diff prompts, and cleanbuild menus. **`purr` (Project Tuki)** transforms that storm into a peaceful, zero-touch 1-click experience.

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
git clone https://github.com/kuasha420/purr.git
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

*(You can also use the alias `tuki`, `purr-universal-app-engine`, or `app-install` interchangeably!)*

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

## 🏛️ CSP-IP Framework & Institutional Governance

`purr` is developed under the **Company-Supported Personal IP (CSP-IP)** framework governed by the **ICARO-42/b Ordinance** of the *Constitution of Purrfect Universe* (mirroring dual-heritage open-source sister projects like [`sakibtamim/Jasper`](https://github.com/sakibtamim/Jasper) and [`kuasha420/purrmission`](https://github.com/kuasha420/purrmission)):

* **Author & Primary IP Holder**: Arafat Zahan ([@kuasha420](https://github.com/kuasha420))
* **Corporate Stewardship & Infrastructure**: [Purrfect Software Limited (PSL)](https://www.purrfecthq.com)
* **Parent Ecosystem**: Purrfect Universe Inc.
* **Core Software Ethos**: *"Functioning program > Functional program"*

---

## 📄 License

This project is licensed under the [MIT License with CSP-IP Protocol](LICENSE) © 2026 Arafat Zahan / Purrfect Software Limited.
