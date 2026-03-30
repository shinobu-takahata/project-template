from abc import ABC, abstractmethod

from app.domain.product.entities.product import Product
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.sku import SKU


class IProductRepository(ABC):
    """商品リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, product_id: ProductId) -> Product | None:
        """IDで商品を取得する"""
        pass

    @abstractmethod
    def find_by_sku(self, sku: SKU) -> Product | None:
        """SKUで商品を取得する"""
        pass

    @abstractmethod
    def find_all(
        self,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Product], int]:
        """商品一覧を取得する（ページネーション対応）

        Returns:
            tuple[list[Product], int]: (商品リスト, 総件数)
        """
        pass

    @abstractmethod
    def save(self, product: Product) -> None:
        """商品を保存する（作成・更新）"""
        pass

    @abstractmethod
    def find_by_ids(self, product_ids: list[ProductId]) -> list[Product]:
        """複数の商品IDで商品を一括取得する"""
        pass
