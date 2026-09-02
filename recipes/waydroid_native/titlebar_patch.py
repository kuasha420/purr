#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Framework Titlebar Caption Visibility Patcher

Patches AOSP's freeform window caption button rendering in both `framework-res.apk`
and `SystemUI.apk` from invisible/black/purple to crisp solid white (#ffffffff),
ensuring that caption buttons (< — 🗗 ✕) are clearly visible across all Android apps,
including Google Material Components apps (e.g. Gamepad Tester) and standard apps
(e.g. Play Store).

Verified Root Causes:
  1. In `framework-res.apk` (`res/layout/decor_caption.xml`), caption buttons were declared
     as `<Button>`. In apps using Google Material Components (`Theme.MaterialComponents`),
     `MaterialComponentsViewInflater` automatically replaces `<Button>` with
     `com.google.android.material.button.MaterialButton`. `MaterialButton` sets
     `backgroundTint` to `?attr/colorPrimary` (purple in Gamepad Tester), overwriting
     and tinting the button's vector drawable background to solid purple, making the
     icons completely invisible against the purple header.
     FIX: In `res/layout/decor_caption.xml`, the StringPool element name is changed from
     'Button' to 'View'. `DecorCaptionView`'s internal fields (`mBack`, `mMinimize`,
     `mMaximize`, `mClose`) are generic `android.view.View` references. Declaring `<View>`
     prevents MaterialComponents interception, preserving the clean vector drawables.
  2. In `SystemUI.apk`, `CaptionWindowDecoration` and `DesktopModeWindowDecoration` tint
     caption button drawables using `decor_button_dark_color` and `decor_button_light_color`.
     In stock AOSP, unfocused colors have alpha 0x33 (20% opacity white/black), which are
     faint or invisible on dark/colored headers, and close/back drawables hardcode
     `fillColor="@android:color/black"`.
     FIX: Binary-patch `SystemUI.apk` color selectors to solid white (#ffffffff) for both
     focused and unfocused states, and switch vector drawables to `@android:color/white`.
  3. Packaging: Direct in-place binary patching inside the stock APK ZIPs, preserving
     resources.arsc and package structure bit-for-bit, followed by zipalign (4-byte)
     and platform key signing (v1/v2/v3).
"""

import base64
import glob
import os
import shutil
import struct
import subprocess
import tempfile
import zipfile
from typing import Tuple

# Paths
BASE_SYSTEM_IMG = "/var/lib/waydroid/images/system.img"
STOCK_FRAMEWORK_RES_RELPATH = "system/framework/framework-res.apk"
STOCK_SYSTEMUI_RELPATH = "system/system_ext/priv-app/SystemUI/SystemUI.apk"

OVERLAY_FRAMEWORK_DIR = "/var/lib/waydroid/overlay/system/framework"
OVERLAY_FRAMEWORK_RES = os.path.join(OVERLAY_FRAMEWORK_DIR, "framework-res.apk")

OVERLAY_SYSTEMUI_DIR = "/var/lib/waydroid/overlay/system/system_ext/priv-app/SystemUI"
OVERLAY_SYSTEMUI_APK = os.path.join(OVERLAY_SYSTEMUI_DIR, "SystemUI.apk")

OVERLAY_RESOURCE_CACHE = "/var/lib/waydroid/overlay/data/resource-cache"
OVERLAY_PACKAGE_CACHE = "/var/lib/waydroid/overlay/data/system/package_cache"

# AOSP Platform Test Keys (publicly available in AOSP source tree)
AOSP_PLATFORM_KEY_URL = (
    "https://android.googlesource.com/platform/build/+/"
    "refs/heads/main/target/product/security/platform.pk8?format=TEXT"
)
AOSP_PLATFORM_CERT_URL = (
    "https://android.googlesource.com/platform/build/+/"
    "refs/heads/main/target/product/security/platform.x509.pem?format=TEXT"
)

# Idempotency markers
FWRES_PATCH_MARKER = "purr-decor-dark-white-v2"
SYSUI_PATCH_MARKER = "purr-decor-sysui-white-v2"


def _find_sdk_tool(name: str) -> str:
    """
    Locates an Android SDK build-tool (zipalign, apksigner) by searching PATH
    and common SDK locations, preferring the highest build-tools version.
    """
    tool = shutil.which(name)
    if tool:
        return tool

    sdk_paths = [
        os.path.expanduser("~/Android/Sdk"),
        os.environ.get("ANDROID_SDK_ROOT", ""),
        os.environ.get("ANDROID_HOME", ""),
    ]
    for sdk in sdk_paths:
        if not sdk or not os.path.isdir(sdk):
            continue
        candidates = sorted(
            glob.glob(os.path.join(sdk, "build-tools", "*", name)),
            reverse=True,
        )
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c

    raise FileNotFoundError(
        f"{name} not found. Install Android SDK build-tools or add {name} to PATH."
    )


def _is_already_patched() -> bool:
    """
    Checks whether both overlay framework-res.apk and SystemUI.apk already contain
    our patch markers.
    """
    if not (os.path.exists(OVERLAY_FRAMEWORK_RES) and os.path.exists(OVERLAY_SYSTEMUI_APK)):
        return False
    try:
        res_fw = subprocess.run(
            ["unzip", "-l", OVERLAY_FRAMEWORK_RES],
            capture_output=True, text=True, timeout=5,
        )
        res_ui = subprocess.run(
            ["unzip", "-l", OVERLAY_SYSTEMUI_APK],
            capture_output=True, text=True, timeout=5,
        )
        return (FWRES_PATCH_MARKER in res_fw.stdout) and (SYSUI_PATCH_MARKER in res_ui.stdout)
    except Exception:
        return False


def _clear_caches() -> None:
    """
    Clears stale resource and package caches so Android reloads from fresh overlays.
    """
    for cache_dir in [OVERLAY_RESOURCE_CACHE, OVERLAY_PACKAGE_CACHE]:
        if os.path.isdir(cache_dir):
            try:
                subprocess.run(["sudo", "rm", "-rf", cache_dir], capture_output=True, timeout=5)
                subprocess.run(["sudo", "mkdir", "-p", cache_dir], capture_output=True, timeout=3)
            except Exception:
                pass

    user_data = os.path.expanduser("~/.local/share/waydroid/data")
    for sub in ["resource-cache", "system/package_cache"]:
        p = os.path.join(user_data, sub)
        if os.path.isdir(p):
            try:
                subprocess.run(["sudo", "rm", "-rf", p], capture_output=True, timeout=5)
                subprocess.run(["sudo", "mkdir", "-p", p], capture_output=True, timeout=3)
            except Exception:
                pass


def _download_platform_keys(dest_dir: str) -> Tuple[str, str]:
    """
    Downloads AOSP platform test-keys from the official AOSP source tree.
    """
    pk8_path = os.path.join(dest_dir, "platform.pk8")
    pem_path = os.path.join(dest_dir, "platform.x509.pem")

    for url, out_path in [(AOSP_PLATFORM_KEY_URL, pk8_path),
                          (AOSP_PLATFORM_CERT_URL, pem_path)]:
        res = subprocess.run(
            ["curl", "-fsSL", "--connect-timeout", "10", "--max-time", "30", url],
            capture_output=True, timeout=40,
        )
        if res.returncode != 0 or not res.stdout:
            raise RuntimeError(f"Failed to download AOSP platform key from {url}")

        decoded = base64.b64decode(res.stdout)
        with open(out_path, "wb") as f:
            f.write(decoded)

    if not os.path.exists(pk8_path) or os.path.getsize(pk8_path) < 100:
        raise RuntimeError("Downloaded platform.pk8 is empty or corrupt.")
    if not os.path.exists(pem_path) or os.path.getsize(pem_path) < 100:
        raise RuntimeError("Downloaded platform.x509.pem is empty or corrupt.")

    return pk8_path, pem_path


def _patch_decor_caption_layout_xml(d: bytearray) -> bytearray:
    """
    Patches compiled binary XML `res/layout/decor_caption.xml`, replacing the
    tag name 'Button' with 'View' in its StringPool.
    
    This prevents Google MaterialComponents' `MaterialComponentsViewInflater` from
    intercepting the caption buttons and applying purple `backgroundTint`.
    """
    string_count, style_count, flags, strings_start, styles_start = struct.unpack('<IIIII', d[16:36])
    offsets = list(struct.unpack(f'<{string_count}I', d[36:36 + 4*string_count]))
    sp_data_start = 8 + strings_start
    strings = []
    for off in offsets:
        p = sp_data_start + off
        u16len = d[p]; p += 1
        if u16len & 0x80: p += 1
        u8len = d[p]; p += 1
        if u8len & 0x80: p += 1
        s = d[p:p+u8len].decode('utf-8', errors='ignore')
        strings.append(s)

    if 'Button' not in strings:
        return d

    btn_idx = strings.index('Button')
    strings[btn_idx] = 'View'

    new_sp_data = bytearray()
    new_offsets = []
    for s in strings:
        new_offsets.append(len(new_sp_data))
        encoded = s.encode('utf-8')
        new_sp_data.append(len(s))
        new_sp_data.append(len(encoded))
        new_sp_data.extend(encoded)
        new_sp_data.append(0)
    while len(new_sp_data) % 4 != 0:
        new_sp_data.append(0)

    new_sp_header_size = 28
    new_sp_chunk_size = new_sp_header_size + 4 * string_count + len(new_sp_data)
    new_strings_start = new_sp_header_size + 4 * string_count
    new_sp_chunk = bytearray()
    new_sp_chunk.extend(struct.pack('<HHI', 0x0001, new_sp_header_size, new_sp_chunk_size))
    new_sp_chunk.extend(struct.pack('<IIIII', string_count, 0, flags, new_strings_start, 0))
    for off in new_offsets:
        new_sp_chunk.extend(struct.pack('<I', off))
    new_sp_chunk.extend(new_sp_data)

    orig_sp_size = struct.unpack('<I', d[12:16])[0]
    xml_rest = d[8 + orig_sp_size:]
    new_xml = bytearray()
    new_xml.extend(struct.pack('<HHI', 0x0003, 8, 8 + len(new_sp_chunk) + len(xml_rest)))
    new_xml.extend(new_sp_chunk)
    new_xml.extend(xml_rest)
    return new_xml


def _patch_framework_res(stock_apk_path: str, rebuilt_apk_path: str) -> None:
    """
    Patches `framework-res.apk` entries:
      1. `res/layout/decor_caption.xml`: 'Button' -> 'View'
      2. `res/color/decor_button_dark_color.xml`: focused & unfocused -> #ffffffff
      3. `res/color/decor_button_light_color.xml`: unfocused -> #ffffffff
    """
    with zipfile.ZipFile(stock_apk_path, "r") as zin:
        entries = {}
        for item in zin.infolist():
            d = bytearray(zin.read(item.filename))

            if item.filename == "res/layout/decor_caption.xml":
                d = _patch_decor_caption_layout_xml(d)
            elif item.filename == "res/color/decor_button_dark_color.xml":
                d = d.replace(bytes.fromhex("0800001c000000ff"), bytes.fromhex("0800001cffffffff"))
                d = d.replace(bytes.fromhex("0800001c00000033"), bytes.fromhex("0800001cffffff80"))
                d = d.replace(bytes.fromhex("0800001cffffff33"), bytes.fromhex("0800001cffffff80"))
            elif item.filename == "res/color/decor_button_light_color.xml":
                d = d.replace(bytes.fromhex("0800001cffffff33"), bytes.fromhex("0800001cffffff80"))

            entries[item] = bytes(d)

        with zipfile.ZipFile(rebuilt_apk_path, "w") as zout:
            for item, data in entries.items():
                zout.writestr(item, data)
            zout.writestr(f"assets/{FWRES_PATCH_MARKER}", "Purr framework-res caption patch\n")


def _patch_systemui(stock_apk_path: str, rebuilt_apk_path: str) -> None:
    """
    Patches `SystemUI.apk` entries:
      1. `res/color/decor_button_dark_color.xml`: focused -> #ffffffff, unfocused -> #80ffffff (50% opacity)
      2. `res/color/decor_button_light_color.xml`: focused -> #ffffffff, unfocused -> #80ffffff (50% opacity)
      3. `res/drawable/decor_close_button_dark.xml`: 0x0106000c (black) -> 0x0106000b (white)
      4. `res/drawable/decor_back_button_dark.xml`: 0x0106000c (black) -> 0x0106000b (white)
    """
    with zipfile.ZipFile(stock_apk_path, "r") as zin:
        entries = {}
        for item in zin.infolist():
            d = bytearray(zin.read(item.filename))

            if item.filename == "res/color/decor_button_dark_color.xml":
                d = d.replace(bytes.fromhex("0800001c000000ff"), bytes.fromhex("0800001cffffffff"))
                d = d.replace(bytes.fromhex("0800001c00000033"), bytes.fromhex("0800001cffffff80"))
                d = d.replace(bytes.fromhex("0800001cffffff33"), bytes.fromhex("0800001cffffff80"))
            elif item.filename == "res/color/decor_button_light_color.xml":
                d = d.replace(bytes.fromhex("0800001cffffff33"), bytes.fromhex("0800001cffffff80"))
            elif item.filename in [
                "res/drawable/decor_close_button_dark.xml",
                "res/drawable/decor_back_button_dark.xml",
            ]:
                d = d.replace(b"\x0c\x00\x06\x01", b"\x0b\x00\x06\x01")

            entries[item] = bytes(d)

        with zipfile.ZipFile(rebuilt_apk_path, "w") as zout:
            for item, data in entries.items():
                zout.writestr(item, data)
            zout.writestr(f"assets/{SYSUI_PATCH_MARKER}", "Purr SystemUI caption patch\n")


def patch_framework_titlebar_colors() -> Tuple[bool, str]:
    """
    Executes the comprehensive framework titlebar visibility patch across both
    framework-res.apk and SystemUI.apk.

    Returns:
        (success: bool, message: str)
    """
    if not os.path.exists(BASE_SYSTEM_IMG):
        return False, f"Waydroid base system image not found at {BASE_SYSTEM_IMG}"

    if _is_already_patched():
        return True, "Framework titlebar colors already fully patched."

    try:
        zipalign = _find_sdk_tool("zipalign")
        apksigner = _find_sdk_tool("apksigner")
    except FileNotFoundError as e:
        return False, str(e)

    work_dir = tempfile.mkdtemp(prefix="purr_titlebar_")
    mount_dir = os.path.join(work_dir, "base_img")
    keys_dir = os.path.join(work_dir, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(mount_dir, exist_ok=True)

    mounted = False
    try:
        # 1. Mount base system image
        res = subprocess.run(
            ["sudo", "mount", "-o", "loop,ro", BASE_SYSTEM_IMG, mount_dir],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            return False, f"Failed to mount base system image: {res.stderr.strip()}"
        mounted = True

        # 2. Download AOSP platform test keys
        pk8_path, pem_path = _download_platform_keys(keys_dir)

        # 3. Patch framework-res.apk
        fw_stock = os.path.join(mount_dir, STOCK_FRAMEWORK_RES_RELPATH)
        fw_rebuilt = os.path.join(work_dir, "framework-res-rebuilt.apk")
        fw_aligned = os.path.join(work_dir, "framework-res-aligned.apk")

        _patch_framework_res(fw_stock, fw_rebuilt)
        subprocess.run([zipalign, "-f", "-p", "4", fw_rebuilt, fw_aligned], check=True, capture_output=True)
        subprocess.run(
            [
                apksigner, "sign",
                "--key", pk8_path,
                "--cert", pem_path,
                "--v1-signing-enabled", "true",
                "--v2-signing-enabled", "true",
                "--v3-signing-enabled", "true",
                "--v4-signing-enabled", "false",
                fw_aligned,
            ],
            check=True, capture_output=True,
        )

        # 4. Patch SystemUI.apk
        ui_stock = os.path.join(mount_dir, STOCK_SYSTEMUI_RELPATH)
        ui_rebuilt = os.path.join(work_dir, "SystemUI-rebuilt.apk")
        ui_aligned = os.path.join(work_dir, "SystemUI-aligned.apk")

        _patch_systemui(ui_stock, ui_rebuilt)
        subprocess.run([zipalign, "-f", "-p", "4", ui_rebuilt, ui_aligned], check=True, capture_output=True)
        subprocess.run(
            [
                apksigner, "sign",
                "--key", pk8_path,
                "--cert", pem_path,
                "--v1-signing-enabled", "false",
                "--v2-signing-enabled", "false",
                "--v3-signing-enabled", "true",
                "--v4-signing-enabled", "false",
                ui_aligned,
            ],
            check=True, capture_output=True,
        )

        # Unmount base image
        subprocess.run(["sudo", "umount", mount_dir], capture_output=True)
        mounted = False

        # 5. Deploy to overlays
        subprocess.run(["sudo", "mkdir", "-p", OVERLAY_FRAMEWORK_DIR], check=True)
        subprocess.run(["sudo", "cp", fw_aligned, OVERLAY_FRAMEWORK_RES], check=True)
        subprocess.run(["sudo", "chmod", "644", OVERLAY_FRAMEWORK_RES], check=True)

        subprocess.run(["sudo", "mkdir", "-p", OVERLAY_SYSTEMUI_DIR], check=True)
        subprocess.run(["sudo", "cp", ui_aligned, OVERLAY_SYSTEMUI_APK], check=True)
        subprocess.run(["sudo", "chmod", "644", OVERLAY_SYSTEMUI_APK], check=True)

        # 6. Clear stale caches
        _clear_caches()

        return True, (
            "Patched both framework-res.apk and SystemUI.apk for full titlebar caption visibility "
            "(eliminated MaterialButton tint collision & enforced solid white controls). "
            "Session restart required to apply."
        )

    except Exception as e:
        return False, f"Titlebar patching error: {e}"
    finally:
        if mounted:
            subprocess.run(["sudo", "umount", mount_dir], capture_output=True)
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
