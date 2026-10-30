from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
from pathlib import Path

import torch
from PIL import Image

from infer import Captioner


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile, deterministic for small benchmark sets."""
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = max(1, int((p / 100) * len(ordered) + 0.999999))
    return ordered[min(rank, len(ordered)) - 1]


def _model_size_mb(model: object) -> float | None:
    try:
        total = sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())
        return round(total / (1024 * 1024), 2)
    except (AttributeError, TypeError):
        return None


def run_benchmark(
    input_dir: Path,
    output: Path,
    summary_output: Path,
    *,
    model_id: str | None = None,
    dtype: str = "auto",
    quantization: str = "none",
    warmup: int = 1,
    repeats: int = 3,
    runtime: str = "unspecified",
) -> dict:
    if warmup < 0 or repeats < 1:
        raise ValueError("warmup must be >= 0 and repeats must be >= 1")
    if quantization != "none":
        raise RuntimeError(
            "Quantization backend is not applied by the default loader yet. "
            "Run tools/check_quantization_support.py first, then wire and record a verified backend."
        )
    if model_id:
        os.environ["MODEL_ID"] = model_id

    load_started = time.perf_counter()
    captioner = Captioner.load(model_id=model_id)
    model_load_ms = (time.perf_counter() - load_started) * 1000
    paths = sorted(path for path in input_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        raise SystemExit(f"No supported images found in {input_dir}")

    if captioner.device == "cuda" and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    rows: list[dict] = []
    all_latencies: list[float] = []
    failures = 0
    for path in paths:
        try:
            with Image.open(path) as image:
                # Warmup calls are excluded from measured rows.
                for _ in range(warmup):
                    captioner.caption(image.copy())
                measured: list[float] = []
                text = ""
                for _ in range(repeats):
                    text, elapsed_ms = captioner.caption(image.copy())
                    measured.append(round(elapsed_ms, 2))
                all_latencies.extend(measured)
            rows.append(
                {
                    "file": path.name,
                    "device": captioner.device,
                    "latency_ms": round(statistics.mean(measured), 2),
                    "repeat_latencies_ms": json.dumps(measured),
                    "caption": text,
                    "error": "",
                }
            )
        except Exception as exc:  # preserve failures in the reproducibility log
            failures += 1
            rows.append(
                {
                    "file": path.name,
                    "device": captioner.device,
                    "latency_ms": "",
                    "repeat_latencies_ms": "[]",
                    "caption": "",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    if not all_latencies:
        raise RuntimeError("All benchmark images failed; inspect the CSV error column")
    peak_memory_mb = None
    if captioner.device == "cuda" and torch.cuda.is_available():
        peak_memory_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)
    summary = {
        "input_dir": str(input_dir),
        "num_images": len(paths),
        "successful_images": len(paths) - failures,
        "failure_count": failures,
        "device": captioner.device,
        "model_id": captioner.model_id,
        "dtype": dtype,
        "quantization": quantization,
        "runtime": runtime,
        "warmup_runs_per_image": warmup,
        "measured_repeats_per_image": repeats,
        "model_load_ms": round(model_load_ms, 2),
        "model_size_mb_estimate": _model_size_mb(captioner.model),
        "peak_memory_mb": peak_memory_mb,
        "num_measurements": len(all_latencies),
        "average_latency_ms": round(statistics.mean(all_latencies), 2),
        "p50_latency_ms": round(percentile(all_latencies, 50), 2),
        "p95_latency_ms": round(percentile(all_latencies, 95), 2),
        "fastest_latency_ms": round(min(all_latencies), 2),
        "slowest_latency_ms": round(max(all_latencies), 2),
        "total_latency_ms": round(sum(all_latencies), 2),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        fieldnames = ["file", "device", "latency_ms", "repeat_latencies_ms", "caption", "error"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote detail rows to {output}")
    print(f"wrote summary to {summary_output}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reproducible multi-image VLM benchmark.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.csv"))
    parser.add_argument("--summary-output", type=Path, default=Path("results/summary.json"))
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--dtype", choices=["auto", "fp16", "fp32"], default="auto")
    parser.add_argument("--quantization", choices=["none", "int8", "int4"], default="none")
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--runtime", default="unspecified")
    args = parser.parse_args()
    run_benchmark(
        args.input_dir,
        args.output,
        args.summary_output,
        model_id=args.model_id,
        dtype=args.dtype,
        quantization=args.quantization,
        warmup=args.warmup,
        repeats=args.repeats,
        runtime=args.runtime,
    )

