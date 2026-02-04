from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank


@dataclass
class Customer:
    """顧客エンティティ（集約ルート）"""

    id: CustomerId
    name: CustomerName
    email: EmailAddress
    member_rank: MemberRank
    shipping_addresses: list[ShippingAddress] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    MAX_ADDRESSES = 5

    @staticmethod
    def create(
        name: CustomerName,
        email: EmailAddress,
    ) -> "Customer":
        """顧客を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Customer(
            id=CustomerId.generate(),
            name=name,
            email=email,
            member_rank=MemberRank.default(),
            shipping_addresses=[],
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        name: CustomerName,
        email: EmailAddress,
    ) -> None:
        """顧客情報を更新する"""
        self.name = name
        self.email = email
        self.updated_at = datetime.now(UTC)

    def add_shipping_address(self, address: ShippingAddress) -> None:
        """配送先住所を追加する"""
        if len(self.shipping_addresses) >= self.MAX_ADDRESSES:
            raise ValueError(
                f"Cannot add more than {self.MAX_ADDRESSES} shipping addresses"
            )

        if address.is_default:
            for existing in self.shipping_addresses:
                existing.is_default = False

        self.shipping_addresses.append(address)
        self.updated_at = datetime.now(UTC)

    def get_shipping_address(self, address_id: str) -> ShippingAddress:
        """指定IDの配送先住所を取得する"""
        for address in self.shipping_addresses:
            if address.id == address_id:
                return address

        raise ValueError(f"Shipping address with ID '{address_id}' not found")

    def get_default_address(self) -> ShippingAddress | None:
        """デフォルト配送先住所を取得する"""
        for address in self.shipping_addresses:
            if address.is_default:
                return address
        return None
