# Smart App Installer (`smart-install`)

> **Universal Application Discovery and Priority Installer for Arch Linux & EndeavourOS**

`smart-install` is an intelligent, multi-source package manager frontend and discovery engine. It searches across **Official Arch Repositories**, **archlinuxcn**, **AUR**, **Flatpak (Flathub)**, and **AppImage**, using heuristic ranking and popularity weighting to automatically recommend and install the best version of any application.

---

## Features

* **Strict Hierarchy Resolution**:
  $$\text{System (Pacman/archlinuxcn)} \longrightarrow \text{AUR (yay)} \longrightarrow \text{Flatpak (Flathub)} \longrightarrow \text{AppImage} \longrightarrow \text{Git}$$
* **Smart Heuristic Discovery Engine**:
  * Multi-term query expansion (e.g. searching `"google chrome"` accurately finds `google-chrome`).
  * Popularity weighting based on community AUR votes ($\log_{10}(\text{Votes})$).
  * Automatic noise and auxiliary package suppression (filters out plugins, extensions, drivers, and language servers).
* **Persistent Session & 1-Click Launcher**:
  * Stays open in an interactive session after installation.
  * Direct shortcut (`[l]`) to launch newly installed applications immediately in the background.
  * Seamless integration with GUI stores (**Bauh**, **Pamac**, **Gear Lever**).
* **Full Desktop Integration**:
  * Launch directly from KDE Plasma Application Launcher, KRunner, or terminal.

---

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/psl/smart-install.git
cd smart-install

# Run the installer
./install.sh
```

### 2. Configure Full Ecosystem (Optional)

To configure `archlinuxcn` mirrors, Flatpak/Flathub, AppImage FUSE compatibility, and GUI stores in one step:

```bash
./setup-ecosystem.sh
```

---

## Usage

### Interactive Search Mode

```bash
smart-install
```

### Direct Search Mode

```bash
smart-install "google chrome"
smart-install "vs code"
smart-install spotify
smart-install "vlc player"
smart-install discord
```

---

## Architecture & Scoring

For deep details on the scoring heuristics, tokenization algorithms, and multi-source resolution math, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## License

[MIT License](LICENSE) © 2026 PSL
