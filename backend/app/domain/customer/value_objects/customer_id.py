from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class CustomerId:
    """顧客ID値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("CustomerId cannot be empty")

    @staticmethod
    def generate() -> "CustomerId":
        """新しい顧客IDを生成する"""
        return CustomerId(str(uuid.uuid4()))
