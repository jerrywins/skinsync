# Performance (NFR-01)

Measured 2026-11-05 with `scripts/loadtest.py`: 300 requests per endpoint, 10 concurrent clients, API with
2 uvicorn workers on a 2-vCPU sandbox, PostgreSQL 16 holding 2,557 imported products plus 13 demo products,
rate limiting disabled for the test.

| Operation | p50 | p95 | Target (p95) | Result |
|---|---|---|---|---|
| Product search (typo-tolerant trigram) | 591 ms | 774 ms | < 1.5 s | Pass |
| Cached comparison | 90 ms | 151 ms | < 2 s | Pass |
| Alternatives, similar mode (up to 400 candidates) | 558 ms | 978 ms | < 3 s | Pass |

## Fix made during measurement

The first run failed alternatives (p95 5.5 s): candidate features were loaded with four queries per
candidate (~1,600 queries). They are now loaded in one batched query, with function classes taken from the
cached ingredient master. A check confirmed the batched loader returns identical features to the old one
on 300 products before it was switched in.

## Not measured

* Frontend Lighthouse scores (no Lighthouse run here). Pages are server-rendered; the whole stylesheet is 42.5 kB (8.3 kB gzipped,
  measured) and fonts are self-hosted. Measure with Lighthouse CI before launch.
* Behaviour at larger catalogue sizes. The trigram indexes and the 400-candidate cap bound the cost, but
  re-run the load test after importing more data.
