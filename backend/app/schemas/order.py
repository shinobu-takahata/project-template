from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    """注文明細リクエスト"""

    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class OrderCreateRequest(BaseModel):
    """注文作成リクエスト"""

    customer_id: str = Field(..., min_length=1)
    shipping_address_id: str = Field(..., min_length=1)
    items: list[OrderItemRequest] = Field(..., min_length=1)
    coupon_code: str | None = None


class OrderItemResponse(BaseModel):
    """注文明細レスポンス"""

    product_id: str
    product_name: str
    unit_price: int
    quantity: int
    subtotal: int


class ShippingAddressResponse(BaseModel):
    """配送先住所レスポンス"""

    postal_code: str
    prefecture: str
    city: str
    street: str


class OrderResponse(BaseModel):
    """注文レスポンス"""

    order_id: str
    status: str
    customer_id: str
    items: list[OrderItemResponse]
    subtotal: int
    discount_amount: int
    tax_amount: int
    shipping_fee: int
    total_amount: int
    shipping_address: ShippingAddressResponse
    ordered_at: datetime


class OrderStatusUpdateRequest(BaseModel):
    """注文ステータス更新リクエスト"""

    status: str = Field(
        ...,
        pattern="^(CONFIRMED|PAID|PREPARING|SHIPPED|DELIVERED)$",
    )


class OrderStatusUpdateResponse(BaseModel):
    """注文ステータス更新レスポンス"""

    order_id: str
    previous_status: str
    current_status: str
    updated_at: datetime


class OrderCancelRequest(BaseModel):
    """注文キャンセルリクエスト"""

    reason: str = Field(..., min_length=1, max_length=500)


class OrderCancelResponse(BaseModel):
    """注文キャンセルレスポンス"""

    order_id: str
    status: str
    cancel_reason: str | None
    cancelled_at: datetime


class OrderDataResponse(BaseModel):
    """注文データラッパー"""

    data: OrderResponse


class OrderStatusDataResponse(BaseModel):
    """注文ステータスデータラッパー"""

    data: OrderStatusUpdateResponse


class OrderCancelDataResponse(BaseModel):
    """注文キャンセルデータラッパー"""

    data: OrderCancelResponse
