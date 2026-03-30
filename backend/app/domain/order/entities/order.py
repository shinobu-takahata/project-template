from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.entities.order_item import OrderItem
from app.domain.order.exceptions import (
    InvalidStatusTransitionError,
    OrderCannotBeCancelledError,
)
from app.domain.order.value_objects.money import Money
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus
from app.domain.order.value_objects.shipping_address import ShippingAddress


@dataclass
class Order:
    """注文エンティティ（集約ルート）"""

    id: OrderId
    customer_id: CustomerId
    status: OrderStatus
    items: list[OrderItem]
    subtotal: Money
    discount_amount: Money
    tax_amount: Money
    shipping_fee: Money
    total_amount: Money
    shipping_address: ShippingAddress
    cancel_reason: str | None = None
    ordered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        customer_id: CustomerId,
        items: list[OrderItem],
        shipping_address: ShippingAddress,
        subtotal: Money,
        discount_amount: Money,
        tax_amount: Money,
        shipping_fee: Money,
        total_amount: Money,
    ) -> "Order":
        """注文を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Order(
            id=OrderId.generate(),
            customer_id=customer_id,
            status=OrderStatus.CONFIRMED,
            items=items,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            shipping_address=shipping_address,
            cancel_reason=None,
            ordered_at=now,
            updated_at=now,
        )

    def transition_to(self, new_status: OrderStatus) -> None:
        """ステータスを遷移させる"""
        if not self.status.can_transition_to(new_status):
            raise InvalidStatusTransitionError(
                f"Invalid status transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def cancel(self, reason: str) -> None:
        """注文をキャンセルする"""
        if not self.status.is_cancellable():
            raise OrderCannotBeCancelledError(
                f"Order in {self.status.value} status cannot be cancelled"
            )
        self.status = OrderStatus.CANCELLED
        self.cancel_reason = reason
        self.updated_at = datetime.now(UTC)

    @property
    def is_cancelled(self) -> bool:
        """キャンセル済みかどうか"""
        return self.status == OrderStatus.CANCELLED
