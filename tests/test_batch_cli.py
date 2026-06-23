import json

from typer.testing import CliRunner

from rag_cleaner_cn.cli import app
from rag_cleaner_cn.core.batch import apply_profile
from rag_cleaner_cn.core.pipeline import CleaningPipeline

runner = CliRunner()


def write_doc(directory, name: str, text: str) -> None:
    (directory / name).write_text(text, encoding="utf-8")


def test_clean_dir_rejects_same_input_and_output(tmp_path):
    write_doc(tmp_path, "a.md", "增长不是更多流量，而是更高质量的转化闭环。")

    result = runner.invoke(app, ["clean-dir", str(tmp_path), "--out", str(tmp_path)])

    assert result.exit_code != 0
    assert "input_dir and output_dir must be different" in result.output


def test_clean_dir_rejects_output_inside_input_dir(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_doc(raw, "a.md", "增长不是更多流量，而是更高质量的转化闭环。")

    result = runner.invoke(app, ["clean-dir", str(raw), "--out", str(raw / "output")])

    assert result.exit_code != 0
    assert "output_dir must not be inside input_dir" in result.output


def test_clean_dir_refuses_existing_output_without_overwrite(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    out = tmp_path / "out"
    write_doc(raw, "a.md", "增长不是更多流量，而是更高质量的转化闭环。")

    first = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out)])
    second = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out)])
    third = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out), "--overwrite"])

    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "already exists" in second.output
    assert third.exit_code == 0


def test_clean_dir_dry_run_writes_only_batch_report(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    out = tmp_path / "out"
    write_doc(raw, "a.md", "增长不是更多流量，而是更高质量的转化闭环。")

    result = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out), "--dry-run"])

    report = json.loads((out / "batch_report.json").read_text(encoding="utf-8"))
    assert result.exit_code == 0
    assert report["dry_run"] is True
    assert report["processed_count"] == 1
    assert not list(out.glob("doc_*"))


def test_clean_dir_limit_sample_profile_and_report_stats(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    out = tmp_path / "out"
    for index in range(5):
        write_doc(
            raw, f"{index}.md", f"# 文档 {index}\n\n增长不是更多流量，而是更高质量的转化闭环。"
        )
    write_doc(raw, "noise.txt", "扫码添加微信，回复 666 领取资料包。")

    limited = runner.invoke(
        app,
        ["clean-dir", str(raw), "--out", str(out), "--limit", "2", "--profile", "balanced"],
    )
    report = json.loads((out / "batch_report.json").read_text(encoding="utf-8"))

    assert limited.exit_code == 0
    assert report["profile"] == "balanced"
    assert report["processed_count"] == 2
    assert report["file_types"][".md"] == 2
    assert "quality_score_distribution" in report
    assert "average_chunk_length" in report

    sample_out = tmp_path / "sample-out"
    sampled = runner.invoke(app, ["clean-dir", str(raw), "--out", str(sample_out), "--sample", "3"])
    sample_report = json.loads((sample_out / "batch_report.json").read_text(encoding="utf-8"))

    assert sampled.exit_code == 0
    assert sample_report["processed_count"] == 3


def test_profile_changes_pure_marketing_threshold_without_keyword_deleting_body():
    pure_marketing = (
        "添加我的微信领取完整资料包，里面有书单、清单、打卡表、福利海报、群内通知、"
        "往期活动记录、每周更新提醒、社群活动安排和线下见面提醒，想要的朋友直接来找我，"
        "错过就等下一次开放。"
    )
    body_with_same_keyword = (
        "添加企业微信不是为了骚扰用户，而是为了让咨询、转化、交付和复购动作在同一条链路中沉淀。"
    )

    conservative = CleaningPipeline.default().run_text(pure_marketing)
    balanced_pipeline = apply_profile(CleaningPipeline.default(), "balanced")
    balanced = balanced_pipeline.run_text(pure_marketing)
    aggressive_pipeline = apply_profile(CleaningPipeline.default(), "aggressive")
    aggressive_body = aggressive_pipeline.run_text(body_with_same_keyword)

    assert len(pure_marketing) > 80
    assert conservative.manifest.dropped_segments == 0
    assert balanced.manifest.dropped_segments == 1
    assert aggressive_body.manifest.dropped_segments == 0
    assert aggressive_body.chunks


def test_validate_batch_detects_all_output_dirs(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    out = tmp_path / "out"
    write_doc(raw, "a.md", "增长不是更多流量，而是更高质量的转化闭环。")

    clean = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out)])
    validate = runner.invoke(app, ["validate-batch", str(out)])

    assert clean.exit_code == 0
    assert validate.exit_code == 0
    assert "valid batch" in validate.output


def test_export_for_vector_defaults_to_importable_chunks_and_supports_include_status(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    out = tmp_path / "out"
    vector_default = tmp_path / "vector_default.jsonl"
    vector_review = tmp_path / "vector_review.jsonl"
    write_doc(raw, "claim.md", "增长不是更多流量，而是更高质量的转化闭环。")
    write_doc(raw, "review.md", "大家看这里，这个图左边就是我们要关注的重点。")

    clean = runner.invoke(app, ["clean-dir", str(raw), "--out", str(out)])
    exported_default = runner.invoke(
        app, ["export-for-vector", str(out), "--out", str(vector_default)]
    )
    exported_review = runner.invoke(
        app,
        [
            "export-for-vector",
            str(out),
            "--out",
            str(vector_review),
            "--include-status",
            "review_chunk",
        ],
    )

    default_rows = [
        json.loads(line) for line in vector_default.read_text(encoding="utf-8").splitlines()
    ]
    review_rows = [
        json.loads(line) for line in vector_review.read_text(encoding="utf-8").splitlines()
    ]

    assert clean.exit_code == 0
    assert exported_default.exit_code == 0
    assert {row["chunk_status"] for row in default_rows} <= {"import_chunk", "import_short"}
    assert exported_review.exit_code == 0
    assert {row["chunk_status"] for row in review_rows} == {"review_chunk"}
