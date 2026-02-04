class OrderApplicationError(Exception):
    """注文アプリケーションエラー基底クラス"""

    pass


class CustomerNotFoundError(OrderApplicationError):
    """顧客未検出エラー"""

    pass


class ProductNotFoundError(OrderApplicationError):
    """商品未検出エラー"""

    pass


class InsufficientStockError(OrderApplicationError):
    """在庫不足エラー"""

    pass


class InvalidCouponError(OrderApplicationError):
    """無効なクーポンエラー"""

    pass


class InvalidShippingAddressError(OrderApplicationError):
    """無効な配送先住所エラー"""

    pass


class OrderNotFoundError(OrderApplicationError):
    """注文未検出エラー"""

    pass


class InvalidStatusTransitionError(OrderApplicationError):
    """不正なステータス遷移エラー"""

    pass


class OrderCannotBeCancelledError(OrderApplicationError):
    """注文キャンセル不可エラー"""

    pass
