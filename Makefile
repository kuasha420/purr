.PHONY: all dev install uninstall test clean aur push help

SHELL := /bin/bash
REPO_DIR := $(shell pwd)

help:
	@echo "🐾 Purr (Project Tuki) Developer Management"
	@echo ""
	@echo "Targets:"
	@echo "  make dev       - Link repository live to /usr/local/bin for instant development"
	@echo "  make install   - Install production copy to system"
	@echo "  make uninstall - Cleanly remove purr from system"
	@echo "  make test      - Run syntax validation and dry-run tests"
	@echo "  make clean     - Clean build caches and temporary files"
	@echo "  make aur       - Validate PKGBUILD and update .SRCINFO"
	@echo "  make push      - Commit all changes and push to GitHub"

dev:
	@echo "==> 🐾 Linking live development instance to /usr/local/bin..."
	@sudo rm -f /usr/local/bin/purr /usr/local/bin/tuki /usr/local/bin/purr-install /usr/local/bin/purr-universal-app-engine /usr/local/bin/smart-install /usr/local/bin/app-install
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/purr
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/tuki
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/purr-install
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/purr-universal-app-engine
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/smart-install
	@sudo ln -sf $(REPO_DIR)/bin/purr /usr/local/bin/app-install
	@sudo install -Dm644 $(REPO_DIR)/data/purr.desktop /usr/local/share/applications/purr.desktop
	@sudo install -Dm644 $(REPO_DIR)/data/icons/purr.svg /usr/local/share/icons/hicolor/scalable/apps/purr.svg
	@sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg
	@if [ -d "/usr/share/bash-completion/completions" ]; then sudo ln -sf $(REPO_DIR)/completions/purr.bash /usr/share/bash-completion/completions/purr; fi
	@if [ -d "/usr/share/zsh/site-functions" ]; then sudo ln -sf $(REPO_DIR)/completions/_purr.zsh /usr/share/zsh/site-functions/_purr; fi
	@sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
	@sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true
	@echo "==> 🐾 Live Development Mode Active! Any edits in $(REPO_DIR)/bin/purr are instantly live."

install:
	@$(REPO_DIR)/install.sh

uninstall:
	@$(REPO_DIR)/uninstall.sh

test:
	@echo "==> Running syntax check..."
	@python3 -m py_compile $(REPO_DIR)/bin/purr
	@echo "==> Testing CLI help and version..."
	@$(REPO_DIR)/bin/purr --version
	@$(REPO_DIR)/bin/purr --help > /dev/null
	@echo "==> Testing dry-run heuristic discovery on 'google chrome'..."
	@$(REPO_DIR)/bin/purr --dry-run "google chrome" <<< "1" > /dev/null
	@echo "==> 🐾 All tests passed cleanly!"

clean:
	@echo "==> Cleaning residual artifacts and caches..."
	@rm -rf __pycache__ *.pyc .cache build dist *.pkg.tar.* pkg src
	@sudo rm -f /usr/local/share/applications/smart-install.desktop /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg
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
