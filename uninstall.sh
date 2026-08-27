#!/usr/bin/env bash
# 🐾 Purr Complete & Clean Uninstaller (Project Tuki)
# Thoroughly removes all binaries, symlinks, desktop files, icons, completions,
# autostart daemons, and KDE Plasma integrations (Task Manager pinning & Kickoff favorites).

set -e

BOLD='\033[1m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
RED='\033[91m'
RESET='\033[0m'

echo -e "${BOLD}${CYAN}🐾 Starting Complete Purr (Project Tuki) Teardown & Uninstall...${RESET}\n"

# 1. Stop all active background processes
echo -e "${BOLD}[1/7] Stopping active background daemons...${RESET}"
pkill -f "purr-tray" 2>/dev/null || true
pkill -f "smart-install-tray" 2>/dev/null || true
echo -e "  ${GREEN}✔${RESET} Purr background daemons stopped."

# 2. Teardown KDE Plasma Integrations (Kickoff Favorites, Task Manager Pinning, Autostart)
echo -e "\n${BOLD}[2/7] Cleaning KDE Plasma desktop integrations...${RESET}"

# A. Unpin from Task Manager panels via Plasma DBus script
QDBUS_BIN=$(command -v qdbus6 || command -v qdbus || echo "qdbus6")
"$QDBUS_BIN" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
var modified = 0;
for (var i = 0; i < panels().length; i++) {
    var p = panels()[i];
    var widgets = p.widgets();
    for (var j = 0; j < widgets.length; j++) {
        var w = widgets[j];
        if (w.type === 'org.kde.plasma.icontasks' || w.type === 'org.kde.plasma.taskmanager') {
            w.currentConfigGroup = ['General'];
            var raw = w.readConfig('launchers');
            var launchers = [];
            if (typeof raw === 'string') {
                launchers = raw.split(',');
            } else if (raw && raw.length) {
                launchers = Array.prototype.slice.call(raw);
            }
            launchers = launchers.filter(function(x) {
                return x !== 'applications:purr.desktop' && x !== 'applications:smart-install.desktop';
            });
            w.writeConfig('launchers', launchers);
            w.reloadConfig();
            modified++;
        }
    }
}
" 2>/dev/null || true

# B. Remove from Kickoff Favorites (Config file + SQLite DB)
PYTHON_BIN=$(command -v /usr/bin/python3 || command -v python3 || echo "python3")
KSTATS_FILE="${HOME}/.config/kactivitymanagerd-statsrc"
if [ -f "$KSTATS_FILE" ]; then
    "$PYTHON_BIN" -c "
import os
kstats = os.path.expanduser('~/.config/kactivitymanagerd-statsrc')
if os.path.exists(kstats):
    with open(kstats, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    new_lines = []
    in_fav = False
    for line in lines:
        if line.startswith('[Favorites-'):
            in_fav = True
            new_lines.append(line)
        elif line.startswith('['):
            in_fav = False
            new_lines.append(line)
        elif in_fav and line.startswith('ordering='):
            parts = [p.strip() for p in line.replace('ordering=', '').split(',') if p.strip()]
            parts = [p for p in parts if p not in ['applications:purr.desktop', 'applications:smart-install.desktop']]
            new_lines.append('ordering=' + ','.join(parts))
        else:
            new_lines.append(line)
    with open(kstats, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
" 2>/dev/null || true
fi

# SQLite ResourceLink cleanup
KACT_DB="${HOME}/.local/share/kactivitymanagerd/resources/database"
if [ -f "$KACT_DB" ]; then
    "$PYTHON_BIN" -c "
import sqlite3, os
db = os.path.expanduser('~/.local/share/kactivitymanagerd/resources/database')
if os.path.exists(db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(\"DELETE FROM ResourceLink WHERE targettedResource IN ('applications:purr.desktop', 'applications:smart-install.desktop');\")
        cur.execute(\"DELETE FROM ResourceScoreCache WHERE targettedResource IN ('applications:purr.desktop', 'applications:smart-install.desktop');\")
        conn.commit()
        conn.close()
    except Exception:
        pass
" 2>/dev/null || true
fi

systemctl --user restart plasma-kactivitymanagerd.service 2>/dev/null || true

# C. Remove Autostart files
rm -f "${HOME}/.config/autostart/purr-tray.desktop"
rm -f "${HOME}/.config/autostart/smart-install-tray.desktop"
echo -e "  ${GREEN}✔${RESET} Plasma Task Manager, Kickoff favorites, and Autostart entries purged."

# 3. Remove all Binaries & Symlinks
echo -e "\n${BOLD}[3/7] Removing installed binaries & command symlinks...${RESET}"
sudo rm -f /usr/local/bin/purr \
           /usr/local/bin/purr-tray \
           /usr/local/bin/purr-integrate \
           /usr/local/bin/tuki \
           /usr/local/bin/purr-install \
           /usr/local/bin/purr-universal-app-engine \
           /usr/local/bin/smart-install \
           /usr/local/bin/app-install \
           /usr/bin/purr \
           /usr/bin/purr-tray \
           /usr/bin/purr-integrate \
           /usr/bin/tuki

rm -f "${HOME}/.local/bin/purr" \
      "${HOME}/.local/bin/purr-tray" \
      "${HOME}/.local/bin/purr-integrate" \
      "${HOME}/.local/bin/tuki" \
      "${HOME}/.local/bin/smart-install"
echo -e "  ${GREEN}✔${RESET} All system and user binary paths cleared."

# 4. Remove Desktop Menu Entries
echo -e "\n${BOLD}[4/7] Removing application menu desktop entries...${RESET}"
sudo rm -f /usr/local/share/applications/purr.desktop \
           /usr/local/share/applications/purr-tray.desktop \
           /usr/local/share/applications/smart-install.desktop \
           /usr/share/applications/purr.desktop \
           /usr/share/applications/purr-tray.desktop \
           /usr/share/applications/smart-install.desktop

rm -f "${HOME}/.local/share/applications/purr.desktop" \
      "${HOME}/.local/share/applications/purr-tray.desktop" \
      "${HOME}/.local/share/applications/smart-install.desktop"
echo -e "  ${GREEN}✔${RESET} All desktop application entries removed."

# 5. Remove Icons across all resolutions
echo -e "\n${BOLD}[5/7] Removing scalable vector and multi-resolution raster icons...${RESET}"
sudo rm -f /usr/local/share/icons/hicolor/scalable/apps/purr.svg \
           /usr/local/share/icons/hicolor/scalable/apps/smart-install.svg \
           /usr/share/icons/hicolor/scalable/apps/purr.svg \
           /usr/share/icons/hicolor/scalable/apps/smart-install.svg \
           /usr/share/pixmaps/purr.* \
           /usr/share/pixmaps/smart-install.* \
           /usr/local/share/pixmaps/purr.*

for size in 16x16 22x22 32x32 48x48 64x64 128x128 256x256 512x512; do
    sudo rm -f "/usr/share/icons/hicolor/${size}/apps/purr.png" \
               "/usr/share/icons/hicolor/${size}/apps/smart-install.png" \
               "/usr/local/share/icons/hicolor/${size}/apps/purr.png" 2>/dev/null || true
    rm -f "${HOME}/.local/share/icons/hicolor/${size}/apps/purr.png" \
          "${HOME}/.local/share/icons/hicolor/${size}/apps/smart-install.png" 2>/dev/null || true
done

rm -f "${HOME}/.local/share/icons/hicolor/scalable/apps/purr.svg" \
      "${HOME}/.local/share/icons/hicolor/scalable/apps/smart-install.svg"
echo -e "  ${GREEN}✔${RESET} All icons removed cleanly across system and user themes."

# 6. Remove Shell Auto-completions
echo -e "\n${BOLD}[6/7] Removing shell auto-completions...${RESET}"
sudo rm -f /usr/share/bash-completion/completions/purr \
           /usr/share/bash-completion/completions/tuki \
           /usr/share/bash-completion/completions/smart-install \
           /usr/share/zsh/site-functions/_purr \
           /usr/share/zsh/site-functions/_smart-install

rm -f "${HOME}/.local/share/bash-completion/completions/purr" \
      "${HOME}/.local/share/zsh/site-functions/_purr"
echo -e "  ${GREEN}✔${RESET} Bash and Zsh completions removed."

# 7. Rebuild System & Desktop Caches
echo -e "\n${BOLD}[7/7] Rebuilding icon databases and desktop caches...${RESET}"
sudo update-desktop-database /usr/share/applications 2>/dev/null || true
sudo update-desktop-database /usr/local/share/applications 2>/dev/null || true
update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true

sudo gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
sudo gtk-update-icon-cache -q -t -f /usr/local/share/icons/hicolor 2>/dev/null || true
gtk-update-icon-cache -q -t -f "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true

kbuildsycoca6 --noincremental 2>/dev/null || true
echo -e "  ${GREEN}✔${RESET} All system caches rebuilt."

echo -e "\n${BOLD}${GREEN}================================================================================${RESET}"
echo -e "${BOLD}${GREEN}  [✔] Purr (Project Tuki) has been completely and cleanly uninstalled!        ${RESET}"
echo -e "${BOLD}${GREEN}================================================================================${RESET}\n"
