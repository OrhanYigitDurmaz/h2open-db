"""
Centralized enum types for the Water Delivery CRM.
These enums match the PostgreSQL ENUM types defined in init.sql.
"""

import enum


class UserRole(str, enum.Enum):
    """Staff user roles."""

    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    DRIVER = "driver"


class AccountStatus(str, enum.Enum):
    """Customer account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class OrderStatus(str, enum.Enum):
    """Order delivery status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CallDirection(str, enum.Enum):
    """Telephony call direction."""

    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class CallSource(str, enum.Enum):
    """Source of the call."""

    FREEPBX = "FREEPBX"
    USB_CLIENT = "USB_CLIENT"
    MOBILE_APP = "MOBILE_APP"


class EndpointType(str, enum.Enum):
    """Telephony endpoint type."""

    SIP_EXTENSION = "sip_extension"
    USB_DEVICE = "usb_device"
