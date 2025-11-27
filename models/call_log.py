"""
Call Log model for telephony tracking.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import CallDirection, CallSource

if TYPE_CHECKING:
    from .customer import Customer


class CallLog(Base):
    """
    Telephony log for tracking inbound and outbound calls.
    Automatically links to customers based on phone number.
    """

    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_uuid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Normalized Data
    caller_number: Mapped[str] = mapped_column(String(30), nullable=False)
    matched_customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    target_identifier: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Extension or Device ID

    source: Mapped[CallSource] = mapped_column(
        Enum(CallSource, name="call_source", create_type=False),
        default=CallSource.FREEPBX,
    )
    direction: Mapped[CallDirection] = mapped_column(
        Enum(CallDirection, name="call_direction", create_type=False),
        default=CallDirection.INBOUND,
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # RINGING, ANSWERED, MISSED

    duration: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    # Relationships
    matched_customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="call_logs"
    )

    __table_args__ = (CheckConstraint("duration >= 0", name="chk_duration_positive"),)

    def __repr__(self) -> str:
        return f"<CallLog(id={self.id}, call_uuid='{self.call_uuid}', caller='{self.caller_number}')>"
