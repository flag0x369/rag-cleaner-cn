from typer.testing import CliRunner

from rag_cleaner_cn.cli import app


def test_readme_documented_cli_commands_are_registered():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in [
        "clean",
        "clean-dir",
        "chunk",
        "validate",
        "validate-batch",
        "acceptance",
        "export-for-vector",
    ]:
        assert command in result.output
