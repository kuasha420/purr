#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — System & Hardware Tuning Subsystem
Handles BinderFS, GPU Gralloc acceleration, PipeWire audio, and Container properties.
"""

import os
import sys
import subprocess
import shutil
from typing import Dict, Any, Tuple, List


def detect_hardware() -> Dict[str, Any]:
    """
    Detects CPU architecture, vendor, and GPU driver to determine optimal settings.
    """
    info = {
        "cpu_arch": "x86_64",
        "cpu_vendor": "unknown",
        "gpu_driver": "default",
        "recommended_translation": "libndk",
        "gralloc": "gbm"
    }

    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "AuthenticAMD" in cpuinfo:
                info["cpu_vendor"] = "amd"
                info["recommended_translation"] = "libndk"
            elif "GenuineIntel" in cpuinfo:
                info["cpu_vendor"] = "intel"
                info["recommended_translation"] = "libndk"
    except Exception:
        pass

    try:
        lspci = subprocess.run(["lspci", "-k"], capture_output=True, text=True).stdout
        if "amdgpu" in lspci:
            info["gpu_driver"] = "amdgpu"
            info["gralloc"] = "minigbm_gbm_mesa"
        elif "nvidia" in lspci:
            info["gpu_driver"] = "nvidia"
            info["gralloc"] = "minigbm"
        elif "i915" in lspci or "xe" in lspci:
            info["gpu_driver"] = "intel"
            info["gralloc"] = "minigbm_gbm_mesa"
    except Exception:
        pass

    return info


def ensure_binderfs() -> Tuple[bool, str]:
    """
    Ensures /dev/binderfs is mounted and binder nodes are accessible.
    """
    if os.path.exists("/dev/binderfs/binder-control") or os.path.exists("/dev/binder"):
        return True, "BinderFS is mounted and active."

    try:
        os.makedirs("/dev/binderfs", exist_ok=True)
        res = subprocess.run(["sudo", "mount", "-t", "binder", "binder", "/dev/binderfs"], capture_output=True, text=True)
        if res.returncode == 0 or os.path.exists("/dev/binderfs/binder-control"):
            # Ensure permanent fstab entry if not present
            try:
                with open("/etc/fstab", "r") as f:
                    fstab = f.read()
                if "/dev/binderfs" not in fstab:
                    line = "binder /dev/binderfs binder defaults 0 0\n"
                    subprocess.run(["sudo", "bash", "-c", f'echo "{line}" >> /etc/fstab'])
            except Exception:
                pass
            return True, "Mounted /dev/binderfs successfully."
        return False, f"Failed to mount binderfs: {res.stderr.strip()}"
    except Exception as e:
        return False, f"BinderFS error: {str(e)}"


def configure_network_forwarding() -> Tuple[bool, str]:
    """
    Ensures net.ipv4.ip_forward is enabled and nftables/dnsmasq are ready.
    """
    try:
        res = subprocess.run(["sysctl", "-n", "net.ipv4.ip_forward"], capture_output=True, text=True)
        if res.stdout.strip() != "1":
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], capture_output=True)
            # Persist sysctl
            sysctl_conf = "/etc/sysctl.d/99-waydroid.conf"
            subprocess.run(["sudo", "bash", "-c", f'echo "net.ipv4.ip_forward = 1" > {sysctl_conf}'])
        return True, "IPv4 forwarding enabled."
    except Exception as e:
        return False, f"Network forwarding error: {str(e)}"


def apply_waydroid_properties(hw_info: Dict[str, Any]) -> List[str]:
    """
    Sets essential Waydroid properties for native multi-window desktop experience,
    hardware acceleration, and cursor integration.
    """
    props = [
        ("persist.waydroid.multi_windows", "true"),
        ("persist.waydroid.cursor_on_subsurface", "true"),
        ("persist.waydroid.suspend", "false"),
        ("ro.hardware.gralloc", hw_info.get("gralloc", "minigbm_gbm_mesa")),
        ("persist.waydroid.fake_touch", "true"),
        ("persist.waydroid.hide_soft_keyboard", "true")
    ]

    applied = []
    clean_env = os.environ.copy()
    clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"

    # 1. Update /var/lib/waydroid/waydroid.cfg directly
    cfg_path = "/var/lib/waydroid/waydroid.cfg"
    if os.path.exists(cfg_path):
        try:
            import configparser
            cfg = configparser.ConfigParser(strict=False, interpolation=None)
            cfg.read(cfg_path)
            if not cfg.has_section("properties"):
                cfg.add_section("properties")
            for k, v in props:
                cfg.set("properties", k, v)
                applied.append(f"{k}={v}")
            # Write via sudo
            import io
            s_out = io.StringIO()
            cfg.write(s_out)
            content = s_out.getvalue()
            p = subprocess.Popen(["sudo", "tee", cfg_path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            p.communicate(input=content)
        except Exception:
            pass

    # 2. Update /var/lib/waydroid/waydroid_base.prop so container init boots multi_windows
    base_prop_path = "/var/lib/waydroid/waydroid_base.prop"
    if os.path.exists(base_prop_path):
        try:
            with open(base_prop_path, "r") as f:
                lines = f.read().splitlines()
            prop_dict = {}
            for l in lines:
                if "=" in l and not l.startswith("#"):
                    pk, pv = l.split("=", 1)
                    prop_dict[pk.strip()] = pv.strip()
            for k, v in props:
                prop_dict[k] = v
            new_base = "\n".join([f"{k}={v}" for k, v in prop_dict.items()]) + "\n"
            p = subprocess.Popen(["sudo", "tee", base_prop_path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            p.communicate(input=new_base)
        except Exception:
            pass

    # 3. Also run prop set command
    clean_env = os.environ.copy()
    clean_env["PATH"] = "/usr/bin:/usr/local/bin"
    for key, val in props:
        try:
            cmd = ["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid", "prop", "set", key, val]
            subprocess.run(cmd, capture_output=True, env=clean_env)
            if f"{key}={val}" not in applied:
                applied.append(f"{key}={val}")
        except Exception:
            pass

    return applied


def get_waydroid_prop(key: str, default: str = "") -> str:
    """
    Reads a Waydroid property from waydroid_base.prop or live container getprop.
    """
    base_prop_path = "/var/lib/waydroid/waydroid_base.prop"
    if os.path.exists(base_prop_path):
        try:
            with open(base_prop_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if k.strip() == key:
                            return v.strip()
        except Exception:
            pass

    try:
        res = subprocess.run(["waydroid", "prop", "get", key], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    return default


def set_waydroid_prop(key: str, val: str) -> bool:
    """
    Persists a Waydroid property using native Waydroid IPC and updates waydroid_base.prop.
    """
    try:
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        subprocess.run([waydroid_bin, "prop", "set", key, val], capture_output=True, timeout=3)

        # Also update base_prop file if possible
        base_prop_path = "/var/lib/waydroid/waydroid_base.prop"
        if os.path.exists(base_prop_path):
            try:
                with open(base_prop_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                prop_dict = {}
                for line in lines:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        prop_dict[k.strip()] = v.strip()
                prop_dict[key] = val
                new_base = "\n".join([f"{k}={v}" for k, v in prop_dict.items()]) + "\n"
                p = subprocess.Popen(["sudo", "tee", base_prop_path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
                p.communicate(input=new_base, timeout=2)
            except Exception:
                pass

        return True
    except Exception:
        return False


def tune_android_keyboard_and_freeform() -> List[str]:
    """
    Applies runtime Android system settings to disable on-screen soft keyboard
    when hardware keyboard is present, enforce freeform multi-window mode,
    and eliminate letterboxing / aspect ratio restrictions on large screens.
    """
    settings_commands = [
        ("secure", "show_ime_with_hard_keyboard", "0"),
        ("secure", "show_ime_with_hard_keyboard_status", "0"),
        ("global", "enable_freeform_support", "1"),
        ("global", "force_resizable_activities", "1"),
        ("global", "force_allow_on_external_displays", "1"),
        ("global", "development_settings_enabled", "1")
    ]
    results = []
    for namespace, key, val in settings_commands:
        try:
            cmd = [
                "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", f"PATH=/system/bin:/system/xbin settings put {namespace} {key} {val}"
            ]
            subprocess.run(cmd, capture_output=True)
            results.append(f"Android {namespace}.{key}={val}")
        except Exception:
            pass

    wm_commands = [
        "cmd window set-ignore-orientation-request 1",
        "cmd window set-multi-window-config --supportsNonResizable 1 --respectsActivityMinWidthHeight -1",
        "cmd window set-letterbox-style --aspectRatio 0 --minAspectRatioForUnresizable 0"
    ]
    for cmd_str in wm_commands:
        try:
            cmd = [
                "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", f"PATH=/system/bin:/system/xbin {cmd_str}"
            ]
            subprocess.run(cmd, capture_output=True)
            results.append(cmd_str)
        except Exception:
            pass

    return results


def patch_numpad_keychars() -> Tuple[bool, str]:
    """
    Installs clean, standard KeyCharacterMaps with direct NumPad digits mapping
    across Virtual.kcm, Generic.kcm, wayland_keyboard.kcm, and Vendor_0001_Product_0001.kcm.
    """
    kcm_overlay_dir = "/var/lib/waydroid/overlay/system/usr/keychars"
    asset_kcm = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets", "Generic.kcm")

    if not os.path.exists(asset_kcm):
        return False, f"KeyCharacterMap asset missing at {asset_kcm}"

    try:
        subprocess.run(["sudo", "mkdir", "-p", kcm_overlay_dir], capture_output=True)
        for fname in ["Virtual.kcm", "Generic.kcm", "wayland_keyboard.kcm", "Vendor_0001_Product_0001.kcm"]:
            target = os.path.join(kcm_overlay_dir, fname)
            subprocess.run(["sudo", "cp", asset_kcm, target], capture_output=True)
            subprocess.run(["sudo", "chmod", "644", target], capture_output=True)

        return True, "Standard AOSP KeyCharacterMaps with NumPad direct digit mapping deployed."
    except Exception as e:
        return False, f"Keymap deployment error: {str(e)}"


def patch_waydroid_clipboard_service() -> Tuple[bool, str]:
    """
    Ensures Waydroid's Python clipboard manager service decodes host clipboard
    bytes to UTF-8 strings for flawless Linux-to-Android clipboard synchronization.
    """
    clip_file = "/usr/lib/waydroid/tools/services/clipboard_manager.py"
    if not os.path.exists(clip_file):
        return True, "Waydroid clipboard manager not present on system."

    try:
        with open(clip_file, "r", encoding="utf-8") as f:
            content = f.read()

        target = """    def getClipboardData():
        try:
            return pyclip.paste()
        except Exception as e:
            logging.debug(str(e))
        return \"\""""

        replacement = """    def getClipboardData():
        try:
            val = pyclip.paste()
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace")
            return str(val) if val else ""
        except Exception as e:
            logging.debug(str(e))
        return \"\""""

        if target in content:
            new_content = content.replace(target, replacement, 1)
            tmp_path = "/tmp/purr_clipboard_manager.py"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            subprocess.run(["sudo", "cp", tmp_path, clip_file], capture_output=True)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return True, "Patched Waydroid clipboard service for UTF-8 Linux-to-Android sync."
        return True, "Waydroid clipboard service is already patched."
    except Exception as e:
        return False, f"Failed to patch Waydroid clipboard service: {str(e)}"


def install_purr_clip_helper() -> Tuple[bool, str]:
    """
    Installs and registers PurrClipHelper inside the Android container to provide
    unrestricted, zero-latency host-to-Android clipboard synchronization across all apps.
    """
    asset_apk = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets", "PurrClipHelper.apk")
    if not os.path.exists(asset_apk):
        return False, f"PurrClipHelper.apk asset missing at {asset_apk}"

    try:
        # 1. Install to system priv-app overlay
        priv_dir = "/var/lib/waydroid/overlay/system/priv-app/PurrClipHelper"
        subprocess.run(["sudo", "mkdir", "-p", priv_dir], capture_output=True)
        subprocess.run(["sudo", "cp", asset_apk, os.path.join(priv_dir, "PurrClipHelper.apk")], capture_output=True)
        subprocess.run(["sudo", "chmod", "644", os.path.join(priv_dir, "PurrClipHelper.apk")], capture_output=True)

        # 2. Install unrestricted ClipboardService framework overlay
        asset_services = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets", "services.jar")
        if os.path.exists(asset_services):
            framework_dir = "/var/lib/waydroid/overlay/system/framework"
            subprocess.run(["sudo", "mkdir", "-p", framework_dir], capture_output=True)
            subprocess.run(["sudo", "cp", asset_services, os.path.join(framework_dir, "services.jar")], capture_output=True)
            subprocess.run(["sudo", "chmod", "644", os.path.join(framework_dir, "services.jar")], capture_output=True)

        # 3. Also install via pm in container if running
        proc = subprocess.Popen(["sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "--",
                                 "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm install -r -g -d -t /data/local/tmp/PurrClipHelper.apk 2>/dev/null"],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "PurrClipHelper & ClipboardService installed for instant host-to-Android clipboard sharing."
    except Exception as e:
        return False, f"Failed to install PurrClipHelper: {e}"


def patch_waydroid_app_manager() -> Tuple[bool, str]:
    """
    Patches /usr/lib/waydroid/tools/actions/app_manager.py to seamlessly handle
    Android Keyguard lock states during app launches and window memory restoration.
    """
    target_file = "/usr/lib/waydroid/tools/actions/app_manager.py"
    if not os.path.exists(target_file):
        return True, "Waydroid app_manager.py not found on host."

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "WaydroidNativeRecipe.is_keyguard_locked()" in content:
            return True, "Waydroid app_manager.py is already patched for keyguard lock auto-transition."

        # Replace justLaunch with keyguard-aware launcher
        old_pattern = """            platformService.launchApp(args.PACKAGE)"""
        new_pattern = """            # Check keyguard lock status
            is_locked = False
            try:
                import sys
                if "/home/kuasha/Dev/purr" not in sys.path:
                    sys.path.insert(0, "/home/kuasha/Dev/purr")
                from recipes.waydroid_native.recipe import WaydroidNativeRecipe
                is_locked = WaydroidNativeRecipe.is_keyguard_locked()
            except Exception:
                pass

            if is_locked:
                showFullUI(args)
                try:
                    WaydroidNativeRecipe.spawn_post_unlock_launcher(args.PACKAGE)
                except Exception:
                    pass
                return

            platformService.launchApp(args.PACKAGE)"""

        if old_pattern in content:
            new_content = content.replace(old_pattern, new_pattern, 1)
            tmp_path = "/tmp/purr_app_manager.py"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            subprocess.run(["sudo", "cp", tmp_path, target_file], capture_output=True)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return True, "Patched Waydroid app_manager for keyguard auto-transition."
        return True, "Waydroid app_manager pattern not found."
    except Exception as e:
        return False, f"Failed to patch Waydroid app_manager: {e}"


def patch_waydroid_user_manager() -> Tuple[bool, str]:
    """
    Patches /usr/lib/waydroid/tools/services/user_manager.py to delegate all
    desktop entry generation and package lifecycle synchronization directly to Purr.
    """
    target_file = "/usr/lib/waydroid/tools/services/user_manager.py"
    if not os.path.exists(target_file):
        return True, "Waydroid user_manager.py not found on host."

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "triggerPurrSync" in content:
            return True, "Waydroid user_manager.py is already patched for Purr desktop management."

        code = """# Copyright 2021 Erfan Abdi
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import shutil
import subprocess
import threading
import tools.config
import tools.helpers.net
from pathlib import Path
from contextlib import suppress
from tools.interfaces import IUserMonitor
from tools.interfaces import IPlatform
from gi.repository import GLib

stopping = False

def start(args, session, unlocked_cb=None):

    apps_dir = Path(session["xdg_data_home"]) / "applications"
    apps_dir.mkdir(0o700, exist_ok=True)

    def triggerPurrSync():
        try:
            purr_bin = shutil.which("purr") or "/usr/local/bin/purr"
            clean_env = dict(**subprocess.os.environ)
            clean_env["PATH"] = "/usr/bin:/usr/local/bin:" + clean_env.get("PATH", "")
            subprocess.Popen([purr_bin, "apk", "sync"], env=clean_env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        except Exception:
            pass

    def userUnlocked(uid):
        cfg = tools.config.load(args)
        logging.info("Android with user {} is ready".format(uid))

        if cfg["waydroid"]["auto_adb"] == "True":
            with suppress(RuntimeError):
                tools.helpers.net.adb_connect(args)

        triggerPurrSync()
        if unlocked_cb:
            unlocked_cb()

    def packageStateChanged(mode, packageName, uid):
        triggerPurrSync()

    def service_thread():
        while not stopping:
            IUserMonitor.add_service(args, userUnlocked, packageStateChanged)

    global stopping
    stopping = False
    args.user_manager = threading.Thread(target=service_thread)
    args.user_manager.start()

def stop(args):
    global stopping
    stopping = True
    try:
        if args.userMonitorLoop:
            args.userMonitorLoop.quit()
    except AttributeError:
        logging.debug("UserMonitor service is not even started")
"""
        tmp_path = "/tmp/purr_user_manager.py"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)
        subprocess.run(["sudo", "cp", tmp_path, target_file], capture_output=True)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return True, "Patched Waydroid user_manager to delegate desktop management to Purr."
    except Exception as e:
        return False, f"Failed to patch Waydroid user_manager: {e}"


