from enum import Enum


class MemberRank(str, Enum):
    """会員ランク値オブジェクト"""

    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"

    @staticmethod
    def default() -> "MemberRank":
        """デフォルトランクを返す"""
        return MemberRank.BRONZE
