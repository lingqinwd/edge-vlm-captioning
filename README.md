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

## 实验结果

使用同一张 AUP Learning Cloud 页面截图、同一模型和相同生成设置进行测试：

| 模式 | 运行设备 | 单次推理延迟 | 生成结果 |
|---|---|---:|---|
| CPU | `cpu` | 24,869.5 ms | `This is a webpage.` |
| GPU | AMD Radeon AI Pro R9700 / ROCm | 6,796.9 ms | `This is a webpage.` |

GPU 推理约为 CPU 的 **3.7 倍**，两种模式生成内容一致。GPU 模式使用 `device_map="auto"` 和半精度权重加载，以适配 ROCm 环境。

## 实验记录

```powershell
python benchmark.py --input-dir data/images --output results/benchmark.csv
```

## 项目结构

- `infer.py`：模型加载、设备选择和图像描述推理
- `app.py`：Gradio Demo
- `benchmark.py`：批量延迟测试
- `download_model.py`：模型缓存脚本
- `data/`：数据说明和示例数据目录

项目不包含模型权重、账号密码、访问令牌或私有图片。
