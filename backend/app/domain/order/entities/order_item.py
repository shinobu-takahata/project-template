from dataclasses import dataclass

from app.domain.order.value_objects.money import Money
from app.domain.product.value_objects.product_id import ProductId


@dataclass
class OrderItem:
    """注文明細エンティティ"""

    product_id: ProductId
    product_name: str
    unit_price: Money
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    @property
    def subtotal(self) -> Money:
        """小計を計算する"""
        return Money(self.unit_price.value * self.quantity)
