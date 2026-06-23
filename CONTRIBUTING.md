# Contributing

感谢你改进 `rag-cleaner-cn`。

## 开发流程

1. 安装开发依赖：

   ```bash
   python -m pip install -e ".[dev]"
   ```

2. 修改前先为目标行为补测试。

3. 运行验证：

   ```bash
   ruff check .
   ruff format --check .
   pytest
   ```

## 规则贡献

- 新增 drop 规则时，必须证明它不会误删包含相同关键词的正文段落。
- 新增 repair 规则时，必须写入 `repairs.jsonl` 并说明高置信理由。
- 新增 review 规则时，必须说明人工应如何复核。

## 隐私与样例

不要提交真实用户资料、私密 URL、token、cookie、API key 或未授权内容。示例数据应使用虚构文本或已授权文本。
