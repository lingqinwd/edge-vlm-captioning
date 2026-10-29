from __future__ import annotations

import os

from huggingface_hub import snapshot_download


model_id = os.getenv("MODEL_ID", "HuggingFaceTB/SmolVLM-256M-Instruct")
print(f"downloading {model_id} into the Hugging Face cache...")
cache_path = snapshot_download(repo_id=model_id)
print(f"model files are cached at {cache_path}")

