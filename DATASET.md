# Dataset: TaxDost

Helps a salaried first-jobber choose the old or new tax regime and prepare for filing, citing the right Act for the right year.

- **Start target:** Salary-related sections of both Acts + ITR-1/ITR-2 instructions + FAQs
- **Full target:** Full Acts, Rules and 5 years of circulars (6,000+ pages)
- **Collected by:** `scripts/fetch.py` as `examate-student-bot` ([https://github.com/vidhya-7/prince28-fin02-taxdost](https://github.com/vidhya-7/prince28-fin02-taxdost)): robots.txt respected, at most 4 requests at once, 0.5 s between requests to one site.

## Where the documents come from

- [https://incometaxindia.gov.in/](https://incometaxindia.gov.in/)
- [https://www.incometax.gov.in/iec/foportal/](https://www.incometax.gov.in/iec/foportal/)

## Terms I follow

Public government documents. Cite Act, section and year.

- Every answer links to the original document.
- No personal data is collected.

<!-- generated:start -->
**## Sources (generated 2026-11-23 12:22 UTC by scripts/dataset_report.py)**

| Source | Licence / terms | Files | MB | Pages* | How | Fetched | Example URL |
|---|---|---|---|---|---|---|---|
| incometax | Public government document; cite Act section and year | 5 | 3.2 | 24 | http | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/section-15-64](https://wm.incometaxindia.gov.in/w/section-15-64) |

**Total:** 5 files, 3.2 MB, 24 pages. Not downloaded: 0 blocked by robots.txt, 5 failed.

*Pages = PDF pages, plus one page per 3,000 characters of text or HTML.

**## Files (first 5 of 5)**

The complete list, with a sha256 fingerprint of every file, is `data/manifest.jsonl`.

| # | Title / file | Source | Pages | Fetched | URL |
|---|---|---|---|---|---|
| 1 | Employees Benefits Allowable | incometax | 14 | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/employees-benefits-allowable](https://wm.incometaxindia.gov.in/w/employees-benefits-allowable) |
| 2 | Income Tax Act 1961 Section 15 Salaries | incometax | 2 | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/section-15-64](https://wm.incometaxindia.gov.in/w/section-15-64) |
| 3 | Income Tax Act 2025 Section 16 Salary | incometax | 2 | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/section-16-220](https://wm.incometaxindia.gov.in/w/section-16-220) |
| 4 | Income Tax Act 1961 Section 16 Deductions | incometax | 2 | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/section-16-64](https://wm.incometaxindia.gov.in/w/section-16-64) |
| 5 | Income Tax Act 1961 Section 17 Salary Definition | incometax | 5 | 2026-11-23 | [https://wm.incometaxindia.gov.in/w/section-17-64](https://wm.incometaxindia.gov.in/w/section-17-64) |
<!-- generated:end -->

## Known gaps

- The Income Tax Act 2025 PDF could not be downloaded because the server returned HTTP 403 Forbidden.
- ITR-1 and ITR-2 instructions could not be downloaded because the server returned HTTP 403 Forbidden.
- The Income Tax Department salary guide and FAQ page also returned HTTP 403 Forbidden.
- Therefore, the start target is only partially collected: 5 of the 10 listed URLs were downloaded successfully.
- The full target of 6,000+ pages has not yet been collected.
