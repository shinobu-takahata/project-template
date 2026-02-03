from dataclasses import dataclass


@dataclass(frozen=True)
class StockQuantity:
    """在庫数量値オブジェクト"""

    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("StockQuantity must be non-negative")
