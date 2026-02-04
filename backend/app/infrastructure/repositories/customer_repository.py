from sqlalchemy.orm import Session

from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank
from app.infrastructure.database.models import CustomerModel, ShippingAddressModel


class CustomerRepository(ICustomerRepository):
    """顧客リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, customer_id: CustomerId) -> Customer | None:
        model = (
            self.db.query(CustomerModel)
            .filter(CustomerModel.id == customer_id.value)
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_email(self, email: EmailAddress) -> Customer | None:
        model = (
            self.db.query(CustomerModel)
            .filter(CustomerModel.email == email.value)
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def save(self, customer: Customer) -> None:
        model = (
            self.db.query(CustomerModel)
            .filter(CustomerModel.id == customer.id.value)
            .first()
        )

        if model is None:
            model = CustomerModel(
                id=customer.id.value,
                name=customer.name.value,
                email=customer.email.value,
                member_rank=customer.member_rank.value,
                created_at=customer.created_at,
                updated_at=customer.updated_at,
            )
            self.db.add(model)
        else:
            model.name = customer.name.value
            model.email = customer.email.value
            model.member_rank = customer.member_rank.value
            model.updated_at = customer.updated_at

        # 既存の配送先住所を削除して再作成
        self.db.query(ShippingAddressModel).filter(
            ShippingAddressModel.customer_id == customer.id.value
        ).delete()

        for addr in customer.shipping_addresses:
            addr_model = ShippingAddressModel(
                id=addr.id,
                customer_id=customer.id.value,
                label=addr.label,
                postal_code=addr.address.postal_code,
                prefecture=addr.address.prefecture,
                city=addr.address.city,
                street=addr.address.street,
                is_default=addr.is_default,
                created_at=addr.created_at,
                updated_at=addr.updated_at,
            )
            self.db.add(addr_model)

        self.db.flush()

    def _to_entity(self, model: CustomerModel) -> Customer:
        shipping_addresses = [
            ShippingAddress(
                id=addr.id,
                label=addr.label,
                address=Address(
                    postal_code=addr.postal_code,
                    prefecture=addr.prefecture,
                    city=addr.city,
                    street=addr.street,
                ),
                is_default=addr.is_default,
                created_at=addr.created_at,
                updated_at=addr.updated_at,
            )
            for addr in model.shipping_addresses
        ]

        return Customer(
            id=CustomerId(model.id),
            name=CustomerName(model.name),
            email=EmailAddress(model.email),
            member_rank=MemberRank(model.member_rank),
            shipping_addresses=shipping_addresses,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
