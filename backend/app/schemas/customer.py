from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


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


class AddressResponse(BaseModel):
    """住所レスポンス"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    postal_code: str
    prefecture: str
    city: str
    street: str


class ShippingAddressResponse(BaseModel):
    """配送先住所レスポンス"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    label: str
    address: AddressResponse
    is_default: bool


class CustomerResponse(BaseModel):
    """顧客レスポンス"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
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
