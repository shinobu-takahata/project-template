from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SKU:
    """SKU（在庫管理単位）値オブジェクト"""

    value: str

    PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("SKU cannot be empty")
        if len(self.value) > 50:
            raise ValueError("SKU must be 50 characters or less")
        if not self.PATTERN.match(self.value):
            raise ValueError(
                "SKU must contain only alphanumeric characters and hyphens"
            )
