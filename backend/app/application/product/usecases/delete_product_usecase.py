from sqlalchemy.orm import Session

from app.application.product.exceptions import ProductInUseError, ProductNotFoundError
from app.domain.product.repositories.order_repository import IOrderRepository
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.product.value_objects.product_id import ProductId


class DeleteProductUseCase:
    """商品削除ユースケース"""

    def __init__(
        self,
        product_repository: IProductRepository,
        order_repository: IOrderRepository,
        db: Session,
    ):
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.db = db

    def execute(self, product_id: str) -> None:
        product = self.product_repository.find_by_id(ProductId(product_id))
        if product is None:
            raise ProductNotFoundError(
                f"Product with ID '{product_id}' not found"
            )

        if self.order_repository.exists_active_order_with_product(product.id):
            raise ProductInUseError(
                f"Product '{product_id}' cannot be deleted because it is in active orders"
            )

        product.delete()

        try:
            self.product_repository.save(product)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
