#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Framework Titlebar Color Patcher

Patches AOSP's `decor_button_dark_color` in `framework-res.apk` from solid black
to solid white, making freeform multi-window caption buttons (< — 🗗 ✕) visible
on dark-themed app headers.

Approach: Direct binary color patch inside the compiled `res/color/decor_button_dark_color.xml`
entry within the stock APK ZIP, then zipalign and v3-sign with AOSP platform test-keys.
This preserves the exact resources.arsc layout and all other entries bit-for-bit,
avoiding the PackageManagerService "Failed to load frameworks package" crash that
occurs when apktool rebuilds the APK with a different binary resource table structure.

Critical lessons learned (do NOT repeat):
  1. Never hex-edit resources.arsc — string pool offsets corrupt libandroidfw.so.
  2. Never build AAPT2 RROs without namespace mapping — ColorStateList returns transparent.
  3. Never deploy unsigned APKs — PackageManagerService rejects unsigned framework packages.
  4. Never use apktool to rebuild framework-res.apk — the rebuilt resources.arsc binary
     layout differs from stock and causes InitAppsHelper.scanSystemDirs to crash.
  5. Must sign with AOSP platform test-keys using v3 signing scheme (not v1 JAR).
"""

import base64
import glob
import os
import shutil
import subprocess
import tempfile
import zipfile
from typing import Tuple

# Paths
BASE_SYSTEM_IMG = "/var/lib/waydroid/images/system.img"
STOCK_FRAMEWORK_RES_RELPATH = "system/framework/framework-res.apk"
OVERLAY_FRAMEWORK_DIR = "/var/lib/waydroid/overlay/system/framework"
OVERLAY_FRAMEWORK_RES = os.path.join(OVERLAY_FRAMEWORK_DIR, "framework-res.apk")
OVERLAY_RESOURCE_CACHE = "/var/lib/waydroid/overlay/data/resource-cache"

# AOSP Platform Test Keys (publicly available in AOSP source tree)
AOSP_PLATFORM_KEY_URL = (
    "https://android.googlesource.com/platform/build/+/"
    "refs/heads/main/target/product/security/platform.pk8?format=TEXT"
)
AOSP_PLATFORM_CERT_URL = (
    "https://android.googlesource.com/platform/build/+/"
    "refs/heads/main/target/product/security/platform.x509.pem?format=TEXT"
)

# Binary patterns for the compiled Android color XML (res/color/decor_button_dark_color.xml).
# In compiled binary XML, color values are stored as:
#   type=0x1c (TYPE_INT_COLOR_ARGB8), followed by the 4-byte ARGB value (little-endian).
# Focused state: #ff000000 (solid black) → #ffffffff (solid white)
OLD_FOCUSED_PATTERN = bytes.fromhex("0800001c000000ff")
NEW_FOCUSED_PATTERN = bytes.fromhex("0800001cffffffff")
# Unfocused state: #33000000 (20% black) → #33ffffff (20% white)
OLD_UNFOCUSED_PATTERN = bytes.fromhex("0800001c00000033")
NEW_UNFOCUSED_PATTERN = bytes.fromhex("0800001cffffff33")

# Idempotency marker embedded in the APK's assets/ directory
PATCH_MARKER = "purr-decor-dark-white-v1"

# Target entry inside the APK
TARGET_ENTRY = "res/color/decor_button_dark_color.xml"


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
    Checks whether the overlay framework-res.apk already contains our patch marker
    asset file, indicating the patch has already been applied.
    """
    if not os.path.exists(OVERLAY_FRAMEWORK_RES):
        return False
    try:
        res = subprocess.run(
            ["unzip", "-l", OVERLAY_FRAMEWORK_RES],
            capture_output=True, text=True, timeout=5,
        )
        return PATCH_MARKER in res.stdout
    except Exception:
        return False


def _clear_resource_cache() -> None:
    """
    Clears stale resource cache entries so Android reloads from the fresh overlay.
    """
    if os.path.isdir(OVERLAY_RESOURCE_CACHE):
        try:
            subprocess.run(
                ["sudo", "rm", "-rf", OVERLAY_RESOURCE_CACHE],
                capture_output=True, timeout=5,
            )
            subprocess.run(
                ["sudo", "mkdir", "-p", OVERLAY_RESOURCE_CACHE],
                capture_output=True, timeout=3,
            )
        except Exception:
            pass


def _download_platform_keys(dest_dir: str) -> Tuple[str, str]:
    """
    Downloads AOSP platform test-keys (platform.pk8 and platform.x509.pem)
    from the official AOSP source tree. These are the publicly available keys
    used to sign system packages in Waydroid's LineageOS-based test-keys build.

    Returns:
        (pk8_path, pem_path) tuple
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

        # googlesource serves raw files as base64-encoded TEXT
        decoded = base64.b64decode(res.stdout)
        with open(out_path, "wb") as f:
            f.write(decoded)

    if not os.path.exists(pk8_path) or os.path.getsize(pk8_path) < 100:
        raise RuntimeError("Downloaded platform.pk8 is empty or corrupt.")
    if not os.path.exists(pem_path) or os.path.getsize(pem_path) < 100:
        raise RuntimeError("Downloaded platform.x509.pem is empty or corrupt.")

    return pk8_path, pem_path


def _binary_patch_color_xml(data: bytes) -> bytes:
    """
    Patches the compiled Android binary XML for `decor_button_dark_color.xml`,
    replacing black color values with white while preserving the exact binary
    structure, string pool, and attribute indices.

    The compiled XML contains two color selectors:
      - Focused:   0800001c 000000ff (#ff000000) → 0800001c ffffffff (#ffffffff)
      - Unfocused: 0800001c 00000033 (#33000000) → 0800001c ffffff33 (#33ffffff)

    Returns:
        Patched binary data

    Raises:
        ValueError if expected color patterns are not found
    """
    patched = bytearray(data)
    patch_count = 0

    idx = patched.find(OLD_FOCUSED_PATTERN)
    if idx >= 0:
        patched[idx:idx + 8] = NEW_FOCUSED_PATTERN
        patch_count += 1

    idx = patched.find(OLD_UNFOCUSED_PATTERN)
    if idx >= 0:
        patched[idx:idx + 8] = NEW_UNFOCUSED_PATTERN
        patch_count += 1

    if patch_count != 2:
        raise ValueError(
            f"Expected 2 color pattern matches in compiled XML, found {patch_count}. "
            "The binary format may have changed."
        )

    return bytes(patched)


def patch_framework_titlebar_colors() -> Tuple[bool, str]:
    """
    Patches AOSP decor_button_dark_color from solid black (#ff000000) to solid white
    (#ffffffff) in framework-res.apk via OverlayFS replacement.

    Pipeline: mount base system image → read stock APK → binary-patch color XML
    entry → repackage ZIP → zipalign → v3-sign with AOSP platform test-keys → deploy.

    The stock APK is read from the base system image (/var/lib/waydroid/images/system.img)
    rather than the overlaid rootfs, because the rootfs OverlayFS may already contain
    a previously patched version from overlay_rw.

    Returns:
        (success: bool, message: str)
    """
    # 0. Pre-flight: check if base system image exists
    if not os.path.exists(BASE_SYSTEM_IMG):
        return False, f"Waydroid base system image not found at {BASE_SYSTEM_IMG}"

    # 1. Check if already patched (idempotent)
    if _is_already_patched():
        return True, "Framework titlebar colors already patched (marker found in overlay APK)."

    # 2. Find SDK tools
    try:
        zipalign = _find_sdk_tool("zipalign")
        apksigner = _find_sdk_tool("apksigner")
    except FileNotFoundError as e:
        return False, str(e)

    # 3. Work in a temp directory
    work_dir = tempfile.mkdtemp(prefix="purr_fwres_")
    mount_dir = os.path.join(work_dir, "base_img")
    rebuilt_apk = os.path.join(work_dir, "framework-res-rebuilt.apk")
    aligned_apk = os.path.join(work_dir, "framework-res-aligned.apk")
    keys_dir = os.path.join(work_dir, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(mount_dir, exist_ok=True)

    mounted = False
    try:
        # 4. Mount the base system image read-only to access the unpatched stock APK
        res = subprocess.run(
            ["sudo", "mount", "-o", "loop,ro", BASE_SYSTEM_IMG, mount_dir],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            return False, f"Failed to mount base system image: {res.stderr.strip()}"
        mounted = True

        stock_apk_path = os.path.join(mount_dir, STOCK_FRAMEWORK_RES_RELPATH)
        if not os.path.exists(stock_apk_path):
            return False, f"Stock framework-res.apk not found in base image at {STOCK_FRAMEWORK_RES_RELPATH}"

        # 5. Read stock APK, binary-patch the color entry, and repackage
        with zipfile.ZipFile(stock_apk_path, "r") as zin:
            if TARGET_ENTRY not in zin.namelist():
                return False, f"Entry {TARGET_ENTRY} not found in stock framework-res.apk"

            dark_data = zin.read(TARGET_ENTRY)

            try:
                patched_data = _binary_patch_color_xml(dark_data)
            except ValueError as e:
                return False, str(e)

            with zipfile.ZipFile(rebuilt_apk, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == TARGET_ENTRY:
                        zout.writestr(item, patched_data)
                    else:
                        zout.writestr(item, data)

                # Embed patch marker for idempotency detection
                zout.writestr(
                    f"assets/{PATCH_MARKER}",
                    "Purr framework-res.apk decor caption color patch\n",
                )

        # Unmount base image as soon as we're done reading
        subprocess.run(["sudo", "umount", mount_dir], capture_output=True, timeout=5)
        mounted = False

        if not os.path.exists(rebuilt_apk):
            return False, "ZIP repackaging produced no output APK."

        # 6. Zipalign (4-byte page alignment)
        res = subprocess.run(
            [zipalign, "-f", "-p", "4", rebuilt_apk, aligned_apk],
            capture_output=True, text=True, timeout=30,
        )
        if res.returncode != 0:
            return False, f"zipalign failed: {res.stderr.strip()}"

        # 7. Download AOSP platform test-keys and v3-sign
        try:
            pk8_path, pem_path = _download_platform_keys(keys_dir)
        except Exception as e:
            return False, f"Failed to obtain AOSP platform signing keys: {e}"

        res = subprocess.run(
            [
                apksigner, "sign",
                "--key", pk8_path,
                "--cert", pem_path,
                "--v1-signing-enabled", "false",
                "--v2-signing-enabled", "false",
                "--v3-signing-enabled", "true",
                "--v4-signing-enabled", "false",
                aligned_apk,
            ],
            capture_output=True, text=True, timeout=30,
        )
        if res.returncode != 0:
            return False, f"apksigner failed: {res.stderr.strip()}"

        # 8. Verify signature
        res = subprocess.run(
            [apksigner, "verify", aligned_apk],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            return False, f"Signed APK failed verification: {res.stderr.strip()}"

        # 9. Deploy to overlay
        subprocess.run(["sudo", "mkdir", "-p", OVERLAY_FRAMEWORK_DIR], capture_output=True)
        res = subprocess.run(
            ["sudo", "cp", aligned_apk, OVERLAY_FRAMEWORK_RES],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            return False, f"Failed to deploy patched APK to overlay: {res.stderr.strip()}"

        subprocess.run(
            ["sudo", "chmod", "644", OVERLAY_FRAMEWORK_RES],
            capture_output=True, timeout=3,
        )

        # 10. Clear stale resource cache
        _clear_resource_cache()

        return True, (
            "Patched decor_button_dark_color from #ff000000 (black) to #ffffffff (white) "
            "in framework-res.apk overlay (v3 platform-signed). "
            "Session restart required to apply."
        )

    except subprocess.TimeoutExpired:
        return False, "Framework resource patching timed out."
    except Exception as e:
        return False, f"Framework resource patching error: {str(e)}"
    finally:
        if mounted:
            subprocess.run(["sudo", "umount", mount_dir], capture_output=True)
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
