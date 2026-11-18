# Engineering notes: TaxDost

## D03 · PostgreSQL

### Migrations (upgrade, downgrade, upgrade)

```text
Command: uv run alembic downgrade -1

INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade f0d0fb2cb648 -> 76d19a792433, add gin index on metadata

Command: uv run alembic current

INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
76d19a792433

Command: uv run alembic upgrade head

INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 76d19a792433 -> f0d0fb2cb648, add gin index on metadata

Command: uv run alembic history

76d19a792433 -> f0d0fb2cb648 (head), add gin index on metadata
<base> -> 76d19a792433, create documents and pages
```

### The loader is idempotent

```text
Run 1:
records=20 inserted=20 updated=0 unchanged=0

Run 2:
records=20 inserted=0 updated=0 unchanged=20

Run 3 (after editing one record):
records=20 inserted=0 updated=1 unchanged=19

Additional run (after adding source_url to all 20 records):
records=20 inserted=0 updated=20 unchanged=0
```

### EXPLAIN for ?act=VALUE

Command:

```powershell
uv run python scripts/explain.py act "Income-tax Act, 1961"
```

Actual output:

```text
-- 1) What the planner chooses on its own:
Seq Scan on documents  (cost=0.00..4.25 rows=1 width=36) (actual time=0.012..0.026 rows=20.00 loops=1)
  Filter: (metadata @> '{"act": "Income-tax Act, 1961"}'::jsonb)
  Buffers: shared hit=4
Planning:
  Buffers: shared hit=125 read=1
Planning Time: 1.212 ms
Execution Time: 0.050 ms

-- 2) Seq scan switched off, to prove the index can be used:
Bitmap Heap Scan on documents  (cost=8.53..12.55 rows=1 width=36) (actual time=0.044..0.054 rows=20.00 loops=1)
  Recheck Cond: (metadata @> '{"act": "Income-tax Act, 1961"}'::jsonb)
  Heap Blocks: exact=4
  Buffers: shared hit=6
  ->  Bitmap Index Scan on ix_documents_metadata_gin  (cost=0.00..8.53 rows=1 width=0) (actual time=0.026..0.026 rows=20.00 loops=1)
        Index Cond: (metadata @> '{"act": "Income-tax Act, 1961"}'::jsonb)
        Index Searches: 1
        Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.077 ms
Execution Time: 0.107 ms
```

**Why did the planner choose a Seq Scan on my table?**

The table contains only 20 records, so scanning the entire table is inexpensive.

Using an index would add extra overhead compared with reading this small table directly.

**When would it switch to the GIN index?**

When the table grows and PostgreSQL estimates that using the GIN index is more efficient than scanning the entire table.
