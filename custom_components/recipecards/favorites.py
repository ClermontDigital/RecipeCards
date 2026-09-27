"""Per-user favourite recipes."""
from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY = "recipecards_favorites.json"


class FavoriteStore:
    """Recipe ids each Home Assistant user has starred.

    Kept apart from the recipes: the recipes are shared by the household, a
    favourite is one person's. Like the recipe stores it is never deleted
    automatically.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._users: dict[str, list[str]] | None = None
        # Serialises read-change-write, as RecipeStorage does.
        self._lock = asyncio.Lock()

    async def _load(self) -> dict[str, list[str]]:
        if self._users is None:
            raw = await self._store.async_load()
            users = raw.get("users") if isinstance(raw, dict) else None
            self._users = {
                str(user): [str(i) for i in ids]
                for user, ids in (users or {}).items()
                if isinstance(ids, list)
            }
        return self._users

    async def async_get(self, user_id: str) -> set[str]:
        """The recipe ids this user has starred."""
        async with self._lock:
            return set((await self._load()).get(user_id, []))

    async def async_set(
        self, user_id: str, recipe_id: str, favorite: bool, existing: set[str]
    ) -> set[str]:
        """Star or unstar one recipe; ids of deleted recipes are dropped on the way."""
        async with self._lock:
            users = await self._load()
            ids = [i for i in users.get(user_id, []) if i != recipe_id and i in existing]
            if favorite:
                ids.append(recipe_id)
            if ids:
                users[user_id] = ids
            else:
                users.pop(user_id, None)
            await self._store.async_save({"users": users})
            return set(ids)


def get_favorites(hass: HomeAssistant) -> FavoriteStore:
    """The one FavoriteStore for this HA run."""
    domain = hass.data.setdefault(DOMAIN, {})
    store = domain.get("favorites")
    if store is None:
        store = domain["favorites"] = FavoriteStore(hass)
    return store
