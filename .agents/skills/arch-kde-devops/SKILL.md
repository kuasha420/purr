---
name: arch-kde-devops
description: >-
  Runbook and procedures for developing, testing, packaging, and maintaining Arch Linux
  and KDE Plasma 6 applications within the Purr ecosystem. Use when running development cycles,
  verifying desktop integrations, updating PKGBUILD/.SRCINFO, or validating full reinstall cycles.
---

# Arch Linux & KDE Plasma Dev-Ops Runbook

## 1. Development & Live Testing
- To link repository scripts live into `/usr/local/bin` and apply all KDE integrations:
  ```bash
  ./install.sh --dev --all
  # or:
  make dev && make integrate
  ```
- Check active integration status:
  ```bash
  purr integrate --status
  ```

## 2. Non-Destructive Desktop Verification
- Inspect running StatusNotifierItem tray indicator:
  ```bash
  pgrep -fl purr-tray
  ```
- Test non-destructive Task Manager pin/unpin:
  ```bash
  purr integrate --unpin && purr integrate --pin
  ```
- Verify plasmashell stability:
  ```bash
  systemctl --user status plasma-plasmashell.service
  ```

## 3. Packaging & AUR Sync
- Run test suite and syntax verification:
  ```bash
  make test
  ```
- Regenerate `.SRCINFO` whenever `PKGBUILD` is modified:
  ```bash
  make aur
  ```

## 4. Teardown & Reinstall Cycle Validation
- To verify clean teardown and rebuild robustness without leaving orphaned caches or configs:
  ```bash
  ./uninstall.sh && ./install.sh --dev --all
  ```
