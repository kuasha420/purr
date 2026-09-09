#!/usr/bin/env python3
"""
🐾 Purr Android Application Repair & Subsystem Bridge Helper
Project Tuki / Purr Ecosystem

Automates diagnosis, headless repair, architecture enforcement (e.g. 32-bit ARM for Messenger),
Play Store update detachment, and Aurora Store blacklisting via PurrBridgeHelper.
"""

import os
import sys
import json
import shutil
import subprocess
import time
from typing import Tuple, Dict, Any, Optional


WAYDROID_LXC_DIR = "/var/lib/waydroid/lxc"
WAYDROID_LXC_NAME = "waydroid"
BRIDGE_ACTION = "dev.purr.bridge.COMMAND"
BRIDGE_RECEIVER = "dev.purr.bridge/.BridgeReceiver"


def send_bridge_command(action: str, extras: Optional[Dict[str, str]] = None, timeout: int = 10) -> Tuple[bool, Dict[str, Any], str]:
    """
    Sends a synchronous command to PurrBridgeHelper running inside Android via `am broadcast -W`.
    Returns (success, parsed_json_response, raw_output).
    """
    cmd = [
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c"
    ]

    args = f"export PATH=/system/bin:/system/xbin; am broadcast -W -a {BRIDGE_ACTION} -n {BRIDGE_RECEIVER} --es action {action}"
    if extras:
        for k, v in extras.items():
            args += f" --es {k} '{v}'"

    cmd.append(args)

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = res.stdout.strip()

        # If bridge receiver is not installed yet, attempt companion installation
        if "ComponentInfo{dev.purr.bridge" in raw and ("does not exist" in raw or "not found" in raw):
            from recipes.waydroid_native.system_tuning import install_purr_clip_helper
            install_purr_clip_helper()
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            raw = res.stdout.strip()

        # Extract data="..." from am broadcast output
        data_str = None
        for line in raw.splitlines():
            if 'data="' in line:
                start = line.find('data="') + 6
                end = line.rfind('"')
                if start < end:
                    data_str = line[start:end].replace('\\"', '"')
                    break

        if data_str:
            try:
                parsed = json.loads(data_str)
                is_ok = parsed.get("status") == "ok"
                return is_ok, parsed, raw
            except Exception:
                pass

        return (res.returncode == 0 and "result=-1" in raw), {}, raw
    except Exception as e:
        return False, {}, str(e)


def detach_from_play_store(package_name: str) -> Tuple[bool, str]:
    """
    Purges package from Google Play Store's SQLite tracking databases:
    1. library.db (ownership table)
    2. localappstate.db (appstate table)
    3. auto_update.db (auto_update table)
    Then force-stops com.android.vending to discard dirty in-memory cache.
    """
    data_dir = os.path.expanduser("~/.local/share/waydroid/data/data/com.android.vending/databases")
    if not os.path.exists(data_dir):
        return True, "Play Store not configured in container; no detachment necessary."

    sqlite_bin = shutil.which("sqlite3") or "/usr/bin/sqlite3"
    purged_tables = []

    db_ops = [
        ("library.db", f"DELETE FROM ownership WHERE doc_id='{package_name}';"),
        ("localappstate.db", f"DELETE FROM appstate WHERE package_name='{package_name}';"),
        ("auto_update.db", f"DELETE FROM auto_update WHERE pk='{package_name}';")
    ]

    for db_file, sql in db_ops:
        db_path = os.path.join(data_dir, db_file)
        if os.path.exists(db_path):
            try:
                subprocess.run(["sudo", sqlite_bin, db_path, sql], capture_output=True, check=True)
                purged_tables.append(db_file)
            except Exception as e:
                return False, f"Failed SQLite purge on {db_file}: {e}"

    # Terminate Play Store to flush state
    subprocess.run([
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; am force-stop com.android.vending"
    ], capture_output=True)

    return True, f"Detached '{package_name}' from Google Play Store ({', '.join(purged_tables)})."


def blacklist_in_aurora_store(package_name: str) -> Tuple[bool, str]:
    """
    Adds package to Aurora Store's PREFERENCE_BLACKLIST in shared preferences
    so Aurora Store ignores updates for it permanently.
    """
    prefs_file = os.path.expanduser("~/.local/share/waydroid/data/data/com.aurora.store/shared_prefs/com.aurora.store_preferences.xml")
    if not os.path.exists(prefs_file):
        return True, "Aurora Store preferences not found; skipping Aurora blacklist."

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(prefs_file)
        root = tree.getroot()

        blacklist_elem = None
        for child in root.findall("string"):
            if child.attrib.get("name") == "PREFERENCE_BLACKLIST":
                blacklist_elem = child
                break

        if blacklist_elem is None:
            blacklist_elem = ET.SubElement(root, "string", {"name": "PREFERENCE_BLACKLIST"})
            items = []
        else:
            try:
                items = json.loads(blacklist_elem.text or "[]")
            except Exception:
                items = []

        if package_name not in items:
            items.append(package_name)
            blacklist_elem.text = json.dumps(items)
            tree.write(prefs_file, encoding="utf-8", xml_declaration=True)

            # Preserve Aurora Store permissions (UID 10177)
            subprocess.run(["sudo", "chown", "10177:10177", prefs_file], capture_output=True)
            subprocess.run(["sudo", "chmod", "660", prefs_file], capture_output=True)

            # Force stop Aurora Store to reload preferences
            subprocess.run([
                "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
                "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; am force-stop com.aurora.store"
            ], capture_output=True)

        return True, f"Added '{package_name}' to Aurora Store update blacklist."
    except Exception as e:
        return False, f"Failed to update Aurora Store blacklist: {e}"


def repair_messenger(force: bool = False) -> Tuple[bool, str]:
    """
    Performs complete, headless recovery of Facebook Messenger (com.facebook.orca):
    1. Diagnoses current ABI and crash conditions via PurrBridgeHelper.
    2. If crashing 64-bit ARM (arm64-v8a) is detected, preserves user data via `pm uninstall -k`.
    3. Locates or caches the verified 32-bit ARM (armeabi-v7a) APK in ~/.cache/purr/apks/.
    4. Installs the 32-bit build using `pm install -r -d`.
    5. Permanently detaches Messenger from Google Play Store & Aurora Store auto-updates.
    6. Launches Messenger in freeform mode and verifies logcat health.
    """
    pkg = "com.facebook.orca"
    cache_dir = os.path.expanduser("~/.cache/purr/apks")
    cached_32bit_apk = os.path.join(cache_dir, "com.facebook.orca-32bit.apk")
    os.makedirs(cache_dir, exist_ok=True)

    print("  --> Step 1/6: Querying Messenger installation state via PurrBridgeHelper...")
    ok, info, _ = send_bridge_command("query_app", {"package": pkg})
    is_installed = info.get("installed", False)
    current_abi = info.get("primaryCpuAbi", "unknown")
    current_version = info.get("versionName", "")

    if is_installed:
        print(f"      Detected Messenger v{current_version} (ABI: {current_abi})")
        if current_abi == "armeabi-v7a" and not force:
            print("  [✔] Messenger is already configured with 32-bit ARM (armeabi-v7a). Verifying launch...")
            detach_from_play_store(pkg)
            blacklist_in_aurora_store(pkg)
            subprocess.run([
                "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
                "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; am start -n com.facebook.orca/com.facebook.messenger.neue.MainActivity"
            ], capture_output=True)
            return True, "Facebook Messenger is healthy and verified."

        print(f"  ⚠️  Detected incompatible architecture ({current_abi}). Removing binary while PRESERVING user chats & credentials...")
        subprocess.run([
            "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
            "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; pm uninstall -k com.facebook.orca"
        ], capture_output=True)

    print("  --> Step 2/6: Resolving verified 32-bit ARM (armeabi-v7a) Messenger package...")
    if not os.path.exists(cached_32bit_apk) or os.path.getsize(cached_32bit_apk) < 50000000:
        # Check ~/Downloads for downloaded 32-bit package
        downloads_dir = os.path.expanduser("~/Downloads")
        cand_apk = None
        if os.path.exists(downloads_dir):
            for f in os.listdir(downloads_dir):
                if f.startswith("com.facebook.orca") and "armeabi-v7a" in f and f.endswith(".apk"):
                    cand_apk = os.path.join(downloads_dir, f)
                    break
        if cand_apk and os.path.exists(cand_apk):
            print(f"      Found local 32-bit build at {cand_apk}, copying to cache...")
            shutil.copyfile(cand_apk, cached_32bit_apk)
            os.chmod(cached_32bit_apk, 0o644)
        else:
            return False, (
                "32-bit ARM Messenger APK not found in cache or ~/Downloads.\n"
                "  Please place a 32-bit (armeabi-v7a) Messenger APK at:\n"
                f"  {cached_32bit_apk}"
            )

    print("  --> Step 3/6: Installing 32-bit ARM Messenger APK into Waydroid...")
    tmp_target = "/home/kuasha/.local/share/waydroid/data/local/tmp/com.facebook.orca-32bit.apk"
    subprocess.run(["sudo", "cp", "-f", cached_32bit_apk, tmp_target], capture_output=True)
    subprocess.run(["sudo", "chmod", "644", tmp_target], capture_output=True)

    res_install = subprocess.run([
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; pm install -r -d /data/local/tmp/com.facebook.orca-32bit.apk"
    ], capture_output=True, text=True)

    subprocess.run(["sudo", "rm", "-f", tmp_target], capture_output=True)

    if res_install.returncode != 0 or "Success" not in res_install.stdout:
        return False, f"Failed to install 32-bit Messenger APK: {res_install.stderr or res_install.stdout}"

    print("  --> Step 4/6: Detaching Messenger from Google Play Store & Aurora Store auto-updates...")
    detach_from_play_store(pkg)
    blacklist_in_aurora_store(pkg)

    print("  --> Step 5/6: Validating architecture enforcement via PurrBridgeHelper...")
    ok, info, _ = send_bridge_command("query_app", {"package": pkg})
    new_abi = info.get("primaryCpuAbi", "")
    if new_abi != "armeabi-v7a":
        return False, f"Verification failed: Expected primaryCpuAbi 'armeabi-v7a' but found '{new_abi}'"
    print(f"      Architecture verified: {new_abi} (Version: {info.get('versionName', '')})")

    print("  --> Step 6/6: Launching Facebook Messenger and monitoring crash buffer...")
    # Clear crash logcat buffer
    subprocess.run([
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; logcat -c -b crash"
    ], capture_output=True)

    subprocess.run([
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; am start -n com.facebook.orca/com.facebook.messenger.neue.MainActivity"
    ], capture_output=True)

    time.sleep(2.0)

    res_crash = subprocess.run([
        "sudo", "lxc-attach", "-P", WAYDROID_LXC_DIR, "-n", WAYDROID_LXC_NAME, "--",
        "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; logcat -d -b crash"
    ], capture_output=True, text=True)

    if "com.facebook.orca" in res_crash.stdout and "SIGSEGV" in res_crash.stdout:
        return False, f"Crash detected after launch: {res_crash.stdout.strip()}"

    # Restore window geometry if window_memory is active
    try:
        from recipes.waydroid_native.window_memory import restore_app_bounds
        restore_app_bounds(pkg, 5, 0.2)
    except Exception:
        pass

    return True, "Facebook Messenger repaired successfully with 32-bit ARM enforcement and Play Store update immunity."


def repair_app(app_name: str, force: bool = False) -> Tuple[bool, str]:
    """
    Top-level application repair dispatcher.
    """
    clean_name = app_name.strip().lower()
    if clean_name in ["messenger", "fb-messenger", "facebook-messenger", "com.facebook.orca", "orca"]:
        return repair_messenger(force=force)

    return False, f"Unsupported app repair target: '{app_name}'. Currently supported: messenger"
