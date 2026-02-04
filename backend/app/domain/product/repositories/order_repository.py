from abc import ABC, abstractmethod

from app.domain.product.value_objects.product_id import ProductId


class IOrderRepository(ABC):
    """注文リポジトリインターフェース"""

    @abstractmethod
    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        """未完了注文に商品が含まれているか確認する

        未完了注文: CONFIRMED, PAID, PREPARING, SHIPPED
        """
        pass

    @abstractmethod
    def find_by_customer_id(
        self,
        customer_id: str,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        """顧客IDで注文一覧を取得する（ページネーション対応）

        Returns:
            tuple[list[dict], int]: (注文リスト, 総件数)
        """
        pass
