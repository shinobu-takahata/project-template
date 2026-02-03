from sqlalchemy.orm import Session

from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import IStockRepository
from app.domain.stock.value_objects.stock_id import StockId
from app.domain.stock.value_objects.stock_quantity import StockQuantity
from app.infrastructure.database.models import StockModel


class StockRepository(IStockRepository):
    """在庫リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def save(self, stock: Stock) -> None:
        model = self.db.query(StockModel).filter(
            StockModel.id == stock.id.value,
        ).first()

        if model is None:
            model = StockModel(
                id=stock.id.value,
                product_id=stock.product_id.value,
                quantity=stock.quantity.value,
                created_at=stock.created_at,
                updated_at=stock.updated_at,
            )
            self.db.add(model)
        else:
            model.quantity = stock.quantity.value
            model.updated_at = stock.updated_at

        self.db.flush()

    def find_by_product_id(self, product_id: ProductId) -> Stock | None:
        model = self.db.query(StockModel).filter(
            StockModel.product_id == product_id.value,
        ).first()

        if model is None:
            return None

        return Stock(
            id=StockId(model.id),
            product_id=ProductId(model.product_id),
            quantity=StockQuantity(model.quantity),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
