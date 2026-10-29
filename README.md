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

将 10～30 张允许再分发的图片放入 `data/images/`，脚本会逐张生成描述，并输出明细 CSV 与汇总 JSON：

```powershell
python benchmark.py `
  --input-dir data/images `
  --output results/benchmark.csv `
  --summary-output results/summary.json
```

`summary.json` 包含图片数量、平均延迟、最快延迟、最慢延迟、总延迟和运行设备；`benchmark.csv` 保存每张图片的文件名、设备、延迟和生成描述。CPU 与 GPU 使用同一图片目录分别运行，即可得到可复现的速度对比。

## 实验结果

先用同一张 AUP Learning Cloud 页面截图完成端到端基线测试：

| 模式 | 运行设备 | 图片数量 | 平均/单次延迟 | 生成结果 |
|---|---|---:|---:|---|
| CPU 基线 | `cpu` | 1 | 24,869.5 ms | `This is a webpage.` |
| GPU 基线 | AMD Radeon AI Pro R9700 / ROCm | 1 | 6,796.9 ms | `This is a webpage.` |

GPU 基线约为 CPU 的 **3.7 倍**，两种模式生成内容一致。下一步多图片实验将报告平均、最快和最慢延迟，并观察不同图片类型是否造成延迟波动。GPU 模式使用 `device_map="auto"` 和半精度权重加载，以适配 ROCm 环境。

## 项目结构

- `infer.py`：模型加载、设备选择和图像描述推理
- `app.py`：Gradio Demo
- `benchmark.py`：多图片批量测试和延迟汇总
- `download_model.py`：模型缓存脚本
- `data/`：数据说明和示例数据目录

项目不包含模型权重、账号密码、访问令牌或私有图片。
