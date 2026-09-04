#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Desktop Application Sync & Kickoff Integrator
Generates native KDE Plasma .desktop entries and icons for all Android applications.
"""

import os
import sys
import subprocess
import shutil
from typing import Dict, List, Tuple


KNOWN_APPS = {
    "com.android.vending": {
        "name": "Google Play Store",
        "generic": "Android App Store",
        "categories": "Utility;System;PackageManager;X-WayDroid-App;",
        "icon_fallback": "package-manager"
    },
    "com.google.android.vending": {
        "name": "Google Play Store",
        "generic": "Android App Store",
        "categories": "Utility;System;PackageManager;X-WayDroid-App;",
        "icon_fallback": "package-manager"
    },
    "com.aurora.store": {
        "name": "Aurora Store",
        "generic": "Google Play Client",
        "categories": "Utility;System;PackageManager;X-WayDroid-App;",
        "icon_fallback": "package-manager"
    },
    "org.fdroid.fdroid": {
        "name": "F-Droid",
        "generic": "FOSS Android App Store",
        "categories": "Utility;System;PackageManager;X-WayDroid-App;",
        "icon_fallback": "package-manager"
    },
    "com.android.settings": {
        "name": "Android Settings",
        "generic": "Android System Settings",
        "categories": "Settings;System;X-WayDroid-App;",
        "icon_fallback": "preferences-system"
    },
    "com.android.calculator2": {
        "name": "Android Calculator",
        "generic": "Calculator",
        "categories": "Utility;Calculator;X-WayDroid-App;",
        "icon_fallback": "accessories-calculator"
    },
    "com.android.gallery3d": {
        "name": "Android Gallery",
        "generic": "Photo & Video Gallery",
        "categories": "Graphics;Photography;X-WayDroid-App;",
        "icon_fallback": "view-preview"
    },
    "com.android.deskclock": {
        "name": "Android Clock",
        "generic": "Clock, Alarms & Timer",
        "categories": "Utility;Clock;X-WayDroid-App;",
        "icon_fallback": "clock"
    },
    "com.android.documentsui": {
        "name": "Android Files",
        "generic": "Android File Manager",
        "categories": "System;FileManager;X-WayDroid-App;",
        "icon_fallback": "system-file-manager"
    },
    "org.lineageos.jelly": {
        "name": "Jelly Browser",
        "generic": "Android Web Browser",
        "categories": "Network;WebBrowser;X-WayDroid-App;",
        "icon_fallback": "internet-web-browser"
    },
    "org.lineageos.eleven": {
        "name": "Eleven Music",
        "generic": "Android Music Player",
        "categories": "AudioVideo;Player;Music;X-WayDroid-App;",
        "icon_fallback": "audio-player"
    },
    "org.lineageos.etar": {
        "name": "Etar Calendar",
        "generic": "Android Calendar",
        "categories": "Office;Calendar;X-WayDroid-App;",
        "icon_fallback": "office-calendar"
    },
    "org.lineageos.recorder": {
        "name": "Sound Recorder",
        "generic": "Android Voice Recorder",
        "categories": "AudioVideo;Recorder;X-WayDroid-App;",
        "icon_fallback": "media-record"
    },
    "org.lineageos.aperture": {
        "name": "Camera",
        "generic": "Android Camera",
        "categories": "AudioVideo;Camera;X-WayDroid-App;",
        "icon_fallback": "camera-photo"
    },
    "com.google.android.contacts": {
        "name": "Android Contacts",
        "generic": "Address Book",
        "categories": "Office;ContactManagement;X-WayDroid-App;",
        "icon_fallback": "user-identity"
    }
}


def query_launcher_activities() -> List[str]:
    """
    Queries Android PackageManager inside the container for all launcher activities.
    """
    pkgs = []
    try:
        # If container is in FROZEN state, unfreeze it before querying
        st = subprocess.run(["sudo", "-n", "lxc-info", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "-sH"], capture_output=True, text=True, timeout=1.5)
        if "FROZEN" in st.stdout:
            subprocess.run(["sudo", "-n", "lxc-unfreeze", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid"], capture_output=True, timeout=1.5)

        cmd = [
            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm query-activities -a android.intent.action.MAIN -c android.intent.category.LAUNCHER"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.5)
        for line in res.stdout.split("\n"):
            line = line.strip()
            if line.startswith("packageName="):
                pkg = line.replace("packageName=", "").strip()
                if pkg and pkg not in pkgs:
                    pkgs.append(pkg)
    except Exception:
        pass

    # Also query 3rd party packages
    try:
        cmd_3rd = [
            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm list packages -3"
        ]
        res_3rd = subprocess.run(cmd_3rd, capture_output=True, text=True, timeout=3.5)
        for line in res_3rd.stdout.split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                if pkg and pkg not in pkgs:
                    pkgs.append(pkg)
    except Exception:
        pass

    return pkgs


def query_installed_apps() -> Dict[str, Dict[str, str]]:
    """
    Queries Android PackageManager via Waydroid to retrieve official application labels.
    """
    apps = {}
    waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
    try:
        res = subprocess.run([waydroid_bin, "app", "list"], capture_output=True, text=True, timeout=5)
        current_name = None
        current_pkg = None
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("Name:"):
                current_name = line.replace("Name:", "").strip()
            elif line.startswith("packageName:"):
                current_pkg = line.replace("packageName:", "").strip()
                if current_name and current_pkg:
                    apps[current_pkg] = {
                        "name": current_name,
                        "generic": "Android Application",
                        "categories": "Utility;X-WayDroid-App;",
                        "icon_fallback": "application-x-executable"
                    }
                    current_name = None
                    current_pkg = None
    except Exception:
        pass
    return apps


def sync_android_desktop_entries() -> Tuple[bool, List[str]]:
    """
    Generates rich .desktop launchers in ~/.local/share/applications/ for all detected Android apps
    and configures the main Waydroid launcher with smart incremental change detection.
    """
    home = os.path.expanduser("~")
    apps_dir = os.path.join(home, ".local", "share", "applications")
    icons_dir = os.path.join(home, ".local", "share", "waydroid", "data", "icons")
    os.makedirs(apps_dir, exist_ok=True)

    installed_apps = query_installed_apps()
    launcher_pkgs = query_launcher_activities()
    all_pkgs = set(installed_apps.keys()).union(set(launcher_pkgs)).union(set(KNOWN_APPS.keys()))
    
    expected_files: Dict[str, str] = {}
    generated = []
    has_changes = False

    # 1. Main Waydroid Launcher
    main_content = """[Desktop Entry]
Type=Application
Name=Waydroid Android Subsystem
GenericName=Android Container
Comment=Run Android apps natively on KDE Plasma
Exec=waydroid show-full-ui
Icon=waydroid
Categories=Utility;System;X-WayDroid-App;
Actions=stop;restart;

[Desktop Action stop]
Name=Stop Waydroid Session
Exec=waydroid session stop
Icon=process-stop

[Desktop Action restart]
Name=Restart Android Subsystem
Exec=purr apk session restart
Icon=view-refresh
"""
    expected_files["Waydroid.desktop"] = main_content

    # 2. Build expected content for launchable apps
    for pkg in all_pkgs:
        if pkg.startswith("com.android.internal.") or "overlay" in pkg:
            continue

        known = KNOWN_APPS.get(pkg)
        discovered = installed_apps.get(pkg)
        
        app_name = (discovered.get("name") if discovered else None) or (known.get("name") if known else None)
        if not app_name:
            app_name = pkg.split(".")[-1].capitalize()

        generic_name = (known.get("generic") if known else None) or "Android Application"
        categories = (known.get("categories") if known else None) or "Utility;X-WayDroid-App;"
        icon_fallback = (known.get("icon_fallback") if known else None) or "application-x-executable"

        icon_path = os.path.join(icons_dir, f"{pkg}.png")
        icon_val = icon_path if os.path.exists(icon_path) else icon_fallback

        content = f"""[Desktop Entry]
Type=Application
Name={app_name}
GenericName={generic_name}
Comment=Android application running natively via Waydroid
Exec=purr apk launch {pkg}
Icon={icon_val}
Categories={categories}
StartupWMClass=waydroid.{pkg}
X-Purism-FormFactor=Workstation;Mobile;
NoDisplay=false
Actions=app-settings;

[Desktop Action app-settings]
Name=App Settings
Exec=waydroid app intent android.settings.APPLICATION_DETAILS_SETTINGS package:{pkg}
Icon=preferences-system
"""
        expected_files[f"waydroid.{pkg}.desktop"] = content
        generated.append(f"waydroid.{pkg}.desktop")

    # 3. Incremental deletion of stale files
    if os.path.exists(apps_dir):
        for f in os.listdir(apps_dir):
            if f.startswith("waydroid.") and f.endswith(".desktop"):
                if f not in expected_files:
                    try:
                        os.remove(os.path.join(apps_dir, f))
                        has_changes = True
                    except Exception:
                        pass

    # 4. Incremental write (only when content differs)
    for filename, content in expected_files.items():
        filepath = os.path.join(apps_dir, filename)
        needs_write = True
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    if f.read() == content:
                        needs_write = False
            except Exception:
                pass

        if needs_write:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                has_changes = True
            except Exception:
                pass

    # 5. Rebuild desktop cache ONLY if files were actually added/modified/deleted
    if has_changes:
        try:
            subprocess.run(["update-desktop-database", apps_dir], capture_output=True)
            subprocess.run(["kbuildsycoca6", "--noincremental"], capture_output=True)
        except Exception:
            pass

    return True, generated
