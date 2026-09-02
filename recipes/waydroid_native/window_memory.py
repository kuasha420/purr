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


def get_screen_info() -> Tuple[int, int, float]:
    """
    Returns (logical_width, logical_height, scale_factor) for the active display.
    """
    screen_w, screen_h = 1920, 1080
    scale = 1.0
    try:
        res = subprocess.run(["kscreen-doctor", "-o"], capture_output=True, text=True, timeout=2)
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout)
        for line in clean_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("Geometry:"):
                parts = line_str.split()
                for p in parts:
                    if "x" in p and p[0].isdigit() and p[-1].isdigit():
                        sw, sh = p.split("x", 1)
                        screen_w, screen_h = int(sw), int(sh)
                        break
            elif line_str.startswith("Scale:"):
                parts = line_str.split()
                if len(parts) >= 2:
                    try:
                        scale = float(parts[1])
                    except ValueError:
                        pass
    except Exception:
        pass
    return screen_w, screen_h, max(1.0, scale)


def clean_oversized_kwin_rules() -> int:
    """
    Sanitizes kwinrulesrc by removing legacy unscaled or oversized per-app Waydroid rules
    that exceed the logical display geometry and cause off-screen window placement.
    """
    kwinrules_path = os.path.expanduser("~/.config/kwinrulesrc")
    if not os.path.exists(kwinrules_path):
        return 0

    screen_w, screen_h, _ = get_screen_info()
    removed_count = 0

    try:
        import configparser
        config = configparser.ConfigParser(strict=False, interpolation=None)
        config.read(kwinrules_path)

        if not config.has_section("General"):
            return 0

        current_rules = config.get("General", "rules", fallback="").strip()
        rule_list = [r.strip() for r in current_rules.split(",") if r.strip()]
        new_rule_list = list(rule_list)

        for sec_id in list(config.sections()):
            if sec_id == "waydroid_com_android_inputmethod_latin":
                config.remove_section(sec_id)
                if sec_id in new_rule_list:
                    new_rule_list.remove(sec_id)
                removed_count += 1
                continue

            if sec_id.startswith("waydroid_") and sec_id not in ("waydroid_com_android_settings", "waydroid_hide_inputmethod"):
                sec = config[sec_id]
                size_str = sec.get("size", "")
                pos_str = sec.get("position", "")

                should_remove = False
                w, h = 0, 0
                if size_str and "," in size_str:
                    try:
                        w, h = map(int, size_str.split(",", 1))
                        # If width/height exceeds logical screen bounds
                        if w > (screen_w - 40) or h > (screen_h - 40):
                            should_remove = True
                    except Exception:
                        pass

                if pos_str and "," in pos_str:
                    try:
                        x, y = map(int, pos_str.split(",", 1))
                        if x >= screen_w or y >= screen_h or (w > 0 and (x + w) > screen_w) or (h > 0 and (y + h) > screen_h):
                            should_remove = True
                    except Exception:
                        pass

                if should_remove:
                    config.remove_section(sec_id)
                    if sec_id in new_rule_list:
                        new_rule_list.remove(sec_id)
                    removed_count += 1
                else:
                    if sec.get("noborder", "").lower() != "true" or sec.get("decormode", "") != "2" or sec.get("above", "").lower() != "false":
                        sec["noborder"] = "true"
                        sec["noborderrule"] = "2"
                        sec["decormode"] = "2"
                        sec["decormoderule"] = "2"
                        sec["above"] = "false"
                        sec["aboverule"] = "2"
                        sec["below"] = "false"
                        sec["belowrule"] = "2"
                        removed_count += 1

        # Ensure Waydroid master rule has seamless borderless configuration only if it actually belongs to Waydroid
        for master_id in ["1", "waydroid_master"]:
            if config.has_section(master_id):
                wmclass = config.get(master_id, "wmclass", fallback="").lower()
                desc = config.get(master_id, "description", fallback="").lower()
                if "waydroid" in wmclass or "waydroid" in desc:
                    if (config.get(master_id, "noborder", fallback="").lower() != "true" or
                            config.get(master_id, "decormode", fallback="") != "2" or
                            config.get(master_id, "above", fallback="").lower() != "false"):
                        config.set(master_id, "noborder", "true")
                        config.set(master_id, "noborderrule", "2")
                        config.set(master_id, "decormode", "2")
                        config.set(master_id, "decormoderule", "2")
                        config.set(master_id, "above", "false")
                        config.set(master_id, "aboverule", "2")
                        config.set(master_id, "below", "false")
                        config.set(master_id, "belowrule", "2")
                        removed_count += 1

        if removed_count > 0:
            config.set("General", "rules", ",".join(new_rule_list))
            with open(kwinrules_path, "w", encoding="utf-8") as f:
                config.write(f)
            subprocess.run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], capture_output=True)

    except Exception:
        pass

    return removed_count


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
    Saves a persistent, scale-aware KWin window rule for a specific Android application so
    KDE Plasma 6 automatically positions and sizes the window safely on launch.
    """
    if not app_id_or_pkg:
        return False

    # Extract clean package name and wmclass
    pkg = app_id_or_pkg.replace("waydroid.", "").strip()
    if not pkg or pkg.startswith("com.android.systemui") or pkg.startswith("com.android.launcher") or pkg.startswith("com.android.inputmethod"):
        return False

    screen_w, screen_h, scale = get_screen_info()

    # Convert physical coordinates (from Android WindowManager) to logical desktop coordinates
    log_w = int(round(w / scale))
    log_h = int(round(h / scale))
    log_x = int(round(x / scale))
    log_y = int(round(y / scale))

    phys_screen_w = int(round(screen_w * scale))
    phys_screen_h = int(round(screen_h * scale))

    # If the app is maximized / fullscreen in Android, do not create a rigid floating window rule
    if w >= (phys_screen_w - 60) or h >= (phys_screen_h - 100):
        return False

    # Clamp safely inside logical desktop boundaries
    safe_w = max(400, min(log_w, screen_w - 40))
    safe_h = max(300, min(log_h, screen_h - 70))
    safe_x = max(20, min(log_x, max(20, screen_w - safe_w - 20)))
    safe_y = max(35, min(log_y, max(35, screen_h - safe_h - 45)))

    wmclass = f"waydroid.{pkg}"
    section_id = f"waydroid_{pkg.replace('.', '_')}"
    kwinrules_path = os.path.expanduser("~/.config/kwinrulesrc")

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
        sec["fullscreenrule"] = "3"  # Apply Initially
        sec["maximizevert"] = "false"
        sec["maximizevertrule"] = "3"  # Apply Initially
        sec["maximizehoriz"] = "false"
        sec["maximizehorizrule"] = "3"  # Apply Initially
        sec["position"] = f"{safe_x},{safe_y}"
        sec["positionrule"] = "3"  # Apply Initially
        sec["size"] = f"{safe_w},{safe_h}"
        sec["sizerule"] = "3"      # Apply Initially
        sec["minsize"] = "400,300"
        sec["minsizerule"] = "2"   # Force minimum safe desktop size
        sec["noborder"] = "true"
        sec["noborderrule"] = "2"
        sec["decormode"] = "2"
        sec["decormoderule"] = "2"
        sec["above"] = "false"
        sec["aboverule"] = "2"
        sec["below"] = "false"
        sec["belowrule"] = "2"

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
    try:
        from recipes.waydroid_native.system_tuning import get_waydroid_prop
        if get_waydroid_prop("persist.waydroid.multi_windows", "true").lower() != "true":
            return
    except Exception:
        pass

    if not pkg or pkg.startswith("com.android.systemui") or pkg.startswith("com.android.launcher") or pkg.startswith("com.android.inputmethod"):
        return
    if right <= left or bottom <= top:
        return

    width = right - left
    height = bottom - top

    screen_w, screen_h, scale = get_screen_info()
    phys_screen_w = int(round(screen_w * scale))
    phys_screen_h = int(round(screen_h * scale))

    # Filter out maximized / fullscreen windows so they don't corrupt bounds
    if width >= (phys_screen_w - 60) or height >= (phys_screen_h - 100):
        return

    # Filter out uncustomized initial default center phone box (e.g. 495x1230 centered on ultrawide)
    if width < int(520 * scale) and (phys_screen_w * 0.40) <= left <= (phys_screen_w * 0.50):
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

    # Also persist to KWin rule (with scale awareness)
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
    try:
        from recipes.waydroid_native.system_tuning import get_waydroid_prop
        if get_waydroid_prop("persist.waydroid.multi_windows", "true").lower() != "true":
            return False
    except Exception:
        pass

    saved = load_all_bounds().get(pkg)
    if not saved:
        return False

    l, t, r, b = saved["left"], saved["top"], saved["right"], saved["bottom"]
    w = max(400, r - l)
    h = max(300, b - t)
    r = l + w
    b = t + h

    for _ in range(max_retries):
        active = get_active_android_windows()
        if pkg in active:
            task_id = active[pkg].get("taskId")
            if task_id:
                return apply_task_bounds(task_id, l, t, r, b)
        time.sleep(retry_delay)
    return False
