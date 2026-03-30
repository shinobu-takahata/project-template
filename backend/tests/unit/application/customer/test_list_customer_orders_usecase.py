import pytest

from app.application.customer.exceptions import CustomerNotFoundError
from app.application.customer.usecases.list_customer_orders_usecase import (
    ListCustomerOrdersUseCase,
)
from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from tests.unit.mocks.mock_customer_repository import MockCustomerRepository
from tests.unit.mocks.mock_order_repository import MockOrderRepository


class TestListCustomerOrdersUseCase:
    def _setup(self):
        customer_repo = MockCustomerRepository()
        order_repo = MockOrderRepository()
        usecase = ListCustomerOrdersUseCase(customer_repo, order_repo)

        customer = Customer.create(
            name=CustomerName("田中太郎"),
            email=EmailAddress("tanaka@example.com"),
        )
        customer_repo.save(customer)

        return usecase, customer

    def test_list_orders_returns_empty_stub(self):
        usecase, customer = self._setup()

        order_dtos, pagination = usecase.execute(customer.id.value)

        assert len(order_dtos) == 0
        assert pagination.total == 0
        assert pagination.page == 1
        assert pagination.per_page == 20

    def test_list_orders_nonexistent_customer_raises_error(self):
        usecase, _ = self._setup()

        with pytest.raises(CustomerNotFoundError, match="not found"):
            usecase.execute("nonexistent-id")
