from sqlalchemy.orm import Session

from app.domain.product.repositories.order_repository import IOrderRepository
from app.domain.product.value_objects.product_id import ProductId


class OrderRepository(IOrderRepository):
    """注文リポジトリ実装（スタブ）

    注文エンドポイント実装時に完全な実装に置き換える。
    """

    def __init__(self, db: Session):
        self.db = db

    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        # スタブ実装: 常にFalseを返す（削除を許可）
        return False
