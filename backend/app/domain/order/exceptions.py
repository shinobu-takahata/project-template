class OrderDomainError(Exception):
    """注文ドメインエラー基底クラス"""

    pass


class InsufficientStockError(OrderDomainError):
    """在庫不足エラー"""

    pass


class InvalidStatusTransitionError(OrderDomainError):
    """不正なステータス遷移エラー"""

    pass


class OrderCannotBeCancelledError(OrderDomainError):
    """注文キャンセル不可エラー"""

    pass
