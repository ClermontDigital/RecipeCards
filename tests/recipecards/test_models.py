"""Tests for the Recipe dataclass."""
from custom_components.recipecards.models import Recipe


def test_recipe_serialization_round_trip():
    data = {
        "id": "abc123",
        "title": "Test Recipe",
        "description": "desc",
        "ingredients": ["eggs", "milk"],
        "notes": "note",
        "instructions": ["step 1", "step 2"],
        "color": "#FF0000",
        "image": None,
        "prep_time": None,
        "cook_time": None,
        "total_time": None,
        "tags": [],
    }
    recipe = Recipe.from_dict(data)
    assert recipe.id == "abc123"
    assert recipe.title == "Test Recipe"
    assert recipe.ingredients == ["eggs", "milk"]
    assert recipe.instructions == ["step 1", "step 2"]
    assert recipe.color == "#FF0000"
    assert recipe.to_dict() == data


def test_from_dict_tolerates_missing_and_null_fields():
    """A hand-edited or older store file must not break loading."""
    recipe = Recipe.from_dict({"id": "x", "title": "Minimal"})
    assert recipe.ingredients == []
    assert recipe.instructions == []
    assert recipe.color == "#FFD700"
    assert recipe.prep_time is None
    assert recipe.tags == []


def test_parse_times_variants():
    assert Recipe.parse_times("Prep 10 minutes\nBake 90 minutes") == {
        "prep_time": 10, "cook_time": 90, "total_time": 100,
    }
    assert Recipe.parse_times("Roast for 1 hour 30 min") == {
        "prep_time": None, "cook_time": 90, "total_time": None,
    }
    assert Recipe.parse_times("") == {
        "prep_time": None, "cook_time": None, "total_time": None,
    }
