# TaxDost

Helps a salaried first-jobber choose the old or new tax regime and prepare for filing, citing the right Act for the right year.

**Status:** Day 1 foundation (FastAPI skeleton, quality gates). Live URL from Day 5.

## Who it's for

First-job software engineer in Chennai earning about Rs 9 lakh a year, filing an income tax return for the first time.

## The problem

A first-time taxpayer may find it difficult to understand which tax regime is better and which deductions they can claim. Tax rules, deductions, tax slabs and filing requirements can change depending on the financial year. The transition from the Income-tax Act 1961 to the Income-tax Act 2025 makes it even more confusing because section numbers and applicable provisions differ. TaxDost aims to simplify this process by comparing both regimes and providing reliable explanations with references to the relevant tax laws.

## Data sources

Income-tax Act 1961, Income-tax Act 2025, Income-tax Rules, CBDT circulars and notifications, ITR form instructions and FAQs.

- https://incometaxindia.gov.in/
- https://www.incometax.gov.in/iec/foportal/
- Terms: Public government documents. Cite Act, section and year.

## Hardest problem (my interview story)

Two Acts at once: answers must pick the Act by year, map old and new section numbers, and compute tax under both regimes in code (slabs, rebate, standard deduction) instead of letting the LLM do arithmetic.

## Signature feature

Regime calculator: enter salary and deductions and see tax under both regimes with every rule cited.

## Target metric

Tax computed exactly for 100% of 30 test profiles; correct section citations for 90%+ of 40 questions.

## Run it locally

```bash
uv sync
cp .env.example .env   # Windows: copy .env.example .env
uv run uvicorn taxdost.api.main:create_app --factory --reload
```

Then open http://localhost:8000/docs

## Checks

```bash
uv run pytest
uv run ruff check .
```
