from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import IStockRepository


class MockStockRepository(IStockRepository):
    """テスト用モック在庫リポジトリ"""

    def __init__(self):
        self.stocks: dict[str, Stock] = {}

    def save(self, stock: Stock) -> None:
        self.stocks[stock.id.value] = stock

    def find_by_product_id(self, product_id: ProductId) -> Stock | None:
        for stock in self.stocks.values():
            if stock.product_id.value == product_id.value:
                return stock
        return None
