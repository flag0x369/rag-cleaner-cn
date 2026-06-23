from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from rag_cleaner_cn.core.batch import (
    apply_profile,
    export_for_vector,
    run_clean_dir_batch,
    validate_batch,
)
from rag_cleaner_cn.core.enums import SourceType
from rag_cleaner_cn.core.errors import RagCleanerError
from rag_cleaner_cn.core.pipeline import CleaningPipeline
from rag_cleaner_cn.eval.acceptance import acceptance_checks, validate_output_dir
from rag_cleaner_cn.export.jsonl_exporter import write_jsonl

app = typer.Typer(
    help="Conservative Chinese document cleaner and RAG chunk exporter.",
    no_args_is_help=True,
)
console = Console()


@app.command("clean")
def clean_file(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path("output"),
    source_type: Annotated[str | None, typer.Option("--source-type")] = None,
    config: Annotated[Path | None, typer.Option("--config", exists=True, readable=True)] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Cleaning profile: conservative, balanced, aggressive."),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Overwrite an existing document output directory."),
    ] = False,
) -> None:
    """Clean a single source file and export all output artifacts."""

    pipeline = _build_pipeline(config, profile)
    try:
        result = pipeline.run_file(
            input_path,
            out,
            source_type=_source_type(source_type),
            overwrite=overwrite,
        )
    except (RagCleanerError, ValueError) as exc:
        console.print(f"[red]error[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]exported[/green] {result.output_dir}")
    console.print(
        f"chunks={result.manifest.chunk_count} dropped={result.manifest.dropped_segments} "
        f"review={result.manifest.review_segments} quality={result.manifest.quality_score}"
    )


@app.command("clean-dir")
def clean_dir(
    input_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path("output"),
    config: Annotated[Path | None, typer.Option("--config", exists=True, readable=True)] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Cleaning profile: conservative, balanced, aggressive."),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Overwrite existing document output directories."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Only write batch_report.json; do not write doc outputs."),
    ] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1)] = None,
    sample: Annotated[int | None, typer.Option("--sample", min=1)] = None,
) -> None:
    """Clean every supported file in a directory."""

    pipeline = _build_pipeline(config, profile)
    try:
        report = run_clean_dir_batch(
            pipeline,
            input_dir,
            out,
            overwrite=overwrite,
            dry_run=dry_run,
            limit=limit,
            sample=sample,
        )
    except (RagCleanerError, ValueError) as exc:
        console.print(f"[red]error[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]batch report[/green] {out / 'batch_report.json'}")
    console.print(
        f"processed={report['processed_count']} candidates={report['total_candidates']} "
        f"dry_run={report['dry_run']} profile={report['profile']}"
    )


@app.command("chunk")
def chunk_clean_markdown(
    clean_markdown: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    out: Annotated[Path, typer.Option("--out", "-o", help="JSONL output path.")] = Path(
        "chunks.jsonl"
    ),
    config: Annotated[Path | None, typer.Option("--config", exists=True, readable=True)] = None,
) -> None:
    """Generate chunks from an existing clean markdown file."""

    pipeline = CleaningPipeline.from_config_file(config) if config else CleaningPipeline.default()
    text = clean_markdown.read_text(encoding="utf-8")
    result = pipeline.run_text(
        text,
        metadata={"title": clean_markdown.stem, "source_type": SourceType.MARKDOWN.value},
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(out, result.chunks)
    console.print(f"[green]wrote[/green] {out}")


@app.command("validate")
def validate(
    output_doc_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
) -> None:
    """Validate exported files for one processed document."""

    errors = validate_output_dir(output_doc_dir)
    if errors:
        for error in errors:
            console.print(f"[red]error[/red] {error}")
        raise typer.Exit(1)
    console.print("[green]valid[/green]")


@app.command("validate-batch")
def validate_batch_command(
    output_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
) -> None:
    """Validate every document output directory under a batch output directory."""

    result = validate_batch(output_dir)
    if not result["valid"]:
        for doc_dir, errors in result["errors"].items():
            for error in errors:
                console.print(f"[red]error[/red] {doc_dir}: {error}")
        raise typer.Exit(1)
    console.print(f"[green]valid batch[/green] checked={result['checked_count']}")


@app.command("acceptance")
def acceptance(
    output_doc_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
) -> None:
    """Run lightweight acceptance checks for one processed document."""

    issues = acceptance_checks(output_doc_dir)
    if issues:
        for issue in issues:
            console.print(f"[red]issue[/red] {issue}")
        raise typer.Exit(1)
    console.print("[green]accepted[/green]")


@app.command("export-for-vector")
def export_for_vector_command(
    batch_output_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Vector import JSONL output path."),
    ] = Path("vector_import.jsonl"),
    include_status: Annotated[
        list[str] | None,
        typer.Option(
            "--include-status",
            help="Chunk status to include. Repeat to include multiple statuses.",
        ),
    ] = None,
) -> None:
    """Collect importable chunks from a batch output directory into one JSONL file."""

    count = export_for_vector(
        batch_output_dir,
        out,
        include_status=set(include_status) if include_status else None,
    )
    console.print(f"[green]wrote[/green] {out} chunks={count}")


def _build_pipeline(config: Path | None, profile: str | None) -> CleaningPipeline:
    pipeline = CleaningPipeline.from_config_file(config) if config else CleaningPipeline.default()
    return apply_profile(pipeline, profile)


def _source_type(value: str | None) -> SourceType | None:
    if not value:
        return None
    try:
        return SourceType(value)
    except ValueError as exc:
        valid = ", ".join(item.value for item in SourceType)
        raise typer.BadParameter(f"unknown source type {value!r}; valid: {valid}") from exc
