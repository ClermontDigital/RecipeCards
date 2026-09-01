"""Constants for the Recipe Cards integration."""
DOMAIN = "recipecards"

# Create one sensor entity per recipe. Off by default: a large collection would
# otherwise add hundreds of entities, each carrying a full recipe in its
# attributes, which every browser then downloads on connect. The card reads
# recipes over the WebSocket API and does not need them.
CONF_PER_RECIPE_ENTITIES = "per_recipe_entities"
DEFAULT_PER_RECIPE_ENTITIES = False
