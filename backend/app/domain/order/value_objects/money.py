from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額値オブジェクト（円単位）"""

    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Money must be non-negative")

    def add(self, other: "Money") -> "Money":
        """加算"""
        return Money(self.value + other.value)

    def subtract(self, other: "Money") -> "Money":
        """減算"""
        result = self.value - other.value
        if result < 0:
            raise ValueError("Subtraction result cannot be negative")
        return Money(result)

    def multiply(self, factor: int | float) -> "Money":
        """乗算"""
        return Money(int(self.value * factor))

    def calculate_tax(self, tax_rate: float = 0.1) -> "Money":
        """消費税を計算（デフォルト10%）"""
        return Money(int(self.value * tax_rate))
