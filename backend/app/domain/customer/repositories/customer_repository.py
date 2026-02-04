from abc import ABC, abstractmethod

from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.email_address import EmailAddress


class ICustomerRepository(ABC):
    """顧客リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, customer_id: CustomerId) -> Customer | None:
        """IDで顧客を取得する（配送先住所含む）"""
        pass

    @abstractmethod
    def find_by_email(self, email: EmailAddress) -> Customer | None:
        """メールアドレスで顧客を取得する"""
        pass

    @abstractmethod
    def save(self, customer: Customer) -> None:
        """顧客を保存する（作成・更新）"""
        pass
