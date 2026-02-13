"""Recipe system integration — interfaces and placeholder resolver."""

from engine.recipes.interfaces import RecipeResolverInterface, RecipeResult
from engine.recipes.resolver import PlaceholderRecipeResolver

__all__ = ["RecipeResolverInterface", "RecipeResult", "PlaceholderRecipeResolver"]
