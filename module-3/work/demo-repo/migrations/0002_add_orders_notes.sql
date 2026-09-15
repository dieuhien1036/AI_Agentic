-- migrations/0002_add_orders_notes.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.

ALTER TABLE orders ADD COLUMN notes TEXT;

