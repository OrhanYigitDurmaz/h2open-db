"""
Subscription model for recurring delivery subscriptions.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .customer import Customer, CustomerAddress
    from .product import Product


class Subscription(Base):
    """
    Represents a recurring delivery subscription for a customer.
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )
    address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customer_addresses.id"), nullable=True
    )

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    frequency_days: Mapped[int] = mapped_column(Integer, default=7)  # 7 = Weekly
    next_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="subscriptions"
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="subscriptions"
    )
    address: Mapped[Optional["CustomerAddress"]] = relationship(
        "CustomerAddress", back_populates="subscriptions"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_subscription_quantity_positive"),
        CheckConstraint("frequency_days > 0", name="chk_frequency_positive"),
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, customer_id={self.customer_id}, product_id={self.product_id}, active={self.is_active})>"
