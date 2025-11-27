"""
H2Open Water Delivery CRM - SQLAlchemy Models
"""

from .audit import OrderAuditLog
from .base import Base
from .call_log import CallLog
from .customer import Customer, CustomerAddress, CustomerPhone
from .delivery_zone import DeliveryZone
from .enums import (
    AccountStatus,
    CallDirection,
    CallSource,
    EndpointType,
    OrderStatus,
    UserRole,
)
from .order import Order, OrderItem
from .product import Inventory, Product
from .staff import Staff, TelephonyEndpoint
from .subscription import Subscription

__all__ = [
    # Base
    "Base",
    # Enums
    "UserRole",
    "AccountStatus",
    "OrderStatus",
    "CallDirection",
    "CallSource",
    "EndpointType",
    # Staff & Authentication
    "Staff",
    "TelephonyEndpoint",
    # Customer
    "Customer",
    "CustomerPhone",
    "CustomerAddress",
    # Delivery
    "DeliveryZone",
    # Products & Inventory
    "Product",
    "Inventory",
    # Orders
    "Order",
    "OrderItem",
    "OrderAuditLog",
    # Subscriptions
    "Subscription",
    # Telephony
    "CallLog",
]
