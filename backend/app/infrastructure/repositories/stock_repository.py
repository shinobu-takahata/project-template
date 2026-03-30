from sqlalchemy import select, update
from sqlalchemy.orm import Session, load_only

from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import IStockRepository
from app.domain.stock.value_objects.stock_id import StockId
from app.domain.stock.value_objects.stock_quantity import StockQuantity
from app.infrastructure.database.models import StockModel


class StockRepository(IStockRepository):
    """在庫リポジトリ実装"""

    _STOCK_COLUMNS = (
        StockModel.id,
        StockModel.product_id,
        StockModel.quantity,
        StockModel.created_at,
        StockModel.updated_at,
    )

    def __init__(self, db: Session):
        self.db = db

    def save(self, stock: Stock) -> None:
        exists = self.db.scalar(
            select(StockModel.id).where(StockModel.id == stock.id.value)
        )

        if exists is None:
            model = StockModel(
                id=stock.id.value,
                product_id=stock.product_id.value,
                quantity=stock.quantity.value,
                created_at=stock.created_at,
                updated_at=stock.updated_at,
            )
            self.db.add(model)
        else:
            stmt = (
                update(StockModel)
                .where(StockModel.id == stock.id.value)
                .values(
                    quantity=stock.quantity.value,
                    updated_at=stock.updated_at,
                )
            )
            self.db.execute(stmt)

        self.db.flush()

    def find_by_product_id(self, product_id: ProductId) -> Stock | None:
        stmt = (
            select(StockModel)
            .options(load_only(*self._STOCK_COLUMNS))
            .where(StockModel.product_id == product_id.value)
        )
        model = self.db.scalars(stmt).first()

        if model is None:
            return None

        return Stock(
            id=StockId(model.id),
            product_id=ProductId(model.product_id),
            quantity=StockQuantity(model.quantity),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
