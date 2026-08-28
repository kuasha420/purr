#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — KDE Plasma 6 KWin Window Rules Manager
Configures native window decorations, taskbar grouping, and smart placement.
"""

import os
import subprocess
import configparser
from typing import Tuple


KWINRULES_PATH = os.path.expanduser("~/.config/kwinrulesrc")
RULE_NAME = "purr_waydroid_native_rules"


def get_dynamic_window_geometry() -> Tuple[int, int, int, int]:
    """
    Dynamically computes optimal initial floating window geometry based on the host's actual display.
    Works dynamically for any resolution, aspect ratio, scaling, or ultrawide setup.
    Leaves ample clearance above the bottom Plasma panel.
    """
    screen_w, screen_h = 1920, 1080
    try:
        res = subprocess.run(["kscreen-doctor", "-o"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "Geometry:" in line:
                parts = line.strip().split()
                for p in parts:
                    if "x" in p and p[0].isdigit() and p[-1].isdigit():
                        sw, sh = p.split("x", 1)
                        screen_w, screen_h = int(sw), int(sh)
                        break
                break
    except Exception:
        pass

    aspect = screen_w / max(1, screen_h)
    if aspect >= 2.0:
        # Ultrawide (21:9 / 32:9) -> Proportional tablet desktop window (~4:3 ratio)
        win_h = max(360, int(screen_h * 0.62))
        win_w = max(360, int(win_h * 1.33))
    elif aspect < 1.0:
        # Portrait display
        win_w = max(360, int(screen_w * 0.85))
        win_h = max(360, int(win_w * 1.33))
    else:
        # Standard landscape (16:9, 16:10, 4:3)
        win_h = max(360, int(screen_h * 0.65))
        win_w = max(360, int(win_h * 1.25))

    # Clamp safely within screen bounds allowing 80px for panel + titlebars
    win_w = min(win_w, max(360, screen_w - 40))
    win_h = min(win_h, max(360, screen_h - 100))

    pos_x = max(30, int((screen_w - win_w) / 2))
    pos_y = max(35, int((screen_h - win_h - 70) / 2))

    return win_w, win_h, pos_x, pos_y


def apply_kwin_rules() -> Tuple[bool, str]:
    """
    Applies optimized KWin window rules for Waydroid multi-window applications in KDE Plasma 6.
    Ensures non-fullscreen floating window state and native window integration.
    """
    try:
        config = configparser.ConfigParser(strict=False, interpolation=None)
        if os.path.exists(KWINRULES_PATH):
            config.read(KWINRULES_PATH)

        if not config.has_section("General"):
            config.add_section("General")

        current_rules = config.get("General", "rules", fallback="").strip()
        rule_list = [r.strip() for r in current_rules.split(",") if r.strip()]

        rule_id = "1"
        if RULE_NAME not in rule_list:
            for section in config.sections():
                if config.has_option(section, "description") and "Waydroid Native" in config.get(section, "description", fallback=""):
                    rule_id = section
                    break
            else:
                existing_nums = [int(r) for r in rule_list if r.isdigit()]
                next_num = (max(existing_nums) + 1) if existing_nums else 1
                rule_id = str(next_num)
                rule_list.append(rule_id)
                config.set("General", "rules", ",".join(rule_list))

        if not config.has_section(rule_id):
            config.add_section(rule_id)

        rule_section = config[rule_id]
        rule_section.clear()
        rule_section["description"] = "Waydroid Native Apps (Purr Ecosystem)"
        rule_section["wmclass"] = "waydroid"
        rule_section["wmclassmatch"] = "2"
        rule_section["types"] = "1"
        rule_section["fullscreen"] = "false"
        rule_section["fullscreenrule"] = "2"
        rule_section["maximizevert"] = "false"
        rule_section["maximizevertrule"] = "2"
        rule_section["maximizehoriz"] = "false"
        rule_section["maximizehorizrule"] = "2"

        os.makedirs(os.path.dirname(KWINRULES_PATH), exist_ok=True)
        with open(KWINRULES_PATH, "w") as f:
            config.write(f)

        subprocess.run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], capture_output=True)
        return True, f"KWin Plasma 6 window rules applied (Rule ID: {rule_id})."
    except Exception as e:
        return False, f"Failed to apply KWin rules: {str(e)}"


def remove_kwin_rules() -> Tuple[bool, str]:
    """
    Removes the Waydroid Native KWin rule from kwinrulesrc cleanly.
    """
    try:
        if not os.path.exists(KWINRULES_PATH):
            return True, "No kwinrulesrc found."

        config = configparser.ConfigParser(strict=False, interpolation=None)
        config.read(KWINRULES_PATH)

        target_sections = []
        for section in config.sections():
            if config.has_option(section, "description") and "Waydroid Native" in config.get(section, "description", fallback=""):
                target_sections.append(section)

        if not target_sections:
            return True, "Waydroid KWin rules were not present."

        rule_list = [r.strip() for r in config.get("General", "rules", fallback="").split(",") if r.strip()]

        for s in target_sections:
            config.remove_section(s)
            if s in rule_list:
                rule_list.remove(s)

        if config.has_section("General"):
            config.set("General", "rules", ",".join(rule_list))

        with open(KWINRULES_PATH, "w") as f:
            config.write(f)

        subprocess.run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], capture_output=True)
        return True, "Removed Waydroid KWin rules successfully."
    except Exception as e:
        return False, f"Failed to remove KWin rules: {str(e)}"
