# Capacity plan: TaxDost

Full corpus target: Full Acts, Rules and 5 years of circulars (6,000+ pages)

<!-- generated:start -->
**## Measured on my start corpus (2026-11-23 12:22 UTC)**

| What | Value |
|---|---|
| Files | 5 |
| Size on disk | 3.2 MB |
| Pages (PDF pages + 1 per 3,000 characters of text/HTML) | 24 |
| Characters of text | 70,519 |
| Estimated tokens (characters / 4) | 17,630 |
| Tokens per page | 750 |
| PDFs with almost no text (scanned? OCR is Day 7) | 0 |
| Files not measured (zip, xlsx, unreadable) | 0 |

**## Estimate for the full corpus (target: 6,000 pages)**

| What | How | Value |
|---|---|---|
| Scale factor | target / measured | x 255.3 |
| Tokens | measured tokens x scale | 4.50 M |
| Raw files | measured MB x scale | 818 MB |
| Chunks | tokens / 400 x 1.15 overlap | 12,937 |
| Embedding cost, one time | tokens x 1.15 x $0.15 per 1M | $0.78 = Rs 74 |
| Vector storage | chunks x 768 numbers x 4 bytes | 40 MB |
| Text in Postgres | characters x scale x 1.2 | 22 MB |

Assumptions: 4 characters per token, 400-token chunks, 768-dimension embeddings at $0.15 per 1M tokens, Rs 95 per US dollar.
<!-- generated:end -->

## What I conclude

1. **Is embedding cost a problem for this product?**

   No. Embedding is a one-time cost, and the estimated cost is manageable at approximately Rs 74 for the full corpus.

2. **Do the vectors and text fit in my free Postgres?**

   Estimated vector storage is 40 MB and text storage is 22 MB. They should fit within a typical free Postgres storage limit, but I will verify the exact limit on my database dashboard.

3. **Which number above am I least sure about, and how will I measure it better?**

   The estimated token count is least certain because it uses 4 characters per token. I will measure actual tokens using a tokenizer on Day 8.

4. **What changes if the corpus grows 10 times?**

   Embedding cost, vector storage and text storage will increase approximately 10 times.
   I will need more database storage and may need to optimize chunking and indexing.
