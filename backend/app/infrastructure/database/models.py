from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, String, Text

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
