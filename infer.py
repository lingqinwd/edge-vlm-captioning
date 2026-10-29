from __future__ import annotations

import os
import time
from dataclasses import dataclass

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor


DEFAULT_MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"


@dataclass
class Captioner:
    processor: AutoProcessor
    model: AutoModelForImageTextToText
    device: str
    model_id: str

    @classmethod
    def load(cls, model_id: str | None = None) -> "Captioner":
        model_id = model_id or os.getenv("MODEL_ID", DEFAULT_MODEL_ID)
        device = os.getenv("DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
        processor = AutoProcessor.from_pretrained(model_id)
        if device == "cuda":
            model = AutoModelForImageTextToText.from_pretrained(
                model_id, torch_dtype=torch.float16, device_map="auto"
            )
        else:
            model = AutoModelForImageTextToText.from_pretrained(model_id)
        model.eval()
        return cls(processor, model, device, model_id)

    def caption(self, image: Image.Image, max_new_tokens: int = 64) -> tuple[str, float]:
        image = image.convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": "Describe this image in one concise sentence."},
                ],
            }
        ]
        prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=prompt, images=[image], return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        if self.device == "cuda":
            torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        if self.device == "cuda":
            torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - start) * 1000
        text = self.processor.batch_decode(output, skip_special_tokens=True)[0].strip()
        return text, elapsed_ms
