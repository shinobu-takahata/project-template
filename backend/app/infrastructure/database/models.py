from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    """UTC現在時刻を返す"""
    return datetime.now(UTC)


class ExampleModel(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        Index("idx_products_sku", "sku"),
        Index("idx_products_category", "category"),
        Index("idx_products_deleted_at", "deleted_at"),
    )


class StockModel(Base):
    __tablename__ = "stocks"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_quantity_non_negative"),
        Index("idx_stocks_product_id", "product_id"),
    )


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    member_rank = Column(String(20), nullable=False, default="BRONZE")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    shipping_addresses = relationship(
        "ShippingAddressModel",
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

    id = Column(String(36), primary_key=True)
    customer_id = Column(
        String(36), ForeignKey("customers.id"), nullable=False
    )
    label = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    prefecture = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    street = Column(String(200), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    customer = relationship("CustomerModel", back_populates="shipping_addresses")

    __table_args__ = (
        Index("idx_shipping_addresses_customer_id", "customer_id"),
    )
