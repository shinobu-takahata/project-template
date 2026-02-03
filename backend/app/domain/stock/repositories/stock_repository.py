from abc import ABC, abstractmethod

from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.entities.stock import Stock


class IStockRepository(ABC):
    """在庫リポジトリインターフェース"""

    @abstractmethod
    def save(self, stock: Stock) -> None:
        """在庫を保存する"""
        pass

    @abstractmethod
    def find_by_product_id(self, product_id: ProductId) -> Stock | None:
        """商品IDで在庫を取得する"""
        pass
