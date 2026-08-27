# 🐾 Purr Architecture & Heuristic Discovery Engine

This document details the internal design, multi-source resolution logic, and scoring heuristics of `purr` (Project Tuki).

---

## 1. Resolution Hierarchy

When discovering and installing software, `purr` enforces the following priority:

```text
[1] System Repositories (core, extra, multilib, endeavouros, archlinuxcn)
        │ (Native binary packages, fastest, best system integration)
        ▼
[2] Arch User Repository (AUR / yay)
        │ (Community PKGBUILDs built for Arch)
        ▼
[3] Flatpak (Flathub)
        │ (Sandboxed runtime container applications)
        ▼
[4] AppImage (AUR / AppImageHub / Gear Lever)
        │ (Portable standalone bundle)
        ▼
[5] Git / Direct Source Build
          (Fallback repository cloning and build)
```

---

## 2. Multi-Strategy Query Expansion

Naive text search breaks on multi-word queries (e.g. `"google chrome"` vs `google-chrome`) and aliases (`vscode` vs `visual-studio-code-bin`).

`purr` applies:
* **Canonical Tokenization**: Splits input into clean alphanumeric tokens.
* **Slug Generation**: Generates hypenated slugs (`"google chrome"` $\rightarrow$ `google-chrome`).
* **Alias Mapping**: Expands common brand names to their distribution package names.
* **Concurrent Multi-Backend Retrieval**: Queries Pacman, AUR RPC, and Flatpak simultaneously.

---

## 3. Heuristic Scoring Formula

For any package $P$ and query $Q$, the composite score $S(P, Q)$ is computed as:

$$S(P, Q) = S_{\text{match}}(P, Q) + S_{\text{type}}(P) + S_{\text{pop}}(P) + S_{\text{channel}}(P) - P_{\text{aux}}(P)$$

### Component Weights:
1. **$S_{\text{match}}$ (Name & Slug Matching)**:
   * Exact slug / display name match: $+100$ pts
   * Binary / Desktop suffix (`-bin`, `-desktop`): $+95$ pts
   * Prefix match: $+75 - \Delta\text{len}$ pts
   * Token subset overlap: $+70$ pts
   * Description match: $+25$ pts
   * Fuzzy string similarity: $\text{ratio} \times 30$ pts

2. **$S_{\text{type}}$ (Desktop Application Verification)**:
   * Verified Desktop Application in AppStream / Flathub: $+25$ pts

3. **$S_{\text{pop}}$ (Community Trust & Popularity)**:
   * For AUR packages: $\min(30, \; 6 \times \log_{10}(\text{Votes} + 1))$
   * For System repository packages: $+15$ pts baseline

4. **$P_{\text{aux}}$ (Auxiliary Package & Plugin Penalty)**:
   * Extensions, plugins, themes, skins, bindings, drivers (`-plugin`, `-extension`, `-theme`, `-languageserver`, `krunner-`, `uget-integrator-`, `python-`, `chromedriver`): $-60$ pts penalty unless explicitly searched.

5. **Noise Suppression**:
   * When any package scores $\ge 80.0$ (high confidence), all results with score $< 50.0$ are suppressed.

---

* **AUR (`yay`)**: Uses `--needed --noconfirm --answerclean None --answerdiff None --answeredit None --answerupgrade None --overwrite "*"`.
* **System Repos (`pacman`)**: Uses `sudo pacman -S --needed --noconfirm --ask 4`.
* **Flatpak (`flathub`)**: Uses `flatpak install -y --noninteractive flathub <app-id>`.

---

## 5. Universal Upgrade & Auto-Conflict Resolution

During `purr upgrade`, transactions are executed sequentially across three layers with automated diagnostic recovery:

```text
[1] Official Pacman Repositories
    ├── Stale Lock Check: Inspects & purges abandoned /var/lib/pacman/db.lck
    ├── Provider Replacements: Auto-confirms standard package replacements via --ask 4
    └── Conflict Overwrite: Automatically retries with --overwrite "*" for unowned filesystem conflicts
[2] Arch User Repository (AUR / yay)
    ├── Keyring Auto-Recovery: Re-synchronizes archlinux-keyring on PGP signature errors
    └── Clean Rebuild Fallback: Automatically attempts cleanbuilds if cached PKGBUILD artifacts fail
[3] Flatpak & EOL Maintenance
    ├── Flatpak Update: Batch updates user and system Flatpaks non-interactively
    └── EOL Pruning: Auto-removes unreferenced and End-of-Life runtimes via `flatpak uninstall --unused -y`
```

---

## 6. IPC & System Tray Architecture

`purr` pairs its command-line interface with a persistent Qt6/KDE StatusNotifierItem daemon (`purr-tray`):

```text
CLI (purr upgrade / purr <pkg>)
       │
       │ Touch ~/.cache/purr/refresh_trigger & pkill -USR1
       ▼
purr-tray Daemon
       ├── QFileSystemWatcher / POSIX SIGUSR1 Handler
       ├── Debounced Background Worker (Pacman + Yay + Flatpak + EOL Checks)
       └── Dynamic Halo Rendering (Urgency Level -> Color Matrix -> Tray Icon)
```

1. **Non-Destructive KDE Plasma Dynamic Updates**:
   Task Manager widget pin/unpin operations execute in-memory JavaScript via DBus (`qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript`), calling `w.reloadConfig()` to avoid crashing or reloading `plasmashell`.
2. **Adaptive Timing & Network Backoff**:
   - Initial delay: 15 seconds after login to permit network stack and VPN connection.
   - Default recurring interval: 60 minutes.
   - Network failure backoff: 2 minutes when offline.
   - Instant wakeups: CLI transactions trigger instant tray re-checks via IPC.
