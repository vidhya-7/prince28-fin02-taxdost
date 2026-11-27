# TaxDost ingestion report

<!-- generated:start -->
## Ingestion summary

- Documents ingested: 27
- Pages extracted: 180
- Dead-letter items: 0
<!-- generated:end -->

## What I learnt

- Background workers handle long-running ingestion tasks without making the API wait.
- Redis stores queued jobs, and ARQ workers pick them up and process them.
- If a worker stops unexpectedly, unfinished jobs can be retried when the worker restarts.
