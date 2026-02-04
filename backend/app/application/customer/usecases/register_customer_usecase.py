from sqlalchemy.orm import Session

from app.application.customer.dtos.customer_dto import (
    CustomerDTO,
    RegisterCustomerInputDTO,
    ShippingAddressDTO,
)
from app.application.customer.exceptions import DuplicateEmailError
from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress


class RegisterCustomerUseCase:
    """顧客登録ユースケース"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        db: Session,
    ):
        self.customer_repository = customer_repository
        self.db = db

    def execute(self, input_dto: RegisterCustomerInputDTO) -> CustomerDTO:
        # メールアドレス重複チェック
        email = EmailAddress(input_dto.email)
        existing = self.customer_repository.find_by_email(email)
        if existing is not None:
            raise DuplicateEmailError(
                f"Email '{input_dto.email}' already exists"
            )

        # ドメインオブジェクト生成
        customer = Customer.create(
            name=CustomerName(input_dto.name),
            email=email,
        )

        # 初期配送先住所を追加
        initial_address = ShippingAddress.create(
            label=input_dto.shipping_address["label"],
            address=Address(
                postal_code=input_dto.shipping_address["postal_code"],
                prefecture=input_dto.shipping_address["prefecture"],
                city=input_dto.shipping_address["city"],
                street=input_dto.shipping_address["street"],
            ),
            is_default=True,
        )
        customer.add_shipping_address(initial_address)

        # 永続化
        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換
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
