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

**Kill-and-resume test: PASSED using a simulated website with httpx.MockTransport.**

The test used a separate temporary folder:
`%TEMP%\taxdost-d06-resume-check`

- Run 1 (interrupted with Ctrl+C): 3 files completed; 4 other downloads were in progress and cancelled.
- Run 2 (resumed): downloaded=5, skipped=3, blocked=0, failed=0.
- Final verification: 8 manifest records, 8 downloaded files, 0 leftover `.part` files.

This confirms that completed files are skipped and missing files are downloaded after interruption. The test used a simulated website, not the live Income Tax website.

### Capacity (from docs/CAPACITY.md)

- Tokens per page, measured: **750**
- Full corpus: **4.50 M tokens, 12,937 chunks, embedding about Rs 74, vectors 40 MB**
- The number that surprised me most, and why (2 lines):

  The full corpus is estimated to need only about Rs 74 for one-time embedding.
  The estimated vector storage is also relatively small at 40 MB.

### One thing that went wrong today, and how I fixed it

Five URLs returned HTTP 403 Forbidden. I respected the server restrictions and continued with the five successfully downloaded documents. The dataset report was generated successfully.

## D07 · Parser comparison

<!-- parsers:start -->
| File | Parser comparison | Pages | trafilatura result | Strip-tags result | Time | Better, why |
|---|---|---|---|---|---|---|
| tax-rates-and-computation-c0c67447.html | trafilatura / strip tags | 9 | 26,706 chars, 0 headings, 0 tables | 51,147 chars, 0 headings, 0 tables | 0.43 s / 0.02 s | trafilatura: cleaner extraction with less unwanted content. |
| employees-benefits-allowable-434bd290.html | trafilatura / strip tags | 6 | 39,526 chars, 1 headings, 0 tables | 44,168 chars, 0 headings, 0 tables | 0.18 s / 0.02 s | trafilatura: detects a heading and extracts cleaner content. |
| income-from-salary-f1f94d83.html | trafilatura / strip tags | 6 | 38,029 chars, 1 headings, 0 tables | 41,437 chars, 0 headings, 0 tables | 0.20 s / 0.02 s | trafilatura: detects a heading and removes unnecessary webpage content. |
| section-17-64-4c784750.html | trafilatura / strip tags | 5 | 12,370 chars, 0 headings, 13 tables | 17,375 chars, 0 headings, 0 tables | 0.10 s / 0.01 s | trafilatura: preserves 13 tables; strip-tags loses table structure. |
| section-16-220-e919c493.html | trafilatura / strip tags | 1 | 1,291 chars, 0 headings, 0 tables | 5,649 chars, 0 headings, 0 tables | 0.09 s / 0.01 s | trafilatura: extracts less unwanted content. |
| section-15-64-c51641da.html | trafilatura / strip tags | 1 | 1,105 chars, 1 headings, 0 tables | 5,966 chars, 0 headings, 0 tables | 0.09 s / 0.01 s | trafilatura: detects a heading and extracts cleaner content. |
| is-standard-deduction-applicable-to-all-the-sala | trafilatura / strip tags | 1 | 877 chars, 1 headings, 0 tables | 5,301 chars, 0 headings, 0 tables | 0.09 s / 0.01 s | trafilatura: detects a heading and removes extra webpage content. |
| section-16-64-f5bbcc50.html | trafilatura / strip tags | 1 | 1,245 chars, 1 headings, 0 tables | 6,198 chars, 0 headings, 0 tables | 0.07 s / 0.01 s | trafilatura: detects a heading and extracts cleaner content. |
| itr-2-um-8f2d0d83.html | trafilatura / strip tags | 6 | 15,039 chars, 5 headings, 0 tables | 21,224 chars, 0 headings, 0 tables | 1.19 s / 0.01 s | trafilatura: preserves 5 headings and cleaner document structure. |
| itr1-faq-e1a62604.html | trafilatura / strip tags | 6 | 16,617 chars, 34 headings, 0 tables | 23,337 chars, 0 headings, 0 tables | 0.06 s / 0.01 s | trafilatura: detects 34 headings and preserves useful structure. |
<!-- parsers:end -->

### D07 · Parsing my corpus

- Manifest files: 28
- Downloaded files: 13
- Successfully parsed files: 13
- Parsing failures: 0
- Pages saved in PostgreSQL: 53
- Parsing coverage: 100% of downloaded files (13/13).
- 15 files could not be downloaded because they were failed or blocked.

### What I observed

- The ITR-1 FAQ contains 34 detected headings.
- Tax Rates and Computation has 9 pages, but its heading paths are empty because section labels are not detected as Markdown headings.
- Section 17 preserves 13 tables, but some table headers are generic.
- No downloaded PDFs were available for PDF parser comparison.
- The Tax Rates and Computation pages contain flattened table content. Some table rows and columns run together, so the original table structure is not fully preserved.

### My parser choice

I chose trafilatura for HTML parsing because it extracts cleaner content, detects headings, and preserves tables. Simple tag stripping is faster but includes unnecessary webpage content and loses document structure.

### Limitations

Some legal section headings are represented as bold or ordinary text rather than semantic headings. These are not detected by the current heading extraction logic.

### D08 · What the model does without my documents

- Question 6 ("Has my refund been credited?"): Yes, it admitted it cannot know.
- Its exact words: "I am not sure. As TaxDost, I help you understand tax rules and compare regimes, but I cannot access your personal tax account or check the status of your refund."
- Off-topic question ("Who won the 2011 cricket world cup?"): Declined in one sentence.
- Exact response: "That question is outside this product's subject."

- Wrong detail:
  Question: What is the standard deduction under the new tax regime for FY 2024-25?
  TaxDost said: ₹50,000.
  Correct answer: ₹75,000.

- Second known-answer question:
  Question: What is the standard deduction under the old tax regime for FY 2024-25?
  TaxDost said: ₹50,000.
  Correct answer: ₹50,000.
  Result: Correct.

- With primary broken: provider Groq, fallback Yes.
- First words: 2.22 seconds (first fallback request).
- Gemini error stopped appearing at request 4.
- Request 4 went directly to Groq because the circuit was open.
- Request 5 retried Gemini (half-open test), failed, and used Groq.

### D08 · Usage report

- Total calls: 19
- Errors: 5
- Fallbacks: 6
- Input tokens: 3,030
- Output tokens: 1,818
- Estimated cost: ₹0.2323

### D08 · Database verification

- SQL query confirmed that LLM calls are stored in PostgreSQL.
- Invalid Gemini model returned HTTP 404.
- Groq successfully handled requests after Gemini failures.
- A Gemini ConnectTimeout was also recorded, followed by a successful Groq fallback.
- Successful Gemini calls were recorded with fallback_used = false.
- Failed provider calls recorded zero tokens and zero cost.

## D09 · Prompt versions compared

<!-- prompts:start -->

| Prompt version | Correct | Accuracy | Invalid replies | Avg tokens in |
|---|---|---|---|---|
| classify_v1 | 15/20 | 75% | 0 | 46 |
| classify_v2 | 20/20 | 100% | 0 | 174 |
| classify_v3 | 20/20 | 100% | 0 | 246 |
| classify_v4 | 19/20 | 95% | 0 | 199 |

<!-- prompts:end -->

### D09 · Version 4 experiment

- Best versions: classify_v2 and classify_v3, both achieved 100% accuracy.
- classify_v2 is more efficient, averaging 174 input tokens compared with 246 for v3.
- classify_v4 added an explicit instruction to treat user questions as untrusted input.
- v4 achieved 95% accuracy and misclassified test question 4 as personal instead of docs.
- The question provides salary, rent and investment details directly, so it can be answered using tax documents and the supplied information.
- The additional instruction did not improve accuracy. Keep v2 as the preferred prompt.
- No prompt leakage was reported.

### D09 · Extraction run

- Prompt version: `extract_v1`
- Documents processed: 13
- Successful: 13
- Repaired: 2
- Failed: 0
- Total input tokens: 30,099
- Total output tokens: 2,792
- Estimated cost: ₹1.521
- Most common validation issue: `section` returned more than 8 values.
- Fix: The extractor requested corrected JSON and successfully validated both repaired responses.
- Database verification: 13 successful, 0 failed.
- Manual verification: Compared Section 16 and Section 17 against their original Income-tax Department pages.
- Factual issue found: Both pages display Year 2025, but the extractor returned year=null.
- Other checked fields: document kind, language, act, section references, topics and listed amounts were supported by the source text.
- Improvement identified: Update the extraction prompt to explicitly inspect displayed document metadata such as Year.

### One thing that went wrong today, and how I fixed it

Two documents returned more than the allowed 8 section values. The Pydantic validation rejected them, and the extractor retried with a repair instruction. Both documents were successfully saved after correction.

# Day 10
- docs/CAPACITY.md said: 81 pages, 60,554 tokens. docs/INGEST_REPORT.md says: 180 pages, 153,198 tokens.
- The current corpus has 99 more pages and 92,644 more estimated tokens. The corpus contains more extracted content than Monday's starting measurement.

### D10 · Queue and worker
- First run: 10 documents queued, finished in 51 s. Done 10, skipped 0, failed 0
- Pace: 5.1 s per document (INGEST_RPM = 12, INGEST_CONCURRENCY = 2)

### Kill test
- Queued: 20. At the kill: queued 13, running 2, done 5, failed 0
- After the new worker: done 20 + skipped 0 + failed 0 = 20
- Documents in the database: 27, different ids: 27
- The interrupted items came back after about 299 seconds (5 minutes). Why that long: ARQ retry delay before processing interrupted jobs.
- Why nothing was doubled: The database checks the external ID, so the same document is not inserted twice.

### Dead-letter list
| Stage (parse / extract / download / gave up) | Items | What I did |
|---|---|---|
| None | 0 | No failed items; no retry needed |

### One thing that went wrong today, and how I fixed it
- The ingest report script was missing. I created `scripts/ingest_report.py`, ran it, and generated `docs/INGEST_REPORT.md`.

### Live ingestion
- TaxDost on Render: 5 of 5 documents done, 0 failed. 74 pages processed in 27 seconds.
- A request without the token gets status 401.
