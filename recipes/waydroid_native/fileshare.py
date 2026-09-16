#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Bidirectional Host <-> Android Folder Sharing
Binds host ~/Downloads, ~/Pictures, ~/Documents, ~/Music, and ~/Videos into Android /sdcard storage.
"""

import os
import shutil
import subprocess
import logging
from typing import Tuple, List

logger = logging.getLogger("purr.fileshare")

MEDIA_DIRS = [
    ("Downloads", "Download"),
    ("Pictures", "Pictures"),
    ("Documents", "Documents"),
    ("Music", "Music"),
    ("Videos", "Movies")
]


def _run_sudo(cmd: List[str], timeout: float = 5.0) -> Tuple[bool, str]:
    try:
        res = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            err = res.stderr.strip() or f"exit code {res.returncode}"
            return False, err
        return True, ""
    except Exception as e:
        return False, str(e)


def setup_folder_shares() -> Tuple[bool, List[str]]:
    """
    Creates links / mappings so Android apps can seamlessly access host downloads, pictures, documents, music, and videos.
    """
    home = os.path.expanduser("~")
    waydroid_media = os.path.join(home, ".local", "share", "waydroid", "data", "media", "0")
    results = []

    try:
        media_parent = os.path.dirname(waydroid_media)
        if os.path.exists(media_parent):
            ok, err = _run_sudo(["chmod", "775", media_parent])
            if not ok:
                logger.warning(f"chmod 775 on {media_parent} notice: {err}")

        ok, err = _run_sudo(["mkdir", "-p", waydroid_media])
        if not ok:
            logger.warning(f"mkdir -p on {waydroid_media} notice: {err}")

        ok, err = _run_sudo(["chown", "-R", f"{os.getuid()}:{os.getgid()}", waydroid_media])
        if not ok:
            logger.warning(f"chown on {waydroid_media} notice: {err}")

        ok, err = _run_sudo(["chmod", "775", waydroid_media])
        if not ok:
            logger.warning(f"chmod on {waydroid_media} notice: {err}")

        for host_sub, android_sub in MEDIA_DIRS:
            host_path = os.path.join(home, host_sub)
            android_path = os.path.join(waydroid_media, android_sub)

            os.makedirs(host_path, exist_ok=True)

            if not os.path.islink(android_path):
                if os.path.exists(android_path) and os.path.isdir(android_path):
                    try:
                        if not os.listdir(android_path):
                            os.rmdir(android_path)
                    except Exception as e:
                        logger.debug(f"Could not remove empty dir {android_path}: {e}")
                try:
                    if not os.path.exists(android_path):
                        os.symlink(host_path, android_path)
                        results.append(f"Linked ~/{host_sub} -> Android {android_sub}")
                except Exception as e:
                    logger.debug(f"Standard symlink for {android_path} failed, attempting sudo ln: {e}")
                    ok_ln, err_ln = _run_sudo(["ln", "-sfn", host_path, android_path])
                    if ok_ln:
                        results.append(f"Linked ~/{host_sub} -> Android {android_sub}")
                    else:
                        logger.error(f"Failed to link ~/{host_sub} -> {android_path}: {err_ln}")
                        results.append(f"Warning: Failed to link ~/{host_sub} -> {android_sub}: {err_ln}")
            results.append(f"Configured ~/{host_sub} for Android storage")

        return True, results
    except Exception as e:
        logger.error(f"Error setting up folder shares: {e}", exc_info=True)
        return False, [f"Error setting up folder shares: {str(e)}"]
