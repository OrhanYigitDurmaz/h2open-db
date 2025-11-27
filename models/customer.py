"""
Customer-related SQLAlchemy models.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import AccountStatus

if TYPE_CHECKING:
    from .audit import OrderAuditLog
    from .call_log import CallLog
    from .delivery_zone import DeliveryZone
    from .order import Order
    from .subscription import Subscription


class Customer(Base):
    """Customer model representing water delivery customers."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # Bottle tracking logic
    # Positive: They have our bottles. Negative: We owe them bottles (rare).
    bottles_in_hand: Mapped[int] = mapped_column(Integer, default=0)

    # Financials
    account_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )

    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status", native_enum=True),
        default=AccountStatus.ACTIVE,
    )
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=datetime.now
    )

    # Relationships
    phones: Mapped[List["CustomerPhone"]] = relationship(
        "CustomerPhone", back_populates="customer", cascade="all, delete-orphan"
    )
    addresses: Mapped[List["CustomerAddress"]] = relationship(
        "CustomerAddress", back_populates="customer", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="customer"
    )
    call_logs: Mapped[List["CallLog"]] = relationship(
        "CallLog", back_populates="matched_customer"
    )

    __table_args__ = (
        CheckConstraint(
            "bottles_in_hand BETWEEN -100 AND 10000", name="chk_bottles_reasonable"
        ),
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, full_name='{self.full_name}')>"


class CustomerPhone(Base):
    """Customer phone numbers with E.164 format."""

    __tablename__ = "customer_phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    phone_number: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # Store as E.164 (e.g., +90555...)
    label: Mapped[str] = mapped_column(
        String(50), default="Mobile"
    )  # Mobile, Home, Office
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="phones")

    __table_args__ = (
        UniqueConstraint("phone_number", name="unique_phone_per_system"),
        CheckConstraint(
            r"phone_number ~ '^\+?[1-9]\d{6,14}$'", name="chk_phone_format"
        ),
    )

    def __repr__(self) -> str:
        return f"<CustomerPhone(id={self.id}, phone_number='{self.phone_number}')>"


class CustomerAddress(Base):
    """Customer delivery addresses with geolocation."""

    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "Home", "Office"
    address_line_1: Mapped[str] = mapped_column(Text, nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="Istanbul")

    # Geolocation (Lat/Lng for standard mapping/routing, ~10cm precision)
    geo_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    geo_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)

    delivery_zone_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("delivery_zones.id", ondelete="SET NULL"), nullable=True
    )
    has_elevator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="addresses")
    delivery_zone: Mapped[Optional["DeliveryZone"]] = relationship(
        "DeliveryZone", back_populates="addresses"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="address")
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="address"
    )

    def __repr__(self) -> str:
        return f"<CustomerAddress(id={self.id}, title='{self.title}')>"
