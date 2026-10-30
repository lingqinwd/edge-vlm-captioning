from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path


def version(module: str) -> str | None:
    try:
        mod = __import__(module)
        return getattr(mod, "__version__", "unknown")
    except Exception as exc:
        return f"unavailable: {exc.__class__.__name__}"


def main() -> None:
    data = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "torch": version("torch"),
        "transformers": version("transformers"),
        "pillow": version("PIL"),
    }
    try:
        import torch
        data["torch_cuda_available"] = bool(torch.cuda.is_available())
        data["torch_cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            data["gpu_count"] = torch.cuda.device_count()
            data["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception as exc:
        data["torch_runtime_error"] = repr(exc)
    try:
        data["pip_freeze"] = subprocess.check_output(["python", "-m", "pip", "freeze"], text=True).splitlines()
    except Exception as exc:
        data["pip_freeze_error"] = repr(exc)
    out = Path("results/environment.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

