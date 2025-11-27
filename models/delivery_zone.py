from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .customer_address import CustomerAddress


class DeliveryZone(Base):
    """Model for delivery zones used for route optimization."""

    __tablename__ = "delivery_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    addresses: Mapped[List["CustomerAddress"]] = relationship(
        "CustomerAddress", back_populates="delivery_zone"
    )

    def __repr__(self) -> str:
        return f"<DeliveryZone(id={self.id}, name='{self.name}')>"
