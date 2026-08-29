#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Full Lifecycle Implementation
Project Tuki / Purr Ecosystem
"""

import os
import sys
import json
import time
import subprocess
import shutil
from typing import Dict, List, Optional, Any, Tuple

from recipes.base import BaseRecipe, RecipeResult
from recipes.waydroid_native.system_tuning import (
    detect_hardware,
    ensure_binderfs,
    configure_network_forwarding,
    apply_waydroid_properties,
    tune_android_keyboard_and_freeform,
    patch_numpad_keychars,
    patch_waydroid_clipboard_service
)
from recipes.waydroid_native.kwin_rules import apply_kwin_rules, remove_kwin_rules
from recipes.waydroid_native.fileshare import setup_folder_shares
from recipes.waydroid_native.desktop_sync import sync_android_desktop_entries


class WaydroidNativeRecipe(BaseRecipe):
    id = "waydroid-native"
    name = "Waydroid Native Android Subsystem"
    description = "Turnkey Android app runtime on Arch Linux & KDE Plasma 6 with auto ARM translation (libndk), multi-window freeform mode, KWin window rules, PipeWire audio, folder sharing, and Purr APK CLI integration."
    version = "1.0.0"
    author = "Project Tuki / Purr Ecosystem"
    category = "Runtimes & Emulation"
    tags = ["android", "waydroid", "arm-translation", "kde-plasma", "pipewire", "kwin", "purr-apk"]
    icon = "application-vnd.android.package-archive"

    def check_prerequisites(self) -> RecipeResult:
        issues = []
        details = {}

        # 1. Check Wayland Compositor
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        if not wayland_display:
            issues.append("Active session is not running on Wayland. Waydroid requires KDE Plasma Wayland.")
        details["wayland_display"] = wayland_display or "None"

        # 2. Check Hardware
        hw_info = detect_hardware()
        details["hardware"] = hw_info

        # 3. Check Kernel & Binder
        binder_ok, binder_msg = ensure_binderfs()
        details["binder"] = binder_msg
        if not binder_ok:
            issues.append(f"Kernel BinderFS unavailable: {binder_msg}")

        # 4. Check Required Commands & Packages
        required_bins = {
            "waydroid": "waydroid",
            "lxc-info": "lxc",
            "nft": "nftables",
            "dnsmasq": "dnsmasq",
            "adb": "android-tools",
            "wl-copy": "wl-clipboard"
        }
        missing_pkgs = []
        for b, pkg in required_bins.items():
            if not shutil.which(b):
                missing_pkgs.append(pkg)

        if missing_pkgs:
            issues.append(f"Missing required packages: {', '.join(missing_pkgs)}")
        details["missing_packages"] = missing_pkgs

        # 5. Check waydroid-extras
        has_extras = os.path.exists("/usr/bin/waydroid-extras")
        details["waydroid_extras"] = has_extras
        if not has_extras:
            issues.append("Missing 'waydroid-extras' (AUR: waydroid-script-git).")

        success = len(issues) == 0
        msg = "All system prerequisites satisfied." if success else f"Prerequisites incomplete: {'; '.join(issues)}"
        return RecipeResult(success, msg, details)

    def prune(self) -> RecipeResult:
        """
        Cleanly purges legacy Waydroid installations, images, and user data.
        """
        try:
            # 1. Stop services & sessions
            subprocess.run(["sudo", "systemctl", "stop", "waydroid-container.service"], capture_output=True)
            subprocess.run(["sudo", "/usr/bin/python3", "/usr/bin/waydroid", "session", "stop"], capture_output=True)

            # 2. Remove desktop files
            app_dir = os.path.expanduser("~/.local/share/applications")
            if os.path.exists(app_dir):
                for f in os.listdir(app_dir):
                    if f.startswith("waydroid.") and f.endswith(".desktop"):
                        try:
                            os.remove(os.path.join(app_dir, f))
                        except Exception:
                            pass

            # 3. Remove container data & images
            subprocess.run(["sudo", "rm", "-rf", "/var/lib/waydroid", "/var/lib/waydroid-extra"], capture_output=True)
            user_waydroid = os.path.expanduser("~/.local/share/waydroid")
            if os.path.exists(user_waydroid):
                shutil.rmtree(user_waydroid, ignore_errors=True)

            # 4. Remove KWin rules
            remove_kwin_rules()

            # 5. Rebuild desktop cache
            subprocess.run(["kbuildsycoca6", "--noincremental"], capture_output=True)

            return RecipeResult(True, "Successfully pruned legacy Waydroid containers, images, desktop entries, and configurations.")
        except Exception as e:
            return RecipeResult(False, f"Failed to prune Waydroid state: {str(e)}")

    def provision(self, options: Optional[Dict[str, Any]] = None) -> RecipeResult:
        """
        Provisions a fresh Waydroid environment with GAPPS / Vanilla, libndk ARM translation,
        and GPU gralloc acceleration.
        """
        options = options or {}
        system_type = options.get("system_type", "GAPPS")  # GAPPS or VANILLA
        install_ndk = options.get("arm_translation", True)

        # 1. Ensure BinderFS & Network Forwarding
        binder_ok, binder_msg = ensure_binderfs()
        if not binder_ok:
            return RecipeResult(False, f"Cannot initialize: {binder_msg}")
        configure_network_forwarding()

        # 2. Hardware Detection
        hw_info = detect_hardware()

        # 3. Initialize Waydroid Container Images
        print(f"\n🐾 [1/4] Initializing Waydroid System Images ({system_type})...")
        init_cmd = ["sudo", "/usr/bin/python3", "/usr/bin/waydroid", "init", "-s", system_type, "-f"]
        res_init = subprocess.run(init_cmd)
        if res_init.returncode != 0:
            return RecipeResult(False, f"Waydroid init failed with exit code {res_init.returncode}")

        # 4. Apply Optimized System & Hardware Properties
        print(f"🐾 [2/4] Applying Multi-Window & Hardware Acceleration Properties...")
        applied_props = apply_waydroid_properties(hw_info)

        # 5. Enable and Start Container Service
        print(f"🐾 [3/4] Starting Waydroid Container Service...")
        subprocess.run(["sudo", "systemctl", "enable", "--now", "waydroid-container.service"], capture_output=True)

        # 6. Inject ARM Translation Layer (libndk)
        if install_ndk:
            print(f"🐾 [4/5] Injecting ARM Translation Layer (libndk for {hw_info['cpu_vendor'].upper()} CPU)...")
            extras_cmd = ["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid-extras", "install", "libndk"]
            res_extras = subprocess.run(extras_cmd)
            if res_extras.returncode != 0:
                print("⚠️  Warning: libndk injection exited with non-zero status. Will verify during doctor check.")

        # Restart container service to load translation libraries
        subprocess.run(["sudo", "systemctl", "restart", "waydroid-container.service"], capture_output=True)
        time.sleep(3)

        # 7. Pre-install Essential App Stores (F-Droid & Aurora Store)
        if options.get("preinstall_stores", True):
            print(f"🐾 [5/5] Pre-installing Essential Android App Stores (F-Droid & Aurora Store)...")
            self.install_essential_stores()

        return RecipeResult(True, "Waydroid container provisioned with multi-window, GPU acceleration, and ARM translation.", {
            "system_type": system_type,
            "hardware": hw_info,
            "properties": applied_props
        })

    def install_essential_stores(self) -> Tuple[bool, List[str]]:
        """
        Downloads and installs F-Droid and Aurora Store into the Waydroid container.
        """
        stores = {
            "F-Droid": "https://f-droid.org/F-Droid.apk",
            "Aurora Store": "https://auroraoss.com/downloads/AuroraStore/Release/preload/AuroraStore-preload-4.7.5.apk"
        }
        cache_dir = os.path.expanduser("~/.cache/purr/apks")
        os.makedirs(cache_dir, exist_ok=True)
        results = []

        for name, url in stores.items():
            apk_file = os.path.join(cache_dir, f"{name.replace(' ', '_')}.apk")
            if not os.path.exists(apk_file) or os.path.getsize(apk_file) < 1000000:
                print(f"  --> Downloading {name}...")
                subprocess.run(["curl", "-sSL", url, "-o", apk_file], capture_output=True, timeout=180)

            if os.path.exists(apk_file) and os.path.getsize(apk_file) > 1000000:
                ok, msg = self.install_apk(apk_file)
                if ok:
                    results.append(f"Installed {name}")
                else:
                    results.append(f"Failed to install {name}: {msg}")
            else:
                results.append(f"Failed to download valid APK for {name}")

        return True, results

    def integrate_desktop(self) -> RecipeResult:
        """
        Applies KWin Plasma 6 rules, folder sharing, keyboard tuning, and desktop integration.
        """
        results = []

        # 1. KWin Rules (SSD decorations, resizable, floating geometry)
        kwin_ok, kwin_msg = apply_kwin_rules()
        results.append(kwin_msg)

        # 2. Keyboard & Freeform Window Runtime Tuning
        tune_msgs = tune_android_keyboard_and_freeform()
        results.extend(tune_msgs)

        # 3. Patch NumPad Key Character Map, Clipboard Service & Helper
        kcm_ok, kcm_msg = patch_numpad_keychars()
        results.append(kcm_msg)
        clip_ok, clip_msg = patch_waydroid_clipboard_service()
        results.append(clip_msg)
        helper_ok, helper_msg = install_purr_clip_helper()
        results.append(helper_msg)

        # 4. Folder Shares
        share_ok, share_msgs = setup_folder_shares()
        results.extend(share_msgs)

        # 5. Android Desktop Entries & Kickoff Sync
        sync_ok, sync_entries = sync_android_desktop_entries()
        results.append(f"Generated {len(sync_entries)} native KDE Plasma desktop launchers.")

        # 6. Refresh desktop sycoca cache
        subprocess.run(["kbuildsycoca6", "--noincremental"], capture_output=True)
        results.append("Refreshed KDE Plasma application cache.")

        return RecipeResult(True, "KDE Plasma 6 desktop integrations applied successfully.", {"log": results})

    def doctor(self) -> RecipeResult:
        """
        Comprehensive health diagnostics for the Waydroid native subsystem.
        """
        diagnostics = {}
        healthy = True
        warnings = []

        # 1. Binder Check
        binder_mounted = os.path.exists("/dev/binderfs/binder-control") or os.path.exists("/dev/binder")
        diagnostics["binderfs"] = "ACTIVE" if binder_mounted else "MISSING"
        if not binder_mounted:
            healthy = False
            warnings.append("BinderFS is not active.")

        # 2. Container Service Check
        res_svc = subprocess.run(["systemctl", "is-active", "waydroid-container.service"], capture_output=True, text=True)
        svc_active = (res_svc.stdout.strip() == "active")
        diagnostics["container_service"] = "RUNNING" if svc_active else "STOPPED"
        if not svc_active:
            healthy = False
            warnings.append("waydroid-container.service is not active.")

        # 3. Network Bridge Check
        res_ip = subprocess.run(["ip", "addr", "show", "waydroid0"], capture_output=True, text=True)
        net_active = (res_ip.returncode == 0 and "192.168.240." in res_ip.stdout)
        diagnostics["network_bridge"] = "ACTIVE (192.168.240.x)" if net_active else "INACTIVE"
        if not net_active:
            warnings.append("waydroid0 bridge is not active yet (will initialize on first session start).")

        # 4. ARM Translation Check
        ndk_installed = False
        overlay_lib = "/var/lib/waydroid/overlay/system/lib64/libndk_translation.so"
        if os.path.exists(overlay_lib) or os.path.exists("/var/lib/waydroid/rootfs/system/lib64/libndk_translation.so"):
            ndk_installed = True
        diagnostics["arm_translation"] = "INSTALLED (libndk)" if ndk_installed else "NOT INSTALLED"

        # 5. Multi-Window Mode Check
        mw_enabled = False
        cfg_path = "/var/lib/waydroid/waydroid.cfg"
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r") as f:
                    content = f.read()
                    if "persist.waydroid.multi_windows = true" in content:
                        mw_enabled = True
            except Exception:
                pass
        if not mw_enabled:
            res_mw = subprocess.run(["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid", "prop", "get", "persist.waydroid.multi_windows"], capture_output=True, text=True)
            mw_enabled = (res_mw.stdout.strip() == "true")
        diagnostics["multi_window_mode"] = "ENABLED (Freeform Desktop Windows)" if mw_enabled else "DISABLED"

        # 6. Google Device Certification ID Helper
        device_id = self.get_android_id()
        diagnostics["google_play_device_id"] = device_id if device_id else "Not registered / pending first boot"

        msg = "Waydroid Native Subsystem is in healthy condition." if healthy else f"Doctor found issues: {'; '.join(warnings)}"
        return RecipeResult(healthy, msg, diagnostics)

    def get_android_id(self) -> Optional[str]:
        """
        Attempts to read the Android GSF ID for Google Play Store device certification.
        """
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        try:
            res = subprocess.run(["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid-extras", "certified"], capture_output=True, text=True, env=clean_env)
            for line in res.stdout.split("\n"):
                if "Android ID:" in line or line.strip().isdigit():
                    tokens = [t for t in line.split() if t.isdigit() and len(t) > 10]
                    if tokens:
                        return tokens[0]
        except Exception:
            pass
        return None

    def teardown(self) -> RecipeResult:
        """
        Full removal and clean teardown.
        """
        self.prune()
        subprocess.run(["sudo", "systemctl", "disable", "waydroid-container.service"], capture_output=True)
        return RecipeResult(True, "Waydroid native subsystem torn down cleanly.")

    # CLI App helpers for purr apk / purr android
    def install_apk(self, apk_path: str) -> Tuple[bool, str]:
        if not os.path.exists(apk_path):
            return False, f"APK file not found: {apk_path}"
        abs_apk = os.path.abspath(apk_path)
        file_size = os.path.getsize(abs_apk)
        if file_size < 10000:
            return False, f"Invalid APK file size: {file_size} bytes."

        # 1. Primary: Direct streaming installation via PackageManager in LXC
        try:
            cmd = [
                "sudo", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", f"PATH=/system/bin:/system/xbin pm install -r -g -S {file_size}"
            ]
            with open(abs_apk, "rb") as f:
                res = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            if "Success" in res.stdout or "Success" in res.stderr:
                sync_android_desktop_entries()
                return True, f"Installed {os.path.basename(apk_path)} successfully into Waydroid."
        except Exception:
            pass

        # 2. Fallback: waydroid app install
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            cmd = [waydroid_bin, "app", "install", abs_apk]
            res = subprocess.run(cmd, capture_output=True, text=True, env=clean_env)
            if res.returncode == 0:
                sync_android_desktop_entries()
                return True, f"Installed {os.path.basename(apk_path)} successfully into Waydroid."
            return False, f"Install failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Error installing APK: {str(e)}"

    @staticmethod
    def is_keyguard_locked() -> bool:
        """
        Checks whether Android Keyguard (Pattern/PIN/Password lock screen) is currently active.
        """
        try:
            res = subprocess.run([
                "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin dumpsys window policy"
            ], capture_output=True, text=True, timeout=1.2)
            if res.returncode == 0:
                return ("showing=true" in res.stdout or "mIsShowing=true" in res.stdout) and ("secure=true" in res.stdout or "deviceHasKeyguard=true" in res.stdout)
            return False
        except Exception:
            return False

    def launch_app(self, package_name: str) -> Tuple[bool, str]:
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            from recipes.waydroid_native.system_tuning import get_waydroid_prop
            is_multi = (get_waydroid_prop("persist.waydroid.multi_windows", "true").lower() == "true")
            locked = self.is_keyguard_locked()

            if is_multi:
                if locked:
                    # In Multi-Window mode, trigger the native floating ConfirmLockPattern window
                    subprocess.run([
                        "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                        "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin am start -a android.app.action.CONFIRM_DEVICE_CREDENTIAL"
                    ], capture_output=True)
                    subprocess.run([waydroid_bin, "app", "launch", "com.android.settings"], capture_output=True, env=clean_env)
                    import time
                    time.sleep(0.5)

                # Launch via official Waydroid session IPC
                cmd = [waydroid_bin, "app", "launch", package_name]
                res = subprocess.run(cmd, capture_output=True, text=True, env=clean_env)
                if res.returncode == 0:
                    if locked:
                        return True, f"Subsystem is locked. Opened pattern unlock window to launch {package_name}."
                    return True, f"Launched {package_name} in floating freeform mode."
                return False, f"Launch failed: {res.stderr.strip() or res.stdout.strip()}"
            else:
                # Full Subsystem Tablet UI Mode:
                # Ensure the unified Waydroid Full UI tablet window is visible
                subprocess.Popen([waydroid_bin, "show-full-ui"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(0.5)

                cmd = [waydroid_bin, "app", "launch", package_name]
                res = subprocess.run(cmd, capture_output=True, text=True, env=clean_env)
                if res.returncode == 0:
                    return True, f"Launched {package_name} in Full Tablet UI."
                return False, f"Launch failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Error launching app: {str(e)}"

    def list_apps(self) -> List[Dict[str, str]]:
        apps = []
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            res = subprocess.run([waydroid_bin, "app", "list"], capture_output=True, text=True, env=clean_env)
            for line in res.stdout.split("\n"):
                if line.strip() and not line.startswith("[") and ":" in line:
                    parts = line.split(":", 1)
                    name = parts[0].strip()
                    pkg = parts[1].strip() if len(parts) > 1 else name
                    apps.append({"name": name, "package": pkg})
        except Exception:
            pass

        # Fallback 1: Desktop entries in ~/.local/share/applications/
        if not apps:
            app_dir = os.path.expanduser("~/.local/share/applications")
            if os.path.exists(app_dir):
                for f in os.listdir(app_dir):
                    if f.startswith("waydroid.") and f.endswith(".desktop"):
                        pkg = f.replace("waydroid.", "").replace(".desktop", "")
                        app_name = pkg
                        try:
                            with open(os.path.join(app_dir, f), "r") as df:
                                for line in df:
                                    if line.startswith("Name="):
                                        app_name = line.replace("Name=", "").strip()
                                        break
                        except Exception:
                            pass
                        apps.append({"name": app_name, "package": pkg})

        # Fallback 2: Direct shell package query
        if not apps:
            try:
                res_pm = subprocess.run(["sudo", "env", "PATH=/usr/bin:/usr/local/bin", "/usr/bin/python3", "/usr/bin/waydroid", "shell", "pm", "list", "packages", "-3"], capture_output=True, text=True, env=clean_env)
                for line in res_pm.stdout.split("\n"):
                    if line.startswith("package:"):
                        pkg = line.replace("package:", "").strip()
                        apps.append({"name": pkg.split(".")[-1].capitalize(), "package": pkg})
            except Exception:
                pass

        return apps
