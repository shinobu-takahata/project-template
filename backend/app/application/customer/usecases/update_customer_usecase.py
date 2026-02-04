from sqlalchemy.orm import Session

from app.application.customer.dtos.customer_dto import (
    CustomerDTO,
    ShippingAddressDTO,
    UpdateCustomerInputDTO,
)
from app.application.customer.exceptions import (
    CustomerNotFoundError,
    DuplicateEmailError,
)
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress


class UpdateCustomerUseCase:
    """顧客情報更新ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository, db: Session):
        self.customer_repository = customer_repository
        self.db = db

    def execute(
        self, customer_id: str, input_dto: UpdateCustomerInputDTO
    ) -> CustomerDTO:
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID '{customer_id}' not found"
            )

        # メールアドレス変更時は重複チェック
        new_email = EmailAddress(input_dto.email)
        if new_email.value != customer.email.value:
            existing = self.customer_repository.find_by_email(new_email)
            if existing is not None and existing.id.value != customer_id:
                raise DuplicateEmailError(
                    f"Email '{input_dto.email}' already exists"
                )

        customer.update(
            name=CustomerName(input_dto.name),
            email=new_email,
        )

        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        shipping_addresses = [
            ShippingAddressDTO(
                address_id=addr.id,
                label=addr.label,
                postal_code=addr.address.postal_code,
                prefecture=addr.address.prefecture,
                city=addr.address.city,
                street=addr.address.street,
                is_default=addr.is_default,
            )
            for addr in customer.shipping_addresses
        ]

        return CustomerDTO(
            customer_id=customer.id.value,
            name=customer.name.value,
            email=customer.email.value,
            member_rank=customer.member_rank.value,
            shipping_addresses=shipping_addresses,
            created_at=customer.created_at,
        )
