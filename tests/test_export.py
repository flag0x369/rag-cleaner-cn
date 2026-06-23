import json

from rag_cleaner_cn.core.pipeline import CleaningPipeline
from rag_cleaner_cn.eval.acceptance import validate_output_dir


def test_pipeline_writes_expected_output_files(tmp_path):
    source = tmp_path / "wechat_noise.md"
    source.write_text(
        """# 增长的本质

增长不是更多流量，而是更高质量的转化闭环。

扫码添加微信，回复 666 领取资料包。""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")

    doc_dir = tmp_path / "output" / result.document.doc_id
    assert (doc_dir / "clean.md").exists()
    assert (doc_dir / "chunks.jsonl").exists()
    assert (doc_dir / "manifest.json").exists()
    assert (doc_dir / "repairs.jsonl").exists()
    assert (doc_dir / "review.jsonl").exists()
    assert (doc_dir / "dropped.jsonl").exists()

    manifest = json.loads((doc_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dropped_segments"] == 1


def test_validate_checks_manifest_repair_review_and_drop_counts(tmp_path):
    source = tmp_path / "mixed.md"
    source.write_text(
        """# 混合资料

我们我们今天讲一下增长增长的核心问题。

大家看这里，这个图左边就是我们要关注的重点。

扫码添加微信，回复 666 领取资料包。""",
        encoding="utf-8",
    )
    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    doc_dir = tmp_path / "output" / result.document.doc_id

    manifest_path = doc_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["repair_count"] == 1
    assert manifest["review_segments"] == 1
    assert manifest["dropped_segments"] == 1

    manifest["repair_count"] = 0
    manifest["review_segments"] = 0
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    errors = validate_output_dir(doc_dir)
    assert "manifest repair_count does not match repairs.jsonl" in errors
    assert "manifest review_segments does not match review.jsonl" in errors


def test_validate_requires_dropped_jsonl(tmp_path):
    source = tmp_path / "clean.md"
    source.write_text("增长不是更多流量，而是更高质量的转化闭环。", encoding="utf-8")
    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    doc_dir = tmp_path / "output" / result.document.doc_id
    (doc_dir / "dropped.jsonl").unlink()

    assert "missing dropped.jsonl" in validate_output_dir(doc_dir)


def test_review_chunk_carries_review_reasons_and_validate_checks_them(tmp_path):
    source = tmp_path / "review.md"
    source.write_text("大家看这里，这个图左边就是我们要关注的重点。", encoding="utf-8")
    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    doc_dir = tmp_path / "output" / result.document.doc_id

    assert result.chunks[0].metadata["review_reasons"]

    chunks_path = doc_dir / "chunks.jsonl"
    chunk = json.loads(chunks_path.read_text(encoding="utf-8").splitlines()[0])
    chunk["metadata"].pop("review_reasons")
    chunks_path.write_text(json.dumps(chunk, ensure_ascii=False) + "\n", encoding="utf-8")

    errors = validate_output_dir(doc_dir)
    assert f"review_chunk {chunk['chunk_id']} missing review_reasons" in errors


def test_markdown_inline_source_metadata_moves_to_frontmatter(tmp_path):
    source = tmp_path / "wechat.md"
    source.write_text(
        """# 高层啊高层

公众号：广智
发布时间：2026-06-23 08:30
原文：https://example.com/post/1

正文第一段，保留作者原始表达。""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")
    body = clean.split("---", 2)[-1]

    assert 'author_or_account: "广智"' in clean
    assert 'source_type: "wechat_article"' in clean
    assert 'source_url: "https://example.com/post/1"' in clean
    assert 'published_at: "2026-06-23 08:30"' in clean
    assert "公众号：广智" not in body
    assert "发布时间：2026-06-23 08:30" not in body
    assert "原文：https://example.com/post/1" not in body
    assert "正文第一段" in body


def test_empty_wechat_metadata_line_does_not_become_title(tmp_path):
    source = tmp_path / "blocked.md"
    source.write_text(
        """# 

公众号：进化思维
发布时间：
原文：https://example.com/blocked

此内容因违规无法查看
由用户投诉并经平台审核，涉嫌违反相关法律法规和政策，查看对应规则
微信公众平台运营中心""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")
    body = clean.split("---", 2)[-1]

    assert 'title: "blocked"' in clean
    assert "published_at: null" in clean
    assert "发布时间：" not in body
    assert "此内容因违规无法查看" not in body
    assert result.chunks == []
    assert result.manifest.document_status.value == "exclude"
    assert result.manifest.dropped_segments >= 1


def test_clean_markdown_exports_repaired_heading_text(tmp_path):
    source = tmp_path / "transcript.md"
    source.write_text(
        """## 给大家录一节作业课啊

真正重要的是后面的作业拆解。""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")
    body = clean.split("---", 2)[-1]

    assert "## 给大家录一节作业课\n" in body
    assert "## 给大家录一节作业课啊" not in body
