from __future__ import annotations

import importlib.util
import json
import platform


def main() -> None:
    report = {
        "platform": platform.platform(),
        "backends": {
            "bitsandbytes": bool(importlib.util.find_spec("bitsandbytes")),
            "quanto": bool(importlib.util.find_spec("quanto")),
            "torchao": bool(importlib.util.find_spec("torchao")),
        },
        "recommendation": "Use only a backend that imports successfully on this ROCm image; record failed probes.",
    }
    try:
        import torch
        report["torch"] = torch.__version__
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            report["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception as exc:
        report["torch_error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

