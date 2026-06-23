# rag-cleaner-cn

面向中文 RAG、知识库和智能体问答系统的高保真资料清洗、修复、分块与追溯工具。

第一原则：优先保真，其次清洁，再次可读。宁可保留并标记 review，也不擅自删除或改写有潜在知识价值的内容。本项目不是文章润色器。

## 适用场景

- 公众号文章、网页文章、课程文档、Markdown、纯文本入库前清洗。
- SRT/VTT 视频或音频转写文本的语气词、卡顿重复、时间戳处理。
- PDF 文本抽取后的保守分段和 chunk 生成。
- 书籍 OCR 文本中明显跨页断句、页眉页脚、图表缺失风险的处理。
- 输出可被 LangChain、LlamaIndex、Dify、RAGFlow 或自研向量库消费的 JSONL。

## 不适用场景

- 不做复杂 OCR，扫描 PDF 只提示缺少可抽取文本。
- 不默认做 OCR 字符替换；`enable_ocr_character_fix` 在第一版默认关闭，直到有可测试的高置信规则。
- 不做图文联合理解，不凭空补全图片、表格、视频画面信息。
- 不做风格润色、观点改写、事实补充或自动摘要入正文 embedding。
- 不默认调用外部 LLM，也不绑定任何向量数据库。

## 隐私说明

默认所有处理在本地完成，不上传用户资料，不包含 API key，不依赖外部 LLM。未来如果加入 LLM 辅助修复，也应作为显式启用的插件，并保持原文和模型生成字段隔离。

## 安装

```bash
python -m pip install -e ".[dev]"
```

运行命令：

```bash
rag-cleaner-cn --help
rcc --help
```

`rcc` 是短命令，功能与 `rag-cleaner-cn` 相同。

## 快速开始

```bash
rag-cleaner-cn clean examples/wechat_article.md --out output
rag-cleaner-cn clean examples/video_transcript.srt --source-type video_transcript --out output
rag-cleaner-cn clean-dir ./raw_docs --out ./output
rag-cleaner-cn validate output/<doc_id>
rag-cleaner-cn validate-batch output
rag-cleaner-cn acceptance output/<doc_id>
```

只生成 chunks：

```bash
rag-cleaner-cn chunk output/<doc_id>/clean.md --out output/<doc_id>/chunks.jsonl
```

指定配置：

```bash
rag-cleaner-cn clean examples/book_ocr.txt --config examples/config.example.yaml --out output
```

批量安全参数：

```bash
rag-cleaner-cn clean-dir ./raw_docs --out ./output --dry-run
rag-cleaner-cn clean-dir ./raw_docs --out ./output --limit 20
rag-cleaner-cn clean-dir ./raw_docs --out ./output --sample 20
rag-cleaner-cn clean-dir ./raw_docs --out ./output --profile balanced
rag-cleaner-cn clean-dir ./raw_docs --out ./output --overwrite
```

安全默认：

- `clean-dir` 不允许 `input_dir` 和 `output_dir` 是同一路径。
- `clean-dir` 不允许 `output_dir` 位于 `input_dir` 内部，避免递归扫描到历史输出。
- 默认不覆盖已存在的文档输出目录；需要显式传入 `--overwrite`。
- `--dry-run` 只写 `batch_report.json`，不写入各文档正式输出目录。
- `--limit N` 处理排序后的前 N 个支持文件。
- `--sample N` 随机抽样 N 个支持文件；`--limit` 和 `--sample` 不能同时使用。

## Python API

```python
from pathlib import Path

from rag_cleaner_cn import CleaningPipeline

pipeline = CleaningPipeline.default()
result = pipeline.run_file(Path("examples/wechat_article.md"), Path("output"))

print(result.manifest.quality_score)
print(result.chunks[0].embedding_text_main)
```

## 输入格式

- `.txt`：纯文本。
- `.md` / `.markdown`：Markdown。
- `.html` / `.htm`：移除 script/style，保留标题、列表和正文文本。
- `.srt` / `.vtt`：解析字幕序号、时间戳和说话人。
- `.pdf`：使用 `pypdf` 抽取文本，不默认 OCR。
- `.json` / `.jsonl`：支持 `title`、`author`、`source_url`、`source_type`、`published_at`、`content` 字段。

## 输出格式

每个输入文档会输出到独立目录：

```text
output/
  batch_report.json
  doc_xxxxxxxxxxxx/
    clean.md
    chunks.jsonl
    manifest.json
    repairs.jsonl
    review.jsonl
    dropped.jsonl
```

`clean.md` 保存清洗后正文和 YAML frontmatter。frontmatter 会尽量包含 `doc_id`、`title`、`author_or_account`、`source_type`、`source_url`、`published_at`、`content_type`、`document_status`、`cleaning_version` 和 `quality_tags`。公众号 Markdown 中独立出现的“公众号 / 发布时间 / 原文链接”来源行会移入 frontmatter，正文不重复保留这些来源行。

`chunks.jsonl` 每行一个 RAG chunk，默认 embedding 字段为 `embedding_text_main`，只包含清洗后的正文和必要标题路径。`embedding_text_expanded` 默认不生成，避免模型生成字段污染原文事实。进入 review 的 chunk 会在 `metadata.review_reasons` 中保留复核原因。

`batch_report.json` 记录批处理统计，包括每类文件数量、每种 drop reason、每种 review reason、平均 chunk 长度、chunk status 分布和质量分分布。

## 清洗原则

- 永远不覆盖原始文件。
- 不因为内容短而删除，短观点可作为 `import_short` 入库。
- 不按关键词删除正文，必须判断整段功能。
- 只删除确定性无知识价值噪声，例如纯扫码、纯点赞、纯页脚、纯 URL、纯图片占位。
- 面向知识库导入时，训练营报名、课程预约或价格、二维码、个人微信、商品卡片、社群招募等尾部转化信息应作为推广区块删除。
- 销售正文里的客户建联、竞争策略、触达动作和有争议但有方法价值的内容不因敏感或灰度而删除，除非整段功能明确是引流、报名、领取或购买转化。
- 对视频或课程转写只删除独立成段的课堂互动噪声，例如“给我扣个一”“能听到吗”，同类词出现在有语义正文中会保留。
- 不对销售内容额外打合规风险标签，也不把销售话术改写成风险规避文本；工具目标是尽量保留原文并提供可追溯清洗。
- 有潜在知识价值但结构不完整的内容进入 review。

## 知识库稿结构增强

工具会在清洗、修复之后，chunk 之前执行轻量结构增强，让输出更接近可检索、可人工审核的知识库稿：

- 保留原文句子，不做观点改写、风格润色或自动摘要。
- 独立成段、像小标题的原文短句会提升为 `##`，例如公众号文章里的天然小标题。
- 正文超过约 1500 字且缺少二级标题时，会插入少量通用结构锚点：`## 核心观点`、`## 关键论述`、`## 结尾`。
- 这些通用锚点只用于阅读和 chunk section path，不替代正文，也不作为事实扩写。
- 短观点不会被强行结构化。

## 修复原则

直接修复必须同时满足：

1. 原文明显有错；
2. 上下文能高置信确定正确形式；
3. 修复不改变作者观点。

所有实质性修复都会写入 `repairs.jsonl`。低置信 ASR/OCR 错误、行业术语、人名、公司名、产品名、数据和画面依赖内容不会被自动猜测。

内置 ASR 术语修复只包含高置信规则，例如 `乔哈里创 -> 乔哈里窗`、`囚禁已知 -> 穷尽已知`、`SPN -> SPIN`、`BNT -> BANT`、`痛苦恋 -> 痛苦链`、`线刃 -> 线人`、`销 售 -> 销售`、`1 00% -> 100%`。正常中文叠词如“明明、慢慢、悄悄、默默、天天、件件、迟迟”不会因为重复压缩规则被删成单字。

OCR 跨页断句会通过空白规范化处理；OCR 字符级替换默认关闭，因为第一版没有足够安全的内置替换表。

## RAG Chunking

chunk 优先按章节、标题、问答、方法步骤、案例、列表、说话人轮次和时间戳组织，最后才按长度兜底。默认参数：

```yaml
target_chunk_size_chars: 800
min_chunk_size_chars: 120
max_chunk_size_chars: 1500
overlap_chars: 120
```

chunk 文本会带标题路径：

```text
【私域增长 > 用户分层】

高价值用户不是买得最多的人，而是愿意持续反馈的人。
```

## Manifest

`manifest.json` 记录来源类型、原始 hash、处理版本、分段数、删除数、review 数、修复数、chunk 数、主要删除原因、主要 review 原因和质量分。质量分是辅助信号，不用于硬删除短内容。

## Review 队列

`review.jsonl` 用于人工复核：

- 画面或图表依赖；
- 疑似 ASR/OCR 错误但低置信；
- 语义断裂或缺上下文；
- 说话人混淆；
- 表格、图片、公式缺失。

`rag-cleaner-cn validate` 会校验 `chunks.jsonl`、`dropped.jsonl`、`repairs.jsonl`、`review.jsonl` 与 `manifest.json` 的统计一致性，并检查 review chunk 是否带有 `risk_tags` 和 `metadata.review_reasons`。

`rag-cleaner-cn validate-batch output` 会遍历批处理输出目录下的所有文档输出目录，并逐个执行同样的完整性检查。

## 配置文件

配置使用 YAML，示例见 `examples/config.example.yaml`。支持三种 profile：

- `conservative`：少删少改，默认模式。只删除较短且整段功能明确的纯噪声、推广、页脚和课堂互动。
- `balanced`：扩大整段纯噪声/推广段的长度阈值，适合批量清公众号和视频转写稿。
- `aggressive`：进一步扩大整段纯噪声/推广段的长度阈值，但仍要求命中整段功能判断，不按“微信、课程、转化”等关键词删除正文。

规则文件位于 `src/rag_cleaner_cn/config/default_rules.yaml`。新增规则应优先写在规则文件中，并补测试。

## 接入向量数据库

推荐消费 `chunks.jsonl`：

- 向量文本字段：默认使用 `embedding_text_main`。
- 元数据字段：保留 `doc_id`、`chunk_id`、`section_path`、`source_file`、`source_url`、`page_start`、`start_time`、`risk_tags`。
- 如需标题、关键词、摘要等扩展字段，请写入独立 metadata 或使用 `embedding_text_expanded`，不要混入原文正文。

也可以汇总批处理结果：

```bash
rag-cleaner-cn export-for-vector output --out vector_import.jsonl
```

默认只导出 `chunk_status` 为 `import_chunk` 和 `import_short` 的 chunk。需要额外导出 review chunk 时，显式传入：

```bash
rag-cleaner-cn export-for-vector output --out vector_import.jsonl \
  --include-status import_chunk \
  --include-status import_short \
  --include-status review_chunk
```

## 开发

```bash
ruff check .
ruff format --check .
pytest
```

CI 执行同样命令。修改 schema 时必须同步更新 README 和测试。

开源发布前建议额外验证包构建：

```bash
python -m pip wheel . --no-deps -w /tmp/rag-cleaner-cn-wheel-test
```

## 贡献指南

欢迎提交清洗规则、loader、chunker 和评估用例。贡献前请阅读 `CONTRIBUTING.md` 和 `AGENTS.md`。新增清洗规则必须包含至少一个“应删除”和一个“不得误删”测试。

## 可能方向

以下方向尚未实现，除非有清晰测试和隐私边界，否则不应合入主流程：

- 可选 LLM 辅助修复插件。
- 可选 OCR 集成。
- 表格结构恢复。
- 人工 review 标注界面。
- 检索评估 dashboard。
