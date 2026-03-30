from app.domain.customer.entities.customer import Customer
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.email_address import EmailAddress


class MockCustomerRepository(ICustomerRepository):
    """テスト用モック顧客リポジトリ"""

    def __init__(self):
        self.customers: dict[str, Customer] = {}

    def find_by_id(self, customer_id: CustomerId) -> Customer | None:
        return self.customers.get(customer_id.value)

    def find_by_email(self, email: EmailAddress) -> Customer | None:
        for customer in self.customers.values():
            if customer.email.value == email.value:
                return customer
        return None

    def save(self, customer: Customer) -> None:
        self.customers[customer.id.value] = customer
