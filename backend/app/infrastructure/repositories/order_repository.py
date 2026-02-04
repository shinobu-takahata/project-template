from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, load_only, selectinload

from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.entities.order import Order
from app.domain.order.entities.order_item import OrderItem
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.money import Money
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.product.value_objects.product_id import ProductId
from app.infrastructure.database.models import OrderItemModel, OrderModel


class OrderRepository(IOrderRepository):
    """注文リポジトリ実装"""

    _ORDER_COLUMNS = (
        OrderModel.id,
        OrderModel.customer_id,
        OrderModel.status,
        OrderModel.subtotal,
        OrderModel.discount_amount,
        OrderModel.tax_amount,
        OrderModel.shipping_fee,
        OrderModel.total_amount,
        OrderModel.shipping_postal_code,
        OrderModel.shipping_prefecture,
        OrderModel.shipping_city,
        OrderModel.shipping_street,
        OrderModel.cancel_reason,
        OrderModel.ordered_at,
        OrderModel.updated_at,
    )

    _ORDER_ITEM_COLUMNS = (
        OrderItemModel.order_id,
        OrderItemModel.product_id,
        OrderItemModel.product_name,
        OrderItemModel.unit_price,
        OrderItemModel.quantity,
    )

    def __init__(self, db: Session):
        self.db = db

    def save(self, order: Order) -> None:
        exists = self.db.scalar(select(OrderModel.id).where(OrderModel.id == order.id.value))

        if exists is None:
            model = OrderModel(
                id=order.id.value,
                customer_id=order.customer_id.value,
                status=order.status.value,
                subtotal=order.subtotal.value,
                discount_amount=order.discount_amount.value,
                tax_amount=order.tax_amount.value,
                shipping_fee=order.shipping_fee.value,
                total_amount=order.total_amount.value,
                shipping_postal_code=order.shipping_address.postal_code,
                shipping_prefecture=order.shipping_address.prefecture,
                shipping_city=order.shipping_address.city,
                shipping_street=order.shipping_address.street,
                cancel_reason=order.cancel_reason,
                ordered_at=order.ordered_at,
                updated_at=order.updated_at,
            )
            self.db.add(model)
            self.db.flush()

            for item in order.items:
                item_model = OrderItemModel(
                    order_id=order.id.value,
                    product_id=item.product_id.value,
                    product_name=item.product_name,
                    unit_price=item.unit_price.value,
                    quantity=item.quantity,
                )
                self.db.add(item_model)
        else:
            stmt = (
                update(OrderModel)
                .where(OrderModel.id == order.id.value)
                .values(
                    status=order.status.value,
                    cancel_reason=order.cancel_reason,
                    updated_at=order.updated_at,
                )
            )
            self.db.execute(stmt)

        self.db.flush()

    def find_by_id(self, order_id: OrderId) -> Order | None:
        stmt = (
            select(OrderModel)
            .options(
                load_only(*self._ORDER_COLUMNS),
                selectinload(OrderModel.items).load_only(*self._ORDER_ITEM_COLUMNS),
            )
            .where(OrderModel.id == order_id.value)
        )
        model = self.db.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Order], int]:
        stmt = (
            select(OrderModel)
            .options(
                load_only(*self._ORDER_COLUMNS),
                selectinload(OrderModel.items).load_only(*self._ORDER_ITEM_COLUMNS),
            )
            .where(OrderModel.customer_id == customer_id.value)
        )

        if status:
            stmt = stmt.where(OrderModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        offset = (page - 1) * per_page
        stmt = stmt.order_by(OrderModel.ordered_at.desc()).offset(offset).limit(per_page)
        models = self.db.scalars(stmt).all()

        orders = [self._to_entity(m) for m in models]
        return orders, total

    def exists_active_order_with_product(self, product_id: str) -> bool:
        stmt = (
            select(OrderItemModel.id)
            .join(OrderModel)
            .where(
                OrderItemModel.product_id == product_id,
                OrderModel.status.in_(["CONFIRMED", "PAID", "PREPARING", "SHIPPED"]),
            )
        )
        result = self.db.scalar(stmt)
        return result is not None

    def _to_entity(self, model: OrderModel) -> Order:
        items = [
            OrderItem(
                product_id=ProductId(item.product_id),
                product_name=item.product_name,
                unit_price=Money(item.unit_price),
                quantity=item.quantity,
            )
            for item in model.items
        ]

        return Order(
            id=OrderId(model.id),
            customer_id=CustomerId(model.customer_id),
            status=OrderStatus(model.status),
            items=items,
            subtotal=Money(model.subtotal),
            discount_amount=Money(model.discount_amount),
            tax_amount=Money(model.tax_amount),
            shipping_fee=Money(model.shipping_fee),
            total_amount=Money(model.total_amount),
            shipping_address=ShippingAddress(
                postal_code=model.shipping_postal_code,
                prefecture=model.shipping_prefecture,
                city=model.shipping_city,
                street=model.shipping_street,
            ),
            cancel_reason=model.cancel_reason,
            ordered_at=model.ordered_at,
            updated_at=model.updated_at,
        )
