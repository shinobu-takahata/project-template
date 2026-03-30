from unittest.mock import MagicMock

import pytest

from app.application.product.dtos.product_dto import UpdateProductInputDTO
from app.application.product.exceptions import ProductNotFoundError
from app.application.product.usecases.update_product_usecase import (
    UpdateProductUseCase,
)
from app.domain.product.entities.product import Product
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from tests.unit.mocks.mock_product_repository import MockProductRepository


class TestUpdateProductUseCase:
    def _setup(self):
        product_repo = MockProductRepository()
        mock_db = MagicMock()
        usecase = UpdateProductUseCase(product_repo, mock_db)

        product = Product.create(
            name=ProductName("Original"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Original",
        )
        product_repo.save(product)

        return usecase, product_repo, mock_db, product

    def test_update_product_success(self):
        usecase, _, mock_db, product = self._setup()

        input_dto = UpdateProductInputDTO(
            name="Updated",
            price=2000,
            category="Updated",
            description="New desc",
        )

        result = usecase.execute(product.id.value, input_dto)

        assert result.name == "Updated"
        assert result.price == 2000
        assert result.category == "Updated"
        assert result.description == "New desc"
        mock_db.commit.assert_called_once()

    def test_update_nonexistent_product_raises_error(self):
        usecase, _, _, _ = self._setup()

        input_dto = UpdateProductInputDTO(
            name="Updated",
            price=2000,
            category="Updated",
            description=None,
        )

        with pytest.raises(ProductNotFoundError, match="not found"):
            usecase.execute("nonexistent-id", input_dto)

    def test_update_deleted_product_raises_error(self):
        usecase, product_repo, _, product = self._setup()

        product.delete()
        product_repo.save(product)

        input_dto = UpdateProductInputDTO(
            name="Updated",
            price=2000,
            category="Updated",
            description=None,
        )

        with pytest.raises(ProductNotFoundError):
            usecase.execute(product.id.value, input_dto)
