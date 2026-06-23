# AGENTS.md

本文件指导后续 AI coding agent 在 `rag-cleaner-cn` 仓库中工作。更高优先级的用户直接指令和系统约束仍然优先。

## 项目目标

构建一个面向中文 RAG 的高保真资料清洗、修复、分块、追溯工具。默认本地执行，不上传用户资料，不依赖外部 LLM，不绑定某个向量数据库。

第一原则：优先保真，其次清洁，再次可读。它不是文章润色器。

## 代码风格

- Python >= 3.11。
- 使用类型标注和清晰的小函数。
- Pydantic schema 位于 `src/rag_cleaner_cn/core/models.py`。
- 枚举位于 `src/rag_cleaner_cn/core/enums.py`。
- 默认规则优先写入 `src/rag_cleaner_cn/config/default_rules.yaml`，不要把大量正则散落在业务逻辑中。
- `conservative`、`balanced`、`aggressive` profile 必须对应真实配置变化；不要只在报告里记录名字。
- 不做无关重构、重命名或格式化。

## 测试命令

```bash
pytest
```

## Lint 命令

```bash
ruff check .
ruff format --check .
```

## 不允许破坏的原则

- 不覆盖原始文件。
- 批处理默认不得覆盖已有文档输出目录；需要用户显式传入 `--overwrite`。
- `clean-dir` 不允许输入目录和输出目录相同。
- `clean-dir` 不允许输出目录位于输入目录内部，避免把历史输出重新当作输入。
- `--dry-run` 只能写批处理报告，不得写正式文档输出目录。
- 不因为内容短而删除。
- 不按关键词直接删除正文。
- 不做风格润色。
- 不自动修复低置信错误。
- 不把模型生成内容混入 `embedding_text_main`。
- 不引入会默认上传用户资料的依赖。
- 不包含 API key、cookie、token 或真实私密样例。

## 中文文本处理注意事项

- 识别段落功能，而不是只看关键词。
- “课程、训练营、价格、微信、社群、私域、转化”等词可能是正文案例，不得直接作为删除依据。
- 调整 profile 阈值时，必须同时覆盖“纯推广应删”和“带相同关键词的正文不得误删”测试。
- 对 ASR/OCR 错误只做高置信修复；无法判断时写入 `review.jsonl`。
- OCR 字符级修复默认关闭；启用前必须先加入真实规则、repair log 断言和误修反例。
- 画面、图表、公式缺失不得凭空补全。
- 说话人和问答结构必须尽量保留。

## 新增清洗规则

新增规则必须加测试，至少覆盖：

- 应删除的纯噪声样例；
- 不得误删的正文样例；
- 必要时增加 `review` 或 `repair` 追溯断言。

所有 drop、repair、review 行为必须同步保持：

- `dropped.jsonl` / `repairs.jsonl` / `review.jsonl` 可追溯；
- `manifest.json` 统计一致；
- `rag-cleaner-cn validate` 能发现统计不一致。

## 批处理和向量导出

- 修改 `clean-dir` 时必须同步更新 `batch_report.json` 的测试。
- `batch_report.json` 至少统计文件类型、drop reason、review reason、平均 chunk 长度和质量分分布。
- `export-for-vector` 默认只能导出 `import_chunk` 和 `import_short`。
- 允许导出其他状态时，必须通过显式 `--include-status`。
- 向量导出不得混入摘要、关键词或其他模型生成内容；默认使用 chunk 里的 `embedding_text_main`。

## Schema 变更

修改 `SourceDocument`、`Segment`、`RepairRecord`、`ReviewRecord`、`Chunk` 或 `Manifest` 时，必须同步更新：

- README 的输出格式说明；
- 相关 tests；
- CLI validate/acceptance 逻辑。
