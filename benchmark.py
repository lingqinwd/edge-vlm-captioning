from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from PIL import Image

from infer import Captioner


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def run_benchmark(input_dir: Path, output: Path, summary_output: Path) -> dict:
    captioner = Captioner.load()
    paths = sorted(path for path in input_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        raise SystemExit(f"No supported images found in {input_dir}")

    rows = []
    for path in paths:
        with Image.open(path) as image:
            text, elapsed_ms = captioner.caption(image)
        rows.append(
            {
                "file": path.name,
                "device": captioner.device,
                "latency_ms": round(elapsed_ms, 2),
                "caption": text,
            }
        )

    latencies = [row["latency_ms"] for row in rows]
    summary = {
        "input_dir": str(input_dir),
        "num_images": len(rows),
        "device": captioner.device,
        "average_latency_ms": round(statistics.mean(latencies), 2),
        "fastest_latency_ms": round(min(latencies), 2),
        "slowest_latency_ms": round(max(latencies), 2),
        "total_latency_ms": round(sum(latencies), 2),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "device", "latency_ms", "caption"])
        writer.writeheader()
        writer.writerows(rows)

    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote detail rows to {output}")
    print(f"wrote summary to {summary_output}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark image captioning latency over a folder of images.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.csv"))
    parser.add_argument("--summary-output", type=Path, default=Path("results/summary.json"))
    args = parser.parse_args()
    run_benchmark(args.input_dir, args.output, args.summary_output)
