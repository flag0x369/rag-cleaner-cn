from rag_cleaner_cn.core.pipeline import CleaningPipeline


def test_chunk_includes_section_path_and_heading_prefix():
    result = CleaningPipeline.default().run_text(
        """# 私域增长

## 用户分层

高价值用户不是买得最多的人，而是愿意持续反馈的人。"""
    )

    chunk = result.chunks[0]
    assert chunk.section_path == ["私域增长", "用户分层"]
    assert chunk.text.startswith("【私域增长 > 用户分层】")


def test_default_chunk_embedding_uses_cleaned_body_only_without_expanded_text():
    result = CleaningPipeline.default().run_text(
        "增长不是更多流量，而是更高质量的转化闭环。",
        metadata={"title": "自动摘要不应混入"},
    )

    chunk = result.chunks[0]
    assert chunk.embedding_text_main == chunk.text
    assert chunk.embedding_text_expanded is None
    assert "摘要" not in chunk.embedding_text_main
