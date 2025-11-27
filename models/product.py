from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Product(Base):
    """Product model for catalog items."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), unique=True)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)

    # Water Delivery Specifics
    is_returnable = Column(Boolean, default=False)  # Is this a 19L Carboy?
    deposit_fee = Column(
        Numeric(10, 2), default=0.00
    )  # Fee if bottle lost/not returned

    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_price_positive"),
        CheckConstraint("deposit_fee >= 0", name="chk_deposit_positive"),
    )

    # Relationships
    inventory = relationship("Inventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    subscriptions = relationship("Subscription", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"


class Inventory(Base):
    """Inventory model for tracking stock levels."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_name = Column(String(100), default="Main Warehouse")
    quantity_full = Column(Integer, default=0)  # Ready to sell
    quantity_empty = Column(Integer, default=0)  # Empties waiting for supplier
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("quantity_full >= 0", name="chk_quantity_full_positive"),
        CheckConstraint("quantity_empty >= 0", name="chk_quantity_empty_positive"),
    )

    # Relationships
    product = relationship("Product", back_populates="inventory")

    def __repr__(self):
        return f"<Inventory(id={self.id}, product_id={self.product_id}, warehouse='{self.warehouse_name}')>"
