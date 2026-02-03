from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.value_objects.stock_id import StockId
from app.domain.stock.value_objects.stock_quantity import StockQuantity


@dataclass
class Stock:
    """在庫エンティティ（集約ルート）"""

    id: StockId
    product_id: ProductId
    quantity: StockQuantity
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def initialize(product_id: ProductId, quantity: StockQuantity) -> "Stock":
        """初期在庫を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Stock(
            id=StockId.generate(),
            product_id=product_id,
            quantity=quantity,
            created_at=now,
            updated_at=now,
        )
