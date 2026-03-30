from sqlalchemy.orm import Session

from app.application.customer.dtos.customer_dto import (
    AddShippingAddressInputDTO,
    ShippingAddressDTO,
)
from app.application.customer.exceptions import CustomerNotFoundError
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_id import CustomerId


class AddShippingAddressUseCase:
    """配送先住所追加ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository, db: Session):
        self.customer_repository = customer_repository
        self.db = db

    def execute(
        self, customer_id: str, input_dto: AddShippingAddressInputDTO
    ) -> ShippingAddressDTO:
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID '{customer_id}' not found"
            )

        new_address = ShippingAddress.create(
            label=input_dto.label,
            address=Address(
                postal_code=input_dto.postal_code,
                prefecture=input_dto.prefecture,
                city=input_dto.city,
                street=input_dto.street,
            ),
            is_default=input_dto.is_default,
        )

        # ドメインルールで最大5件チェック、デフォルト管理
        customer.add_shipping_address(new_address)

        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        return ShippingAddressDTO(
            address_id=new_address.id,
            label=new_address.label,
            postal_code=new_address.address.postal_code,
            prefecture=new_address.address.prefecture,
            city=new_address.address.city,
            street=new_address.address.street,
            is_default=new_address.is_default,
        )
