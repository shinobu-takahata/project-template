from dataclasses import dataclass, field
from datetime import UTC, datetime
import uuid

from app.domain.customer.value_objects.address import Address


@dataclass
class ShippingAddress:
    """配送先住所エンティティ（Customer集約内）"""

    id: str
    label: str
    address: Address
    is_default: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        label: str,
        address: Address,
        is_default: bool = False,
    ) -> "ShippingAddress":
        """配送先住所を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return ShippingAddress(
            id=str(uuid.uuid4()),
            label=label,
            address=address,
            is_default=is_default,
            created_at=now,
            updated_at=now,
        )
