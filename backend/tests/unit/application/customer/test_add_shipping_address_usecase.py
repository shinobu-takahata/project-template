from unittest.mock import MagicMock

import pytest

from app.application.customer.dtos.customer_dto import AddShippingAddressInputDTO
from app.application.customer.exceptions import CustomerNotFoundError
from app.application.customer.usecases.add_shipping_address_usecase import (
    AddShippingAddressUseCase,
)
from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from tests.unit.mocks.mock_customer_repository import MockCustomerRepository


class TestAddShippingAddressUseCase:
    def _setup(self):
        customer_repo = MockCustomerRepository()
        mock_db = MagicMock()
        usecase = AddShippingAddressUseCase(customer_repo, mock_db)

        customer = Customer.create(
            name=CustomerName("田中太郎"),
            email=EmailAddress("tanaka@example.com"),
        )
        customer_repo.save(customer)

        return usecase, customer_repo, mock_db, customer

    def _create_input(self, is_default: bool = False):
        return AddShippingAddressInputDTO(
            label="会社",
            postal_code="150-0001",
            prefecture="東京都",
            city="渋谷区",
            street="渋谷2-2-2",
            is_default=is_default,
        )

    def test_add_shipping_address_success(self):
        usecase, _, mock_db, customer = self._setup()

        result = usecase.execute(customer.id.value, self._create_input())

        assert result.label == "会社"
        assert result.postal_code == "150-0001"
        assert result.is_default is False
        mock_db.commit.assert_called_once()

    def test_add_shipping_address_nonexistent_customer_raises_error(self):
        usecase, _, _, _ = self._setup()

        with pytest.raises(CustomerNotFoundError, match="not found"):
            usecase.execute("nonexistent-id", self._create_input())

    def test_add_shipping_address_exceeds_limit_raises_error(self):
        usecase, customer_repo, _, customer = self._setup()

        for i in range(5):
            addr = ShippingAddress.create(
                label=f"住所{i + 1}",
                address=Address("100-0001", "東京都", "千代田区", f"千代田{i + 1}"),
            )
            customer.add_shipping_address(addr)
        customer_repo.save(customer)

        with pytest.raises(ValueError, match="Cannot add more than 5"):
            usecase.execute(customer.id.value, self._create_input())

    def test_add_default_address_unsets_previous(self):
        usecase, customer_repo, _, customer = self._setup()

        addr = ShippingAddress.create(
            label="自宅",
            address=Address("100-0001", "東京都", "千代田区", "千代田1-1-1"),
            is_default=True,
        )
        customer.add_shipping_address(addr)
        customer_repo.save(customer)

        result = usecase.execute(
            customer.id.value, self._create_input(is_default=True)
        )

        assert result.is_default is True
        updated = customer_repo.customers[customer.id.value]
        non_default = [
            a for a in updated.shipping_addresses if not a.is_default
        ]
        assert len(non_default) == 1
