# Recipe System Integration

This directory contains the interface and placeholder implementation for the AI Matrx Recipe system.

## Architecture

- `interfaces.py` — The `RecipeResolverInterface` ABC and `RecipeResult` Pydantic model. **Do not modify.**
- `resolver.py` — `PlaceholderRecipeResolver` that returns sensible defaults for any agent ID.

## Replacing the Placeholder

To integrate the real Recipe system:

1. Create a new class that extends `RecipeResolverInterface`
2. Implement the `resolve()` async method
3. Update the dependency injection in `engine/main.py` to use your implementation
4. The `resolve_sync()` method is inherited and handles sync-context calls automatically

The `RecipeResult` model is the **contract**. Every resolver must return this exact shape.
