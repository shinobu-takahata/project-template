from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.address import Address


class TestShippingAddress:
    def test_create_shipping_address(self):
        addr = ShippingAddress.create(
            label="自宅",
            address=Address(
                postal_code="100-0001",
                prefecture="東京都",
                city="千代田区",
                street="千代田1-1-1",
            ),
            is_default=True,
        )

        assert addr.id is not None
        assert addr.label == "自宅"
        assert addr.address.postal_code == "100-0001"
        assert addr.is_default is True

    def test_create_non_default_address(self):
        addr = ShippingAddress.create(
            label="会社",
            address=Address(
                postal_code="150-0001",
                prefecture="東京都",
                city="渋谷区",
                street="渋谷2-2-2",
            ),
        )

        assert addr.is_default is False

    def test_unique_ids(self):
        addr1 = ShippingAddress.create(
            label="自宅",
            address=Address("100-0001", "東京都", "千代田区", "千代田1-1-1"),
        )
        addr2 = ShippingAddress.create(
            label="会社",
            address=Address("150-0001", "東京都", "渋谷区", "渋谷2-2-2"),
        )

        assert addr1.id != addr2.id
