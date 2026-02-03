from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class StockId:
    """在庫ID値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("StockId cannot be empty")

    @staticmethod
    def generate() -> "StockId":
        """新しい在庫IDを生成する"""
        return StockId(str(uuid.uuid4()))
