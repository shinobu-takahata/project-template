import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderId:
    """注文ID値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("OrderId cannot be empty")

    @staticmethod
    def generate() -> "OrderId":
        """新しいOrderIdを生成する"""
        return OrderId(str(uuid.uuid4()))
