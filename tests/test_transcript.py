from pathlib import Path

from rag_cleaner_cn.core.enums import ChunkType, SourceType
from rag_cleaner_cn.core.pipeline import CleaningPipeline


def test_srt_loader_preserves_timestamp_speaker_and_transcript_chunk_type(tmp_path):
    source = tmp_path / "video.srt"
    source.write_text(
        """1
00:00:01,000 --> 00:00:04,200
讲师：嗯，我们今天呢，主要讲三个问题。

2
00:00:04,300 --> 00:00:08,000
讲师：第一个问题是用户是谁。""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(
        source,
        tmp_path / "output",
        source_type=SourceType.VIDEO_TRANSCRIPT,
    )

    chunk = result.chunks[0]
    assert chunk.start_time == "00:00:01.000"
    assert chunk.end_time == "00:00:08.000"
    assert chunk.speaker == "讲师"
    assert chunk.chunk_type == ChunkType.TRANSCRIPT
    assert "嗯" not in chunk.embedding_text_main
    assert "主要讲三个问题" in chunk.embedding_text_main


def test_transcript_fixture_exists_for_video_coverage():
    assert Path("tests/fixtures/transcript_noise.srt").exists()
