# Contributing to Smart App Installer

We welcome contributions, bug reports, and heuristic improvements!

---

## 🛠️ Development Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/psl/smart-install.git
   cd smart-install
   ```

2. **Run locally**:
   ```bash
   ./bin/smart-install "google chrome"
   ```

3. **Dry-Run Testing**:
   ```bash
   ./bin/smart-install --dry-run "vscode"
   ```

---

## 💡 Adding Aliases or Heuristic Rules

If an application is tricky to find or has unique package naming:
1. Open `bin/smart-install`.
2. Add the mapping to the `ALIASES` dictionary or update `score_package()`.
3. Test edge cases across Pacman, AUR, and Flatpak.

---

## 📝 Pull Request Guidelines

1. Ensure code adheres to standard Python 3.10+ conventions.
2. Verify syntax:
   ```bash
   python3 -m py_compile bin/smart-install
   ```
3. Update `CHANGELOG.md` and `docs/` if modifying features or architecture.
