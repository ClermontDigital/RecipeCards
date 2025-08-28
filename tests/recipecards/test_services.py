import pytest

ha = pytest.importorskip("homeassistant")
from unittest.mock import AsyncMock, MagicMock  # noqa: E402
from custom_components.recipecards.services import cleanup_recipe_entities  # noqa: E402


def test_cleanup_recipe_entities_removes_matching(monkeypatch):
    hass = MagicMock()

    class DummyEntry:
        def __init__(self, entity_id, platform, config_entry_id, unique_id):
            self.entity_id = entity_id
            self.platform = platform
            self.config_entry_id = config_entry_id
            self.unique_id = unique_id

    class DummyRegistry:
        def __init__(self):
            self.entities = {
                "sensor.a": DummyEntry("sensor.a", "sensor", "e1", "e1_r1"),
                "sensor.b": DummyEntry("sensor.b", "sensor", "e1", "e1_r2"),
                "sensor.c": DummyEntry("sensor.c", "light", "e1", "e1_r1"),
            }
            self.removed = []

        def async_remove(self, entity_id):
            self.removed.append(entity_id)

    dummy = DummyRegistry()

    # Patch the entity registry getter
    from homeassistant.helpers import entity_registry as er

    monkeypatch.setattr(er, "async_get", lambda hass_arg: dummy)

    cleanup_recipe_entities(hass, "e1", "r1")

    assert "sensor.a" in dummy.removed
    assert "sensor.b" not in dummy.removed
    # Non-sensor platform not removed
    assert "sensor.c" not in dummy.removed

