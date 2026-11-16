"""Latency check for NFR-01: product search < 1.5 s, cached comparison < 2 s, alternatives < 3 s (p95).

Usage: python scripts/loadtest.py --base http://127.0.0.1:8001 --requests 300 --concurrency 10
Run against an API instance with SKINSYNC_RATE_LIMIT_ENABLED=false (the limiter would reject a load test).
"""

import argparse
import asyncio
import random
import statistics
import time

import httpx

QUERIES = ["serum", "nivea", "cream", "sunscreen", "glycerin", "hydra", "creme visage", "la roche", "aloe", "cleanser",
           "moisturiser", "spf 50", "vitamin c", "nght cream", "garnier", "micellar"]


async def timed(client, method, url, **kw):
    t = time.perf_counter()
    r = await client.request(method, url, **kw)
    return time.perf_counter() - t, r.status_code


def report(name, samples, target):
    lat = sorted(s for s, _ in samples)
    errors = sum(1 for _, c in samples if c >= 400)
    p95 = lat[int(len(lat) * 0.95) - 1]
    ok = "PASS" if p95 < target and errors == 0 else "FAIL"
    print(f"{name:22s} n={len(lat):4d} p50={statistics.median(lat) * 1000:7.1f}ms p95={p95 * 1000:7.1f}ms "
          f"max={lat[-1] * 1000:7.1f}ms errors={errors} target<{target * 1000:.0f}ms {ok}")
    return ok == "PASS"


async def main(base, n, conc):
    async with httpx.AsyncClient(base_url=base, timeout=30) as c:
        csrf = (await c.get("/api/v1/auth/csrf")).json()["csrf_token"]
        h = {"X-CSRF-Token": csrf}
        ids = [p["id"] for p in (await c.get("/api/v1/products", params={"category": "moisturizer", "limit": 50})).json()["items"]
               if p["has_ingredients"]]
        pairs = [(random.choice(ids), random.choice(ids)) for _ in range(20)]
        for a, b in pairs:  # warm the cache: this test measures cached comparisons
            await c.post("/api/v1/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}, headers=h)
        sem = asyncio.Semaphore(conc)

        async def run(make):
            async with sem:
                return await make()

        search = await asyncio.gather(*[run(lambda: timed(c, "GET", "/api/v1/products", params={"q": random.choice(QUERIES)}))
                                        for _ in range(n)])
        comp = await asyncio.gather(*[run(lambda p=random.choice(pairs): timed(
            c, "POST", "/api/v1/comparisons", json={"a": {"product_id": p[0]}, "b": {"product_id": p[1]}}, headers=h))
            for _ in range(n)])
        alts = await asyncio.gather(*[run(lambda: timed(
            c, "POST", "/api/v1/alternatives/search", json={"product_id": random.choice(ids), "mode": "similar"}, headers=h))
            for _ in range(max(n // 3, 30))])
    results = [report("product search", search, 1.5), report("cached comparison", comp, 2.0),
               report("alternatives (similar)", alts, 3.0)]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--requests", type=int, default=300)
    ap.add_argument("--concurrency", type=int, default=10)
    a = ap.parse_args()
    random.seed(1)
    asyncio.run(main(a.base, a.requests, a.concurrency))
