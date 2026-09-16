#!/usr/bin/env python3
"""
🐾 Purr Recipes — Base Recipe Abstract Class and Data Structures
Project Tuki / Purr Ecosystem
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple


class RecipeResult:
    def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data
        }

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<RecipeResult {status}: {self.message}>"


class BaseRecipe(ABC):
    """
    Abstract Base Class for all Purr Ecosystem Recipes.
    Each recipe encapsulates prerequisite checks, provisioning, desktop integrations,
    diagnostics (doctor), pruning, and clean teardown.
    """

    id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.1.0"
    author: str = ""
    category: str = "General"
    tags: List[str] = []
    icon: str = "application-x-executable"
    highlights: List[str] = []

    def __init__(self):
        pass

    @staticmethod
    def get_manifest_path() -> str:
        manifest_dir = os.path.expanduser("~/.config/purr")
        os.makedirs(manifest_dir, exist_ok=True)
        return os.path.join(manifest_dir, "deployed_recipes.json")

    def get_deployed_state(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the persistent deployment record for this recipe.
        If deployed on the host but not recorded in manifest, infers baseline v1.0.0.
        """
        if not self.is_deployed():
            return None

        manifest_path = self.get_manifest_path()
        if os.path.exists(manifest_path):
            try:
                import json
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self.id in data:
                        return data[self.id]
            except Exception as e:
                if os.environ.get("PURR_DEBUG") or os.environ.get("DEBUG"):
                    sys.stderr.write(f"🐾 [Purr Recipes] Debug: Failed to read deployment manifest {manifest_path}: {e}\n")

        # Inferred state for existing legacy installations
        return {
            "version": "1.0.0",
            "deployed_at": None,
            "last_synced": None,
            "inferred": True
        }

    def set_deployed_state(self, version: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> None:
        """
        Persists updated deployment metadata (version, timestamp, options).
        """
        import json
        import datetime
        manifest_path = self.get_manifest_path()
        data = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                if os.environ.get("PURR_DEBUG") or os.environ.get("DEBUG"):
                    sys.stderr.write(f"🐾 [Purr Recipes] Debug: Failed to load existing manifest for update: {e}\n")
                data = {}

        now_str = datetime.datetime.now().isoformat()
        current_record = data.get(self.id, {})
        data[self.id] = {
            "version": version or self.version,
            "deployed_at": current_record.get("deployed_at") or now_str,
            "last_synced": now_str,
            "options": options or current_record.get("options", {}),
            "inferred": False
        }

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"🐾 [Purr Recipes] Warning: Failed to write deployment manifest: {e}\n")

    def remove_deployed_state(self) -> None:
        """
        Removes this recipe from the deployment manifest on teardown.
        """
        import json
        manifest_path = self.get_manifest_path()
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if self.id in data:
                    del data[self.id]
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                if os.environ.get("PURR_DEBUG") or os.environ.get("DEBUG"):
                    sys.stderr.write(f"🐾 [Purr Recipes] Debug: Failed to remove state from manifest: {e}\n")

    def has_update(self) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """
        Checks if the currently deployed version differs from the available recipe version.
        Returns: (has_update, installed_version, available_version, highlights)
        """
        if not self.is_deployed():
            return False, None, self.version, self.highlights

        state = self.get_deployed_state()
        installed_ver = state.get("version", "1.0.0") if state else "1.0.0"
        has_up = (installed_ver != self.version)
        return has_up, installed_ver, self.version, self.highlights

    @abstractmethod
    def check_prerequisites(self) -> RecipeResult:
        """
        Verify hardware, kernel features, drivers, and required system packages.
        """
        pass

    @abstractmethod
    def prune(self) -> RecipeResult:
        """
        Safely clean up any existing containers, old images, legacy configurations, or state.
        """
        pass

    @abstractmethod
    def provision(self, options: Optional[Dict[str, Any]] = None) -> RecipeResult:
        """
        Perform automated setup, image downloads, translation layer configuration, and system service startup.
        """
        pass

    @abstractmethod
    def integrate_desktop(self) -> RecipeResult:
        """
        Apply KDE Plasma 6 desktop integrations, KWin window rules, folder bind mounts, and desktop entries.
        """
        pass

    @abstractmethod
    def doctor(self) -> RecipeResult:
        """
        Perform comprehensive health diagnostics (binder, networking, audio, translation, GPU gralloc).
        """
        pass

    @abstractmethod
    def is_deployed(self) -> bool:
        """
        Check if this recipe is currently deployed and active on the host system.
        """
        pass

    @abstractmethod
    def sync(self, options: Optional[Dict[str, Any]] = None) -> RecipeResult:
        """
        Non-destructively converge deployed subsystem state with current recipe assets
        (companion APKs, patches, KWin rules, desktop entries) WITHOUT wiping container
        images or user data.
        """
        pass

    @abstractmethod
    def teardown(self) -> RecipeResult:
        """
        Completely remove the recipe configuration, restore desktop rules, and revert system changes cleanly.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Returns a dictionary summary of the recipe metadata and capabilities.
        """
        deployed_state = self.get_deployed_state()
        has_up, inst_v, avail_v, hls = self.has_update()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "icon": self.icon,
            "highlights": self.highlights,
            "is_deployed": self.is_deployed(),
            "deployed_version": inst_v,
            "has_update": has_up
        }
