from unittest.mock import MagicMock

import pytest

from app.application.customer.dtos.customer_dto import UpdateCustomerInputDTO
from app.application.customer.exceptions import (
    CustomerNotFoundError,
    DuplicateEmailError,
)
from app.application.customer.usecases.update_customer_usecase import (
    UpdateCustomerUseCase,
)
from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from tests.unit.mocks.mock_customer_repository import MockCustomerRepository


class TestUpdateCustomerUseCase:
    def _setup(self):
        customer_repo = MockCustomerRepository()
        mock_db = MagicMock()
        usecase = UpdateCustomerUseCase(customer_repo, mock_db)

        customer = Customer.create(
            name=CustomerName("田中太郎"),
            email=EmailAddress("tanaka@example.com"),
        )
        customer_repo.save(customer)

        return usecase, customer_repo, mock_db, customer

    def test_update_customer_success(self):
        usecase, _, mock_db, customer = self._setup()

        input_dto = UpdateCustomerInputDTO(
            name="佐藤花子",
            email="sato@example.com",
        )

        result = usecase.execute(customer.id.value, input_dto)

        assert result.name == "佐藤花子"
        assert result.email == "sato@example.com"
        mock_db.commit.assert_called_once()

    def test_update_nonexistent_customer_raises_error(self):
        usecase, _, _, _ = self._setup()

        input_dto = UpdateCustomerInputDTO(
            name="佐藤花子",
            email="sato@example.com",
        )

        with pytest.raises(CustomerNotFoundError, match="not found"):
            usecase.execute("nonexistent-id", input_dto)

    def test_update_customer_duplicate_email_raises_error(self):
        usecase, customer_repo, _, customer = self._setup()

        other = Customer.create(
            name=CustomerName("佐藤花子"),
            email=EmailAddress("sato@example.com"),
        )
        customer_repo.save(other)

        input_dto = UpdateCustomerInputDTO(
            name="田中太郎",
            email="sato@example.com",
        )

        with pytest.raises(DuplicateEmailError, match="already exists"):
            usecase.execute(customer.id.value, input_dto)

    def test_update_customer_same_email_no_error(self):
        usecase, _, mock_db, customer = self._setup()

        input_dto = UpdateCustomerInputDTO(
            name="田中太郎（更新）",
            email="tanaka@example.com",
        )

        result = usecase.execute(customer.id.value, input_dto)

        assert result.name == "田中太郎（更新）"
        assert result.email == "tanaka@example.com"
