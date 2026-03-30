from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, utc_now


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
