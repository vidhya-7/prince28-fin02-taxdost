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
## Sources (generated 2026-11-24 08:44 UTC by scripts/dataset_report.py)

| Source | Licence / terms | Files | MB | Pages* | How | Fetched | Example URL |
|---|---|---|---|---|---|---|---|
| incometax | Public government document; cite Act section and year | 13 | 6.1 | 81 | http | 2026-11-24 | https://wm.incometaxindia.gov.in/w/section-15-64 |

**Total:** 13 files, 6.1 MB, 81 pages. Not downloaded: 4 blocked by robots.txt, 6 failed.

*Pages = PDF pages, plus one page per 3,000 characters of text or HTML.

## Files (first 13 of 13)

The complete list, with a sha256 fingerprint of every file, is `data/manifest.jsonl`.

| # | Title / file | Source | Pages | Fetched | URL |
|---|---|---|---|---|---|
| 1 | Employees Benefits Allowable | incometax | 14 | 2026-11-23 | https://wm.incometaxindia.gov.in/w/employees-benefits-allowable |
| 2 | ITR-2 FAQs | incometax | 6 | 2026-11-24 | https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/file-itr-2-online |
| 3 | Income from Salary Guide | incometax | 13 | 2026-11-24 | https://wm.incometaxindia.gov.in/w/income-from-salary |
| 4 | Income Tax Act 2025 Overview | incometax | 2 | 2026-11-24 | https://www.incometax.gov.in/iec/foportal/newdownloads/income-tax-act-2025 |
| 5 | Salary Income FAQ Standard Deduction | incometax | 2 | 2026-11-24 | https://wm.incometaxindia.gov.in/w/is-standard-deduction-applicable-to-all-the-salaried-person-whether-he-is-an-employee-of-central-or-state-government- |
| 6 | ITR-2 Online User Manual | incometax | 6 | 2026-11-24 | https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/file-itr-2-online/itr-2-UM |
| 7 | ITR-1 Online User Manual | incometax | 6 | 2026-11-24 | https://www.incometax.gov.in/iec/foportal/newdownloads/itr/itr-UM |
| 8 | ITR-1 FAQs | incometax | 7 | 2026-11-24 | https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/ITR1-FAQ |
| 9 | Income Tax Act 1961 Section 15 Salaries | incometax | 2 | 2026-11-23 | https://wm.incometaxindia.gov.in/w/section-15-64 |
| 10 | Income Tax Act 2025 Section 16 Salary | incometax | 2 | 2026-11-23 | https://wm.incometaxindia.gov.in/w/section-16-220 |
| 11 | Income Tax Act 1961 Section 16 Deductions | incometax | 2 | 2026-11-23 | https://wm.incometaxindia.gov.in/w/section-16-64 |
| 12 | Income Tax Act 1961 Section 17 Salary Definition | incometax | 5 | 2026-11-23 | https://wm.incometaxindia.gov.in/w/section-17-64 |
| 13 | Tax Rates and Computation | incometax | 16 | 2026-11-24 | https://wm.incometaxindia.gov.in/w/tax-rates-and-computation |
<!-- generated:end -->

## Known gaps

- The start corpus has been collected: salary-related sections of both Acts, ITR-1 and ITR-2 user manuals, and relevant FAQs.
- Some earlier source URLs returned HTTP 403 or were blocked by robots.txt. Working official Income Tax Department replacement URLs were added and downloaded successfully.
- Historical failed and blocked attempts remain in data/manifest.jsonl for traceability.
- The full target of 6,000+ pages has not yet been collected.
