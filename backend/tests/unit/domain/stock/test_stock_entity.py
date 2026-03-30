import pytest

from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.entities.stock import Stock
from app.domain.stock.value_objects.stock_quantity import StockQuantity


class TestStockInitialize:
    def test_initialize_stock(self):
        product_id = ProductId.generate()
        stock = Stock.initialize(
            product_id=product_id,
            quantity=StockQuantity(100),
        )

        assert stock.id is not None
        assert stock.product_id.value == product_id.value
        assert stock.quantity.value == 100

    def test_initialize_with_zero_quantity(self):
        product_id = ProductId.generate()
        stock = Stock.initialize(
            product_id=product_id,
            quantity=StockQuantity(0),
        )

        assert stock.quantity.value == 0

    def test_negative_quantity_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            StockQuantity(-1)
