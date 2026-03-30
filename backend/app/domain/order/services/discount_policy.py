from app.domain.customer.value_objects.member_rank import MemberRank
from app.domain.order.value_objects.money import Money


class DiscountPolicy:
    """割引ポリシー（ドメインサービス）"""

    MEMBER_RANK_DISCOUNT: dict[MemberRank, float] = {
        MemberRank.BRONZE: 0.0,
        MemberRank.SILVER: 0.05,
        MemberRank.GOLD: 0.10,
    }

    QUANTITY_DISCOUNT_THRESHOLD = 5
    QUANTITY_DISCOUNT_RATE = 0.10

    @staticmethod
    def apply_member_rank_discount(
        subtotal: Money, member_rank: MemberRank
    ) -> Money:
        """会員ランク割引を適用"""
        discount_rate = DiscountPolicy.MEMBER_RANK_DISCOUNT.get(
            member_rank, 0.0
        )
        return subtotal.multiply(discount_rate)

    @staticmethod
    def apply_quantity_discount(unit_price: Money, quantity: int) -> Money:
        """数量割引を適用（商品単位）"""
        if quantity >= DiscountPolicy.QUANTITY_DISCOUNT_THRESHOLD:
            total = unit_price.multiply(quantity)
            return total.multiply(DiscountPolicy.QUANTITY_DISCOUNT_RATE)
        return Money(0)

    @staticmethod
    def apply_coupon_discount(
        total: Money, coupon_code: str | None
    ) -> Money:
        """クーポン割引を適用（簡易実装）"""
        if coupon_code == "SPRING2026":
            return total.multiply(0.10)
        return Money(0)
