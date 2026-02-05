from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU


@dataclass
class Product:
    """商品エンティティ（集約ルート）"""

    id: ProductId
    name: ProductName
    sku: SKU
    price: Price
    category: str
    description: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        name: ProductName,
        sku: SKU,
        price: Price,
        category: str,
        description: str | None = None,
    ) -> "Product":
        """商品を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Product(
            id=ProductId.generate(),
            name=name,
            sku=sku,
            price=price,
            category=category,
            description=description,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        name: ProductName,
        price: Price,
        category: str,
        description: str | None,
    ) -> None:
        """商品情報を更新する"""
        if self.deleted_at is not None:
            raise ValueError("Cannot update a deleted product")

        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.updated_at = datetime.now(UTC)

    def delete(self) -> None:
        """論理削除する"""
        if self.deleted_at is not None:
            raise ValueError("Product is already deleted")

        now = datetime.now(UTC)
        self.deleted_at = now
        self.updated_at = now

    @property
    def is_deleted(self) -> bool:
        """削除済みかどうか"""
        return self.deleted_at is not None
