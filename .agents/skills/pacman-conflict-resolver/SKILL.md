---
name: pacman-conflict-resolver
description: >-
  Actionable procedures and runbook for diagnosing and automatically recovering from
  Arch Linux, AUR, and Flatpak package conflicts, stale database locks, signature errors,
  unowned file collisions, and IPC indicator signaling.
---

# Pacman, AUR & Flatpak Conflict Resolution Runbook

## 1. Stale Database Lock Resolution
- **Symptom**: `error: failed to init transaction (unable to lock database)`
- **Diagnostic**: Check if a package manager process is actually running:
  ```bash
  pgrep -x "pacman" || pgrep -x "yay"
  ```
- **Resolution**: If no process is active, safely remove `/var/lib/pacman/db.lck`.

## 2. Unowned File Collisions
- **Symptom**: `error: failed to commit transaction (conflicting files)` (e.g. `/usr/bin/<binary> exists in filesystem`)
- **Diagnostic**: Check if the file is owned by any installed package:
  ```bash
  pacman -Qo /path/to/conflicting/file
  ```
- **Resolution**: If unowned, pass `--overwrite "*"` to `pacman` or `yay` to cleanly overwrite the orphaned file.

## 3. PGP Keyring & Signature Failures
- **Symptom**: `error: ... signature from ... is unknown trust`
- **Resolution**: Refresh system keyring packages:
  ```bash
  sudo pacman -Sy --needed --noconfirm archlinux-keyring archlinuxcn-keyring endeavouros-keyring
  sudo pacman-key --refresh-keys
  ```

## 4. Flatpak EOL & Orphan Runtime Pruning
- **Diagnostic**: Check for unused or EOL runtimes:
  ```bash
  flatpak uninstall --unused --dry-run
  ```
- **Resolution**: Non-interactively remove obsolete runtimes:
  ```bash
  flatpak uninstall --unused -y --noninteractive
  ```

## 5. Instant Desktop Indicator IPC
- To signal the running `purr-tray` daemon to immediately re-check updates and refresh its icon badge:
  ```python
  # Update trigger timestamp
  with open(os.path.expanduser("~/.cache/purr/refresh_trigger"), "w") as f:
      f.write(str(time.time()))
  # Send POSIX signal
  subprocess.run(['pkill', '-USR1', '-f', 'purr-tray'])
  ```
