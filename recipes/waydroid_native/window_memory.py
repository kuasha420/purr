#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Android Window Position & Geometry Memory Engine
Tracks Android task bounds via container WindowManager and automatically restores
customized window positions and dimensions across cold launches.
"""

import os
import re
import json
import time
import subprocess
from typing import Dict, Any, Tuple, Optional

BOUNDS_FILE = os.path.expanduser("~/.config/purr/android_window_bounds.json")


def load_all_bounds() -> Dict[str, Dict[str, int]]:
    """
    Loads all saved Android app window bounds from disk.
    """
    if os.path.exists(BOUNDS_FILE):
        try:
            with open(BOUNDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_app_window_rule(app_id_or_pkg: str, x: int, y: int, w: int, h: int) -> bool:
    """
    Saves a persistent KWin window rule for a specific Android application so KDE Plasma 6
    automatically positions and sizes the window on launch.
    """
    if not app_id_or_pkg:
        return False

    # Extract clean package name and wmclass
    pkg = app_id_or_pkg.replace("waydroid.", "").strip()
    if not pkg or pkg.startswith("com.android.systemui") or pkg.startswith("com.android.launcher"):
        return False

    wmclass = f"waydroid.{pkg}"
    section_id = f"waydroid_{pkg.replace('.', '_')}"
    kwinrules_path = os.path.expanduser("~/.config/kwinrulesrc")

    # Safe desktop bounds clamping: y >= 40 prevents titlebar/top-bar occlusion
    safe_x = max(20, int(x))
    safe_y = max(40, int(y))
    safe_w = max(560, int(w))
    safe_h = max(420, int(h))

    try:
        import configparser
        config = configparser.ConfigParser(strict=False, interpolation=None)
        if os.path.exists(kwinrules_path):
            config.read(kwinrules_path)

        if not config.has_section("General"):
            config.add_section("General")

        current_rules = config.get("General", "rules", fallback="").strip()
        rule_list = [r.strip() for r in current_rules.split(",") if r.strip()]

        # Ensure specific rule is ordered before the generic rule '1'
        if section_id not in rule_list:
            if "1" in rule_list:
                rule_list.remove("1")
                rule_list.append(section_id)
                rule_list.append("1")
            else:
                rule_list.append(section_id)
            config.set("General", "rules", ",".join(rule_list))

        if not config.has_section(section_id):
            config.add_section(section_id)

        sec = config[section_id]
        sec.clear()
        sec["description"] = f"Purr Auto-Remembered: {wmclass}"
        sec["wmclass"] = wmclass
        sec["wmclassmatch"] = "1"
        sec["types"] = "1"
        sec["fullscreen"] = "false"
        sec["fullscreenrule"] = "2"
        sec["maximizevert"] = "false"
        sec["maximizevertrule"] = "2"
        sec["maximizehoriz"] = "false"
        sec["maximizehorizrule"] = "2"
        sec["position"] = f"{safe_x},{safe_y}"
        sec["positionrule"] = "3"  # Apply Initially
        sec["size"] = f"{safe_w},{safe_h}"
        sec["sizerule"] = "3"      # Apply Initially
        sec["minsize"] = "560,420"
        sec["minsizerule"] = "2"   # Force minimum safe desktop size

        os.makedirs(os.path.dirname(kwinrules_path), exist_ok=True)
        with open(kwinrules_path, "w", encoding="utf-8") as f:
            config.write(f)

        subprocess.run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], capture_output=True)
        return True
    except Exception:
        return False


def save_pkg_bounds(pkg: str, left: int, top: int, right: int, bottom: int):
    """
    Persists exact (left, top, right, bottom) frame coordinates for an Android package
    and syncs to KWin window rules for permanent geometry memory.
    """
    if not pkg or pkg.startswith("com.android.systemui") or pkg.startswith("com.android.launcher"):
        return
    if right <= left or bottom <= top:
        return

    width = right - left
    height = bottom - top

    # Filter out uncustomized initial default center phone box (e.g. 495x1230 centered at 1479 on ultrawide)
    if width < 520 and 1400 <= left <= 1550:
        return

    # Ensure safe top clearance
    safe_top = max(40, int(top))
    safe_left = max(20, int(left))

    data = load_all_bounds()
    data[pkg] = {
        "left": safe_left,
        "top": safe_top,
        "right": safe_left + width,
        "bottom": safe_top + height,
        "width": int(width),
        "height": int(height)
    }

    try:
        os.makedirs(os.path.dirname(BOUNDS_FILE), exist_ok=True)
        with open(BOUNDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    # Also persist to KWin rule
    save_app_window_rule(pkg, safe_left, safe_top, width, height)


def get_active_android_windows() -> Dict[str, Dict[str, Any]]:
    """
    Queries Android WindowManager inside the LXC container to extract active packages,
    their task IDs, and their exact on-screen frame rectangles.
    """
    try:
        cmd = [
            "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin dumpsys window windows"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode != 0 or not res.stdout:
            return {}

        windows = {}
        current_pkg = None
        current_task = None

        for line in res.stdout.splitlines():
            if "package=" in line:
                m_pkg = re.search(r"package=([\w\.]+)", line)
                if m_pkg:
                    current_pkg = m_pkg.group(1)
            if "rootTaskId=" in line:
                m_task = re.search(r"rootTaskId=(\d+)", line)
                if m_task:
                    current_task = m_task.group(1)
            if "Frames: parent=" in line and "frame=[" in line:
                m_f = re.search(r"frame=\[(\d+),(\d+)\]\[(\d+),(\d+)\]", line)
                if m_f and current_pkg and not current_pkg.startswith("com.android.systemui") and not current_pkg.startswith("com.android.launcher"):
                    left, top, right, bottom = map(int, m_f.groups())
                    if right > left and bottom > top and current_task:
                        windows[current_pkg] = {
                            "taskId": current_task,
                            "left": left,
                            "top": top,
                            "right": right,
                            "bottom": bottom,
                            "width": right - left,
                            "height": bottom - top
                        }
        return windows
    except Exception:
        return {}


def apply_task_bounds(task_id: str, left: int, top: int, right: int, bottom: int) -> bool:
    """
    Resizes and positions an active Android task using the container's activity manager.
    """
    try:
        cmd = [
            "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c",
            f"PATH=/system/bin:/system/xbin cmd activity task resize {task_id} {left} {top} {right} {bottom}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception:
        return False


def restore_app_bounds(pkg: str, max_retries: int = 5, retry_delay: float = 0.3) -> bool:
    """
    Restores the saved window coordinates for a package. Retries briefly to allow cold-started
    apps to finish initial window mapping.
    """
    saved = load_all_bounds().get(pkg)
    if not saved:
        return False

    l, t, r, b = saved["left"], saved["top"], saved["right"], saved["bottom"]

    for _ in range(max_retries):
        active = get_active_android_windows()
        if pkg in active:
            task_id = active[pkg].get("taskId")
            if task_id:
                return apply_task_bounds(task_id, l, t, r, b)
        time.sleep(retry_delay)
    return False
