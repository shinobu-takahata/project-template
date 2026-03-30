from unittest.mock import MagicMock

import pytest

from app.application.product.dtos.product_dto import RegisterProductInputDTO
from app.application.product.exceptions import DuplicateSKUError
from app.application.product.usecases.register_product_usecase import (
    RegisterProductUseCase,
)
from app.domain.product.entities.product import Product
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from tests.unit.mocks.mock_product_repository import MockProductRepository
from tests.unit.mocks.mock_stock_repository import MockStockRepository


class TestRegisterProductUseCase:
    def _create_usecase(self):
        product_repo = MockProductRepository()
        stock_repo = MockStockRepository()
        mock_db = MagicMock()
        usecase = RegisterProductUseCase(product_repo, stock_repo, mock_db)
        return usecase, product_repo, stock_repo, mock_db

    def test_register_product_success(self):
        usecase, product_repo, stock_repo, mock_db = self._create_usecase()

        input_dto = RegisterProductInputDTO(
            name="ワイヤレスマウス",
            sku="WM-001",
            price=3000,
            category="PC周辺機器",
            description="Bluetooth対応",
            initial_stock=100,
        )

        result = usecase.execute(input_dto)

        assert result.name == "ワイヤレスマウス"
        assert result.sku == "WM-001"
        assert result.price == 3000
        assert result.stock_quantity == 100
        assert len(product_repo.products) == 1
        assert len(stock_repo.stocks) == 1
        mock_db.commit.assert_called_once()

    def test_register_product_duplicate_sku_raises_error(self):
        usecase, product_repo, _, _ = self._create_usecase()

        existing = Product.create(
            name=ProductName("Existing"),
            sku=SKU("WM-001"),
            price=Price(1000),
            category="Test",
        )
        product_repo.save(existing)

        input_dto = RegisterProductInputDTO(
            name="New Product",
            sku="WM-001",
            price=2000,
            category="Test",
            description=None,
            initial_stock=50,
        )

        with pytest.raises(DuplicateSKUError, match="already exists"):
            usecase.execute(input_dto)

    def test_register_product_invalid_price_raises_error(self):
        usecase, _, _, _ = self._create_usecase()

        input_dto = RegisterProductInputDTO(
            name="Test",
            sku="SKU-001",
            price=-100,
            category="Test",
            description=None,
            initial_stock=10,
        )

        with pytest.raises(ValueError, match="non-negative"):
            usecase.execute(input_dto)

    def test_register_product_invalid_sku_raises_error(self):
        usecase, _, _, _ = self._create_usecase()

        input_dto = RegisterProductInputDTO(
            name="Test",
            sku="INVALID SKU!",
            price=1000,
            category="Test",
            description=None,
            initial_stock=10,
        )

        with pytest.raises(ValueError, match="alphanumeric"):
            usecase.execute(input_dto)
