from __future__ import annotations

import gradio as gr

from infer import Captioner


captioner = Captioner.load()


def run(image):
    if image is None:
        return "请先上传图片。", ""
    text, elapsed_ms = captioner.caption(image)
    return text, f"device={captioner.device}; latency={elapsed_ms:.1f} ms"


with gr.Blocks(title="Edge VLM Captioning") as demo:
    gr.Markdown("# 端侧视觉语言模型图像描述")
    gr.Markdown("上传图片，查看生成描述和单次推理延迟。")
    image = gr.Image(type="pil", label="图片")
    button = gr.Button("生成描述")
    caption = gr.Textbox(label="描述")
    stats = gr.Textbox(label="运行信息")
    button.click(run, inputs=image, outputs=[caption, stats])


if __name__ == "__main__":
    demo.launch()

