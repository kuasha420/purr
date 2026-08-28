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
        cmd = [
            "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm query-activities -a android.intent.action.MAIN -c android.intent.category.LAUNCHER"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
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
            "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm list packages -3"
        ]
        res_3rd = subprocess.run(cmd_3rd, capture_output=True, text=True)
        for line in res_3rd.stdout.split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                if pkg and pkg not in pkgs:
                    pkgs.append(pkg)
    except Exception:
        pass

    return pkgs


def sync_android_desktop_entries() -> Tuple[bool, List[str]]:
    """
    Generates rich .desktop launchers in ~/.local/share/applications/ for all detected Android apps
    and configures the main Waydroid launcher.
    """
    home = os.path.expanduser("~")
    apps_dir = os.path.join(home, ".local", "share", "applications")
    icons_dir = os.path.join(home, ".local", "share", "waydroid", "data", "icons")
    os.makedirs(apps_dir, exist_ok=True)

    # 1. Clean stale waydroid desktop files
    if os.path.exists(apps_dir):
        for f in os.listdir(apps_dir):
            if f.startswith("waydroid.") and f.endswith(".desktop"):
                try:
                    os.remove(os.path.join(apps_dir, f))
                except Exception:
                    pass

    launcher_pkgs = query_launcher_activities()
    candidate_pkgs = set(launcher_pkgs) if launcher_pkgs else set(KNOWN_APPS.keys())
    generated = []

    # 2. Generate/Fix Main Waydroid Launcher
    main_desktop = os.path.join(apps_dir, "Waydroid.desktop")
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
    try:
        with open(main_desktop, "w") as f:
            f.write(main_content)
        generated.append("Waydroid.desktop")
    except Exception:
        pass

    # 3. Generate entries for launchable apps
    for pkg in candidate_pkgs:
        meta = KNOWN_APPS.get(pkg)
        if not meta and not pkg.startswith("com.android.internal.") and not "overlay" in pkg:
            # User installed third-party app
            friendly_name = pkg.split(".")[-1].capitalize()
            meta = {
                "name": f"{friendly_name} (Android)",
                "generic": "Android Application",
                "categories": "Utility;X-WayDroid-App;",
                "icon_fallback": "application-x-executable"
            }

        if not meta:
            continue

        desktop_file = os.path.join(apps_dir, f"waydroid.{pkg}.desktop")
        icon_path = os.path.join(icons_dir, f"{pkg}.png")
        icon_val = icon_path if os.path.exists(icon_path) else meta["icon_fallback"]

        content = f"""[Desktop Entry]
Type=Application
Name={meta['name']}
GenericName={meta.get('generic', 'Android App')}
Comment=Android application running natively via Waydroid
Exec=purr apk launch {pkg}
Icon={icon_val}
Categories={meta['categories']}
StartupWMClass=waydroid.{pkg}
X-Purism-FormFactor=Workstation;Mobile;
NoDisplay=false
Actions=app-settings;

[Desktop Action app-settings]
Name=App Settings
Exec=waydroid app intent android.settings.APPLICATION_DETAILS_SETTINGS package:{pkg}
Icon=preferences-system
"""
        try:
            with open(desktop_file, "w") as f:
                f.write(content)
            generated.append(f"waydroid.{pkg}.desktop")
        except Exception:
            pass

    # 4. Update desktop and MIME databases
    try:
        subprocess.run(["update-desktop-database", apps_dir], capture_output=True)
        subprocess.run(["kbuildsycoca6", "--noincremental"], capture_output=True)
    except Exception:
        pass

    return True, generated
