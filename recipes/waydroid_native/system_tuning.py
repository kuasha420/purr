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
                    line = "binder /dev/binderfs binder default 0 0\n"
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
        ("persist.waydroid.fake_touch", "false"),
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
    for key, val in props:
        try:
            cmd = ["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid", "prop", "set", key, val]
            subprocess.run(cmd, capture_output=True, env=clean_env)
            if f"{key}={val}" not in applied:
                applied.append(f"{key}={val}")
        except Exception:
            pass

    return applied


def tune_android_keyboard_and_freeform() -> List[str]:
    """
    Applies runtime Android system settings to disable on-screen soft keyboard
    when hardware keyboard is present and enforce freeform multi-window mode.
    """
    settings_commands = [
        ("secure", "show_ime_with_hard_keyboard", "0"),
        ("secure", "show_ime_with_hard_keyboard_status", "0"),
        ("global", "enable_freeform_support", "1"),
        ("global", "force_resizable_activities", "1"),
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
    return results


def patch_numpad_keychars() -> Tuple[bool, str]:
    """
    Patches Generic.kcm in the system overlay so physical NumPad keys always output numbers.
    """
    kcm_overlay_dir = "/var/lib/waydroid/overlay/system/usr/keychars"
    kcm_overlay_file = os.path.join(kcm_overlay_dir, "Generic.kcm")
    src_kcm = "/var/lib/waydroid/rootfs/system/usr/keychars/Generic.kcm"

    try:
        subprocess.run(["sudo", "mkdir", "-p", kcm_overlay_dir], capture_output=True)
        if not os.path.exists(kcm_overlay_file) and os.path.exists(src_kcm):
            subprocess.run(["sudo", "cp", src_kcm, kcm_overlay_file], capture_output=True)

        if os.path.exists(kcm_overlay_file):
            script = """
kcm_path = "/var/lib/waydroid/overlay/system/usr/keychars/Generic.kcm"
with open(kcm_path, "r") as f:
    content = f.read()

replacements = {
    "key NUMPAD_0 {\\n    label:                              '0'\\n    base:                               fallback INSERT\\n    numlock:                            '0'\\n}": "key NUMPAD_0 {\\n    label:                              '0'\\n    base:                               '0'\\n    numlock:                            '0'\\n}",
    "key NUMPAD_1 {\\n    label:                              '1'\\n    base:                               fallback MOVE_END\\n    numlock:                            '1'\\n}": "key NUMPAD_1 {\\n    label:                              '1'\\n    base:                               '1'\\n    numlock:                            '1'\\n}",
    "key NUMPAD_2 {\\n    label:                              '2'\\n    base:                               fallback DPAD_DOWN\\n    numlock:                            '2'\\n}": "key NUMPAD_2 {\\n    label:                              '2'\\n    base:                               '2'\\n    numlock:                            '2'\\n}",
    "key NUMPAD_3 {\\n    label:                              '3'\\n    base:                               fallback PAGE_DOWN\\n    numlock:                            '3'\\n}": "key NUMPAD_3 {\\n    label:                              '3'\\n    base:                               '3'\\n    numlock:                            '3'\\n}",
    "key NUMPAD_4 {\\n    label:                              '4'\\n    base:                               fallback DPAD_LEFT\\n    numlock:                            '4'\\n}": "key NUMPAD_4 {\\n    label:                              '4'\\n    base:                               '4'\\n    numlock:                            '4'\\n}",
    "key NUMPAD_5 {\\n    label:                              '5'\\n    base:                               fallback DPAD_CENTER\\n    numlock:                            '5'\\n}": "key NUMPAD_5 {\\n    label:                              '5'\\n    base:                               '5'\\n    numlock:                            '5'\\n}",
    "key NUMPAD_6 {\\n    label:                              '6'\\n    base:                               fallback DPAD_RIGHT\\n    numlock:                            '6'\\n}": "key NUMPAD_6 {\\n    label:                              '6'\\n    base:                               '6'\\n    numlock:                            '6'\\n}",
    "key NUMPAD_7 {\\n    label:                              '7'\\n    base:                               fallback MOVE_HOME\\n    numlock:                            '7'\\n}": "key NUMPAD_7 {\\n    label:                              '7'\\n    base:                               '7'\\n    numlock:                            '7'\\n}",
    "key NUMPAD_8 {\\n    label:                              '8'\\n    base:                               fallback DPAD_UP\\n    numlock:                            '8'\\n}": "key NUMPAD_8 {\\n    label:                              '8'\\n    base:                               '8'\\n    numlock:                            '8'\\n}",
    "key NUMPAD_9 {\\n    label:                              '9'\\n    base:                               fallback PAGE_UP\\n    numlock:                            '9'\\n}": "key NUMPAD_9 {\\n    label:                              '9'\\n    base:                               '9'\\n    numlock:                            '9'\\n}",
    "key NUMPAD_DOT {\\n    label:                              '.'\\n    base:                               fallback FORWARD_DEL\\n    numlock:                            '.'\\n}": "key NUMPAD_DOT {\\n    label:                              '.'\\n    base:                               '.'\\n    numlock:                            '.'\\n}"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(kcm_path, "w") as f:
    f.write(content)
"""
            subprocess.run(["sudo", "python3", "-c", script], capture_output=True)
            return True, "NumPad KeyCharacterMap patched for desktop keyboard support."
        return False, "Generic.kcm file not found."
    except Exception as e:
        return False, f"Keymap patch error: {str(e)}"
