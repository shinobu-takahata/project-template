from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.entities.order import Order
from app.domain.order.entities.order_item import OrderItem
from app.domain.order.services.discount_policy import DiscountPolicy
from app.domain.order.value_objects.money import Money
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.product.entities.product import Product


class OrderDomainService:
    """注文ドメインサービス"""

    SHIPPING_FEE = Money(500)
    TAX_RATE = 0.1

    @staticmethod
    def create_order(
        customer: Customer,
        products: list[Product],
        quantities: dict[str, int],
        shipping_address: ShippingAddress,
        coupon_code: str | None = None,
    ) -> Order:
        """注文を生成する"""
        items: list[OrderItem] = []
        subtotal = Money(0)

        for product in products:
            quantity = quantities.get(product.id.value, 0)
            if quantity <= 0:
                continue

            item = OrderItem(
                product_id=product.id,
                product_name=product.name.value,
                unit_price=Money(product.price.value),
                quantity=quantity,
            )
            items.append(item)
            subtotal = subtotal.add(item.subtotal)

        # 1. 会員ランク割引（小計に適用）
        member_discount = DiscountPolicy.apply_member_rank_discount(
            subtotal, customer.member_rank
        )

        # 2. 数量割引（商品単位）
        quantity_discount = Money(0)
        for item in items:
            discount = DiscountPolicy.apply_quantity_discount(
                item.unit_price, item.quantity
            )
            quantity_discount = quantity_discount.add(discount)

        # 3. クーポン割引（最終合計に適用）
        subtotal_after_discount = subtotal.subtract(member_discount).subtract(
            quantity_discount
        )
        coupon_discount = DiscountPolicy.apply_coupon_discount(
            subtotal_after_discount, coupon_code
        )

        total_discount = (
            member_discount.add(quantity_discount).add(coupon_discount)
        )

        # 税込合計金額を計算
        subtotal_after_all_discount = subtotal.subtract(total_discount)
        tax_amount = subtotal_after_all_discount.calculate_tax(
            OrderDomainService.TAX_RATE
        )
        total_amount = subtotal_after_all_discount.add(tax_amount).add(
            OrderDomainService.SHIPPING_FEE
        )

        return Order.create(
            customer_id=CustomerId(customer.id.value),
            items=items,
            shipping_address=shipping_address,
            subtotal=subtotal,
            discount_amount=total_discount,
            tax_amount=tax_amount,
            shipping_fee=OrderDomainService.SHIPPING_FEE,
            total_amount=total_amount,
        )
