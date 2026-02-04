from datetime import UTC, datetime

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

from app.core.database import Base


def utc_now():
    """UTC現在時刻を返す"""
    return datetime.now(UTC)


class ExampleModel(Base):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    price: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        Index("idx_products_sku", "sku"),
        Index("idx_products_category", "category"),
        Index("idx_products_deleted_at", "deleted_at"),
    )


class StockModel(Base):
    __tablename__ = "stocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(36), unique=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_quantity_non_negative"),
        Index("idx_stocks_product_id", "product_id"),
    )


class CustomerModel(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    member_rank: Mapped[str] = mapped_column(String(20), default="BRONZE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    shipping_addresses: Mapped[list["ShippingAddressModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "member_rank IN ('BRONZE', 'SILVER', 'GOLD')",
            name="check_member_rank",
        ),
        Index("idx_customers_email", "email"),
    )


class ShippingAddressModel(Base):
    __tablename__ = "shipping_addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id")
    )
    label: Mapped[str] = mapped_column(String(50))
    postal_code: Mapped[str] = mapped_column(String(10))
    prefecture: Mapped[str] = mapped_column(String(10))
    city: Mapped[str] = mapped_column(String(100))
    street: Mapped[str] = mapped_column(String(200))
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped["CustomerModel"] = relationship(
        back_populates="shipping_addresses"
    )

    __table_args__ = (
        Index("idx_shipping_addresses_customer_id", "customer_id"),
    )


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
        CheckConstraint("total_amount >= 0", name="check_total_non_negative"),
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
