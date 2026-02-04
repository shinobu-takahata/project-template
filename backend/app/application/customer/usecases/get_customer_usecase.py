from app.application.customer.dtos.customer_dto import CustomerDTO, ShippingAddressDTO
from app.application.customer.exceptions import CustomerNotFoundError
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId


class GetCustomerUseCase:
    """顧客情報取得ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository):
        self.customer_repository = customer_repository

    def execute(self, customer_id: str) -> CustomerDTO:
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID '{customer_id}' not found"
            )

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
