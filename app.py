from __future__ import annotations

import html
import os
import time
from pathlib import Path
from threading import Lock

import gradio as gr

from infer import Captioner


MODEL_OPTIONS = {
    "SmolVLM 256M · 实时基线": "HuggingFaceTB/SmolVLM-256M-Instruct",
    "SmolVLM 500M · 平衡配置": "HuggingFaceTB/SmolVLM-500M-Instruct",
    "Qwen2.5-VL 3B · 质量参考": "Qwen/Qwen2.5-VL-3B-Instruct",
}
MODEL_ROLES = {
    "SmolVLM 256M · 实时基线": "参数量最小，适合实时交互",
    "SmolVLM 500M · 平衡配置": "观察模型规模与速度的平衡",
    "Qwen2.5-VL 3B · 质量参考": "质量优先，资源消耗更高",
}

_CACHE: dict[str, Captioner] = {}
_CACHE_LOCK = Lock()


def _get_captioner(model_label: str) -> Captioner:
    model_id = MODEL_OPTIONS[model_label]
    with _CACHE_LOCK:
        if model_id not in _CACHE:
            _CACHE[model_id] = Captioner.load(model_id=model_id)
        return _CACHE[model_id]


def _metric_card(title: str, value: str, hint: str = "") -> str:
    return f'''<div class="metric-card"><div class="metric-label">{html.escape(title)}</div><div class="metric-value">{html.escape(value)}</div><div class="metric-hint">{html.escape(hint)}</div></div>'''


def _bar_chart(rows: list[tuple[str, float]]) -> str:
    if not rows:
        return '<div class="chart-empty">运行批量测试后，这里会显示延迟分布。</div>'
    max_value = max(v for _, v in rows) or 1
    bars = []
    for name, value in rows:
        width = max(3, int(value / max_value * 100))
        bars.append(f'''<div class="bar-row"><div class="bar-name">{html.escape(name)}</div><div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div><div class="bar-value">{value:.0f} ms</div></div>''')
    return '<div class="chart-wrap"><div class="chart-title">本次批量测试 · 单张生成延迟</div>' + ''.join(bars) + '</div>'


def run_single(image, model_label: str, precision: str):
    if image is None:
        return "请先上传图片。", _metric_card("等待输入", "—", "选择图片后开始"), ""
    if precision.startswith("INT"):
        return "当前环境尚未验证该量化后端。请先运行量化兼容性检查，再进行实测。", _metric_card("量化状态", "待验证", "避免把未量化结果误标"), ""
    started = time.perf_counter()
    try:
        captioner = _get_captioner(model_label)
        text, elapsed_ms = captioner.caption(image)
        role = MODEL_ROLES[model_label]
        cards = ''.join([
            _metric_card("生成延迟", f"{elapsed_ms:.0f} ms", "不含首次模型加载"),
            _metric_card("运行设备", captioner.device.upper(), "当前推理后端"),
            _metric_card("模型角色", role, "实验配置"),
        ])
        return text, cards, f"已完成 · {time.perf_counter() - started:.1f}s"
    except Exception as exc:
        return f"运行失败：{type(exc).__name__}: {exc}", _metric_card("运行状态", "失败", "请查看服务器日志"), ""


def run_batch(files, model_label: str, precision: str):
    if not files:
        return [], _bar_chart([]), _metric_card("批量状态", "—", "请选择多张图片")
    if precision.startswith("INT"):
        return [], _bar_chart([]), _metric_card("量化状态", "待验证", "当前环境未执行量化推理")
    try:
        captioner = _get_captioner(model_label)
    except Exception as exc:
        return [], _bar_chart([]), _metric_card("模型加载", "失败", str(exc))
    rows: list[list[str | float]] = []
    chart_rows: list[tuple[str, float]] = []
    for file_obj in files:
        path = Path(getattr(file_obj, "name", file_obj))
        try:
            from PIL import Image
            with Image.open(path) as image:
                text, elapsed_ms = captioner.caption(image)
            rows.append([path.name, round(elapsed_ms, 2), text, captioner.device])
            chart_rows.append((path.name, elapsed_ms))
        except Exception as exc:
            rows.append([path.name, "失败", f"{type(exc).__name__}: {exc}", captioner.device])
    values = [float(row[1]) for row in rows if isinstance(row[1], (int, float))]
    if values:
        summary = ''.join([
            _metric_card("图片数量", str(len(rows)), "批量输入"),
            _metric_card("平均延迟", f"{sum(values)/len(values):.0f} ms", "生成阶段"),
            _metric_card("最快 / 最慢", f"{min(values):.0f} / {max(values):.0f} ms", "样本范围"),
        ])
    else:
        summary = _metric_card("批量状态", "全部失败", "请查看错误列")
    return rows, _bar_chart(chart_rows), summary


CSS = '''
:root { --ink:#101828; --muted:#667085; --blue:#1677ff; --line:#e6eaf0; --surface:rgba(255,255,255,.82); }
body { background: radial-gradient(circle at 10% 0%, #eaf3ff 0, #f7f9fc 38%, #ffffff 100%); color:var(--ink); }
.gradio-container { max-width: 1240px !important; margin: 0 auto !important; }
.hero { padding: 48px 8px 28px; animation: rise .7s ease both; }
.eyebrow { color:var(--blue); letter-spacing:.12em; font-weight:700; font-size:12px; text-transform:uppercase; }
.hero h1 { font-size: clamp(34px, 5vw, 62px); letter-spacing:-.05em; line-height:1.02; margin:12px 0; }
.hero p { color:var(--muted); font-size:17px; max-width:740px; line-height:1.7; }
.panel { border:1px solid var(--line); border-radius:24px; background:var(--surface); box-shadow:0 14px 44px rgba(16,24,40,.08); padding:22px; }
.panel h3 { margin-top:0; letter-spacing:-.02em; }
.metric-card { border:1px solid var(--line); border-radius:18px; background:#fff; padding:16px 18px; min-height:92px; box-shadow:0 8px 24px rgba(16,24,40,.05); }
.metric-label { color:var(--muted); font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.metric-value { color:var(--ink); font-size:25px; font-weight:750; margin-top:7px; line-height:1.12; }
.metric-hint { color:var(--muted); font-size:12px; margin-top:7px; }
.chart-wrap { border:1px solid var(--line); border-radius:18px; background:#fff; padding:20px; margin-top:12px; }
.chart-title { font-weight:700; margin-bottom:15px; }
.bar-row { display:grid; grid-template-columns:150px 1fr 90px; gap:12px; align-items:center; margin:10px 0; font-size:12px; }
.bar-name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--muted); }
.bar-track { background:#edf2f7; height:10px; border-radius:999px; overflow:hidden; }
.bar-fill { background:linear-gradient(90deg,#1677ff,#7c3aed); height:100%; border-radius:999px; animation:grow .8s ease both; }
.bar-value { color:var(--ink); text-align:right; font-variant-numeric:tabular-nums; }
.chart-empty { color:var(--muted); padding:26px; border:1px dashed var(--line); border-radius:18px; text-align:center; }
button.primary { background:linear-gradient(100deg,#1677ff,#5b5cf6) !important; border:0 !important; }
footer { color:var(--muted); font-size:12px; text-align:center; padding:28px 0; }
@keyframes rise { from {opacity:0; transform:translateY(12px)} to {opacity:1; transform:none} }
@keyframes grow { from {transform:scaleX(0); transform-origin:left} to {transform:scaleX(1); transform-origin:left} }
@media (max-width: 760px) { .bar-row { grid-template-columns:90px 1fr 72px; } .hero { padding-top:25px; } }
'''

with gr.Blocks(title="Edge VLM Studio", css=CSS, theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate")) as demo:
    gr.HTML('''<div class="hero"><div class="eyebrow">EDGE VLM STUDIO · ROCm EXPERIMENT</div><h1>让图像，<br>变成可解释的结果。</h1><p>一个面向端侧部署的视觉语言模型实验台。选择模型、上传图片，观察生成质量与推理成本之间的关系。</p></div>''')
    with gr.Row():
        with gr.Column(scale=4, elem_classes="panel"):
            gr.Markdown("### 选择实验配置")
            model = gr.Dropdown(list(MODEL_OPTIONS), value=list(MODEL_OPTIONS)[0], label="模型")
            precision = gr.Dropdown(["FP16 · GPU 推荐", "FP32 · CPU/兼容模式", "INT8 · 后端验证后启用", "INT4 · 后端验证后启用"], value="FP16 · GPU 推荐", label="精度 / 量化")
            gr.Markdown("**建议路径**：先完成三个模型的 FP16 基线，再根据 ROCm 后端检查结果执行量化实验。")
        with gr.Column(scale=6, elem_classes="panel"):
            gr.Markdown("### 单图探索")
            image = gr.Image(type="pil", label="拖入一张图片", height=300)
            run_button = gr.Button("生成描述  →", variant="primary", elem_classes="primary")
            caption = gr.Textbox(label="模型输出", lines=3, placeholder="结果会显示在这里…")
            single_metrics = gr.HTML(_metric_card("等待输入", "—", "选择图片后开始"))
            single_status = gr.Markdown()
    gr.Markdown("### 批量实验")
    with gr.Row():
        with gr.Column(scale=4, elem_classes="panel"):
            files = gr.Files(file_count="multiple", file_types=["image"], label="上传多张图片")
            batch_button = gr.Button("运行批量测试  →", variant="primary", elem_classes="primary")
            batch_metrics = gr.HTML(_metric_card("批量状态", "—", "请选择多张图片"))
        with gr.Column(scale=6):
            batch_chart = gr.HTML(_bar_chart([]))
            table = gr.Dataframe(headers=["文件", "延迟 (ms)", "描述", "设备"], datatype=["str", "number", "str", "str"], label="逐图结果", wrap=True)
    with gr.Accordion("实验说明与当前基线", open=False):
        gr.Markdown("""
**研究目标**：比较模型规模、精度和运行设备对端侧图像描述速度与资源成本的影响。\
**当前 GPU 基线**：5 张图片平均 **848.96 ms**，最快 **144.11 ms**，最慢 **3606.73 ms**。\
**当前 CPU 基线**：5 张图片平均 **19383.48 ms**，GPU 平均速度约为 CPU 的 **22.83 倍**。\
**数据集**：仓库 `data/images/` 中的 27 张确定性合成图片，按物体、图案、场景、动物、文字和抽象类别组织。
        """)
    gr.HTML("<footer>Edge VLM Studio · SmolVLM / Qwen2.5-VL · AUP Learning Cloud AMD ROCm</footer>")

    run_button.click(run_single, inputs=[image, model, precision], outputs=[caption, single_metrics, single_status])
    batch_button.click(run_batch, inputs=[files, model, precision], outputs=[table, batch_chart, batch_metrics])


if __name__ == "__main__":
    demo.launch()

