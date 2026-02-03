from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductDTO:
    """商品DTO（UseCase層の出力）"""

    id: str
    name: str
    sku: str
    price: int
    category: str
    description: str | None
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


@dataclass
class RegisterProductInputDTO:
    """商品登録入力DTO"""

    name: str
    sku: str
    price: int
    category: str
    description: str | None
    initial_stock: int


@dataclass
class UpdateProductInputDTO:
    """商品更新入力DTO"""

    name: str
    price: int
    category: str
    description: str | None


@dataclass
class PaginationDTO:
    """ページネーションDTO"""

    total: int
    page: int
    per_page: int
