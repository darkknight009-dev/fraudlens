"""Small reproducible local latency probe for the liveness endpoint."""

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx


def run(url: str, requests: int, workers: int) -> dict[str, float]:
    def request() -> float:
        started = time.perf_counter()
        response = httpx.get(url, timeout=2.0)
        response.raise_for_status()
        return (time.perf_counter() - started) * 1000

    with ThreadPoolExecutor(max_workers=workers) as executor:
        durations = list(executor.map(lambda _: request(), range(requests)))
    ordered = sorted(durations)

    def percentile(value: float) -> float:
        return ordered[min(len(ordered) - 1, int(len(ordered) * value))]

    return {
        "requests": float(requests),
        "workers": float(workers),
        "p50_ms": percentile(0.50),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "mean_ms": statistics.mean(durations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000/health/live")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    print(run(args.url, args.requests, args.workers))


if __name__ == "__main__":
    main()
