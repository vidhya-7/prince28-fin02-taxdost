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

## D04 · Docker, testing, and quality gates

### Docker Compose services

The Docker Compose environment contains:

| Service | Purpose |
|---|---|
| `db` | PostgreSQL 17 with pgvector |
| `redis` | Redis 7 |
| `migrate` | Applies Alembic migrations and loads sample data |
| `api` | Runs the FastAPI application |

The API waits for PostgreSQL and Redis health checks and for the migration service to complete successfully.

Useful commands:

```powershell
uv run poe up
docker compose ps
uv run poe logs
uv run poe down
```

To remove the database volume and reset local database state:

```powershell
uv run poe reset
```

**Warning:** `reset` removes the PostgreSQL volume and its stored data.

### Test organization

Tests are separated by purpose:

- `tests/unit/` — unit and API tests.
- `tests/integration/` — tests that require the PostgreSQL test database.
- `tests/integration/conftest.py` — integration-test fixtures.

Run the test groups separately:

```powershell
uv run poe test
uv run poe test-integration
```

### Coverage verification

Command:

```powershell
$env:TEST_DATABASE_URL = "postgresql://<username>:<password>@localhost:5433/app_test"
uv run poe cov
Remove-Item Env:TEST_DATABASE_URL
```

Recorded result:

```text
23 passed
Total coverage: 92%
```

### Code quality checks

Command:

```powershell
uv run poe lint
```

Recorded result:

- Ruff lint check passed.
- Ruff formatting check passed.

Pre-commit hooks configured:

- Trailing whitespace check
- End-of-file fixer
- YAML and TOML validation
- Large-file check
- Private-key detection
- Ruff lint and formatting
- Secret detection

### Poe tasks and Makefile

Poe tasks provide project commands for development, Docker Compose, tests, coverage, migrations, and sample-data loading.

A Makefile also provides shortcuts that delegate to Poe tasks. GNU Make is not installed in the current Windows environment, so use `uv run poe <task>` directly.

### Git hygiene

The `.gitignore` excludes:

- Python bytecode and cache directories
- `.venv`
- `.env` files, except `.env.example`
- Raw data
- Coverage output
- Editor and operating-system files

The `.coverage` file is generated test output and should not be committed.

## D05 · CI/CD and going live

- Live URL: https://taxdost.onrender.com

### Where my secrets live
- Neon string: GitHub Secret DATABASE_URL + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret RENDER_DEPLOY_HOOK only.

### Monitoring
- UptimeRobot checks /health every 5 minutes; alerts go to my email.
- One thing that would make my live app faster on its first request: Render's free instance may spin down after inactivity, so the first request can be slower while it starts up.

### Rollback drill
- Rolled back to sha `b9ff59fe116de1bfaacb7067e8fd7d2319d21b00`: CD #3, smoke test passed (44 seconds).
- Rolled forward to sha `3c35da6fa6f418fadea63063d393a4b0117f02ab`: CD #4, smoke test passed (42 seconds).
- During the rollback, the database stayed on the newer schema. Why is that safe here?
  The rollback changes only the application image; it does not reverse database migrations. The older application remains compatible with the current database schema.

  ### Deployment links

- First deploy that ran by itself (CD #1): https://github.com/vidhya-7/prince28-fin02-taxdost/actions/runs/44710029695
- Rollback (CD #3): https://github.com/vidhya-7/prince28-fin02-taxdost/actions/runs/44730158800
- Roll-forward (CD #4): https://github.com/vidhya-7/prince28-fin02-taxdost/actions/runs/44730660905

## D06 · Collecting the corpus

- Start target: Salary-related sections of both Acts + ITR-1/ITR-2 instructions + FAQs
- Collected today: **5 files, 24 pages, 3.2 MB**
- Doors used: **URL list**

### Licence check

| Source | Licence or terms, in my words | May I show full text in answers? |
|---|---|---|
| incometax.gov.in / incometaxindia.gov.in | Public government documents; cite the Act, section and year. | Not confirmed; show relevant excerpts and link to the original document until reuse terms are verified. |

### robots.txt

- Site: incometaxindia.gov.in. Its robots.txt says: **The downloader checked robots.txt and respected the site's crawling rules. Exact rules have not been recorded.**
- Was anything blocked for my bot? **No robots.txt blocks were reported. Five URLs returned HTTP 403 Forbidden. I left them unavailable and did not bypass the restriction.**

### Kill and resume

- Run 1: I did not press Ctrl+C; the run completed with 5 downloaded and 5 failed.
- Run 2: downloaded=0 skipped=5 failed=5
- Run 3: downloaded=0 skipped=5 failed=5

### Capacity (from docs/CAPACITY.md)

- Tokens per page, measured: **750**
- Full corpus: **4.50 M tokens, 12,937 chunks, embedding about Rs 74, vectors 40 MB**
- The number that surprised me most, and why (2 lines):

  The full corpus is estimated to need only about Rs 74 for one-time embedding.
  The estimated vector storage is also relatively small at 40 MB.

### One thing that went wrong today, and how I fixed it

Five URLs returned HTTP 403 Forbidden. I respected the server restrictions and continued with the five successfully downloaded documents. The dataset report was generated successfully.
