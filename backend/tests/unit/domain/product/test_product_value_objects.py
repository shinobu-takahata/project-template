import pytest

from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU


class TestProductId:
    def test_create_with_valid_value(self):
        pid = ProductId("test-id-123")
        assert pid.value == "test-id-123"

    def test_generate_creates_unique_ids(self):
        id1 = ProductId.generate()
        id2 = ProductId.generate()
        assert id1.value != id2.value

    def test_empty_string_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ProductId("")

    def test_whitespace_only_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ProductId("   ")

    def test_is_immutable(self):
        pid = ProductId("test-id")
        with pytest.raises(AttributeError):
            pid.value = "new-id"


class TestProductName:
    def test_create_with_valid_value(self):
        name = ProductName("ワイヤレスマウス")
        assert name.value == "ワイヤレスマウス"

    def test_empty_string_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ProductName("")

    def test_whitespace_only_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ProductName("   ")

    def test_over_200_chars_raises_error(self):
        with pytest.raises(ValueError, match="200 characters or less"):
            ProductName("a" * 201)

    def test_exactly_200_chars_is_valid(self):
        name = ProductName("a" * 200)
        assert len(name.value) == 200


class TestSKU:
    def test_create_with_valid_value(self):
        sku = SKU("WM-001")
        assert sku.value == "WM-001"

    def test_alphanumeric_only_is_valid(self):
        sku = SKU("ABC123")
        assert sku.value == "ABC123"

    def test_with_hyphens_is_valid(self):
        sku = SKU("WM-001-A")
        assert sku.value == "WM-001-A"

    def test_empty_string_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            SKU("")

    def test_over_50_chars_raises_error(self):
        with pytest.raises(ValueError, match="50 characters or less"):
            SKU("a" * 51)

    def test_special_chars_raises_error(self):
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            SKU("WM@001")

    def test_spaces_raises_error(self):
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            SKU("WM 001")

    def test_underscore_raises_error(self):
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            SKU("WM_001")


class TestPrice:
    def test_create_with_valid_value(self):
        price = Price(3000)
        assert price.value == 3000

    def test_zero_is_valid(self):
        price = Price(0)
        assert price.value == 0

    def test_negative_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            Price(-1)

    def test_is_immutable(self):
        price = Price(1000)
        with pytest.raises(AttributeError):
            price.value = 2000
