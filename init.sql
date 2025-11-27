/*
 * WATER DELIVERY CRM - INITIALIZATION SCRIPT
 * Version: 1.3
 * System: PostgreSQL
 */

BEGIN;

-- ==========================================
-- 1. ENUMS & EXTENSIONS
-- ==========================================

-- Status Enums ensure data integrity (prevents typos like "pendng")
CREATE TYPE user_role AS ENUM ('admin', 'dispatcher', 'driver');
CREATE TYPE account_status AS ENUM ('active', 'suspended', 'banned');
CREATE TYPE order_status AS ENUM ('pending', 'assigned', 'out_for_delivery', 'delivered', 'cancelled');
CREATE TYPE call_direction AS ENUM ('INBOUND', 'OUTBOUND');
CREATE TYPE call_source AS ENUM ('FREEPBX', 'USB_CLIENT', 'MOBILE_APP');
CREATE TYPE endpoint_type AS ENUM ('sip_extension', 'usb_device');

-- ==========================================
-- 2. STAFF & AUTHENTICATION
-- ==========================================

CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Store Bcrypt/Argon2 hashes here (60+ chars for bcrypt)
    full_name VARCHAR(100) NOT NULL,
    role user_role DEFAULT 'driver',
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Telephony mappings: Links a Staff member to a specific Extension or Hardware ID
CREATE TABLE telephony_endpoints (
    id SERIAL PRIMARY KEY,
    staff_id INT REFERENCES staff(id) ON DELETE CASCADE,

    type endpoint_type NOT NULL,
    identifier VARCHAR(100) NOT NULL, -- e.g., '201' or 'USB-PC-FRONT-DESK'

    -- SIP Credentials for Mobile App Auto-Provisioning
    sip_server_host VARCHAR(150),
    sip_user VARCHAR(100),
    sip_secret VARCHAR(100),

    last_registered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(identifier)
);

-- ==========================================
-- 3. CUSTOMER DATA (CORE CRM)
-- ==========================================

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),

    -- BOTTLE TRACKING LOGIC
    -- Positive: They have our bottles. Negative: We owe them bottles (rare).
    bottles_in_hand INT DEFAULT 0,

    -- FINANCIALS
    account_balance DECIMAL(12, 2) DEFAULT 0.00,

    status account_status DEFAULT 'active',
    internal_notes TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_bottles_reasonable CHECK (bottles_in_hand BETWEEN -100 AND 10000)
);

CREATE TABLE customer_phones (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
    phone_number VARCHAR(30) NOT NULL, -- Store as E.164 (e.g., +90555...)
    label VARCHAR(50) DEFAULT 'Mobile', -- Mobile, Home, Office
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_phone_per_system UNIQUE (phone_number),
    CONSTRAINT chk_phone_format CHECK (phone_number ~ '^\+?[1-9]\d{6,14}$')
);

-- ==========================================
-- 4. DELIVERY ZONES (For Future Route Optimization)
-- ==========================================

CREATE TABLE delivery_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE customer_addresses (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
    title VARCHAR(50), -- e.g., "Home", "Office"
    address_line_1 TEXT NOT NULL,
    address_line_2 TEXT,
    city VARCHAR(100) DEFAULT 'Istanbul',

    -- GEOLOCATION (Lat/Lng for standard mapping/routing, ~10cm precision)
    geo_lat DECIMAL(9, 6),
    geo_lng DECIMAL(9, 6),

    delivery_zone_id INT REFERENCES delivery_zones(id) ON DELETE SET NULL,
    has_elevator BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE
);

-- ==========================================
-- 5. CATALOG & INVENTORY
-- ==========================================

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE,
    description TEXT,

    price DECIMAL(10, 2) NOT NULL,

    -- Water Delivery Specifics
    is_returnable BOOLEAN DEFAULT FALSE, -- Is this a 19L Carboy?
    deposit_fee DECIMAL(10, 2) DEFAULT 0.00, -- Fee if bottle lost/not returned

    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_price_positive CHECK (price >= 0),
    CONSTRAINT chk_deposit_positive CHECK (deposit_fee >= 0)
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),

    warehouse_name VARCHAR(100) DEFAULT 'Main Warehouse',

    quantity_full INT DEFAULT 0, -- Ready to sell
    quantity_empty INT DEFAULT 0, -- Empties waiting for supplier

    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_quantity_full_positive CHECK (quantity_full >= 0),
    CONSTRAINT chk_quantity_empty_positive CHECK (quantity_empty >= 0)
);

-- ==========================================
-- 6. OPERATIONS: ORDERS & SUBSCRIPTIONS
-- ==========================================

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    driver_id INT REFERENCES staff(id), -- Who is delivering
    address_id INT REFERENCES customer_addresses(id),

    status order_status DEFAULT 'pending',

    -- LOGISTICS
    requested_delivery_date DATE,
    delivery_window VARCHAR(50), -- e.g. "10:00 - 12:00"

    -- BOTTLE MOVEMENT (Filled by Driver App upon delivery)
    bottles_delivered INT DEFAULT 0,
    bottles_returned INT DEFAULT 0,

    -- FINANCIALS
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50), -- Cash, POS, Online
    is_paid BOOLEAN DEFAULT FALSE,

    is_deleted BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_bottles_positive CHECK (bottles_delivered >= 0 AND bottles_returned >= 0),
    CONSTRAINT chk_total_positive CHECK (total_amount >= 0)
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL, -- Snapshot of price

    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_unit_price_positive CHECK (unit_price >= 0)
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    product_id INT REFERENCES products(id),
    address_id INT REFERENCES customer_addresses(id),

    quantity INT DEFAULT 1,
    frequency_days INT DEFAULT 7, -- 7 = Weekly
    next_delivery_date DATE,

    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_subscription_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_frequency_positive CHECK (frequency_days > 0)
);

-- ==========================================
-- 7. TELEPHONY LOGS (Event Sourcing)
-- ==========================================

CREATE TABLE call_logs (
    id SERIAL PRIMARY KEY,
    call_uuid VARCHAR(100) UNIQUE NOT NULL, -- Unique Link ID

    -- Normalized Data
    caller_number VARCHAR(30) NOT NULL,
    matched_customer_id INT REFERENCES customers(id), -- Linked automatically if found
    target_identifier VARCHAR(100), -- Extension or Device ID

    source call_source DEFAULT 'FREEPBX',
    direction call_direction DEFAULT 'INBOUND',
    status VARCHAR(20), -- RINGING, ANSWERED, MISSED

    duration INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_duration_positive CHECK (duration >= 0)
);

-- ==========================================
-- 8. AUDIT LOG (For Order Changes)
-- ==========================================

CREATE TABLE order_audit_log (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    customer_id INT,
    action VARCHAR(50) NOT NULL, -- 'DELIVERED', 'DELIVERY_REVERTED', 'CORRECTION', 'SOFT_DELETED'
    old_status order_status,
    new_status order_status,
    bottles_delta INT, -- Positive = added to customer, Negative = removed
    balance_delta DECIMAL(10, 2),
    details TEXT, -- JSON or text description of what changed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 9. PERFORMANCE INDEXES
-- ==========================================

-- Vital for "Screen Pop" speed (Finding customer by phone < 10ms)
CREATE INDEX idx_customer_phone ON customer_phones(phone_number);
CREATE INDEX idx_customer_phones_customer_id ON customer_phones(customer_id);

-- Vital for Route Optimization (Filtering orders by location)
CREATE INDEX idx_address_geo ON customer_addresses(geo_lat, geo_lng);
CREATE INDEX idx_address_customer_id ON customer_addresses(customer_id);

-- Order lookups
CREATE INDEX idx_orders_status_driver ON orders(driver_id, status);
CREATE INDEX idx_orders_delivery_date ON orders(requested_delivery_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status) WHERE is_deleted = FALSE;

-- Vital for Dashboard (Recent calls)
CREATE INDEX idx_calls_created ON call_logs(created_at DESC);
CREATE INDEX idx_calls_customer ON call_logs(matched_customer_id);

-- Subscription auto-generation queries
CREATE INDEX idx_subscriptions_next_delivery ON subscriptions(next_delivery_date)
    WHERE is_active = TRUE AND is_deleted = FALSE;
CREATE INDEX idx_subscriptions_customer ON subscriptions(customer_id);

-- Soft delete filters (partial indexes for fast "active" queries)
CREATE INDEX idx_customers_active ON customers(id) WHERE is_deleted = FALSE;
CREATE INDEX idx_orders_active ON orders(id) WHERE is_deleted = FALSE;
CREATE INDEX idx_staff_active ON staff(id) WHERE is_deleted = FALSE;
CREATE INDEX idx_products_active ON products(id) WHERE is_deleted = FALSE;
CREATE INDEX idx_subscriptions_active ON subscriptions(id) WHERE is_deleted = FALSE;

-- Audit log lookups
CREATE INDEX idx_order_audit_order ON order_audit_log(order_id);
CREATE INDEX idx_order_audit_customer ON order_audit_log(customer_id);
CREATE INDEX idx_order_audit_created ON order_audit_log(created_at DESC);

-- ==========================================
-- 10. TRIGGERS & BUSINESS LOGIC
-- ==========================================

-- Generic trigger for auto-updating timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER trg_staff_updated
BEFORE UPDATE ON staff
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_customers_updated
BEFORE UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_orders_updated
BEFORE UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_subscriptions_updated
BEFORE UPDATE ON subscriptions
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Function: Automatically update customer bottle balance with differential logic
-- Handles: INSERT, UPDATE with soft delete support
-- Treats is_deleted = TRUE as having zero effect (like pending status)
CREATE OR REPLACE FUNCTION update_bottle_balance()
RETURNS TRIGGER AS $$
DECLARE
    old_bottles_effect INT := 0;
    new_bottles_effect INT := 0;

    old_balance_effect DECIMAL(10, 2) := 0;
    new_balance_effect DECIMAL(10, 2) := 0;

    old_customer_id INT := NULL;
    new_customer_id INT := NULL;

    bottles_delta INT := 0;
    balance_delta DECIMAL(10, 2) := 0;
    audit_action VARCHAR(50) := '';
BEGIN
    -- ==========================================
    -- Handle INSERT and UPDATE
    -- ==========================================
    new_customer_id := NEW.customer_id;

    -- Calculate NEW row's effect (only if delivered AND not soft-deleted)
    IF NEW.status = 'delivered' AND NEW.is_deleted = FALSE THEN
        new_bottles_effect := COALESCE(NEW.bottles_delivered, 0) - COALESCE(NEW.bottles_returned, 0);
        IF NEW.is_paid = TRUE THEN
            new_balance_effect := COALESCE(NEW.total_amount, 0);
        END IF;
    END IF;

    -- Handle UPDATE: OLD exists
    IF TG_OP = 'UPDATE' THEN
        old_customer_id := OLD.customer_id;

        -- Calculate OLD row's effect (only if was delivered AND not soft-deleted)
        IF OLD.status = 'delivered' AND OLD.is_deleted = FALSE THEN
            old_bottles_effect := COALESCE(OLD.bottles_delivered, 0) - COALESCE(OLD.bottles_returned, 0);
            IF OLD.is_paid = TRUE THEN
                old_balance_effect := COALESCE(OLD.total_amount, 0);
            END IF;
        END IF;

        -- Check if customer changed
        IF old_customer_id IS DISTINCT FROM new_customer_id THEN
            audit_action := 'CUSTOMER_CHANGED';

            -- Reverse effect from OLD customer
            IF old_customer_id IS NOT NULL AND (old_bottles_effect != 0 OR old_balance_effect != 0) THEN
                UPDATE customers
                SET
                    bottles_in_hand = bottles_in_hand - old_bottles_effect,
                    account_balance = account_balance + old_balance_effect
                WHERE id = old_customer_id;

                -- Audit log for old customer
                INSERT INTO order_audit_log (order_id, customer_id, action, old_status, new_status, bottles_delta, balance_delta, details)
                VALUES (NEW.id, old_customer_id, 'CUSTOMER_CHANGED_FROM', OLD.status, NEW.status, -old_bottles_effect, old_balance_effect,
                    FORMAT('Order reassigned to customer %s. Reversed: bottles=%s, balance=%s', new_customer_id, -old_bottles_effect, old_balance_effect));

                RAISE NOTICE 'Order %: Reversed from old customer %: bottles=%, balance=%',
                    NEW.id, old_customer_id, -old_bottles_effect, old_balance_effect;
            END IF;

            -- Apply full effect to NEW customer
            IF new_customer_id IS NOT NULL AND (new_bottles_effect != 0 OR new_balance_effect != 0) THEN
                UPDATE customers
                SET
                    bottles_in_hand = bottles_in_hand + new_bottles_effect,
                    account_balance = account_balance - new_balance_effect
                WHERE id = new_customer_id;

                -- Audit log for new customer
                INSERT INTO order_audit_log (order_id, customer_id, action, old_status, new_status, bottles_delta, balance_delta, details)
                VALUES (NEW.id, new_customer_id, 'CUSTOMER_CHANGED_TO', OLD.status, NEW.status, new_bottles_effect, -new_balance_effect,
                    FORMAT('Order reassigned from customer %s. Applied: bottles=%s, balance=%s', old_customer_id, new_bottles_effect, -new_balance_effect));

                RAISE NOTICE 'Order %: Applied to new customer %: bottles=%, balance=%',
                    NEW.id, new_customer_id, new_bottles_effect, -new_balance_effect;
            END IF;
        ELSE
            -- Same customer: apply only the delta
            bottles_delta := new_bottles_effect - old_bottles_effect;
            balance_delta := new_balance_effect - old_balance_effect;

            IF bottles_delta != 0 OR balance_delta != 0 THEN
                UPDATE customers
                SET
                    bottles_in_hand = bottles_in_hand + bottles_delta,
                    account_balance = account_balance - balance_delta
                WHERE id = new_customer_id;

                -- Determine audit action type
                IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
                    audit_action := 'SOFT_DELETED';
                ELSIF OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE THEN
                    audit_action := 'RESTORED';
                ELSIF OLD.status != 'delivered' AND NEW.status = 'delivered' THEN
                    audit_action := 'DELIVERED';
                ELSIF OLD.status = 'delivered' AND NEW.status != 'delivered' THEN
                    audit_action := 'DELIVERY_REVERTED';
                ELSE
                    audit_action := 'CORRECTION';
                END IF;

                -- Audit log
                INSERT INTO order_audit_log (order_id, customer_id, action, old_status, new_status, bottles_delta, balance_delta, details)
                VALUES (NEW.id, new_customer_id, audit_action, OLD.status, NEW.status, bottles_delta, -balance_delta,
                    FORMAT('Bottles: %s->%s (delta=%s), Paid: %s->%s, Amount: %s->%s, Deleted: %s->%s',
                        COALESCE(OLD.bottles_delivered, 0) - COALESCE(OLD.bottles_returned, 0),
                        COALESCE(NEW.bottles_delivered, 0) - COALESCE(NEW.bottles_returned, 0),
                        bottles_delta,
                        OLD.is_paid, NEW.is_paid,
                        OLD.total_amount, NEW.total_amount,
                        OLD.is_deleted, NEW.is_deleted));

                RAISE NOTICE 'Order %: Delta for customer %: bottles=%, balance=%, action=%',
                    NEW.id, new_customer_id, bottles_delta, -balance_delta, audit_action;
            END IF;
        END IF;

    -- Handle INSERT: No OLD, just apply NEW effect directly
    ELSIF TG_OP = 'INSERT' THEN
        IF new_customer_id IS NOT NULL AND (new_bottles_effect != 0 OR new_balance_effect != 0) THEN
            UPDATE customers
            SET
                bottles_in_hand = bottles_in_hand + new_bottles_effect,
                account_balance = account_balance - new_balance_effect
            WHERE id = new_customer_id;

            -- Audit log
            INSERT INTO order_audit_log (order_id, customer_id, action, new_status, bottles_delta, balance_delta, details)
            VALUES (NEW.id, new_customer_id, 'INSERTED_AS_DELIVERED', NEW.status, new_bottles_effect, -new_balance_effect,
                FORMAT('Order created with delivered status. Bottles: %s, Balance: %s', new_bottles_effect, -new_balance_effect));

            RAISE NOTICE 'Order % (INSERT): Applied to customer %: bottles=%, balance=%',
                NEW.id, new_customer_id, new_bottles_effect, -new_balance_effect;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger handles INSERT and UPDATE (no DELETE needed with soft deletes)
CREATE TRIGGER trg_update_bottles_on_delivery
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_bottle_balance();

-- Function: Normalize phone number to E.164 format on insert
CREATE OR REPLACE FUNCTION normalize_phone_number()
RETURNS TRIGGER AS $$
BEGIN
    -- Remove all non-digit characters except leading +
    NEW.phone_number = regexp_replace(NEW.phone_number, '[^0-9+]', '', 'g');

    -- If doesn't start with +, assume Turkish number and add +90
    IF LEFT(NEW.phone_number, 1) != '+' THEN
        -- Remove leading 0 if present
        IF LEFT(NEW.phone_number, 1) = '0' THEN
            NEW.phone_number = SUBSTRING(NEW.phone_number FROM 2);
        END IF;
        NEW.phone_number = '+90' || NEW.phone_number;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_normalize_phone
BEFORE INSERT OR UPDATE ON customer_phones
FOR EACH ROW
EXECUTE FUNCTION normalize_phone_number();

-- Function: Auto-link Call Logs to Customers
CREATE OR REPLACE FUNCTION link_call_to_customer()
RETURNS TRIGGER AS $$
DECLARE
    found_cust_id INT;
BEGIN
    -- Try to find customer by phone number (only non-deleted customers)
    SELECT cp.customer_id INTO found_cust_id
    FROM customer_phones cp
    JOIN customers c ON c.id = cp.customer_id
    WHERE cp.phone_number = NEW.caller_number
      AND c.is_deleted = FALSE
    LIMIT 1;

    -- If found, update the row with the ID
    IF found_cust_id IS NOT NULL THEN
        NEW.matched_customer_id = found_cust_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_link_call_log
BEFORE INSERT ON call_logs
FOR EACH ROW
EXECUTE FUNCTION link_call_to_customer();

-- ==========================================
-- 11. VIEWS (Convenience for Application Layer)
-- ==========================================

-- Active customers only
CREATE VIEW v_customers AS
SELECT * FROM customers WHERE is_deleted = FALSE;

-- Active orders only
CREATE VIEW v_orders AS
SELECT * FROM orders WHERE is_deleted = FALSE;

-- Active staff only
CREATE VIEW v_staff AS
SELECT * FROM staff WHERE is_deleted = FALSE;

-- Active products only
CREATE VIEW v_products AS
SELECT * FROM products WHERE is_deleted = FALSE;

-- Active subscriptions only
CREATE VIEW v_subscriptions AS
SELECT * FROM subscriptions WHERE is_deleted = FALSE;

-- ==========================================
-- 12. SEED DATA (For Testing)
-- ==========================================

-- Add Delivery Zones
INSERT INTO delivery_zones (name, description)
VALUES
('Kadikoy', 'Asian side - Kadikoy district'),
('Besiktas', 'European side - Besiktas district'),
('Uskudar', 'Asian side - Uskudar district');

-- Add Products
INSERT INTO products (name, price, is_returnable, deposit_fee, sku)
VALUES
('19L Spring Water', 5.00, TRUE, 10.00, 'W19L'),
('0.5L x 12 Pack', 3.50, FALSE, 0.00, 'W050x12');

-- Add Staff Members
INSERT INTO staff (username, password_hash, full_name, role)
VALUES
('admin', 'hashed_secret_admin', 'System Admin', 'admin'),
('dispatcher1', 'hashed_secret_disp', 'Fatma Demir', 'dispatcher'),
('driver1', 'hashed_secret_123', 'Ahmet Yilmaz', 'driver');

-- Add a Customer
INSERT INTO customers (full_name, bottles_in_hand) VALUES ('Orhan Veli', 1);

INSERT INTO customer_phones (customer_id, phone_number, is_primary)
VALUES (1, '905551234567', TRUE);

INSERT INTO customer_addresses (customer_id, address_line_1, city, geo_lat, geo_lng, delivery_zone_id)
VALUES (1, 'Bagdat Cad. No:10', 'Istanbul', 40.963400, 29.065800, 1);

-- Add Inventory
INSERT INTO inventory (product_id, warehouse_name, quantity_full, quantity_empty)
VALUES
(1, 'Main Warehouse', 500, 50),
(2, 'Main Warehouse', 200, 0);

COMMIT;
