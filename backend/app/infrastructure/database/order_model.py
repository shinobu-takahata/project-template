from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, utc_now


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    subtotal: Mapped[int] = mapped_column(Integer)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    tax_amount: Mapped[int] = mapped_column(Integer)
    shipping_fee: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer)
    shipping_postal_code: Mapped[str] = mapped_column(String(10))
    shipping_prefecture: Mapped[str] = mapped_column(String(10))
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_street: Mapped[str] = mapped_column(String(200))
    cancel_reason: Mapped[str | None] = mapped_column(Text, default=None)
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('CONFIRMED', 'PAID', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED')",
            name="check_order_status",
        ),
        CheckConstraint("subtotal >= 0", name="check_subtotal_non_negative"),
        CheckConstraint(
            "discount_amount >= 0", name="check_discount_non_negative"
        ),
        CheckConstraint("tax_amount >= 0", name="check_tax_non_negative"),
        CheckConstraint(
            "shipping_fee >= 0", name="check_shipping_fee_non_negative"
        ),
        CheckConstraint(
            "total_amount >= 0", name="check_total_non_negative"
        ),
        Index("idx_orders_customer_id", "customer_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_ordered_at", "ordered_at"),
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id")
    )
    product_id: Mapped[str] = mapped_column(String(36))
    product_name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped["OrderModel"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "unit_price >= 0", name="check_unit_price_non_negative"
        ),
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )
