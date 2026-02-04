class CustomerApplicationError(Exception):
    """顧客Application層例外の基底クラス"""

    pass


class CustomerNotFoundError(CustomerApplicationError):
    """顧客が見つからないエラー"""

    pass


class DuplicateEmailError(CustomerApplicationError):
    """メールアドレス重複エラー"""

    pass
