from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerName:
    """顧客名値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("CustomerName cannot be empty")
        if len(self.value) > 100:
            raise ValueError("CustomerName must be 100 characters or less")
