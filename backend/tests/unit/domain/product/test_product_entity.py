import pytest

from app.domain.product.entities.product import Product
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU


class TestProductCreate:
    def test_create_product(self):
        product = Product.create(
            name=ProductName("ワイヤレスマウス"),
            sku=SKU("WM-001"),
            price=Price(3000),
            category="PC周辺機器",
            description="Bluetooth対応",
        )

        assert product.id is not None
        assert product.name.value == "ワイヤレスマウス"
        assert product.sku.value == "WM-001"
        assert product.price.value == 3000
        assert product.category == "PC周辺機器"
        assert product.description == "Bluetooth対応"
        assert product.deleted_at is None
        assert product.is_deleted is False

    def test_create_product_without_description(self):
        product = Product.create(
            name=ProductName("マウス"),
            sku=SKU("M-001"),
            price=Price(1000),
            category="PC周辺機器",
        )

        assert product.description is None

    def test_create_generates_unique_ids(self):
        p1 = Product.create(
            name=ProductName("Product 1"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        p2 = Product.create(
            name=ProductName("Product 2"),
            sku=SKU("SKU-002"),
            price=Price(2000),
            category="Test",
        )

        assert p1.id.value != p2.id.value


class TestProductUpdate:
    def test_update_product(self):
        product = Product.create(
            name=ProductName("Original"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Original",
        )
        original_updated_at = product.updated_at

        product.update(
            name=ProductName("Updated"),
            price=Price(2000),
            category="Updated",
            description="New description",
        )

        assert product.name.value == "Updated"
        assert product.price.value == 2000
        assert product.category == "Updated"
        assert product.description == "New description"
        assert product.updated_at >= original_updated_at

    def test_update_deleted_product_raises_error(self):
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        product.delete()

        with pytest.raises(ValueError, match="Cannot update a deleted product"):
            product.update(
                name=ProductName("Updated"),
                price=Price(2000),
                category="Test",
                description=None,
            )


class TestProductDelete:
    def test_delete_product(self):
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )

        product.delete()

        assert product.is_deleted is True
        assert product.deleted_at is not None

    def test_delete_already_deleted_raises_error(self):
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        product.delete()

        with pytest.raises(ValueError, match="already deleted"):
            product.delete()
