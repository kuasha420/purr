#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — KDE Plasma 6 KWin Window Rules Manager
Configures native window decorations, taskbar grouping, and smart placement.
"""

import os
import subprocess
import configparser
from typing import Tuple


from recipes.waydroid_native.window_memory import get_screen_info, clean_oversized_kwin_rules


KWINRULES_PATH = os.path.expanduser("~/.config/kwinrulesrc")
RULE_NAME = "purr_waydroid_native_rules"


def get_screen_dimensions() -> Tuple[int, int]:
    w, h, _ = get_screen_info()
    return w, h


def get_dynamic_window_geometry() -> Tuple[int, int, int, int]:
    """
    Dynamically computes optimal initial floating window geometry based on the host's actual display.
    Works dynamically for any resolution, aspect ratio, scaling, or ultrawide setup.
    Leaves ample clearance above the bottom Plasma panel.
    """
    screen_w, screen_h, _ = get_screen_info()

    aspect = screen_w / max(1, screen_h)
    if aspect >= 2.0:
        # Ultrawide (21:9 / 32:9) -> Generous tablet / desktop landscape window (16:10 ratio)
        win_h = max(500, int(screen_h * 0.78))
        win_w = max(720, int(win_h * 1.5))
    elif aspect < 1.0:
        # Portrait display
        win_w = max(450, int(screen_w * 0.85))
        win_h = max(600, int(win_w * 1.33))
    else:
        # Standard landscape (16:9, 16:10, 4:3)
        win_h = max(480, int(screen_h * 0.75))
        win_w = max(640, int(win_h * 1.35))

    # Clamp safely within screen bounds allowing clearance for Plasma panels
    win_w = min(win_w, max(400, screen_w - 60))
    win_h = min(win_h, max(360, screen_h - 90))

    pos_x = max(30, int((screen_w - win_w) / 2))
    pos_y = max(35, int((screen_h - win_h - 70) / 2))

    return win_w, win_h, pos_x, pos_y


def apply_kwin_rules() -> Tuple[bool, str]:
    """
    Applies optimized KWin window rules for Waydroid multi-window applications in KDE Plasma 6.
    Ensures non-fullscreen floating window state and native window integration.
    """
    try:
        # First sanitize any corrupted or oversized legacy rules
        clean_oversized_kwin_rules()

        screen_w, screen_h, _ = get_screen_info()
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
        rule_section["wmclass"] = "waydroid."
        rule_section["wmclassmatch"] = "2"
        rule_section["types"] = "1"
        rule_section["fullscreen"] = "false"
        rule_section["fullscreenrule"] = "3"  # Apply Initially
        rule_section["maximizevert"] = "false"
        rule_section["maximizevertrule"] = "3"  # Apply Initially
        rule_section["maximizehoriz"] = "false"
        rule_section["maximizehorizrule"] = "3"  # Apply Initially
        
        # Initial proportional desktop window geometry anchored at display origin
        win_w, win_h, _, _ = get_dynamic_window_geometry()
        rule_section["position"] = "0,0"
        rule_section["positionrule"] = "3"  # Apply Initially
        rule_section["size"] = f"{win_w},{win_h}"
        rule_section["sizerule"] = "3"      # Apply Initially
        rule_section["minsize"] = "560,420"
        rule_section["minsizerule"] = "2"
        rule_section["noborder"] = "true"
        rule_section["noborderrule"] = "2"
        rule_section["decormode"] = "2"
        rule_section["decormoderule"] = "2"
        rule_section["above"] = "false"
        rule_section["aboverule"] = "2"
        rule_section["below"] = "false"
        rule_section["belowrule"] = "2"

        # Settings & Credential Unlock Dialog Rule (Centered Compact Dimensions)
        settings_section_id = "waydroid_com_android_settings"
        if settings_section_id not in rule_list:
            rule_list.insert(0, settings_section_id)
            config.set("General", "rules", ",".join(rule_list))

        if not config.has_section(settings_section_id):
            config.add_section(settings_section_id)

        settings_sec = config[settings_section_id]
        settings_sec.clear()
        settings_sec["description"] = "Waydroid Settings & Pattern Unlock (Purr Ecosystem)"
        settings_sec["wmclass"] = "waydroid.com.android.settings"
        settings_sec["wmclassmatch"] = "1"
        settings_sec["types"] = "1"
        settings_sec["fullscreen"] = "false"
        settings_sec["fullscreenrule"] = "2"
        settings_sec["maximizevert"] = "false"
        settings_sec["maximizevertrule"] = "2"
        settings_sec["maximizehoriz"] = "false"
        settings_sec["maximizehorizrule"] = "2"

        # Centered Compact Layout so all 4x4 / 3x3 pattern dots are 100% visible on ultrawide and standard screens
        set_w = min(680, max(520, int(screen_w * 0.35)))
        set_h = min(860, max(620, int(screen_h * 0.75)))
        set_x = max(20, int((screen_w - set_w) / 2))
        set_y = max(35, int((screen_h - set_h - 70) / 2))

        settings_sec["position"] = f"{set_x},{set_y}"
        settings_sec["positionrule"] = "3"
        settings_sec["size"] = f"{set_w},{set_h}"
        settings_sec["sizerule"] = "3"
        settings_sec["noborder"] = "false"
        settings_sec["noborderrule"] = "2"

        # Hide Waydroid Input Method Popup (LatinIME / AOSP Keyboard)
        ime_section_id = "waydroid_hide_inputmethod"
        if ime_section_id not in rule_list:
            rule_list.insert(0, ime_section_id)
            config.set("General", "rules", ",".join(rule_list))

        if not config.has_section(ime_section_id):
            config.add_section(ime_section_id)

        ime_sec = config[ime_section_id]
        ime_sec.clear()
        ime_sec["description"] = "Hide Waydroid Input Method Popup (Purr Ecosystem)"
        ime_sec["title"] = "InputMethod"
        ime_sec["titlematch"] = "2"
        ime_sec["wmclass"] = "waydroid."
        ime_sec["wmclassmatch"] = "2"
        ime_sec["types"] = "4294967295"
        ime_sec["fullscreen"] = "false"
        ime_sec["fullscreenrule"] = "2"
        ime_sec["maximizevert"] = "false"
        ime_sec["maximizevertrule"] = "2"
        ime_sec["maximizehoriz"] = "false"
        ime_sec["maximizehorizrule"] = "2"
        ime_sec["minimize"] = "true"
        ime_sec["minimizerule"] = "2"
        ime_sec["noborder"] = "true"
        ime_sec["noborderrule"] = "2"
        ime_sec["opacityactive"] = "0"
        ime_sec["opacityactiverule"] = "2"
        ime_sec["opacityinactive"] = "0"
        ime_sec["opacityinactiverule"] = "2"
        ime_sec["position"] = "-10000,-10000"
        ime_sec["positionrule"] = "2"
        ime_sec["size"] = "1,1"
        ime_sec["sizerule"] = "2"
        ime_sec["skiptaskbar"] = "true"
        ime_sec["skiptaskbarrule"] = "2"
        ime_sec["skippager"] = "true"
        ime_sec["skippagerrule"] = "2"
        ime_sec["skipswitcher"] = "true"
        ime_sec["skipswitcherrule"] = "2"

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
