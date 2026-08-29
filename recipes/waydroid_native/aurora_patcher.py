#!/usr/bin/env python3
"""
🐾 Purr Aurora Store Patcher — Curated Multi-Architecture Device Profiles (Android 10–14)
Project Tuki / Purr Ecosystem
"""

import os
import sys
import shutil
import zipfile
import subprocess
from typing import Tuple, Optional


def find_android_build_tool(tool_name: str) -> Optional[str]:
    """
    Search system PATH and Android SDK directories for build tools (zipalign, apksigner).
    """
    which_path = shutil.which(tool_name)
    if which_path:
        return which_path

    sdk_roots = [
        os.path.expanduser("~/Android/Sdk/build-tools"),
        "/opt/android-sdk/build-tools",
        "/usr/lib/android-sdk/build-tools"
    ]
    for sdk_root in sdk_roots:
        if os.path.exists(sdk_root) and os.path.isdir(sdk_root):
            versions = sorted(os.listdir(sdk_root), reverse=True)
            for v in versions:
                cand = os.path.join(sdk_root, v, tool_name)
                if os.path.isfile(cand) and os.access(cand, os.X_OK):
                    return cand
    return None


PURR_DEVICE_MAP = {
    "Samsung A02s": "! [Purr: 32-Bit ARM Safe] Samsung Galaxy A02s (Android 12)",
    "BRAVIA VU2": "! [Purr: 32-Bit ARM Legacy] Sony BRAVIA VU2 (Android 11)",
    "Samsung J5 Prime": "! [Purr: 32-Bit ARM Compact] Samsung Galaxy J5 Prime (Android 10)",
    "Google Play Games on PC": "! [Purr: x86_64 Native PC] Google Play Games on PC (Android 14)",
    "Samsung S20+": "! [Purr: 64-Bit ARM Full] Samsung Galaxy S20+ (Android 13)",
    "Redmi Note 12 4G": "! [Purr: 64-Bit ARM Fast] Xiaomi Redmi Note 12 4G (Android 13)",
    "Google Pixel Tablet": "! [Purr: 64-Bit ARM Tablet] Google Pixel Tablet (Android 13)",
    "Galaxy S24 Ultra": "! [Purr: 64-Bit ARM Latest] Samsung Galaxy S24 Ultra (Android 14)",
    "Google Pixel 5a": "! [Purr: 64-Bit ARM Pixel] Google Pixel 5a (Android 14)",
    "Google Pixel 7a": "! [Purr: 64-Bit ARM Pixel] Google Pixel 7a (Android 13)",
    "Samsung S20 Ultra": "! [Purr: 64-Bit ARM Ultra] Samsung Galaxy S20 Ultra (Android 13)"
}


def build_and_sign_aurora_store(output_apk: Optional[str] = None) -> Tuple[bool, str]:
    """
    Downloads upstream Aurora Store APK, patches built-in device presets with
    curated multi-architecture profiles (Android 10–14), performs 4-byte zipalign,
    and signs with standard Android debug keystore.
    """
    zipalign_bin = find_android_build_tool("zipalign")
    apksigner_bin = find_android_build_tool("apksigner")

    if not zipalign_bin or not apksigner_bin:
        return False, "Android SDK build-tools (zipalign and apksigner) are required to build Aurora Store."

    cache_dir = os.path.expanduser("~/.cache/purr")
    work_dir = os.path.join(cache_dir, "aurora_build")
    if not output_apk:
        output_apk = os.path.join(cache_dir, "apks", "AuroraStore_PurrEdition.apk")

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_apk), exist_ok=True)

    upstream_apk = os.path.join(work_dir, "AuroraStore_upstream.apk")
    unaligned_apk = os.path.join(work_dir, "AuroraStore_unaligned.apk")
    aligned_apk = os.path.join(work_dir, "AuroraStore_aligned.apk")
    keystore_path = os.path.join(work_dir, "debug.keystore")

    # 1. Fetch official APK if missing
    if not os.path.exists(upstream_apk) or os.path.getsize(upstream_apk) < 1000000:
        urls = [
            "https://f-droid.org/repo/com.aurora.store_65.apk",
            "https://auroraoss.com/downloads/AuroraStore/Release/preload/AuroraStore-preload-4.7.5.apk",
            "https://gitlab.com/AuroraOSS/AuroraStore/-/releases/v4.7.5/downloads/AuroraStore-4.7.5.apk"
        ]
        downloaded = False
        last_error = ""
        for url in urls:
            res = subprocess.run([
                "curl", "-fsSL", "--connect-timeout", "15", "--max-time", "180",
                "-o", upstream_apk, url
            ], capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(upstream_apk) and os.path.getsize(upstream_apk) > 1000000:
                downloaded = True
                break
            else:
                last_error = res.stderr.strip() or f"curl exit code {res.returncode}"
                if os.path.exists(upstream_apk):
                    try:
                        os.remove(upstream_apk)
                    except Exception:
                        pass
        if not downloaded:
            return False, f"Failed to download upstream Aurora Store APK: {last_error}"

    # 2. Patch resource properties
    patched_purr_count = 0
    try:
        with zipfile.ZipFile(upstream_apk, "r") as zin:
            with zipfile.ZipFile(unaligned_apk, "w") as zout:
                for item in zin.infolist():
                    # Strip original META-INF signatures
                    if item.filename.startswith("META-INF/") and (item.filename.endswith(".SF") or item.filename.endswith(".RSA") or item.filename.endswith(".MF")):
                        continue

                    if item.filename.startswith("res/") and item.filename.endswith(".properties"):
                        content = zin.read(item.filename).decode("utf-8", errors="replace")
                        lines = content.splitlines()
                        orig_name = None
                        for line in lines:
                            if line.startswith("UserReadableName="):
                                orig_name = line.split("=", 1)[1].strip()
                                break

                        if orig_name and orig_name in PURR_DEVICE_MAP:
                            new_name = PURR_DEVICE_MAP[orig_name]
                            new_lines = [
                                f"UserReadableName={new_name}" if line.startswith("UserReadableName=") else line
                                for line in lines
                            ]
                            new_data = ("\n".join(new_lines) + "\n").encode("utf-8")
                            zout.writestr(item, new_data)
                            patched_purr_count += 1
                        elif orig_name:
                            new_lines = [
                                f"UserReadableName=Stock: {orig_name}" if line.startswith("UserReadableName=") and not orig_name.startswith("Stock:") and not orig_name.startswith("!") else line
                                for line in lines
                            ]
                            new_data = ("\n".join(new_lines) + "\n").encode("utf-8")
                            zout.writestr(item, new_data)
                        else:
                            zout.writestr(item, content.encode("utf-8"))
                    else:
                        zout.writestr(item, zin.read(item.filename))
    except Exception as e:
        return False, f"Failed to patch APK properties: {e}"

    if patched_purr_count < 3:
        return False, f"APK does not contain expected device profiles (only found {patched_purr_count} matches)."

    # 3. Zipalign 4-byte
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)
    res_align = subprocess.run([zipalign_bin, "-p", "-f", "-v", "4", unaligned_apk, aligned_apk], capture_output=True, text=True)
    if res_align.returncode != 0:
        return False, f"zipalign failed: {res_align.stderr.strip()}"

    # 4. Generate keystore if missing
    if not os.path.exists(keystore_path):
        keytool_bin = shutil.which("keytool")
        if not keytool_bin:
            candidates = [
                "/usr/lib/jvm/default/bin/keytool",
                "/usr/lib/jvm/default-runtime/bin/keytool",
                "/usr/bin/keytool"
            ]
            for c in candidates:
                if os.path.isfile(c) and os.access(c, os.X_OK):
                    keytool_bin = c
                    break
        if not keytool_bin:
            return False, "Java keytool binary is required to generate Android debug keystore."

        res_key = subprocess.run([
            keytool_bin, "-genkeypair", "-v",
            "-keystore", keystore_path,
            "-storepass", "android",
            "-alias", "androiddebugkey",
            "-keypass", "android",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-dname", "CN=Android Debug,O=Android,C=US"
        ], capture_output=True, text=True)
        if res_key.returncode != 0 or not os.path.exists(keystore_path):
            return False, f"keytool keystore generation failed: {res_key.stderr.strip()}"

    # 5. Sign with apksigner (v1, v2, v3 schemes)
    if os.path.exists(output_apk):
        try:
            os.remove(output_apk)
        except Exception:
            pass
    shutil.copyfile(aligned_apk, output_apk)
    res_sign = subprocess.run([
        apksigner_bin, "sign",
        "--ks", keystore_path,
        "--ks-pass", "pass:android",
        "--ks-key-alias", "androiddebugkey",
        "--key-pass", "pass:android",
        output_apk
    ], capture_output=True, text=True)

    if res_sign.returncode != 0:
        return False, f"apksigner failed: {res_sign.stderr.strip()}"

    try:
        os.chmod(output_apk, 0o644)
    except Exception:
        pass

    return True, f"Aurora Store Purr Edition built and signed successfully at {output_apk}"


if __name__ == "__main__":
    ok, msg = build_and_sign_aurora_store()
    print(msg)
    sys.exit(0 if ok else 1)
