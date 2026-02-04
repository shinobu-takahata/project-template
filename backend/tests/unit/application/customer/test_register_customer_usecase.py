from unittest.mock import MagicMock

import pytest

from app.application.customer.dtos.customer_dto import RegisterCustomerInputDTO
from app.application.customer.exceptions import DuplicateEmailError
from app.application.customer.usecases.register_customer_usecase import (
    RegisterCustomerUseCase,
)
from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from tests.unit.mocks.mock_customer_repository import MockCustomerRepository


class TestRegisterCustomerUseCase:
    def _create_usecase(self):
        customer_repo = MockCustomerRepository()
        mock_db = MagicMock()
        usecase = RegisterCustomerUseCase(customer_repo, mock_db)
        return usecase, customer_repo, mock_db

    def _create_input(self, email: str = "tanaka@example.com"):
        return RegisterCustomerInputDTO(
            name="田中太郎",
            email=email,
            shipping_address={
                "label": "自宅",
                "postal_code": "100-0001",
                "prefecture": "東京都",
                "city": "千代田区",
                "street": "千代田1-1-1",
            },
        )

    def test_register_customer_success(self):
        usecase, customer_repo, mock_db = self._create_usecase()

        result = usecase.execute(self._create_input())

        assert result.name == "田中太郎"
        assert result.email == "tanaka@example.com"
        assert result.member_rank == "BRONZE"
        assert len(result.shipping_addresses) == 1
        assert result.shipping_addresses[0].is_default is True
        assert len(customer_repo.customers) == 1
        mock_db.commit.assert_called_once()

    def test_register_customer_duplicate_email_raises_error(self):
        usecase, customer_repo, _ = self._create_usecase()

        existing = Customer.create(
            name=CustomerName("既存顧客"),
            email=EmailAddress("tanaka@example.com"),
        )
        customer_repo.save(existing)

        with pytest.raises(DuplicateEmailError, match="already exists"):
            usecase.execute(self._create_input())

    def test_register_customer_invalid_email_raises_error(self):
        usecase, _, _ = self._create_usecase()

        with pytest.raises(ValueError, match="Invalid email format"):
            usecase.execute(self._create_input(email="invalid"))

    def test_register_customer_invalid_postal_code_raises_error(self):
        usecase, _, _ = self._create_usecase()

        input_dto = RegisterCustomerInputDTO(
            name="田中太郎",
            email="tanaka@example.com",
            shipping_address={
                "label": "自宅",
                "postal_code": "invalid",
                "prefecture": "東京都",
                "city": "千代田区",
                "street": "千代田1-1-1",
            },
        )

        with pytest.raises(ValueError, match="NNN-NNNN format"):
            usecase.execute(input_dto)
