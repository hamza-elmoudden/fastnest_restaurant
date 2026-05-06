-- ══════════════════════════════════════════════════════════════
--  Restaurant Booking System — PostgreSQL Schema
--  Run: psql -U postgres -d restaurant_db -f schema.sql
-- ══════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Enums ─────────────────────────────────────────────────────
CREATE TYPE user_role       AS ENUM ('admin', 'staff', 'customer');
CREATE TYPE table_status    AS ENUM ('available', 'occupied', 'reserved', 'maintenance');
CREATE TYPE booking_status  AS ENUM ('pending', 'active', 'completed', 'cancelled');

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE users (
    id             UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    role           user_role    NOT NULL DEFAULT 'customer',
    phone          VARCHAR(20),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Refresh Tokens ────────────────────────────────────────────
CREATE TABLE refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Restaurant Tables ─────────────────────────────────────────
CREATE TABLE restaurant_tables (
    id           UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    number       INTEGER      NOT NULL UNIQUE,
    capacity     INTEGER      NOT NULL CHECK (capacity > 0),
    location     VARCHAR(50)  DEFAULT 'main',   -- 'main', 'terrace', 'private'
    status       table_status NOT NULL DEFAULT 'available',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Plates (Menu) ─────────────────────────────────────────────
CREATE TABLE plates (
    id           UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(150)  NOT NULL,
    description  TEXT,
    price        NUMERIC(8,2)  NOT NULL CHECK (price >= 0),
    category     VARCHAR(50)   DEFAULT 'main',  -- 'starter','main','dessert','drink'
    image_url    TEXT,
    is_available BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── Bookings ──────────────────────────────────────────────────
CREATE TABLE bookings (
    id            UUID           PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID           NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    table_id      UUID           NOT NULL REFERENCES restaurant_tables(id),
    status        booking_status NOT NULL DEFAULT 'pending',
    guests        INTEGER        NOT NULL DEFAULT 1,
    booked_at     TIMESTAMPTZ    NOT NULL,           -- when the reservation is for
    activated_at  TIMESTAMPTZ,                        -- when status -> active
    notes         TEXT,
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ── Booking → Plates (pre-ordered items) ─────────────────────
CREATE TABLE booking_plates (
    id          UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id  UUID         NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    plate_id    UUID         NOT NULL REFERENCES plates(id),
    quantity    INTEGER      NOT NULL DEFAULT 1 CHECK (quantity > 0),
    note        TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX idx_bookings_user_id    ON bookings(user_id);
CREATE INDEX idx_bookings_table_id   ON bookings(table_id);
CREATE INDEX idx_bookings_status     ON bookings(status);
CREATE INDEX idx_bookings_booked_at  ON bookings(booked_at);
CREATE INDEX idx_refresh_user_id     ON refresh_tokens(user_id);
CREATE INDEX idx_plates_category     ON plates(category);

-- ── Auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_tables_updated_at
    BEFORE UPDATE ON restaurant_tables FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_plates_updated_at
    BEFORE UPDATE ON plates FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_bookings_updated_at
    BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Seed Data ─────────────────────────────────────────────────
-- Password for all seed users: secret123
-- sha256('secret123') = fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4

INSERT INTO users (name, email, password_hash, role) VALUES
    ('Admin',    'admin@restaurant.com', 'fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4', 'admin'),
    ('Staff',    'staff@restaurant.com', 'fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4', 'staff'),
    ('Customer', 'user@restaurant.com',  'fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4', 'customer');

INSERT INTO restaurant_tables (number, capacity, location) VALUES
    (1, 2, 'main'), (2, 4, 'main'), (3, 4, 'main'),
    (4, 6, 'main'), (5, 6, 'terrace'), (6, 8, 'terrace'),
    (7, 2, 'private'), (8, 10, 'private');

INSERT INTO plates (name, description, price, category) VALUES
    ('Bruschetta',       'Toasted bread with tomatoes',      8.50,  'starter'),
    ('Soup of the Day',  'Ask your waiter',                  6.00,  'starter'),
    ('Grilled Salmon',   'With lemon butter sauce',         22.00,  'main'),
    ('Beef Tenderloin',  'With truffle mashed potato',      35.00,  'main'),
    ('Margherita Pizza', 'Classic tomato and mozzarella',   14.00,  'main'),
    ('Pasta Carbonara',  'Egg, pancetta, parmesan',         16.00,  'main'),
    ('Tiramisu',         'Classic Italian dessert',          9.00,  'dessert'),
    ('Cheesecake',       'New York style',                   8.00,  'dessert'),
    ('Still Water',      '750ml',                            4.00,  'drink'),
    ('House Wine',       'Red or white, per glass',          7.00,  'drink');

SELECT 'users'  AS t, COUNT(*) FROM users
UNION ALL SELECT 'tables', COUNT(*) FROM restaurant_tables
UNION ALL SELECT 'plates', COUNT(*) FROM plates;
