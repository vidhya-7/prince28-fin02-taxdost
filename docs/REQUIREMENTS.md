# Requirements: TaxDost

## Functional (what it does)

1. A user can ask a question in plain English and get an answer drawn from my sources.
2. Every answer cites the document and page (or section) it came from.
3. If the documents do not contain the answer, the product says "I don't know" instead of guessing.
4. Signature feature: Regime calculator: enter salary and deductions and see tax under both regimes with every rule cited.
5. A user can browse and search the underlying records through GET /v1/documents.

## Non-functional (how well, with numbers)

| # | Quality | Target | How I will measure it |
|---|---|---|---|
| 1 | Speed: record lookups | p95 under 300 ms for GET /v1/documents | Load test (Week 6) |
| 2 | Speed: answers | p95 under 4 s for a full answer; first token under 1.5 s | Traces (Week 5) |
| 3 | Accuracy | Tax computed exactly for 100% of 30 test profiles; correct section citations for 90%+ of 40 questions | Golden question set (Weeks 4 and 5) |
| 4 | Cost | Under Rs 0.50 per answered question | llm_calls table (Week 2) |
| 5 | Availability | 99% monthly uptime of the live URL | Uptime monitor from Day 5 |
