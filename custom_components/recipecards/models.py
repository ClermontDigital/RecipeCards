from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class Recipe:
    id: str
    title: str
    description: Optional[str] = ""
    ingredients: List[str] = field(default_factory=list)
    notes: Optional[str] = ""
    instructions: List[str] = field(default_factory=list)
    color: str = "#FFD700"  # Default gold

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ingredients": self.ingredients,
            "notes": self.notes,
            "instructions": self.instructions,
            "color": self.color,
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
        ) 