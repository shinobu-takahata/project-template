from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class Example:
    """サンプルエンティティ"""

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    def update_name(self, new_name: str) -> None:
        """名前を更新"""
        if not new_name or len(new_name.strip()) == 0:
            raise ValueError("Name cannot be empty")
        self.name = new_name
        self.updated_at = datetime.now(UTC)
