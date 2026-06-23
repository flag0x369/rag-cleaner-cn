from rag_cleaner_cn.segment.segmenter import segment_text


def test_segment_text_preserves_markdown_headings():
    segments = segment_text("# 标题\n\n正文段落。", doc_id="doc_test")

    assert segments[0].text_original == "# 标题"
    assert segments[1].text_original == "正文段落。"
