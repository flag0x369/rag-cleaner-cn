from rag_cleaner_cn.normalize.whitespace import normalize_whitespace


def test_normalize_whitespace_joins_chinese_broken_line():
    assert normalize_whitespace("持续完成\n转化。") == "持续完成转化。"
