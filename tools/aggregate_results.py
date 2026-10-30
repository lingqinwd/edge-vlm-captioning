from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * q
    lower, upper = int(rank), min(int(rank) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize_csv(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    values = [float(row["latency_ms"]) for row in rows if row.get("latency_ms")]
    if not values:
        raise ValueError(f"no latency values in {path}")
    return {
        "source": str(path),
        "num_rows": len(rows),
        "failure_count": len(rows) - len(values),
        "average_latency_ms": round(statistics.mean(values), 2),
        "p50_latency_ms": round(percentile(values, 0.50), 2),
        "p95_latency_ms": round(percentile(values, 0.95), 2),
        "fastest_latency_ms": round(min(values), 2),
        "slowest_latency_ms": round(max(values), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate benchmark CSV files into one JSON summary.")
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/aggregate_summary.json"))
    args = parser.parse_args()
    summary = [summarize_csv(path) for path in args.input]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

