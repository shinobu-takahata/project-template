class CustomerDomainError(Exception):
    """顧客ドメイン例外の基底クラス"""

    pass


class MaxAddressLimitExceededError(CustomerDomainError):
    """配送先住所上限超過エラー"""

    pass


class ShippingAddressNotFoundError(CustomerDomainError):
    """配送先住所が見つからないエラー"""

    pass


class InvalidEmailFormatError(CustomerDomainError):
    """不正なメールアドレスフォーマットエラー"""

    pass


class InvalidPostalCodeFormatError(CustomerDomainError):
    """不正な郵便番号フォーマットエラー"""

    pass
