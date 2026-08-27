# 🐾 Purr Project & Architecture Invariants

## 1. System Python & Runtime Environment
- **System Python Shebangs**: All executable scripts in `bin/` (`purr`, `purr-tray`, `purr-integrate`) and subprocess launchers MUST target `/usr/bin/python3` to ensure system Qt bindings (`python-pyqt6`) and desktop libraries are loaded rather than user-level pyenv/virtualenv shims.
- **Dependency Guarding**: Always import PyQt6 and other desktop libraries inside `try/except ImportError` blocks with user-friendly remediation instructions.

## 2. Non-Destructive KDE Plasma 6 Desktop Integrations
- **Zero-Crash Task Manager Updates**: Never invoke destructive DBus methods like `refreshCurrentShell` or restart `plasmashell`.
- **In-Memory Configuration Reloads**: When modifying Task Manager pinned launchers (`org.kde.plasma.icontasks` / `taskmanager`), use `qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript` to update the `launchers` configuration array and invoke `w.reloadConfig()`.

## 3. Package Management & Conflict Resolution
- **Pacman Automation**: Always pass `--needed --noconfirm --ask 4` (to auto-confirm package replacements) and use `--overwrite "*"` when resolving unowned file conflicts.
- **AUR (yay) Automation**: Always pass `--noconfirm --answerclean All --answerdiff None --answeredit None --answerupgrade None --removemake --cleanafter --overwrite "*"`.
- **Flatpak Maintenance**: Always pass `-y --noninteractive` and prune unreferenced/EOL runtimes via `flatpak uninstall --unused -y --noninteractive`.
- **Stale Locks**: Check and remove abandoned `/var/lib/pacman/db.lck` locks before starting package transactions.

## 4. In-Lockstep Maintainability Invariant
Whenever any new CLI flag, subcommand, cache file, or desktop integration is added or modified, the following MUST be updated in lockstep:
1. Built-in CLI help (`parser.epilog` / `parser.description` in `bin/purr`)
2. UNIX manual pages in `man/man1/` (`purr.1`, `purr-tray.1`, `purr-integrate.1`, `tuki.1`)
3. Shell completions (`completions/purr.bash`, `completions/_purr.zsh`)
4. Installer (`install.sh`) and complete uninstaller (`uninstall.sh`)
5. Packaging definitions (`PKGBUILD`, `.SRCINFO`) via `make aur`
6. Project documentation (`README.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `CHANGELOG.md`)
