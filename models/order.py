"""
Order and OrderItem models for the Water Delivery CRM.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import OrderStatus

if TYPE_CHECKING:
    from .customer import Customer, CustomerAddress
    from .product import Product
    from .staff import Staff


class Order(Base):
    """
    Represents a delivery order in the system.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    driver_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("staff.id"), nullable=True
    )
    address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customer_addresses.id"), nullable=True
    )

    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING)

    # Logistics
    requested_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_window: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g. "10:00 - 12:00"

    # Bottle movement (filled by driver app upon delivery)
    bottles_delivered: Mapped[int] = mapped_column(Integer, default=0)
    bottles_returned: Mapped[int] = mapped_column(Integer, default=0)

    # Financials
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Cash, POS, Online
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=datetime.now
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="orders"
    )
    driver: Mapped[Optional["Staff"]] = relationship("Staff", back_populates="orders")
    address: Mapped[Optional["CustomerAddress"]] = relationship(
        "CustomerAddress", back_populates="orders"
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "bottles_delivered >= 0 AND bottles_returned >= 0",
            name="chk_bottles_positive",
        ),
        CheckConstraint("total_amount >= 0", name="chk_total_positive"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


class OrderItem(Base):
    """
    Represents an individual line item within an order.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Snapshot of price

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="order_items"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_unit_price_positive"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.quantity})>"
