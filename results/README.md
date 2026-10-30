# 结果目录说明

- `cpu_local.*` 和 `gpu_cloud.json`：已完成的单模型基线。
- `multimodel_results_template.csv`：每个模型/精度配置一行的汇总表。
- `quality_scores_template.csv`：人工评分表，评分字段暂时留空。
- 正式运行时，逐图 CSV 和配置级 JSON 一起提交，保留失败行和错误信息。

建议命名：`{model}_{dtype}_{quantization}_{repeat}.csv` 和对应的 `.json`。

