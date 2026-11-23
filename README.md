# TaxDost

[![CI](https://github.com/vidhya-7/prince28-fin02-taxdost/actions/workflows/ci.yml/badge.svg)](https://github.com/vidhya-7/prince28-fin02-taxdost/actions/workflows/ci.yml) [![Live](https://img.shields.io/website?url=https%3A%2F%2Ftaxdost.onrender.com%2Fhealth&label=live)](https://taxdost.onrender.com/docs) [![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/m804746134-2e9a989f95f0c9d4c84c19dc)](https://taxdost.onrender.com/health)

**Live:** [https://taxdost.onrender.com](https://taxdost.onrender.com) · [API docs](https://taxdost.onrender.com/docs) · [health](https://taxdost.onrender.com/health)
TaxDost is a tax preparation assistant for salaried individuals. It helps first-time taxpayers compare the old and new tax regimes and understand filing requirements with references to the applicable income-tax laws.

**Status:** Week 1 complete · live at https://taxdost.onrender.com

## Who it's for

A first-job software engineer in Chennai earning about Rs 9 lakh a year and filing an income tax return for the first time.

## The problem

A first-time taxpayer may find it difficult to understand which tax regime is better and which deductions they can claim. Tax rules, deductions, tax slabs, and filing requirements can change depending on the financial year.

The transition from the Income-tax Act 1961 to the Income-tax Act 2025 makes this more confusing because section numbers and applicable provisions differ. TaxDost aims to simplify this process by comparing both regimes and providing reliable explanations with references to the relevant tax laws.

## Data sources

Income-tax Act 1961, Income-tax Act 2025, Income-tax Rules, CBDT circulars and notifications, ITR form instructions and FAQs.

- https://incometaxindia.gov.in/
- https://www.incometax.gov.in/iec/foportal/

Terms: Public government documents. Cite the Act, section, and year.

## Hardest problem (my interview story)

Two Acts at once: answers must select the applicable Act by year, map old and new section numbers, and compute tax under both regimes in code (slabs, rebate, standard deduction) instead of letting an LLM perform the arithmetic.

## Signature feature

Regime calculator: enter salary and deductions and see tax under both regimes with every rule cited.

## Target metric

Tax computed exactly for 100% of 30 test profiles; correct section citations for 90%+ of 40 questions.

## Tech stack

- Python 3.12
- FastAPI
- PostgreSQL with pgvector
- Redis
- SQLAlchemy and Alembic
- Docker and Docker Compose
- pytest and pytest-cov
- Ruff
- Poe the Poet
- pre-commit

## Run locally in one command

### Run with Docker Compose

### Requirements

- Docker Desktop with Docker Compose
- Git
- Python 3.12
- uv

### Clone the repository

```bash
git clone https://github.com/vidhya-7/prince28-fin02-taxdost.git
cd prince28-fin02-taxdost
```


### Start the application

```bash
uv run poe up
```

This builds the application image and starts:

- PostgreSQL with pgvector
- Redis
- Database migration and sample-data loading service
- FastAPI application

Check service status:

```bash
docker compose ps
```

### Access the application

- API documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

### View logs

```bash
uv run poe logs
```

### Stop the services

```bash
uv run poe down
```

### Reset the database

```bash
uv run poe reset
```

**Warning:** Reset removes the PostgreSQL Docker volume and permanently deletes its local database data.

## Local development

Install dependencies:

```bash
uv sync
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Run the development server:

```bash
uv run poe dev
```

The local API requires a reachable PostgreSQL database and the appropriate environment configuration.

## Database operations

Apply migrations:

```bash
uv run poe migrate
```

Load sample data:

```bash
uv run poe seed
```

## Tests and coverage

Run unit tests:

```bash
uv run poe test
```

Run integration tests:

```bash
uv run poe test-integration
```

Run tests with coverage:

```bash
uv run poe cov
```

Integration tests require the PostgreSQL test database from Docker Compose to be available.

## Code quality

Run Ruff lint and formatting checks:

```bash
uv run poe lint
```

Pre-commit hooks are configured to check:

- Trailing whitespace
- End-of-file formatting
- YAML and TOML validity
- Large files
- Private keys
- Ruff linting and formatting
- Potential secrets

## Available Poe tasks

| Command | Purpose |
|---|---|
| `uv run poe dev` | Start the local development server |
| `uv run poe up` | Build and start Docker services |
| `uv run poe down` | Stop Docker services |
| `uv run poe logs` | Follow Docker service logs |
| `uv run poe reset` | Remove Docker services and volumes |
| `uv run poe test` | Run unit tests |
| `uv run poe test-integration` | Run integration tests |
| `uv run poe cov` | Run tests with coverage |
| `uv run poe lint` | Run lint and formatting checks |
| `uv run poe migrate` | Apply database migrations |
| `uv run poe seed` | Load sample records |

A Makefile is also included for shortcut commands on systems with GNU Make installed. On Windows, Poe commands can be used directly.
