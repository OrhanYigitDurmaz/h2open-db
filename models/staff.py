"""
Staff and TelephonyEndpoint SQLAlchemy models.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import EndpointType, UserRole

if TYPE_CHECKING:
    from .order import Order


class Staff(Base):
    """Staff members for the water delivery CRM system."""

    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True, create_constraint=False),
        default=UserRole.DRIVER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    telephony_endpoints: Mapped[List["TelephonyEndpoint"]] = relationship(
        "TelephonyEndpoint", back_populates="staff", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="driver")

    def __repr__(self) -> str:
        return (
            f"<Staff(id={self.id}, username='{self.username}', role={self.role.value})>"
        )


class TelephonyEndpoint(Base):
    """Telephony mappings: Links a Staff member to a specific Extension or Hardware ID."""

    __tablename__ = "telephony_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[EndpointType] = mapped_column(
        Enum(
            EndpointType,
            name="endpoint_type",
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
    )
    identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # SIP Credentials for Mobile App Auto-Provisioning
    sip_server_host: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    sip_user: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sip_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    last_registered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    # Relationships
    staff: Mapped[Optional["Staff"]] = relationship(
        "Staff", back_populates="telephony_endpoints"
    )

    def __repr__(self) -> str:
        return f"<TelephonyEndpoint(id={self.id}, type={self.type.value}, identifier='{self.identifier}')>"
