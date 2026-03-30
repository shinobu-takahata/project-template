from dataclasses import dataclass
from datetime import datetime


@dataclass
class ShippingAddressDTO:
    """配送先住所DTO"""

    address_id: str
    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool


@dataclass
class CustomerDTO:
    """顧客DTO"""

    customer_id: str
    name: str
    email: str
    member_rank: str
    shipping_addresses: list[ShippingAddressDTO]
    created_at: datetime


@dataclass
class RegisterCustomerInputDTO:
    """顧客登録入力DTO"""

    name: str
    email: str
    shipping_address: dict


@dataclass
class UpdateCustomerInputDTO:
    """顧客更新入力DTO"""

    name: str
    email: str


@dataclass
class AddShippingAddressInputDTO:
    """配送先住所追加入力DTO"""

    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool
