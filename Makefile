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

install:
	@$(REPO_DIR)/install.sh

integrate:
	@$(REPO_DIR)/bin/purr-integrate --all

test:
	@echo "==> Running syntax checks..."
	@python3 -m py_compile $(REPO_DIR)/bin/purr
	@python3 -m py_compile $(REPO_DIR)/bin/purr-tray
	@python3 -m py_compile $(REPO_DIR)/bin/purr-integrate
	@echo "==> Testing CLI help and version..."
	@$(REPO_DIR)/bin/purr --version
	@$(REPO_DIR)/bin/purr --help > /dev/null
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
