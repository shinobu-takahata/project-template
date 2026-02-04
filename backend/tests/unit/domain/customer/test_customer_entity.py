import pytest

from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank


class TestCustomerEntity:
    def _create_customer(self) -> Customer:
        return Customer.create(
            name=CustomerName("田中太郎"),
            email=EmailAddress("tanaka@example.com"),
        )

    def _create_address(
        self, label: str = "自宅", is_default: bool = False, index: int = 1
    ) -> ShippingAddress:
        return ShippingAddress.create(
            label=label,
            address=Address(
                postal_code="100-0001",
                prefecture="東京都",
                city="千代田区",
                street=f"千代田{index}-1-1",
            ),
            is_default=is_default,
        )

    def test_create_customer(self):
        customer = self._create_customer()

        assert customer.id is not None
        assert customer.name.value == "田中太郎"
        assert customer.email.value == "tanaka@example.com"
        assert customer.member_rank == MemberRank.BRONZE
        assert len(customer.shipping_addresses) == 0

    def test_update_customer(self):
        customer = self._create_customer()

        customer.update(
            name=CustomerName("佐藤花子"),
            email=EmailAddress("sato@example.com"),
        )

        assert customer.name.value == "佐藤花子"
        assert customer.email.value == "sato@example.com"

    def test_add_shipping_address(self):
        customer = self._create_customer()
        addr = self._create_address(is_default=True)

        customer.add_shipping_address(addr)

        assert len(customer.shipping_addresses) == 1
        assert customer.shipping_addresses[0].is_default is True

    def test_add_max_addresses(self):
        customer = self._create_customer()

        for i in range(5):
            addr = self._create_address(label=f"住所{i + 1}", index=i + 1)
            customer.add_shipping_address(addr)

        assert len(customer.shipping_addresses) == 5

    def test_add_address_exceeds_limit(self):
        customer = self._create_customer()

        for i in range(5):
            addr = self._create_address(label=f"住所{i + 1}", index=i + 1)
            customer.add_shipping_address(addr)

        with pytest.raises(ValueError, match="Cannot add more than 5"):
            addr6 = self._create_address(label="住所6", index=6)
            customer.add_shipping_address(addr6)

    def test_add_default_address_unsets_previous(self):
        customer = self._create_customer()

        addr1 = self._create_address(label="自宅", is_default=True, index=1)
        customer.add_shipping_address(addr1)

        addr2 = self._create_address(label="会社", is_default=True, index=2)
        customer.add_shipping_address(addr2)

        assert customer.shipping_addresses[0].is_default is False
        assert customer.shipping_addresses[1].is_default is True

    def test_get_shipping_address(self):
        customer = self._create_customer()
        addr = self._create_address()
        customer.add_shipping_address(addr)

        found = customer.get_shipping_address(addr.id)
        assert found.id == addr.id

    def test_get_shipping_address_not_found(self):
        customer = self._create_customer()

        with pytest.raises(ValueError, match="not found"):
            customer.get_shipping_address("nonexistent-id")

    def test_get_default_address(self):
        customer = self._create_customer()
        addr = self._create_address(is_default=True)
        customer.add_shipping_address(addr)

        default = customer.get_default_address()
        assert default is not None
        assert default.id == addr.id

    def test_get_default_address_none(self):
        customer = self._create_customer()

        assert customer.get_default_address() is None
