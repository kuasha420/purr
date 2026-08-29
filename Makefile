.PHONY: all dev install uninstall test clean aur push integrate help

SHELL := /bin/bash
REPO_DIR := $(shell pwd)

help:
	@echo "🐾 Purr (Project Tuki) Developer Management"
	@echo ""
	@echo "Targets:"
	@echo "  make dev          - Link repository live to /usr/local/bin for instant development"
	@echo "  make install      - Install production copy to system"
	@echo "  make integrate    - Enable all KDE Plasma desktop integrations (Favorites, Task Manager, Tray, Autostart)"
	@echo "  make test         - Run syntax validation and dry-run tests"
	@echo "  make clean        - Clean build caches and temporary files"
	@echo "  make aur          - Validate PKGBUILD and update .SRCINFO"
	@echo "  make push         - Commit all changes and push to GitHub"

dev:
	@$(REPO_DIR)/install.sh --dev
	@$(REPO_DIR)/bin/purr-integrate --restart-tray

reload-tray:
	@$(REPO_DIR)/bin/purr-integrate --restart-tray

install:
	@$(REPO_DIR)/install.sh

uninstall:
	@$(REPO_DIR)/uninstall.sh

integrate:
	@$(REPO_DIR)/bin/purr-integrate --all

test:
	@echo "==> Running syntax checks..."
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/bin/purr
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/bin/purr-tray
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/bin/purr-integrate
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/base.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/manager.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/recipe.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/system_tuning.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/kwin_rules.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/fileshare.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/desktop_sync.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/window_memory.py
	@/usr/bin/python3 -m py_compile $(REPO_DIR)/recipes/waydroid_native/aurora_patcher.py
	@echo "==> Testing CLI help and version..."
	@$(REPO_DIR)/bin/purr --version
	@$(REPO_DIR)/bin/purr --help > /dev/null
	@/usr/bin/python3 $(REPO_DIR)/bin/purr-tray --help > /dev/null
	@/usr/bin/python3 $(REPO_DIR)/bin/purr-integrate --help > /dev/null
	@echo "==> Testing Purr Recipes registry..."
	@$(REPO_DIR)/bin/purr recipe list > /dev/null
	@echo "==> Testing Aurora Store patcher profile validation..."
	@/usr/bin/python3 -c "import sys; sys.path.insert(0, '$(REPO_DIR)'); from recipes.waydroid_native.aurora_patcher import PURR_DEVICE_MAP; assert len(PURR_DEVICE_MAP) >= 10; print(f'Aurora patcher verified with {len(PURR_DEVICE_MAP)} curated profiles.')"
	@echo "==> Testing KDE Plasma integration status..."
	@$(REPO_DIR)/bin/purr integrate --status
	@echo "==> 🐾 All tests passed cleanly!"

clean:
	@echo "==> Cleaning residual artifacts and caches..."
	@rm -rf __pycache__ *.pyc .cache build dist *.pkg.tar.* pkg src
	@sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg
	@sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
	@echo "==> Clean complete."

aur:
	@echo "==> Regenerating .SRCINFO..."
	@makepkg --printsrcinfo > $(REPO_DIR)/.SRCINFO
	@echo "==> .SRCINFO successfully updated!"

push: test aur
	@git add .
	@git status
	@git commit -m "update: automated dev sync" || true
	@git push -u origin main
