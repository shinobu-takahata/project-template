from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class ProductId:
    """商品ID値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("ProductId cannot be empty")

    @staticmethod
    def generate() -> "ProductId":
        """新しい商品IDを生成する"""
        return ProductId(str(uuid.uuid4()))
