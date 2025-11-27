"""
Order Audit Log model for tracking order changes.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, TIMESTAMP, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import OrderStatus

if TYPE_CHECKING:
    from .customer import Customer


class OrderAuditLog(Base):
    """
    Audit log for tracking order changes including status changes,
    bottle movements, and balance adjustments.
    """

    __tablename__ = "order_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'DELIVERED', 'DELIVERY_REVERTED', 'CORRECTION', 'SOFT_DELETED'
    old_status: Mapped[Optional[OrderStatus]] = mapped_column(nullable=True)
    new_status: Mapped[Optional[OrderStatus]] = mapped_column(nullable=True)
    bottles_delta: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Positive = added to customer, Negative = removed
    balance_delta: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON or text description of what changed
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<OrderAuditLog(id={self.id}, order_id={self.order_id}, action='{self.action}')>"
