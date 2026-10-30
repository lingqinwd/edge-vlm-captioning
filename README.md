# Edge VLM Captioning

一个面向 AMD AUP 云端的端侧视觉语言模型实践：上传图片，生成描述，并记录推理延迟与运行设备。

默认模型是 [HuggingFaceTB/SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)，约 2.6 亿参数。模型权重不提交到本仓库，首次运行时会从 Hugging Face 下载并缓存。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python download_model.py
python app.py
```

程序默认使用可用的 CUDA/ROCm 设备，否则回退到 CPU。也可以通过环境变量显式选择设备：

```powershell
$env:DEVICE="cuda"   # GPU/ROCm
$env:DEVICE="cpu"    # CPU 回退
```

也可以通过 `MODEL_ID` 环境变量替换模型，例如 `Salesforce/blip-image-captioning-base`。

## 多图片实验

仓库已在 `data/images/` 准备 27 张确定性合成图片，`data/manifest.csv` 记录类别和参考描述；也可以追加有明确许可的真实图片，脚本会逐张生成描述，并输出明细 CSV 与汇总 JSON：

```powershell
python benchmark.py `
  --input-dir data/images `
  --output results/benchmark.csv `
  --summary-output results/summary.json
```

`summary.json` 包含图片数量、模型加载时间、平均/P50/P95/最快/最慢延迟、峰值显存、模型大小估计和失败数；`benchmark.csv` 保存每张图片每轮延迟、生成描述和错误信息。CPU 与 GPU 使用同一批图片分别运行，即可得到可复现的速度对比。正式实验示例：

```powershell
python benchmark.py `
  --input-dir data/images `
  --model-id HuggingFaceTB/SmolVLM-256M-Instruct `
  --dtype fp16 `
  --warmup 3 `
  --repeats 3 `
  --runtime "AUP ROCm R9700" `
  --output results/smolvlm_256m_fp16.csv `
  --summary-output results/smolvlm_256m_fp16.json
```

量化参数会写入结果元数据；实际 INT8/INT4 运行前先执行 `python tools/check_quantization_support.py`，只使用在当前 ROCm 环境中成功导入的量化后端。

## 升级版实验计划

项目的正式扩展方案见 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)，模型和运行参数见 [`model_configs.yaml`](model_configs.yaml)。正式实验先完成 3 个模型的 FP16 对比，再在 ROCm 兼容的后端上测试 INT8/INT4；每个配置使用同一批图片并重复 3 次。质量评分模板位于 [`quality_rubric.csv`](quality_rubric.csv)，其中 27 行评分项已预填，分数留待人工盲评。

## 实验结果

本轮多图片测试使用 5 张本地生成的无隐私示例图：红色圆形、蓝色方形、绿色三角形、日落渐变和棋盘格。两种模式都使用 `HuggingFaceTB/SmolVLM-256M-Instruct`，统计的是模型生成阶段延迟，不含首次模型加载。

| 模式 | 运行环境 | 图片数量 | 平均延迟 | 最快 | 最慢 | 总延迟 |
|---|---|---:|---:|---:|---:|---:|
| CPU 多图片实测 | Windows Anaconda / PyTorch CPU | 5 | **19383.48 ms** | **18675.20 ms** | **20100.44 ms** | 96917.38 ms |
| GPU 多图片实测 | AUP Learning Cloud AMD ROCm | 5 | **848.96 ms** | **144.11 ms** | **3606.73 ms** | 4244.79 ms |

在同一批 5 张图片上，GPU 平均延迟约为 CPU 的 **22.83 倍**（19383.48 ms 对 848.96 ms）。CPU 最快样本为 18.68 秒，GPU 最快样本为 0.14 秒；GPU 最慢样本为 3.61 秒，主要反映首次算子缓存和图片内容带来的波动。两种模式均能生成可读的图像描述。

CPU 结果来自本地 Windows CPU 环境；GPU 结果来自 AUP Learning Cloud 的 AMD ROCm 环境。AUP 的 Basic Python CPU 镜像未预装 PyTorch，因此 CPU 多图片统计在本地完成；两边使用同一批示例图、同一模型和同一 `benchmark.py`，可用于课堂上的端侧速度对比。详细结果保存在 `results/cpu_local.csv`、`results/cpu_local.json` 和 `results/gpu_cloud.json`。GPU 模式使用 `device_map="auto"` 和半精度权重加载，以适配 ROCm 环境。

## 项目结构

- `infer.py`：模型加载、设备选择和图像描述推理
- `app.py`：Gradio Demo
- `benchmark.py`：多图片、多轮次延迟测试和资源统计
- `download_model.py`：模型缓存脚本
- `tools/collect_environment.py`：保存 Python、PyTorch、Transformers、GPU 和依赖版本
- `tools/check_quantization_support.py`：检查 ROCm 量化后端是否可用
- `tools/aggregate_results.py`：把多次 CSV 测试汇总为 JSON
- `data/`：27 张合成实验图片、manifest 和可复现生成脚本

项目不包含模型权重、账号密码、访问令牌或私有图片。



