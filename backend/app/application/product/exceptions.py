class ProductApplicationError(Exception):
    """商品Application層例外の基底クラス"""

    pass


class ProductNotFoundError(ProductApplicationError):
    """商品が見つからないエラー"""

    pass


class DuplicateSKUError(ProductApplicationError):
    """SKU重複エラー"""

    pass


class ProductInUseError(ProductApplicationError):
    """使用中商品の削除エラー"""

    pass
