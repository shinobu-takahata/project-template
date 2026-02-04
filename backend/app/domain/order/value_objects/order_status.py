from enum import Enum


class OrderStatus(str, Enum):
    """注文ステータス値オブジェクト"""

    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """指定されたステータスへの遷移が可能か判定する"""
        transitions: dict[OrderStatus, list[OrderStatus]] = {
            OrderStatus.CONFIRMED: [OrderStatus.PAID],
            OrderStatus.PAID: [OrderStatus.PREPARING],
            OrderStatus.PREPARING: [OrderStatus.SHIPPED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }
        return new_status in transitions.get(self, [])

    def is_cancellable(self) -> bool:
        """キャンセル可能か判定する"""
        return self in {
            OrderStatus.CONFIRMED,
            OrderStatus.PAID,
            OrderStatus.PREPARING,
        }
