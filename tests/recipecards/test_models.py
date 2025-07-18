import pytest
from custom_components.recipecards.models import Recipe

def test_recipe_serialization():
    data = {
        "id": "abc123",
        "title": "Test Recipe",
        "description": "desc",
        "ingredients": ["eggs", "milk"],
        "notes": "note",
        "instructions": ["step 1", "step 2"],
        "color": "#FF0000",
    }
    recipe = Recipe.from_dict(data)
    assert recipe.id == "abc123"
    assert recipe.title == "Test Recipe"
    assert recipe.description == "desc"
    assert recipe.ingredients == ["eggs", "milk"]
    assert recipe.notes == "note"
    assert recipe.instructions == ["step 1", "step 2"]
    assert recipe.color == "#FF0000"
    assert recipe.to_dict() == data 