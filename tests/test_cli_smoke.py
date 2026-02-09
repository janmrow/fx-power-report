from __future__ import annotations

from typer.testing import CliRunner

from fxpower.cli import app


def test_cli_help_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "fxpower" in result.stdout
