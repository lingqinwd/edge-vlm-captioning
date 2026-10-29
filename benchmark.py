from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image

from infer import Captioner


parser = argparse.ArgumentParser()
parser.add_argument("--input-dir", type=Path, required=True)
parser.add_argument("--output", type=Path, default=Path("results/benchmark.csv"))
args = parser.parse_args()

captioner = Captioner.load()
args.output.parent.mkdir(parents=True, exist_ok=True)
rows = []
for path in sorted(args.input_dir.iterdir()):
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        continue
    text, elapsed_ms = captioner.caption(Image.open(path))
    rows.append({"file": path.name, "device": captioner.device, "latency_ms": f"{elapsed_ms:.2f}", "caption": text})

with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=["file", "device", "latency_ms", "caption"])
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {len(rows)} rows to {args.output}")

