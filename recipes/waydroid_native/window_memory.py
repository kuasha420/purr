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


def save_pkg_bounds(pkg: str, left: int, top: int, right: int, bottom: int):
    """
    Persists exact (left, top, right, bottom) frame coordinates for an Android package.
    """
    if not pkg or pkg.startswith("com.android.systemui") or pkg.startswith("com.android.launcher"):
        return
    if right <= left or bottom <= top:
        return

    data = load_all_bounds()
    data[pkg] = {
        "left": int(left),
        "top": int(top),
        "right": int(right),
        "bottom": int(bottom),
        "width": int(right - left),
        "height": int(bottom - top)
    }

    try:
        os.makedirs(os.path.dirname(BOUNDS_FILE), exist_ok=True)
        with open(BOUNDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


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
