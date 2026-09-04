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
import threading
from typing import Dict, List, Optional, Any, Tuple

from recipes.base import BaseRecipe, RecipeResult
from recipes.waydroid_native.system_tuning import (
    detect_hardware,
    ensure_binderfs,
    configure_network_forwarding,
    apply_waydroid_properties,
    tune_android_keyboard_and_freeform,
    patch_numpad_keychars,
    patch_waydroid_clipboard_service,
    patch_waydroid_mount_helper,
    patch_waydroid_lxc_helper,
    patch_waydroid_app_manager,
    patch_waydroid_user_manager,
    install_purr_clip_helper,
    tune_game_controller_and_webcam_passthrough,
    patch_framework_titlebar,
    tune_chromium_rendering,
    ensure_linkerconfig,
    ensure_container_unfrozen
)
from recipes.waydroid_native.kwin_rules import apply_kwin_rules, remove_kwin_rules
from recipes.waydroid_native.fileshare import setup_folder_shares
from recipes.waydroid_native.desktop_sync import sync_android_desktop_entries


def sync_container_input_nodes():
    """
    Ensures ONLY host gamepads and joysticks are passed into the container.
    Mouse and keyboard MUST be handled exclusively by Wayland (wl_pointer/wl_keyboard)
    to prevent duplicate/erratic cursor movements and stray keycode assist triggers.
    """
    try:
        import glob
        # 1. Gamepad / Joystick nodes (js0..js3)
        for dev in glob.glob("/dev/input/js*"):
            st = os.stat(dev)
            major, minor = os.major(st.st_rdev), os.minor(st.st_rdev)
            name = os.path.basename(dev)
            subprocess.run([
                "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", f"export PATH=/system/bin:/system/xbin; [ ! -e /dev/input/{name} ] && mknod -m 666 /dev/input/{name} c {major} {minor}"
            ], capture_output=True, timeout=1.0)

        # 2. Gamepad event nodes (DualSense, Xbox, generic joysticks)
        patterns = [
            "/dev/input/by-id/*joystick*",
            "/dev/input/by-id/*DualSense*",
            "/dev/input/by-id/*Wireless_Controller*",
            "/dev/input/by-id/*gamepad*",
            "/dev/input/by-id/*Gamepad*",
            "/dev/input/by-id/*Xbox*"
        ]
        for pat in patterns:
            for link in glob.glob(pat):
                if os.path.islink(link):
                    target = os.path.realpath(link)
                    if "event" in target:
                        st = os.stat(target)
                        major, minor = os.major(st.st_rdev), os.minor(st.st_rdev)
                        name = os.path.basename(target)
                        subprocess.run([
                            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                            "--", "/system/bin/sh", "-c", f"export PATH=/system/bin:/system/xbin; [ ! -e /dev/input/{name} ] && mknod -m 666 /dev/input/{name} c {major} {minor}"
                        ], capture_output=True, timeout=1.0)
    except Exception:
        pass


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
        print(f"\n🐾 [1/5] Initializing Waydroid System Images ({system_type})...")
        init_cmd = ["sudo", "/usr/bin/python3", "/usr/bin/waydroid", "init", "-s", system_type, "-f"]
        res_init = subprocess.run(init_cmd)
        if res_init.returncode != 0:
            return RecipeResult(False, f"Waydroid init failed with exit code {res_init.returncode}")

        # 4. Apply Optimized System & Hardware Properties
        print(f"🐾 [2/5] Applying Multi-Window & Hardware Acceleration Properties...")
        applied_props = apply_waydroid_properties(hw_info)

        # 5. Enable and Start Container Service
        print(f"🐾 [3/5] Starting Waydroid Container Service...")
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
        Downloads and installs F-Droid and Aurora Store (Purr Edition with curated architecture profiles) into the Waydroid container.
        """
        cache_dir = os.path.expanduser("~/.cache/purr/apks")
        os.makedirs(cache_dir, exist_ok=True)
        results = []

        # 1. Install F-Droid
        fdroid_apk = os.path.join(cache_dir, "F-Droid.apk")
        if not os.path.exists(fdroid_apk) or os.path.getsize(fdroid_apk) < 1000000:
            print("  --> Downloading F-Droid...")
            subprocess.run(["curl", "-fsSL", "--connect-timeout", "15", "--max-time", "180", "https://f-droid.org/F-Droid.apk", "-o", fdroid_apk], capture_output=True)
        if os.path.exists(fdroid_apk) and os.path.getsize(fdroid_apk) > 1000000:
            ok, msg = self.install_apk(fdroid_apk)
            results.append("Installed F-Droid" if ok else f"Failed to install F-Droid: {msg}")
        else:
            results.append("Failed to download valid APK for F-Droid")

        # 2. Build & Install Aurora Store (Purr Edition with Curated Architecture Profiles)
        aurora_apk = os.path.join(cache_dir, "AuroraStore_PurrEdition.apk")
        try:
            from recipes.waydroid_native.aurora_patcher import build_and_sign_aurora_store
            print("  --> Patching & building Aurora Store with Curated Architecture Profiles...")
            b_ok, b_msg = build_and_sign_aurora_store(aurora_apk)
            if b_ok and os.path.exists(aurora_apk):
                ok, msg = self.install_apk(aurora_apk)
                results.append("Installed Aurora Store (Purr Edition)" if ok else f"Failed to install Aurora Store: {msg}")
            else:
                raise RuntimeError(b_msg)
        except Exception as e:
            # Fallback to upstream preload if build tools (apksigner/zipalign) are missing
            print(f"  ⚠️  Aurora Store patching unavailable ({e}). Falling back to upstream preload...")
            upstream_url = "https://auroraoss.com/downloads/AuroraStore/Release/preload/AuroraStore-preload-4.7.5.apk"
            fallback_apk = os.path.join(cache_dir, "AuroraStore_preload.apk")
            if not os.path.exists(fallback_apk) or os.path.getsize(fallback_apk) < 1000000:
                subprocess.run(["curl", "-fsSL", "--connect-timeout", "15", "--max-time", "180", upstream_url, "-o", fallback_apk], capture_output=True)
            if os.path.exists(fallback_apk) and os.path.getsize(fallback_apk) > 1000000:
                ok, msg = self.install_apk(fallback_apk)
                results.append("Installed Aurora Store (Upstream Preload)" if ok else f"Failed to install Aurora Store: {msg}")
            else:
                results.append("Failed to download valid fallback APK for Aurora Store")

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

        # 3. Patch NumPad Key Character Map, Clipboard Service, App & User Managers, Helper
        kcm_ok, kcm_msg = patch_numpad_keychars()
        results.append(kcm_msg)
        clip_ok, clip_msg = patch_waydroid_clipboard_service()
        results.append(clip_msg)
        mount_ok, mount_msg = patch_waydroid_mount_helper()
        results.append(mount_msg)
        lxc_ok, lxc_msg = patch_waydroid_lxc_helper()
        results.append(lxc_msg)
        appmgr_ok, appmgr_msg = patch_waydroid_app_manager()
        results.append(appmgr_msg)
        usrmgr_ok, usrmgr_msg = patch_waydroid_user_manager()
        results.append(usrmgr_msg)
        helper_ok, helper_msg = install_purr_clip_helper()
        results.append(helper_msg)
        titlebar_ok, titlebar_msg = patch_framework_titlebar()
        results.append(titlebar_msg)
        hw_ok, hw_msg = tune_game_controller_and_webcam_passthrough()
        results.append(hw_msg)
        chrome_ok, chrome_msg = tune_chromium_rendering()
        results.append(chrome_msg)
        linker_ok, linker_msg = ensure_linkerconfig()
        results.append(linker_msg)

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

    def stop_session(self) -> Tuple[bool, str]:
        """
        Cleanly stops active Waydroid sessions and user daemons without hanging.
        """
        subprocess.run(["systemctl", "--user", "stop", "waydroid-session.service"], capture_output=True, timeout=6)
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            subprocess.run([waydroid_bin, "session", "stop"], capture_output=True, timeout=5)
        except Exception:
            pass
        subprocess.run(["pkill", "-9", "-f", "waydroid session start"], capture_output=True)
        return True, "Waydroid session stopped."

    def start_session(self, background: bool = True) -> Tuple[bool, str]:
        """
        Starts Waydroid session cleanly using user systemd service or background daemon.
        """
        res = subprocess.run(["systemctl", "--user", "is-active", "waydroid-session.service"], capture_output=True, text=True)
        if res.returncode == 0 and "active" in res.stdout:
            return True, "Waydroid session is already active."

        # Try user systemd service first for full desktop GUI integration
        res = subprocess.run(["systemctl", "--user", "start", "waydroid-session.service"], capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            for _ in range(20):
                time.sleep(0.25)
                check = subprocess.run(["systemctl", "--user", "is-active", "waydroid-session.service"], capture_output=True, text=True)
                if "active" in check.stdout:
                    return True, "Waydroid session started via systemd service."

        # Fallback to direct invocation with full environment
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        env = os.environ.copy()
        env["PATH"] = "/usr/bin:/bin:" + env.get("PATH", "")
        if "WAYLAND_DISPLAY" not in env:
            env["WAYLAND_DISPLAY"] = "wayland-0"
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
        env["XDG_SESSION_TYPE"] = "wayland"

        if background:
            subprocess.Popen([waydroid_bin, "session", "start"],
                             env=env,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True, close_fds=True)
            for _ in range(20):
                time.sleep(0.25)
                res = subprocess.run(["pgrep", "-f", "waydroid session start"], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    break
            return True, "Waydroid session started in background."
        else:
            subprocess.run([waydroid_bin, "session", "start"], env=env)
            return True, "Waydroid session started."

    def restart_session(self) -> Tuple[bool, str]:
        """
        Full reliable end-to-end restart sequence:
        1. Stop user session
        2. Restart LXC container service
        3. Start session daemon via systemd user service
        4. Wait for Android boot completion
        5. Re-apply desktop rules, gamepad passthrough, and overlay permissions
        """
        self.stop_session()
        time.sleep(0.6)
        subprocess.run(["sudo", "systemctl", "restart", "waydroid-container.service"], capture_output=True, timeout=12)
        time.sleep(1.5)
        self.start_session(background=True)

        # Wait for Android subsystem boot completion
        for _ in range(25):
            res = subprocess.run([
                "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; getprop sys.boot_completed"
            ], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip() == "1":
                break
            time.sleep(0.5)

        # Regenerate full APEX dynamic linker configuration
        ensure_linkerconfig()

        # Clean dangling synthetic password handles ONLY if spblob directory is empty/missing
        try:
            spblob_check = subprocess.run([
                "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                "--", "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; ls /data/system_de/0/spblob 2>/dev/null"
            ], capture_output=True, text=True, timeout=1.5)
            if not spblob_check.stdout.strip():
                for db in [
                    os.path.expanduser("~/.local/share/waydroid/data/system/locksettings.db"),
                    "/var/lib/waydroid/data/system/locksettings.db",
                    "/var/lib/waydroid/overlay/data/system/locksettings.db"
                ]:
                    if os.path.exists(db):
                        subprocess.run([
                            "sqlite3", db,
                            "DELETE FROM locksettings WHERE name LIKE '%sp-handle%' OR name LIKE 'lockscreen.password%' OR name LIKE 'lockscreen.pattern%';"
                        ], capture_output=True, timeout=2.0)
        except Exception:
            pass

        time.sleep(1.0)
        # Dismiss initial keyguard so subsystem is permanently unlocked and ready for apps
        subprocess.run([
            "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
            "--", "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; wm dismiss-keyguard; input keyevent 82"
        ], capture_output=True, timeout=3.0)

        sync_container_input_nodes()
        self.integrate_desktop()
        return True, "Waydroid container and session restarted cleanly."

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

    @staticmethod
    def spawn_post_unlock_launcher(package_name: str) -> None:
        """
        Spawns a detached background watcher that monitors Keyguard unlock state
        and automatically launches the requested app in floating freeform mode.
        """
        curr_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        watcher_code = f"""
import sys, os, time, subprocess, shutil
for _p in [{repr(curr_dir)}, "/usr/share/purr", "/usr/local/share/purr"]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
from recipes.waydroid_native.recipe import WaydroidNativeRecipe
waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"

for _ in range(120):
    time.sleep(0.5)
    try:
        if not WaydroidNativeRecipe.is_keyguard_locked():
            time.sleep(0.3)
            clean_env = dict(**subprocess.os.environ)
            clean_env["PATH"] = "/usr/bin:/usr/local/bin:" + clean_env.get("PATH", "")
            subprocess.run([waydroid_bin, "app", "launch", {repr(package_name)}], env=clean_env)
            break
    except Exception:
        pass
"""
        python_bin = "/usr/bin/python3" if os.path.exists("/usr/bin/python3") else sys.executable
        subprocess.Popen(
            [python_bin, "-c", watcher_code],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True
        )

    def launch_app(self, package_name: str) -> Tuple[bool, str]:
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            # 1. Wake screen, prompt keyguard unlock if secure, and sync input nodes
            try:
                subprocess.run([
                    "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                    "--", "/system/bin/sh", "-c", "export PATH=/system/bin:/system/xbin; wm dismiss-keyguard; input keyevent 82"
                ], capture_output=True, timeout=2.0)
                sync_container_input_nodes()
            except Exception:
                pass

            # 2. Check if a secure Keyguard challenge (Pattern/PIN) is currently active
            if self.is_keyguard_locked():
                self.spawn_post_unlock_launcher(package_name)
                return True, f"Keyguard unlock required. {package_name} will launch automatically upon entering your Pattern/PIN."

            # 3. Ensure container is not frozen
            ensure_container_unfrozen()

            # 4. Launch via official Waydroid session DBus to map Wayland XDG surface into KWin
            cmd = [waydroid_bin, "app", "launch", package_name]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, env=clean_env, timeout=8.0)
            except subprocess.TimeoutExpired:
                # If launch timed out, verify linkerconfig and retry once
                ensure_linkerconfig()
                res = subprocess.run(cmd, capture_output=True, text=True, env=clean_env, timeout=8.0)

            if res.returncode == 0:
                from recipes.waydroid_native.window_memory import restore_app_bounds
                import threading
                threading.Thread(target=restore_app_bounds, args=(package_name, 10, 0.25), daemon=True).start()
                return True, f"Launched {package_name} in floating freeform mode."
            
            # If failed, attempt linker self-healing and retry once
            ensure_linkerconfig()
            res_retry = subprocess.run(cmd, capture_output=True, text=True, env=clean_env, timeout=6.0)
            if res_retry.returncode == 0:
                return True, f"Launched {package_name} in floating freeform mode."

            return False, f"Launch failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Launch error: {str(e)}"

    def list_apps(self) -> List[Dict[str, str]]:
        apps = []
        clean_env = os.environ.copy()
        clean_env["PATH"] = f"/usr/bin:/usr/local/bin:{clean_env.get('PATH', '')}"
        waydroid_bin = shutil.which("waydroid") or "/usr/bin/waydroid"
        try:
            res = subprocess.run([waydroid_bin, "app", "list"], capture_output=True, text=True, env=clean_env, timeout=5)
            curr_name = None
            curr_pkg = None
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("Name:"):
                    curr_name = line.replace("Name:", "").strip()
                elif line.startswith("packageName:"):
                    curr_pkg = line.replace("packageName:", "").strip()
                    if curr_name and curr_pkg:
                        apps.append({"name": curr_name, "package": curr_pkg})
                        curr_name = None
                        curr_pkg = None
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
                            with open(os.path.join(app_dir, f), "r", encoding="utf-8") as df:
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
                st = subprocess.run(["sudo", "-n", "lxc-info", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "-sH"], capture_output=True, text=True, timeout=1.5)
                if "FROZEN" in st.stdout:
                    subprocess.run(["sudo", "-n", "lxc-unfreeze", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid"], capture_output=True, timeout=1.5)

                res_pm = subprocess.run([
                    "sudo", "-n", "lxc-attach", "-P", "/var/lib/waydroid/lxc", "-n", "waydroid",
                    "--", "/system/bin/sh", "-c", "PATH=/system/bin:/system/xbin pm list packages -3"
                ], capture_output=True, text=True, timeout=3)
                for line in res_pm.stdout.splitlines():
                    if line.startswith("package:"):
                        pkg = line.replace("package:", "").strip()
                        apps.append({"name": pkg.split(".")[-1].capitalize(), "package": pkg})
            except Exception:
                pass

        return apps
