# Changelog

## Unreleased

- 增加整篇推广标题排除规则，用于过滤明显报名、开营、课程发售和社群招募类文章。
- 增强公众号尾部转化区块清洗，覆盖训练营报名、课程预约、价格、二维码、个人微信、商品卡片等噪声。
- 保护销售知识正文中的客户建联、触达和添加客户微信等方法内容，避免按关键词误删。
- 增加相关回归测试，覆盖“应删除广告尾巴”和“不得误删销售正文”两类场景。

## 0.1.0 - 2026-06-23

- 初始化 `rag-cleaner-cn` 工程结构。
- 增加 txt、Markdown、HTML、PDF、SRT/VTT、JSON/JSONL loader。
- 增加保守清洗、修复、review 标记、语义 chunk、manifest 和导出。
- 增加 Typer CLI、pytest 测试、ruff 配置和 GitHub Actions CI。
- 增加安全批处理、dry-run、batch_report、validate-batch 和 vector_import 导出能力。
- 增加可生效的 conservative/balanced/aggressive 清洗 profile。
