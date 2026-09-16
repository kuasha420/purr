.PHONY: all dev install uninstall test clean aur push integrate release release-check changelog-compact audit-errors help

SHELL := /bin/bash
REPO_DIR := $(shell pwd)

help:
	@echo "🐾 Purr (Project Tuki) Developer Management"
	@echo ""
	@echo "Targets:"
	@echo "  make dev               - Link repository live to /usr/local/bin for instant development"
	@echo "  make install           - Install production copy to system"
	@echo "  make integrate         - Enable all KDE Plasma desktop integrations (Favorites, Task Manager, Tray, Autostart)"
	@echo "  make audit-errors      - Statically verify Zero Error Swallowing & Silent Failures"
	@echo "  make test              - Run error audit, syntax validation, recipe diagnostics, and tests"
	@echo "  make clean             - Clean build caches and temporary files"
	@echo "  make aur               - Validate PKGBUILD and update .SRCINFO"
	@echo "  make release           - Run automated release engine (prompts for version/codename if not set)"
	@echo "  make release-check     - Dry-run validation of release engine without altering git state"
	@echo "  make changelog-compact - Validate Two-Tier formatting in CHANGELOG.md"
	@echo "  make push              - Commit all changes and push to GitHub"

dev:
	@"$(REPO_DIR)/install.sh" --dev
	@"$(REPO_DIR)/bin/purr-integrate" --restart-tray

reload-tray:
	@"$(REPO_DIR)/bin/purr-integrate" --restart-tray

install:
	@"$(REPO_DIR)/install.sh"

uninstall:
	@"$(REPO_DIR)/uninstall.sh"

integrate:
	@"$(REPO_DIR)/bin/purr-integrate" --all

audit-errors:
	@/usr/bin/python3 "$(REPO_DIR)/scripts/audit_errors.py"

release:
	@/usr/bin/python3 "$(REPO_DIR)/scripts/release.py"

release-check:
	@/usr/bin/python3 "$(REPO_DIR)/scripts/release.py" --version 1.1.0 --codename "Prionailurus bengalensis" --descriptive-name "Purr Recipes & Android Native Subsystem" --dry-run --skip-tests

changelog-compact:
	@/usr/bin/python3 "$(REPO_DIR)/scripts/compact_changelog.py" --check

test: audit-errors
	@echo "==> Running syntax checks..."
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/bin/purr"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/bin/purr-tray"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/bin/purr-integrate"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/scripts/audit_errors.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/scripts/compact_changelog.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/scripts/release.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/base.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/manager.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/recipe.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/system_tuning.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/kwin_rules.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/fileshare.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/desktop_sync.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/window_memory.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/aurora_patcher.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/titlebar_patch.py"
	@/usr/bin/python3 -m py_compile "$(REPO_DIR)/recipes/waydroid_native/app_repair.py"
	@echo "==> Testing CLI help and version..."
	@"$(REPO_DIR)/bin/purr" --version
	@"$(REPO_DIR)/bin/purr" --help > /dev/null
	@/usr/bin/python3 "$(REPO_DIR)/bin/purr-tray" --help > /dev/null
	@/usr/bin/python3 "$(REPO_DIR)/bin/purr-integrate" --help > /dev/null
	@echo "==> Testing Purr Recipes registry and convergence engine..."
	@"$(REPO_DIR)/bin/purr" recipe list > /dev/null
	@/usr/bin/python3 -c "import sys; sys.path.insert(0, '$(REPO_DIR)'); from recipes.manager import RecipeManager; mgr = RecipeManager(); r = mgr.get_recipe('waydroid-native'); assert r is not None; assert hasattr(r, 'is_deployed') and hasattr(r, 'sync'); print('Recipe convergence interface verified.')"
	@echo "==> Testing Aurora Store patcher profile validation..."
	@/usr/bin/python3 -c "import sys; sys.path.insert(0, '$(REPO_DIR)'); from recipes.waydroid_native.aurora_patcher import PURR_DEVICE_MAP; assert len(PURR_DEVICE_MAP) >= 10; print(f'Aurora patcher verified with {len(PURR_DEVICE_MAP)} curated profiles.')"
	@echo "==> Testing Purr App Repair and Bridge IPC engine..."
	@/usr/bin/python3 -c "import sys; sys.path.insert(0, '$(REPO_DIR)'); from recipes.waydroid_native.app_repair import repair_app, send_bridge_command; assert callable(repair_app); print('Purr app repair and bridge engine verified.')"
	@echo "==> Testing KDE Plasma integration status..."
	@"$(REPO_DIR)/bin/purr" integrate --status
	@echo "==> 🐾 All tests passed cleanly!"

clean:
	@echo "==> Cleaning residual artifacts and caches..."
	@rm -rf __pycache__ *.pyc .cache build dist *.pkg.tar.* pkg src
	@sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg
	@if [ -d /usr/local/share/applications ]; then sudo update-desktop-database /usr/local/share/applications; fi
	@echo "==> Clean complete."

aur:
	@echo "==> Regenerating .SRCINFO..."
	@makepkg --printsrcinfo > "$(REPO_DIR)/.SRCINFO"
	@echo "==> .SRCINFO successfully updated!"

push: test aur
	@git add .
	@git status
	@git commit -m "update: automated dev sync" || true
	@git push -u origin main
