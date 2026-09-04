#!/usr/bin/env python3
"""
🐾 Waydroid Native Recipe — Bidirectional Host <-> Android Folder Sharing
Binds host ~/Downloads, ~/Pictures, ~/Documents, ~/Music, and ~/Videos into Android /sdcard storage.
"""

import os
import shutil
from typing import Tuple, List


MEDIA_DIRS = [
    ("Downloads", "Download"),
    ("Pictures", "Pictures"),
    ("Documents", "Documents"),
    ("Music", "Music"),
    ("Videos", "Movies")
]


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
            subprocess.run(["sudo", "chmod", "775", media_parent], capture_output=True)
        subprocess.run(["sudo", "mkdir", "-p", waydroid_media], capture_output=True)
        subprocess.run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", waydroid_media], capture_output=True)
        subprocess.run(["sudo", "chmod", "775", waydroid_media], capture_output=True)

        for host_sub, android_sub in MEDIA_DIRS:
            host_path = os.path.join(home, host_sub)
            android_path = os.path.join(waydroid_media, android_sub)

            os.makedirs(host_path, exist_ok=True)

            if not os.path.exists(android_path):
                try:
                    os.symlink(host_path, android_path)
                    results.append(f"Linked ~/{host_sub} -> Android {android_sub}")
                except Exception:
                    subprocess.run(["sudo", "ln", "-sf", host_path, android_path], capture_output=True)
                    results.append(f"Linked ~/{host_sub} -> Android {android_sub}")
            results.append(f"Configured ~/{host_sub} for Android storage")

        return True, results
    except Exception as e:
        return False, [f"Error setting up folder shares: {str(e)}"]
