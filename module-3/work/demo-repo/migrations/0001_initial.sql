-- migrations/0001_initial.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    total           NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id);
