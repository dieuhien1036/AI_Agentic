-- migrations/0003_rename_orders_created_at_to_placed_at.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.

ALTER TABLE orders RENAME COLUMN created_at TO placed_at;

