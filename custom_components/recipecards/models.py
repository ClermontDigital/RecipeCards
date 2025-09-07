from dataclasses import dataclass, field
from typing import List, Optional, Any
import re

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
        )

    @classmethod
    @classmethod
    def parse_times(cls, text: str) -> dict[str, Optional[int]]:
        """Parse prep_time, cook_time, total_time from instructions/notes text using regex."""
        # Combine all text for parsing
        full_text = text.lower() if isinstance(text, str) else str(text)

        times: dict[str, Optional[int]] = {'prep_time': None, 'cook_time': None, 'total_time': None}

        # Regex patterns for common time formats (minutes or hours)
        def extract_time(match_groups: tuple) -> Optional[int]:
            if not match_groups or match_groups[0] is None:
                return None
            mins = 0
            min_str = str(match_groups[0]).strip()
            # Extract hours
            hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:h|hr|hour|hours)', min_str)
            if hours_match:
                hours = float(hours_match.group(1))
                mins += int(hours * 60)
            # Extract minutes
            min_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes)', min_str)
            if min_match:
                mins += int(float(min_match.group(1)))
            return mins if mins > 0 else None

        # Prep time
        prep_match = re.search(r'(?:prep|preparation)[\s:]*(\d+(?:\.\d+)?)\s*(?:min|minutes|mins|(?:hr|hours|h)\.?\s*(\d+(?:\.\d+)?)?)', full_text, re.IGNORECASE)
        if prep_match:
            times['prep_time'] = extract_time(prep_match.groups())

        # Cook/Bake time
        cook_match = re.search(r'(?:cook|bake|roast|grill)[\s:]*(\d+(?:\.\d+)?)\s*(?:min|minutes|mins|(?:hr|hours|h)\.?\s*(\d+(?:\.\d+)?)?)', full_text, re.IGNORECASE)
        if cook_match:
            times['cook_time'] = extract_time(cook_match.groups())

        # Total time (direct or sum if both prep and cook present)
        total_match = re.search(r'(?:total|overall)[\s:]*(\d+(?:\.\d+)?)\s*(?:min|minutes|mins|(?:hr|hours|h)\.?\s*(\d+(?:\.\d+)?)?)', full_text, re.IGNORECASE)
        if total_match:
            times['total_time'] = extract_time(total_match.groups())
        elif times['prep_time'] is not None and times['cook_time'] is not None:
            times['total_time'] = times['prep_time'] + times['cook_time']

        return times