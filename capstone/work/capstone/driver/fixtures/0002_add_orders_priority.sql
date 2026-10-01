-- migrations/0002_add_orders_priority.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.
--
-- Request: add an optional priority (smallint) to orders
-- HAND-WRITTEN for the verifier demo: the rollback drops the wrong column, so reverting
-- this migration would fail and leave orders.priority behind.
--
-- Rollback: the block under the ROLLBACK marker undoes this migration exactly. It stays
-- commented out and is run only on an approved revert.

ALTER TABLE orders ADD COLUMN priority SMALLINT;

-- ROLLBACK
-- ALTER TABLE orders DROP COLUMN priority_level;
