from unittest.mock import MagicMock

import pytest

from app.application.product.exceptions import ProductInUseError, ProductNotFoundError
from app.application.product.usecases.delete_product_usecase import (
    DeleteProductUseCase,
)
from app.domain.product.entities.product import Product
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from tests.unit.mocks.mock_order_repository import MockOrderRepository
from tests.unit.mocks.mock_product_repository import MockProductRepository


class TestDeleteProductUseCase:
    def _setup(self, active_product_ids: list[str] | None = None):
        product_repo = MockProductRepository()
        order_repo = MockOrderRepository(active_product_ids)
        mock_db = MagicMock()
        usecase = DeleteProductUseCase(product_repo, order_repo, mock_db)

        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        product_repo.save(product)

        return usecase, product_repo, mock_db, product

    def test_delete_product_success(self):
        usecase, product_repo, mock_db, product = self._setup()

        usecase.execute(product.id.value)

        deleted = product_repo.products[product.id.value]
        assert deleted.is_deleted is True
        mock_db.commit.assert_called_once()

    def test_delete_nonexistent_product_raises_error(self):
        usecase, _, _, _ = self._setup()

        with pytest.raises(ProductNotFoundError, match="not found"):
            usecase.execute("nonexistent-id")

    def test_delete_product_in_use_raises_error(self):
        product_repo = MockProductRepository()
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        product_repo.save(product)

        order_repo = MockOrderRepository([product.id.value])
        mock_db = MagicMock()
        usecase = DeleteProductUseCase(product_repo, order_repo, mock_db)

        with pytest.raises(ProductInUseError, match="active orders"):
            usecase.execute(product.id.value)
