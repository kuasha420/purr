#!/usr/bin/env python3
"""
🐾 Purr Recipes — Base Recipe Abstract Class and Data Structures
Project Tuki / Purr Ecosystem
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


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
    version: str = "1.0.0"
    author: str = ""
    category: str = "General"
    tags: List[str] = []
    icon: str = "application-x-executable"

    def __init__(self):
        pass

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
    def teardown(self) -> RecipeResult:
        """
        Completely remove the recipe configuration, restore desktop rules, and revert system changes cleanly.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Returns a dictionary summary of the recipe metadata and capabilities.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "icon": self.icon
        }
