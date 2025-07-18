from .const import DOMAIN
from .storage import RecipeStorage
from .api import register_api

async def async_setup(hass, config):
    hass.data[DOMAIN] = RecipeStorage(hass)
    register_api(hass)
    return True 