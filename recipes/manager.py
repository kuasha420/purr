#!/usr/bin/env python3
"""
🐾 Purr Recipes — Recipe Discovery, Registry, and Execution Manager
Project Tuki / Purr Ecosystem
"""

import sys
import os
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Type

from recipes.base import BaseRecipe, RecipeResult


class RecipeManager:
    """
    Central discovery and lifecycle manager for Purr recipes.
    """

    SEARCH_PATHS = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recipes"),
        os.path.expanduser("~/.config/purr/recipes"),
        "/usr/share/purr/recipes",
        "/usr/local/share/purr/recipes"
    ]

    def __init__(self):
        self._recipes: Dict[str, BaseRecipe] = {}
        self._discover_all()

    def _discover_all(self):
        """
        Scan search paths and load all valid recipe modules.
        """
        for search_dir in self.SEARCH_PATHS:
            if not os.path.exists(search_dir) or not os.path.isdir(search_dir):
                continue

            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)
                if not os.path.isdir(item_path):
                    continue

                recipe_py = os.path.join(item_path, "recipe.py")
                if os.path.isfile(recipe_py):
                    try:
                        self._load_recipe_from_file(recipe_py)
                    except Exception as e:
                        pass

    def _load_recipe_from_file(self, file_path: str):
        """
        Dynamically import recipe.py and instantiate any BaseRecipe subclasses.
        """
        module_name = f"purr_recipe_{os.path.basename(os.path.dirname(file_path))}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseRecipe) and attr is not BaseRecipe:
                    instance = attr()
                    if instance.id:
                        self._recipes[instance.id] = instance

    def list_recipes(self) -> List[BaseRecipe]:
        """
        Return a list of all registered recipes.
        """
        return list(self._recipes.values())

    def get_recipe(self, recipe_id: str) -> Optional[BaseRecipe]:
        """
        Lookup recipe by ID (e.g. 'waydroid-native').
        """
        return self._recipes.get(recipe_id)

    def apply(self, recipe_id: str, options: Optional[Dict[str, Any]] = None) -> RecipeResult:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return RecipeResult(False, f"Recipe '{recipe_id}' not found.")

        # 1. Prerequisite checks
        pre = recipe.check_prerequisites()
        if not pre.success:
            return RecipeResult(False, f"Prerequisite check failed: {pre.message}", pre.data)

        # 2. Provisioning
        prov = recipe.provision(options)
        if not prov.success:
            return RecipeResult(False, f"Provisioning failed: {prov.message}", prov.data)

        # 3. Desktop Integration
        integ = recipe.integrate_desktop()
        if not integ.success:
            return RecipeResult(False, f"Desktop integration failed: {integ.message}", integ.data)

        return RecipeResult(True, f"Recipe '{recipe_id}' applied successfully!", {
            "provision": prov.data,
            "integration": integ.data
        })

    def doctor(self, recipe_id: str) -> RecipeResult:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return RecipeResult(False, f"Recipe '{recipe_id}' not found.")
        return recipe.doctor()

    def prune(self, recipe_id: str) -> RecipeResult:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return RecipeResult(False, f"Recipe '{recipe_id}' not found.")
        return recipe.prune()

    def teardown(self, recipe_id: str) -> RecipeResult:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return RecipeResult(False, f"Recipe '{recipe_id}' not found.")
        return recipe.teardown()
