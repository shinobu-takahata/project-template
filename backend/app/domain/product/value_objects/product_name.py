from dataclasses import dataclass


@dataclass(frozen=True)
class ProductName:
    """商品名値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("ProductName cannot be empty")
        if len(self.value) > 200:
            raise ValueError("ProductName must be 200 characters or less")
