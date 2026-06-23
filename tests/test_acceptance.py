from rag_cleaner_cn.core.pipeline import CleaningPipeline
from rag_cleaner_cn.eval.acceptance import acceptance_checks


def test_acceptance_does_not_flag_wechat_keyword_inside_kept_method(tmp_path):
    source = tmp_path / "method.md"
    source.write_text("添加企业微信是私域承接链路的关键动作。", encoding="utf-8")
    result = CleaningPipeline.default().run_file(source, tmp_path / "output")

    assert acceptance_checks(tmp_path / "output" / result.document.doc_id) == []
