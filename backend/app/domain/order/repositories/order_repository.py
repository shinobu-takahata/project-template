from abc import ABC, abstractmethod

from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.entities.order import Order
from app.domain.order.value_objects.order_id import OrderId


class IOrderRepository(ABC):
    """注文リポジトリインターフェース"""

    @abstractmethod
    def save(self, order: Order) -> None:
        """注文を保存する"""
        pass

    @abstractmethod
    def find_by_id(self, order_id: OrderId) -> Order | None:
        """注文IDで注文を取得する"""
        pass

    @abstractmethod
    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Order], int]:
        """顧客IDで注文一覧を取得する"""
        pass

    @abstractmethod
    def exists_active_order_with_product(self, product_id: str) -> bool:
        """未完了注文に商品が含まれているか確認する"""
        pass
