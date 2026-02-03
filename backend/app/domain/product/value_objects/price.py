from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    """価格値オブジェクト（円単位）"""

    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Price must be non-negative")
