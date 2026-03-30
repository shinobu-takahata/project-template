from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    """商品登録リクエスト"""

    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Za-z0-9\-]+$")
    price: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    initial_stock: int = Field(..., ge=0)


class ProductUpdateRequest(BaseModel):
    """商品更新リクエスト"""

    name: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class ProductResponse(BaseModel):
    """商品レスポンス"""

    id: str
    name: str
    sku: str
    price: int
    category: str
    description: str | None
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class PaginationResponse(BaseModel):
    """ページネーションレスポンス"""

    total: int
    page: int
    per_page: int


class ProductListResponse(BaseModel):
    """商品一覧レスポンス"""

    data: list[ProductResponse]
    pagination: PaginationResponse
