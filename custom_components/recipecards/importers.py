"""Importers that turn other recipe apps' data into Recipe Cards recipes.

Each importer returns a list of plain dicts in the shape `add_recipe` accepts, so
adding a new source means writing a parser rather than a new integration.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import os
import re
import zipfile
from typing import Any, Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|m)\b", re.IGNORECASE
)
_ISO_RE = re.compile(
    r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?$", re.IGNORECASE
)


def parse_duration(value: Any) -> int | None:
    """Minutes from either an ISO 8601 duration or free text like '1 hour 30 mins'.

    Mealie stores times as whatever the user typed, so both shapes turn up.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = int(value)
        return v if 0 < v <= 1440 else None
    text = str(value).strip()
    if not text:
        return None

    iso = _ISO_RE.match(text)
    if iso and any(iso.groups()):
        d, h, m = (int(x) if x else 0 for x in iso.groups())
        total = d * 1440 + h * 60 + m
        return total if 0 < total <= 1440 else None

    total = 0
    for amount, unit in _UNIT_RE.findall(text):
        total += float(amount) * (60 if unit.lower().startswith("h") else 1)
    total = int(round(total))
    return total if 0 < total <= 1440 else None


def _clean(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _mealie_ingredient(item: Any) -> str:
    """Mealie ingredients are either a plain string or a structured object."""
    if isinstance(item, str):
        return _clean(item)
    if not isinstance(item, dict):
        return ""
    # `display` is what Mealie itself renders, so prefer it when present
    if _clean(item.get("display")):
        return _clean(item.get("display"))
    parts = []
    qty = item.get("quantity")
    if qty:
        qty = int(qty) if float(qty).is_integer() else qty
        parts.append(str(qty))
    unit = item.get("unit")
    if isinstance(unit, dict):
        unit = unit.get("name")
    if unit:
        parts.append(_clean(unit))
    food = item.get("food")
    if isinstance(food, dict):
        food = food.get("name")
    if food:
        parts.append(_clean(food))
    note = _clean(item.get("note"))
    line = " ".join(p for p in parts if p)
    if note:
        line = f"{line}, {note}" if line else note
    return line.strip(", ")


def _names(values: Iterable[Any]) -> list[str]:
    out = []
    for v in values or []:
        name = v.get("name") if isinstance(v, dict) else v
        name = _clean(name)
        if name and name not in out:
            out.append(name)
    return out


def mealie_to_recipe(data: dict, base_url: str) -> dict | None:
    """Map one Mealie recipe onto the Recipe Cards shape."""
    title = _clean(data.get("name"))
    if not title:
        return None

    ingredients = [i for i in (_mealie_ingredient(x) for x in data.get("recipeIngredient") or []) if i]
    instructions = []
    for step in data.get("recipeInstructions") or []:
        text = _clean(step.get("text") if isinstance(step, dict) else step)
        if text:
            instructions.append(text)

    tags = _names(data.get("tags"))
    for category in _names(data.get("recipeCategory")):
        if category not in tags:
            tags.append(category)

    notes = []
    for note in data.get("notes") or []:
        text = _clean(note.get("text") if isinstance(note, dict) else note)
        title_ = _clean(note.get("title")) if isinstance(note, dict) else ""
        if text:
            notes.append(f"{title_}: {text}" if title_ else text)
    if data.get("orgURL"):
        notes.append(f"Source: {_clean(data['orgURL'])}")
    if data.get("recipeYield"):
        notes.insert(0, f"Serves/makes: {_clean(data['recipeYield'])}")

    recipe: dict[str, Any] = {
        "title": title[:100],
        "description": _clean(data.get("description"))[:480],
        "ingredients": [i[:200] for i in ingredients][:60],
        "instructions": [s[:500] for s in instructions][:40],
        "notes": "\n\n".join(notes)[:1000],
        "tags": tags[:20],
    }
    prep = parse_duration(data.get("prepTime"))
    cook = parse_duration(data.get("performTime") or data.get("cookTime"))
    total = parse_duration(data.get("totalTime"))
    if prep: recipe["prep_time"] = prep
    if cook: recipe["cook_time"] = cook
    if total: recipe["total_time"] = total

    rid = data.get("id")
    if rid:
        recipe["image"] = f"{base_url.rstrip('/')}/api/media/recipes/{rid}/images/original.webp"
    return recipe


async def fetch_mealie(hass: HomeAssistant, base_url: str, token: str) -> list[dict]:
    """Pull every recipe out of a Mealie server."""
    session = async_get_clientsession(hass)
    base = base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    slugs: list[str] = []
    page = 1
    while True:
        async with session.get(
            f"{base}/api/recipes",
            headers=headers,
            params={"page": page, "perPage": 100},
            timeout=60,
        ) as resp:
            if resp.status == 401:
                raise ValueError("Mealie rejected the token (401). Check the API token.")
            resp.raise_for_status()
            payload = await resp.json()
        items = payload.get("items", payload if isinstance(payload, list) else [])
        if not items:
            break
        slugs.extend(i.get("slug") or i.get("id") for i in items if isinstance(i, dict))
        if len(items) < 100:
            break
        page += 1

    recipes: list[dict] = []
    for slug in slugs:
        if not slug:
            continue
        try:
            async with session.get(f"{base}/api/recipes/{slug}", headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                detail = await resp.json()
        except Exception:  # noqa: BLE001 - one bad recipe must not stop the import
            _LOGGER.warning("Recipe Cards: could not read Mealie recipe '%s'", slug)
            continue
        mapped = mealie_to_recipe(detail, base)
        if mapped:
            recipes.append(mapped)
    return recipes


# --------------------------------------------------------------------------
# Mela (https://mela.recipes/fileformat/)
#
# A .melarecipe is a single JSON document. A .melarecipes is a zip of those.
# Ingredients and instructions are one string each, newline separated, and may
# carry markdown. Images are base64 strings, which is why they are written out
# to <config>/www rather than stuffed into the store: a few hundred recipes of
# embedded photos would be tens of megabytes of JSON.
# --------------------------------------------------------------------------

_MD_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_MD_HEADING = re.compile(r"^\s*#{1,6}\s*")

IMAGE_MAGIC = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF8", "gif"),
)


def _strip_markdown(line: str) -> str:
    line = _MD_HEADING.sub("", line)
    line = _MD_BULLET.sub("", line)
    line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    line = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", line)
    return line.strip()


def _lines(blob: Any) -> list[str]:
    out = []
    for raw in str(blob or "").replace("\r\n", "\n").split("\n"):
        line = _strip_markdown(raw)
        if line:
            out.append(line)
    return out


def _image_kind(data: bytes) -> str | None:
    for magic, ext in IMAGE_MAGIC:
        if data.startswith(magic):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[4:8] == b"ftyp" and b"hei" in data[8:16].lower():
        return "heic"  # iOS native; browsers will not render it
    return None


def _write_image(blob: str, image_dir: str, url_base: str) -> str | None:
    """Decode one base64 image to <config>/www and return its /local URL."""
    payload = str(blob or "")
    if payload.startswith("data:"):
        payload = payload.split(",", 1)[-1]
    try:
        data = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError):
        return None
    if len(data) < 64:
        return None
    kind = _image_kind(data)
    if kind is None:
        _LOGGER.debug("Recipe Cards: skipping a Mela image of unrecognised type")
        return None
    if kind == "heic":
        _LOGGER.warning(
            "Recipe Cards: a Mela photo is HEIC, which browsers cannot display. Skipped."
        )
        return None
    name = f"{hashlib.sha1(data).hexdigest()[:16]}.{kind}"
    os.makedirs(image_dir, exist_ok=True)
    path = os.path.join(image_dir, name)
    if not os.path.exists(path):
        with open(path, "wb") as handle:
            handle.write(data)
    return f"{url_base}/{name}"


def mela_to_recipe(data: dict, image_dir: str | None, url_base: str) -> dict | None:
    title = _clean(data.get("title"))
    if not title:
        return None

    notes = []
    if _clean(data.get("yield")):
        notes.append(f"Serves/makes: {_clean(data['yield'])}")
    for line in _lines(data.get("notes")):
        notes.append(line)
    if _clean(data.get("nutrition")):
        notes.append(f"Nutrition: {_clean(data['nutrition'])}")
    if _clean(data.get("link")):
        notes.append(f"Source: {_clean(data['link'])}")

    recipe: dict[str, Any] = {
        "title": title[:100],
        "description": _clean(data.get("text"))[:480],
        "ingredients": [i[:200] for i in _lines(data.get("ingredients"))][:60],
        "instructions": [s[:500] for s in _lines(data.get("instructions"))][:40],
        "notes": "\n\n".join(notes)[:1000],
        "tags": [t for t in (_clean(c) for c in data.get("categories") or []) if t][:20],
    }
    for key, field in (("prepTime", "prep_time"), ("cookTime", "cook_time"), ("totalTime", "total_time")):
        value = parse_duration(data.get(key))
        if value:
            recipe[field] = value

    images = data.get("images") or []
    if images and image_dir:
        url = _write_image(images[0], image_dir, url_base)
        if url:
            recipe["image"] = url
    return recipe


def parse_mela(path: str, image_dir: str | None, url_base: str) -> list[dict]:
    """Read a .melarecipe or .melarecipes file. Blocking: call in the executor."""
    if not os.path.exists(path):
        raise ValueError(f"No such file: {path}")

    documents: list[dict] = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith("/") or os.path.basename(name).startswith("."):
                    continue
                if not name.lower().endswith(".melarecipe"):
                    continue
                try:
                    documents.append(json.loads(archive.read(name).decode("utf-8")))
                except Exception:  # noqa: BLE001 - one bad entry must not stop the import
                    _LOGGER.warning("Recipe Cards: could not read '%s' from the Mela archive", name)
    else:
        with open(path, "rb") as handle:
            raw = handle.read().decode("utf-8")
        parsed = json.loads(raw)
        documents = parsed if isinstance(parsed, list) else [parsed]

    if not documents:
        raise ValueError(
            "No recipes found. Expected a .melarecipe file, or a .melarecipes archive."
        )

    out = []
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        mapped = mela_to_recipe(doc, image_dir, url_base)
        if mapped:
            out.append(mapped)
    return out
