from app.application.customer.dtos.customer_dto import CustomerDTO, ShippingAddressDTO
from app.domain.customer.repositories.customer_repository import ICustomerRepository


class ListCustomersUseCase:
    """顧客一覧取得ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository):
        self.customer_repository = customer_repository

    def execute(self) -> list[CustomerDTO]:
        customers = self.customer_repository.find_all()

        return [
            CustomerDTO(
                customer_id=c.id.value,
                name=c.name.value,
                email=c.email.value,
                member_rank=c.member_rank.value,
                shipping_addresses=[
                    ShippingAddressDTO(
                        address_id=addr.id,
                        label=addr.label,
                        postal_code=addr.address.postal_code,
                        prefecture=addr.address.prefecture,
                        city=addr.address.city,
                        street=addr.address.street,
                        is_default=addr.is_default,
                    )
                    for addr in c.shipping_addresses
                ],
                created_at=c.created_at,
            )
            for c in customers
        ]
