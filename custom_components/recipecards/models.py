from dataclasses import dataclass, field
from typing import List, Optional, Any
import re

_DURATION_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours|hour|hrs|hr|h|minutes|minute|mins|min)\b",
    re.IGNORECASE,
)

_TIME_PHRASE_RE = re.compile(
    r"(?P<label>preparation|prep|cook|bake|roast|grill|total|overall)"
    r"(?:\s*time)?[\s:\-]*(?:for\s+)?"
    r"(?P<body>(?:\d+(?:\.\d+)?\s*"
    r"(?:hours|hour|hrs|hr|h|minutes|minute|mins|min)\b\s*)+)",
    re.IGNORECASE,
)


@dataclass
class Recipe:
    id: str
    title: str
    description: Optional[str] = ""
    ingredients: List[str] = field(default_factory=list)
    notes: Optional[str] = ""
    instructions: List[str] = field(default_factory=list)
    color: str = "#FFD700"  # Default gold
    image: Optional[str] = None  # Base64 image or URL
    prep_time: Optional[int] = None  # Minutes
    cook_time: Optional[int] = None  # Minutes
    total_time: Optional[int] = None  # Minutes
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ingredients": self.ingredients,
            "notes": self.notes,
            "instructions": self.instructions,
            "color": self.color,
            "image": self.image,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "total_time": self.total_time,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recipe":
        import uuid
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            ingredients=data.get("ingredients", []),
            notes=data.get("notes", ""),
            instructions=data.get("instructions", []),
            color=data.get("color", "#FFD700"),
            image=data.get("image"),
            prep_time=data.get("prep_time"),
            cook_time=data.get("cook_time"),
            total_time=data.get("total_time"),
            tags=[str(t).strip() for t in (data.get("tags") or []) if str(t).strip()],
        )

    @classmethod
    def parse_times(cls, text: str) -> dict[str, Optional[int]]:
        """Parse prep_time, cook_time and total_time (minutes) out of recipe text.

        Recognises phrasings like "Prep: 15 min", "bake for 1 hour 30 minutes",
        "total 45 mins". Returns None for anything it cannot find.
        """
        times: dict[str, Optional[int]] = {
            "prep_time": None,
            "cook_time": None,
            "total_time": None,
        }
        if not text:
            return times

        for match in _TIME_PHRASE_RE.finditer(str(text)):
            label = match.group("label").lower()
            minutes = cls._duration_to_minutes(match.group("body"))
            if minutes is None:
                continue
            if label.startswith("prep"):
                key = "prep_time"
            elif label in ("total", "overall"):
                key = "total_time"
            else:
                key = "cook_time"
            if times[key] is None:  # first mention wins
                times[key] = minutes

        if (
            times["total_time"] is None
            and times["prep_time"] is not None
            and times["cook_time"] is not None
        ):
            times["total_time"] = times["prep_time"] + times["cook_time"]

        return times

    @staticmethod
    def _duration_to_minutes(body: str) -> Optional[int]:
        """Sum every "<number> <unit>" pair in `body` into whole minutes."""
        total = 0.0
        found = False
        for value, unit in _DURATION_UNIT_RE.findall(body):
            if unit.lower().startswith("h"):
                total += float(value) * 60
            else:
                total += float(value)
            found = True
        if not found or total <= 0:
            return None
        return int(round(total))
