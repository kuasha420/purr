# Contributing to 🐾 Purr (Project Tuki)

We welcome contributions, bug reports, and heuristic improvements!

---

## 🏛️ Project Standards & Ethos

Purr is an open-source project by **Purrfect Software Limited (PSL)** under the **Purrfect Universe** parent ecosystem.
We adhere to the core technical laws of PSL:
1. **"Functioning Program > Functional Program"**: Pragmatic user value and rock-solid stability take precedence over unneeded abstraction.
2. **"Code Never Lies"**: Contributions are evaluated strictly through working pull requests and verified test coverage.

---

## 🛠️ Development Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/purrfecthq/purr.git
   cd purr
   ```

2. **Run locally**:
   ```bash
   ./bin/purr "google chrome"
   ```

3. **Dry-Run Testing**:
   ```bash
   ./bin/purr --dry-run "vscode"
   ```

---

## 💡 Adding Brand Aliases or Heuristic Rules

If an application is tricky to discover on Arch Linux:
1. Open `bin/purr`.
2. Add the mapping to the `ALIASES` dictionary or refine `score_package()`.
3. Test edge cases across Pacman, AUR, and Flatpak.

---

## 📝 Pull Request Guidelines

1. Ensure code adheres to Python 3.10+ conventions.
2. Verify syntax:
   ```bash
   python3 -m py_compile bin/purr
   ```
3. Update `CHANGELOG.md` and `docs/` where applicable.
