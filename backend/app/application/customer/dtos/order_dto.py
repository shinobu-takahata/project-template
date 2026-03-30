from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderSummaryDTO:
    """注文サマリーDTO（顧客注文履歴用）"""

    order_id: str
    status: str
    total_amount: int
    item_count: int
    ordered_at: datetime


@dataclass
class PaginationDTO:
    """ページネーションDTO"""

    total: int
    page: int
    per_page: int
