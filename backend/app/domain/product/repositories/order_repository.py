from abc import ABC, abstractmethod

from app.domain.product.value_objects.product_id import ProductId


class IOrderRepository(ABC):
    """注文リポジトリインターフェース（商品削除チェック用）"""

    @abstractmethod
    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        """未完了注文に商品が含まれているか確認する

        未完了注文: CONFIRMED, PAID, PREPARING, SHIPPED
        """
        pass
