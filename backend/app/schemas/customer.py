from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ShippingAddressRequest(BaseModel):
    """配送先住所リクエスト"""

    label: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., pattern=r"^\d{3}-\d{4}$")
    prefecture: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=200)


class CustomerRegisterRequest(BaseModel):
    """顧客登録リクエスト"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    shipping_address: ShippingAddressRequest


class CustomerUpdateRequest(BaseModel):
    """顧客更新リクエスト"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class ShippingAddressAddRequest(BaseModel):
    """配送先住所追加リクエスト"""

    label: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., pattern=r"^\d{3}-\d{4}$")
    prefecture: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=200)
    is_default: bool = False


class ShippingAddressResponse(BaseModel):
    """配送先住所レスポンス"""

    address_id: str
    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool


class CustomerResponse(BaseModel):
    """顧客レスポンス"""

    customer_id: str
    name: str
    email: str
    member_rank: str
    shipping_addresses: list[ShippingAddressResponse]
    created_at: datetime


class OrderSummaryResponse(BaseModel):
    """注文サマリーレスポンス"""

    order_id: str
    status: str
    total_amount: int
    item_count: int
    ordered_at: datetime


class PaginationResponse(BaseModel):
    """ページネーションレスポンス"""

    total: int
    page: int
    per_page: int


class CustomerOrderListResponse(BaseModel):
    """顧客注文履歴レスポンス"""

    data: list[OrderSummaryResponse]
    pagination: PaginationResponse
