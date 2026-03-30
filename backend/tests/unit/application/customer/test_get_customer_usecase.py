import pytest

from app.application.customer.exceptions import CustomerNotFoundError
from app.application.customer.usecases.get_customer_usecase import (
    GetCustomerUseCase,
)
from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from tests.unit.mocks.mock_customer_repository import MockCustomerRepository


class TestGetCustomerUseCase:
    def _setup(self):
        customer_repo = MockCustomerRepository()
        usecase = GetCustomerUseCase(customer_repo)

        customer = Customer.create(
            name=CustomerName("田中太郎"),
            email=EmailAddress("tanaka@example.com"),
        )
        addr = ShippingAddress.create(
            label="自宅",
            address=Address("100-0001", "東京都", "千代田区", "千代田1-1-1"),
            is_default=True,
        )
        customer.add_shipping_address(addr)
        customer_repo.save(customer)

        return usecase, customer

    def test_get_customer_success(self):
        usecase, customer = self._setup()

        result = usecase.execute(customer.id.value)

        assert result.customer_id == customer.id.value
        assert result.name == "田中太郎"
        assert result.email == "tanaka@example.com"
        assert result.member_rank == "BRONZE"
        assert len(result.shipping_addresses) == 1
        assert result.shipping_addresses[0].is_default is True

    def test_get_nonexistent_customer_raises_error(self):
        usecase, _ = self._setup()

        with pytest.raises(CustomerNotFoundError, match="not found"):
            usecase.execute("nonexistent-id")
