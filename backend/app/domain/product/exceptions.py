class ProductDomainError(Exception):
    """商品ドメイン例外の基底クラス"""

    pass


class ProductAlreadyDeletedError(ProductDomainError):
    """論理削除済み商品の操作エラー"""

    pass


class InvalidPriceError(ProductDomainError):
    """不正な価格エラー"""

    pass


class InvalidSKUFormatError(ProductDomainError):
    """不正なSKUフォーマットエラー"""

    pass
