from dataclasses import dataclass
from datetime import datetime

from app.domain.order.entities.order import Order


@dataclass
class OrderItemInputDTO:
    """注文明細入力DTO"""

    product_id: str
    quantity: int


@dataclass
class CreateOrderInputDTO:
    """注文作成入力DTO"""

    customer_id: str
    shipping_address_id: str
    items: list[OrderItemInputDTO]
    coupon_code: str | None = None


@dataclass
class OrderItemDTO:
    """注文明細DTO"""

    product_id: str
    product_name: str
    unit_price: int
    quantity: int
    subtotal: int


@dataclass
class ShippingAddressDTO:
    """配送先住所DTO"""

    postal_code: str
    prefecture: str
    city: str
    street: str


@dataclass
class OrderDTO:
    """注文DTO"""

    order_id: str
    status: str
    customer_id: str
    items: list[OrderItemDTO]
    subtotal: int
    discount_amount: int
    tax_amount: int
    shipping_fee: int
    total_amount: int
    shipping_address: ShippingAddressDTO
    ordered_at: datetime

    @staticmethod
    def from_entity(order: Order) -> "OrderDTO":
        """OrderエンティティからDTOに変換"""
        return OrderDTO(
            order_id=order.id.value,
            status=order.status.value,
            customer_id=order.customer_id.value,
            items=[
                OrderItemDTO(
                    product_id=item.product_id.value,
                    product_name=item.product_name,
                    unit_price=item.unit_price.value,
                    quantity=item.quantity,
                    subtotal=item.subtotal.value,
                )
                for item in order.items
            ],
            subtotal=order.subtotal.value,
            discount_amount=order.discount_amount.value,
            tax_amount=order.tax_amount.value,
            shipping_fee=order.shipping_fee.value,
            total_amount=order.total_amount.value,
            shipping_address=ShippingAddressDTO(
                postal_code=order.shipping_address.postal_code,
                prefecture=order.shipping_address.prefecture,
                city=order.shipping_address.city,
                street=order.shipping_address.street,
            ),
            ordered_at=order.ordered_at,
        )


@dataclass
class OrderStatusUpdateDTO:
    """注文ステータス更新DTO"""

    order_id: str
    previous_status: str
    current_status: str
    updated_at: datetime


@dataclass
class OrderCancelDTO:
    """注文キャンセルDTO"""

    order_id: str
    status: str
    cancel_reason: str | None
    cancelled_at: datetime
