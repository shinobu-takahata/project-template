from app.domain.product.repositories.order_repository import IOrderRepository
from app.domain.product.value_objects.product_id import ProductId


class MockOrderRepository(IOrderRepository):
    """テスト用モック注文リポジトリ"""

    def __init__(self, active_product_ids: list[str] | None = None):
        self.active_product_ids: set[str] = set(active_product_ids or [])

    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        return product_id.value in self.active_product_ids
