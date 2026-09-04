#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — System & Hardware Tuning Subsystem
Handles BinderFS, GPU Gralloc acceleration, PipeWire audio, Container properties,
and framework resource overlays (titlebar caption colors).
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
    Ensures net.ipv4.ip_forward is enabled, firewalld trusted zone includes waydroid0,
    and nftables/dnsmasq are ready.
    """
    try:
        res = subprocess.run(["sysctl", "-n", "net.ipv4.ip_forward"], capture_output=True, text=True)
        if res.stdout.strip() != "1":
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], capture_output=True)
            # Persist sysctl
            sysctl_conf = "/etc/sysctl.d/99-waydroid.conf"
            subprocess.run(["sudo", "bash", "-c", f'echo "net.ipv4.ip_forward = 1" > {sysctl_conf}'])

        # Firewalld verification
        fw_status = subprocess.run(["systemctl", "is-active", "--quiet", "firewalld"], capture_output=True)
        if fw_status.returncode == 0:
            query = subprocess.run(["sudo", "firewall-cmd", "--zone=trusted", "--query-interface=waydroid0"], capture_output=True)
            if query.returncode != 0:
                subprocess.run(["sudo", "firewall-cmd", "--zone=trusted", "--add-interface=waydroid0", "--permanent"], capture_output=True)
                subprocess.run(["sudo", "firewall-cmd", "--reload"], capture_output=True)

        return True, "IPv4 forwarding and firewall trust enabled."
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


def ensure_container_unfrozen():
    """
    Ensures Waydroid container is running and not in FROZEN cgroup state before dispatching commands.
    """
    try:
        st = subprocess.run(["sudo", "-n", "lxc-info", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "-sH"], capture_output=True, text=True, timeout=1.5)
        if "FROZEN" in st.stdout:
            subprocess.run(["sudo", "-n", "lxc-unfreeze", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid"], capture_output=True, timeout=1.5)
    except Exception:
        pass


def tune_android_keyboard_and_freeform() -> List[str]:
    """
    Applies runtime Android system settings to disable on-screen soft keyboard
    when hardware keyboard is present, enforce freeform multi-window mode,
    and eliminate letterboxing / aspect ratio restrictions on large screens.
    """
    ensure_container_unfrozen()
    commands = [
        "settings put secure show_ime_with_hard_keyboard 0",
        "settings put secure show_ime_with_hard_keyboard_status 0",
        "settings put global enable_freeform_support 1",
        "settings put global force_resizable_activities 1",
        "settings put global force_allow_on_external_displays 1",
        "settings put global development_settings_enabled 1",
        "cmd window set-ignore-orientation-request 1",
        "cmd window set-multi-window-config --supportsNonResizable 1 --respectsActivityMinWidthHeight -1",
        "cmd window set-letterbox-style --aspectRatio 0 --minAspectRatioForUnresizable 0",
        "if [ -f /data/data/com.whatsapp/shared_prefs/com.whatsapp_preferences_light.xml ]; then sed -i 's/<boolean name=\"input_enter_send\" value=\"false\" \\/>/<boolean name=\"input_enter_send\" value=\"true\" \\/>/g' /data/data/com.whatsapp/shared_prefs/com.whatsapp_preferences_light.xml; fi"
    ]
    results = []
    try:
        combined_script = "export PATH=/system/bin:/system/xbin; " + " ; ".join(commands)
        cmd = [
            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", combined_script
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.5)
        if res.returncode == 0:
            results.append("Applied freeform multi-window, hardware keyboard, and orientation rules.")
        else:
            results.append(f"Tuning applied with note: {res.stderr.strip()}")
    except Exception as e:
        results.append(f"Tuning skipped: {e}")

    return results

    return results


def patch_numpad_keychars() -> Tuple[bool, str]:
    """
    Installs clean, enhanced KeyCharacterMaps with direct NumPad digit mapping,
    Escape-to-Back hardware simulation, and Enter/Shift+Enter multiline bindings
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

        return True, "Enhanced KeyCharacterMaps (Escape-to-Back, Enter/Shift+Enter, NumPad direct) deployed."
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


def patch_waydroid_mount_helper() -> Tuple[bool, str]:
    """
    Patches /usr/lib/waydroid/tools/helpers/mount.py to ensure readonly is set to False
    when upper_dir is provided, resolving fsconfig() ESTALE overlay mount errors on modern Linux kernels.
    """
    mount_file = "/usr/lib/waydroid/tools/helpers/mount.py"
    if not os.path.exists(mount_file):
        return True, "Waydroid mount helper not found on system."

    try:
        with open(mount_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "readonly = False" in content:
            return True, "Waydroid mount helper is already patched for OverlayFS compatibility."

        target = """    if upper_dir:
        dirs.append(upper_dir)
        dirs.append(work_dir)
        options.append("upperdir=" + upper_dir)
        options.append("workdir=" + work_dir)"""

        replacement = """    if upper_dir:
        readonly = False
        dirs.append(upper_dir)
        dirs.append(work_dir)
        options.append("upperdir=" + upper_dir)
        options.append("workdir=" + work_dir)"""

        if target in content:
            new_content = content.replace(target, replacement, 1)
            tmp_path = "/tmp/purr_mount.py"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            subprocess.run(["sudo", "cp", tmp_path, mount_file], capture_output=True)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return True, "Patched Waydroid mount helper for modern OverlayFS compatibility."
        return True, "Waydroid mount helper pattern not found."
    except Exception as e:
        return False, f"Failed to patch Waydroid mount helper: {str(e)}"


def patch_waydroid_lxc_helper() -> Tuple[bool, str]:
    """
    Patches /usr/lib/waydroid/tools/helpers/lxc.py to automatically trigger
    dynamic linker configuration generation (SPHAL, APEX runtime, and network namespaces)
    immediately after container startup, ensuring self-healing boots.
    """
    lxc_file = "/usr/lib/waydroid/tools/helpers/lxc.py"
    if not os.path.exists(lxc_file):
        return True, "Waydroid lxc helper not found on system."

    try:
        with open(lxc_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "linkerconfig --target /linkerconfig" in content:
            return True, "Waydroid lxc helper is already patched with linkerconfig hook."

        target = """    wait_for_running(args)
    # Workaround lxc-start changing stdout/stderr permissions to 700"""

        replacement = """    wait_for_running(args)
    # Ensure full Android 13 APEX, SPHAL and network linker namespaces
    try:
        time.sleep(1.0)
        tools.helpers.run.user(args, [
            "lxc-attach", "-P", tools.config.defaults["lxc"], "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; linkerconfig --target /linkerconfig"
        ])
    except Exception:
        pass
    # Workaround lxc-start changing stdout/stderr permissions to 700"""

        if target in content:
            new_content = content.replace(target, replacement, 1)
            tmp_path = "/tmp/purr_lxc.py"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            subprocess.run(["sudo", "cp", tmp_path, lxc_file], capture_output=True)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return True, "Patched Waydroid lxc helper with auto-linkerconfig generation hook."
        return True, "Waydroid lxc helper pattern not found."
    except Exception as e:
        return False, f"Failed to patch Waydroid lxc helper: {str(e)}"


def install_purr_clip_helper() -> Tuple[bool, str]:
    """
    Installs and registers PurrClipHelper inside the Android container to provide
    unrestricted, zero-latency host-to-Android clipboard synchronization across all apps.
    """
    asset_apk = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets", "PurrClipHelper.apk")
    if not os.path.exists(asset_apk):
        return False, f"PurrClipHelper.apk asset missing at {asset_apk}"

    try:
        # 1. Install companions to system priv-app / app overlay
        assets_to_install = [
            ("PurrClipHelper.apk", "priv-app/PurrClipHelper"),
            ("PurrNullIME.apk", "app/PurrNullIME"),
            ("GamepadTester.apk", "app/GamepadTester"),
            ("PurrWindowDecorOverlay.apk", "product/overlay/PurrWindowDecorOverlay")
        ]
        assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
        for apk_name, rel_dest in assets_to_install:
            apk_path = os.path.join(assets_dir, apk_name)
            if os.path.exists(apk_path):
                dest_dir = f"/var/lib/waydroid/overlay/system/{rel_dest}"
                subprocess.run(["sudo", "mkdir", "-p", dest_dir], capture_output=True)
                subprocess.run(["sudo", "cp", apk_path, os.path.join(dest_dir, apk_name)], capture_output=True)
                subprocess.run(["sudo", "chmod", "644", os.path.join(dest_dir, apk_name)], capture_output=True)

        # 2. Install unrestricted ClipboardService framework overlay
        asset_services = os.path.join(assets_dir, "services.jar")
        if os.path.exists(asset_services):
            framework_dir = "/var/lib/waydroid/overlay/system/framework"
            subprocess.run(["sudo", "mkdir", "-p", framework_dir], capture_output=True)
            subprocess.run(["sudo", "cp", asset_services, os.path.join(framework_dir, "services.jar")], capture_output=True)
            subprocess.run(["sudo", "chmod", "644", os.path.join(framework_dir, "services.jar")], capture_output=True)

        # 3. If container is running, live install and configure PurrNullIME & GamepadTester
        live_setup_script = (
            "export PATH=/system/bin:/system/xbin; "
            "pm install -r -g -d -t /system/priv-app/PurrClipHelper/PurrClipHelper.apk 2>/dev/null; "
            "pm install -r -g -d -t /system/app/PurrNullIME/PurrNullIME.apk 2>/dev/null; "
            "pm install -r -g -d -t /system/app/GamepadTester/GamepadTester.apk 2>/dev/null; "
            "cmd overlay enable --user 0 com.android.theme.purr.windowdecor.systemui 2>/dev/null; "
            "ime enable dev.purr.nullime/.NullInputMethodService 2>/dev/null; "
            "ime set dev.purr.nullime/.NullInputMethodService 2>/dev/null; "
            "settings put secure default_input_method dev.purr.nullime/.NullInputMethodService 2>/dev/null; "
            "settings put secure show_ime_with_hard_keyboard 0 2>/dev/null; "
            "settings put secure show_ime_with_hard_keyboard_status 0 2>/dev/null"
        )
        subprocess.run(["sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "--",
                        "/system/bin/sh", "-c", live_setup_script],
                       capture_output=True, timeout=5)

        return True, "PurrClipHelper, PurrNullIME, GamepadTester, and PurrWindowDecorOverlay companions active."
    except Exception as e:
        return False, f"Failed to install Purr companions: {e}"


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
                import sys, os
                for _p in ["/usr/share/purr", "/usr/local/share/purr", "/home/psl/purr", os.path.expanduser("~/.local/share/purr"), os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]:
                    if os.path.exists(_p) and _p not in sys.path:
                        sys.path.insert(0, _p)
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


def get_host_gamepad_devices() -> List[str]:
    """
    Identifies all physical hardware game controllers, joysticks, and motion sensors
    attached to the Linux host, strictly excluding host keyboards, mice, and power buttons.
    """
    gamepad_events = []
    try:
        import glob
        for js in glob.glob("/dev/input/js*"):
            try:
                js_name = os.path.basename(js)
                sys_dev = os.path.realpath(f"/sys/class/input/{js_name}/device")
                for entry in os.listdir(sys_dev):
                    if entry.startswith("event"):
                        gamepad_events.append(f"/dev/input/{entry}")
                    elif entry.startswith("input"):
                        for sub in os.listdir(os.path.join(sys_dev, entry)):
                            if sub.startswith("event"):
                                gamepad_events.append(f"/dev/input/{sub}")
            except Exception:
                pass
    except Exception:
        pass
    return sorted(list(set(gamepad_events)))


def sync_host_gamepads_to_container() -> Tuple[bool, int]:
    """
    Synchronizes physical game controller (DualSense, Xbox, etc.) and webcam nodes
    into the running Waydroid container, strictly excluding host keyboards/mice to prevent
    background key interception and phantom search events.
    """
    try:
        import glob
        gamepad_events = get_host_gamepad_devices()
        js_nodes = glob.glob("/dev/input/js*")
        video_nodes = glob.glob("/dev/video*") + glob.glob("/dev/media*")
        all_nodes = list(gamepad_events) + list(js_nodes) + list(video_nodes)
        if os.path.exists("/dev/uinput"):
            all_nodes.append("/dev/uinput")

        # 1. Ensure 0666 permissions on host for valid nodes
        if all_nodes:
            chmod_cmd = ["sudo", "chmod", "0666"] + all_nodes
            subprocess.run(chmod_cmd, capture_output=True)

        # 2. Prune non-gamepad event nodes from container and create gamepad/video nodes
        mknod_cmds = []

        allowed_basenames = " ".join([os.path.basename(n) for n in gamepad_events])
        prune_cmd = (
            "for node in /dev/input/event*; do "
            "  if [ -e \"$node\" ]; then "
            "    name=$(basename \"$node\"); "
            f"    case \" {allowed_basenames} \" in "
            "      *\" $name \"*) ;; "
            "      *) rm -f \"$node\" ;; "
            "    esac; "
            "  fi; "
            "done"
        )
        mknod_cmds.append(prune_cmd)

        for node in all_nodes:
            try:
                stat_info = os.stat(node)
                import stat
                if stat.S_ISCHR(stat_info.st_mode):
                    major = os.major(stat_info.st_rdev)
                    minor = os.minor(stat_info.st_rdev)
                    dirname = os.path.dirname(node)
                    mknod_cmds.append(
                        f"mkdir -p {dirname} && chmod 755 {dirname} && "
                        f"[ -e {node} ] || mknod -m 666 {node} c {major} {minor} ; "
                        f"chmod 666 {node} ; "
                        f"touch {node}"
                    )
            except Exception:
                pass
        # 3. Ensure essential Wayland input FIFOs (pointer, keyboard, tablet, touch) exist with 0660 system permissions
        fifo_cmd = (
            "mkdir -p /dev/input && chmod 755 /dev/input; "
            "for fifo in wl_pointer_events wl_keyboard_events wl_tablet_events wl_touch_events; do "
            "  if [ ! -p \"/dev/input/$fifo\" ]; then "
            "    rm -f \"/dev/input/$fifo\"; "
            "    mkfifo -m 660 \"/dev/input/$fifo\"; "
            "    chown system:system \"/dev/input/$fifo\" 2>/dev/null || true; "
            "    chmod 660 \"/dev/input/$fifo\" 2>/dev/null || true; "
            "  fi; "
            "done"
        )
        mknod_cmds.append(fifo_cmd)

        if mknod_cmds:
            combined_script = "export PATH=/system/bin:/system/xbin; " + " ; ".join(mknod_cmds)
            subprocess.run(
                ["sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "--", "/system/bin/sh", "-c", combined_script],
                capture_output=True, timeout=4
            )

        return True, len(all_nodes)
    except Exception:
        return False, 0


def tune_game_controller_and_webcam_passthrough() -> Tuple[bool, str]:
    """
    Configures LXC cgroup2 device filters, Waydroid python helpers, and runtime node mounts
    for full hardware game controller (DualSense, Xbox, Switch, generic) and webcam passthrough.
    """
    try:
        results = []

        # 1. Update /var/lib/waydroid/lxc/waydroid/config with cgroup2 device allow rules
        cfg_path = "/var/lib/waydroid/lxc/waydroid/config"
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg_content = f.read()

            cgroup_rules = [
                "lxc.cgroup2.devices.allow = c 1:* rwm",     # Standard /dev/null, /dev/zero, /dev/full, /dev/random, /dev/urandom
                "lxc.cgroup2.devices.allow = c 5:* rwm",     # /dev/tty, /dev/ptmx
                "lxc.cgroup2.devices.allow = c 10:* rwm",    # /dev/ashmem, /dev/uinput, misc
                "lxc.cgroup2.devices.allow = c 13:* rwm",    # Input devices (/dev/input/event*, /dev/input/js*)
                "lxc.cgroup2.devices.allow = c 81:* rwm",    # V4L2 webcams (/dev/video*)
                "lxc.cgroup2.devices.allow = c 226:* rwm",   # DRM graphics render nodes (/dev/dri/renderD*)
                "lxc.cgroup2.devices.allow = c 511:* rwm",   # Media controllers (/dev/media*)
                "lxc.cgroup2.devices.allow = c 240:* rwm",   # HIDRAW devices
                "lxc.cgroup2.devices.allow = c 241:* rwm",
                "lxc.cgroup2.devices.allow = c 242:* rwm",   # BinderFS
                "lxc.cgroup2.devices.allow = c 243:* rwm",
                "lxc.cgroup2.devices.allow = c 244:* rwm",
                "lxc.cgroup2.devices.allow = c 245:* rwm",
                "lxc.cgroup2.devices.allow = c 10:223 rwm",  # uinput
                "lxc.cgroup2.devices.allow = c 10:239 rwm",  # uhid
            ]

            modified = False
            lines = cfg_content.splitlines()
            for rule in cgroup_rules:
                if rule not in lines:
                    lines.append(rule)
                    modified = True

            if modified:
                new_cfg = "\n".join(lines) + "\n"
                p = subprocess.Popen(["sudo", "tee", cfg_path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
                p.communicate(input=new_cfg)
                results.append("Updated LXC cgroup2 device filters for gamepads and webcams.")

        # 2. Patch /usr/lib/waydroid/tools/helpers/lxc.py
        lxc_py = "/usr/lib/waydroid/tools/helpers/lxc.py"
        if os.path.exists(lxc_py):
            with open(lxc_py, "r", encoding="utf-8") as f:
                lxc_src = f.read()

            if 'glob.glob("/dev/input/event*")' not in lxc_src:
                target = 'for n in glob.glob("/dev/video*"):\n        make_entry(n)'
                replacement = (
                    'for n in glob.glob("/dev/video*"):\n        make_entry(n)\n'
                    '    for n in glob.glob("/dev/media*"):\n        make_entry(n)\n'
                    '    for n in glob.glob("/dev/input/event*"):\n        make_entry(n)\n'
                    '    for n in glob.glob("/dev/input/js*"):\n        make_entry(n)\n'
                    '    for n in glob.glob("/dev/hidraw*"):\n        make_entry(n)\n'
                    '    make_entry("/dev/uinput")'
                )
                if target in lxc_src:
                    new_lxc_src = lxc_src.replace(target, replacement)
                    tmp_lxc = "/tmp/purr_lxc.py"
                    with open(tmp_lxc, "w", encoding="utf-8") as f:
                        f.write(new_lxc_src)
                    subprocess.run(["sudo", "cp", tmp_lxc, lxc_py], capture_output=True)
                    if os.path.exists(tmp_lxc):
                        os.remove(tmp_lxc)
                    results.append("Patched Waydroid lxc.py device mount generator.")

        # 3. Patch /usr/lib/waydroid/tools/actions/container_manager.py
        cm_py = "/usr/lib/waydroid/tools/actions/container_manager.py"
        if os.path.exists(cm_py):
            with open(cm_py, "r", encoding="utf-8") as f:
                cm_src = f.read()

            if 'glob.glob("/dev/input/event*")' not in cm_src:
                target_cm = 'perm_list.extend(glob.glob("/dev/video*"))'
                replacement_cm = (
                    'perm_list.extend(glob.glob("/dev/video*"))\n'
                    '        perm_list.extend(glob.glob("/dev/media*"))\n'
                    '        perm_list.extend(glob.glob("/dev/input/event*"))\n'
                    '        perm_list.extend(glob.glob("/dev/input/js*"))\n'
                    '        perm_list.extend(glob.glob("/dev/hidraw*"))\n'
                    '        perm_list.append("/dev/uinput")'
                )
                if target_cm in cm_src:
                    new_cm_src = cm_src.replace(target_cm, replacement_cm)
                    tmp_cm = "/tmp/purr_container_manager.py"
                    with open(tmp_cm, "w", encoding="utf-8") as f:
                        f.write(new_cm_src)
                    subprocess.run(["sudo", "cp", tmp_cm, cm_py], capture_output=True)
                    if os.path.exists(tmp_cm):
                        os.remove(tmp_cm)
                    results.append("Patched Waydroid container_manager.py device permissions.")

        # 4. Live sync all active host controllers and video devices to running container
        ok, count = sync_host_gamepads_to_container()
        if ok:
            results.append(f"Synchronized {count} controller, HID, and video device nodes into container.")

        return True, " ; ".join(results) if results else "Game controller & webcam passthrough configured."
    except Exception as e:
        return False, f"Error configuring game controller passthrough: {str(e)}"


def patch_framework_titlebar() -> Tuple[bool, str]:
    """
    Patches freeform multi-window caption button rendering across both framework-res.apk
    (bypassing MaterialButton tint collision via decor_caption.xml View tag, and enforcing
    white caption button colors) and SystemUI.apk (enforcing solid white focused and 50%
    dimmed unfocused controls with white vector fills) via OverlayFS deployment.
    """
    try:
        from recipes.waydroid_native.titlebar_patch import patch_framework_titlebar_colors
        return patch_framework_titlebar_colors()
    except ImportError as e:
        return False, f"Titlebar patch module unavailable: {e}"
    except Exception as e:
        return False, f"Titlebar patch error: {e}"


def tune_chromium_rendering() -> Tuple[bool, str]:
    """
    Provisions Chromium command-line overrides (--disable-features=AndroidSurfaceControl,SurfaceControl)
    across Chrome, Android System WebView, Brave, Chromium, and Edge with 0777 permissions in both
    running container (/data/local/tmp/) and persistence overlay (/var/lib/waydroid/overlay/data/local/tmp/).

    Eliminates multi-window freeform transparent webpage rendering by forcing Chromium's Blink/Skia
    GPU compositor to render into the primary Activity window canvas rather than punching a translucent
    hole for a detached SurfaceControl.
    """
    flag_content = "chrome --disable-features=AndroidSurfaceControl,SurfaceControl\n"
    flag_targets = [
        "chrome-command-line",
        "webview-command-line",
        "brave-command-line",
        "chromium-command-line",
        "edge-command-line",
    ]
    results = []
    overlay_success = False
    container_success = False
    try:
        # 1. Direct deployment to OverlayFS persistence directory
        overlay_base = "/var/lib/waydroid/overlay"
        overlay_tmp = os.path.join(overlay_base, "data/local/tmp")
        if os.path.isdir(overlay_base) or os.path.isdir("/var/lib/waydroid"):
            res_mkdir = subprocess.run(["sudo", "mkdir", "-p", overlay_tmp], capture_output=True, text=True)
            if res_mkdir.returncode == 0:
                subprocess.run(["sudo", "chmod", "777", overlay_tmp], capture_output=True)
                write_errors = []
                for fname in flag_targets:
                    target = os.path.join(overlay_tmp, fname)
                    res_tee = subprocess.run(
                        ["sudo", "tee", target],
                        input=flag_content,
                        text=True,
                        capture_output=True
                    )
                    if res_tee.returncode != 0:
                        write_errors.append(f"{fname}: {res_tee.stderr.strip() or 'tee failed'}")
                    else:
                        subprocess.run(["sudo", "chmod", "777", target], capture_output=True)
                if not write_errors:
                    overlay_success = True
                    results.append("Provisioned Chromium command-line flags in OverlayFS.")
                else:
                    results.append(f"OverlayFS flags write errors: {', '.join(write_errors)}")
            else:
                results.append(f"Failed to create OverlayFS directory {overlay_tmp}: {res_mkdir.stderr.strip()}")

        # 2. Live deployment to active container via lxc-attach
        container_cmds = [
            "mkdir -p /data/local/tmp",
            "chmod 777 /data/local/tmp",
        ]
        for fname in flag_targets:
            container_cmds.append(f"printf 'chrome --disable-features=AndroidSurfaceControl,SurfaceControl\\n' > /data/local/tmp/{fname}")
            container_cmds.append(f"chmod 777 /data/local/tmp/{fname}")

        cmd_str = "export PATH=/system/bin:/system/xbin; " + " ; ".join(container_cmds)
        res_lxc = subprocess.run(
            ["sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "--", "/system/bin/sh", "-c", cmd_str],
            capture_output=True, text=True, timeout=4
        )
        if res_lxc.returncode == 0:
            container_success = True
            results.append("Synchronized Chromium command-line flags into active container.")
        else:
            err_msg = res_lxc.stderr.strip() or f"exit code {res_lxc.returncode}"
            results.append(f"Live container sync skipped or unavailable ({err_msg}).")

        overall_ok = overlay_success or container_success
        return overall_ok, " ; ".join(results) if results else "No Chromium flag targets provisioned."
    except Exception as e:
        return False, f"Chromium tuning error: {e}"


def ensure_linkerconfig() -> Tuple[bool, str]:
    """
    Ensures full Android 13 dynamic linker configuration (APEX namespaces, SPHAL/VNDK graphics
    libraries) is permanently generated across all container boots via an Android init hook,
    a systemd service watchdog, and immediate container execution.
    """
    try:
        # 1. Deploy permanent init hook into Android system overlay
        overlay_init_dir = "/var/lib/waydroid/overlay/system/etc/init"
        if os.path.exists("/var/lib/waydroid/overlay/system"):
            rc_content = (
                "# Purr: Generate full dynamic linker configuration with APEX & SPHAL namespaces\n"
                "on post-fs-data\n"
                "    exec -- /system/bin/linkerconfig --target /linkerconfig\n"
            )
            subprocess.run(["sudo", "mkdir", "-p", overlay_init_dir], capture_output=True)
            p = subprocess.Popen(
                ["sudo", "tee", f"{overlay_init_dir}/purr_linkerconfig.rc"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True
            )
            p.communicate(input=rc_content)
            subprocess.run(["sudo", "chmod", "644", f"{overlay_init_dir}/purr_linkerconfig.rc"], capture_output=True)

        # 2. Deploy systemd service post-start watchdog
        watchdog_script = (
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "for i in {1..15}; do\n"
            "    STATUS=$(lxc-info -P /var/lib/waydroid/lxc -n waydroid -sH 2>/dev/null || true)\n"
            "    if [ \"$STATUS\" = \"RUNNING\" ]; then break; fi\n"
            "    sleep 0.5\n"
            "done\n"
            "lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/sh -c \\\n"
            "    \"export PATH=/system/bin:/system/xbin; \\\n"
            "     if [ ! -f /linkerconfig/ld.config.txt ] || ! grep -q 'namespace.sphal' /linkerconfig/ld.config.txt 2>/dev/null; then \\\n"
            "         /system/bin/linkerconfig --target /linkerconfig 2>/dev/null || true; \\\n"
            "     fi\" 2>/dev/null || true\n"
            "if systemctl is-active --quiet firewalld 2>/dev/null; then\n"
            "    if ! firewall-cmd --zone=trusted --query-interface=waydroid0 2>/dev/null; then\n"
            "        firewall-cmd --zone=trusted --add-interface=waydroid0 --permanent >/dev/null 2>&1 || true\n"
            "        firewall-cmd --reload >/dev/null 2>&1 || true\n"
            "    fi\n"
            "fi\n"
            "exit 0\n"
        )
        subprocess.run(["sudo", "mkdir", "-p", "/usr/lib/purr"], capture_output=True)
        p = subprocess.Popen(
            ["sudo", "tee", "/usr/lib/purr/waydroid-container-post-start.sh"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True
        )
        p.communicate(input=watchdog_script)
        subprocess.run(["sudo", "chmod", "+x", "/usr/lib/purr/waydroid-container-post-start.sh"], capture_output=True)

        # 3. Deploy systemd drop-in override
        dropin_dir = "/etc/systemd/system/waydroid-container.service.d"
        dropin_content = "[Service]\nExecStartPost=/usr/lib/purr/waydroid-container-post-start.sh\n"
        subprocess.run(["sudo", "mkdir", "-p", dropin_dir], capture_output=True)
        p = subprocess.Popen(
            ["sudo", "tee", f"{dropin_dir}/10-purr-hardening.conf"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True
        )
        p.communicate(input=dropin_content)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], capture_output=True)

        # 4. Immediate execution if container is running
        cmd = [
            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c",
            "export PATH=/system/bin:/system/xbin; "
            "if [ -x /system/bin/linkerconfig ]; then "
            "  /system/bin/linkerconfig --target /linkerconfig; "
            "fi"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return True, "Android linker configuration permanently provisioned with APEX & SPHAL namespaces."
        return True, "Permanent linker configuration provisioned for next container boot."
    except Exception as e:
        return False, f"Error configuring linkerconfig: {e}"
