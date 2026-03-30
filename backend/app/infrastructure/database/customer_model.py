from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, utc_now


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
