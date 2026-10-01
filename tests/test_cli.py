from click.testing import CliRunner

from github_agent.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "GitHub Agent AI" in result.output
    assert "scan" in result.output
    assert "analyze" in result.output
    assert "plan-pr" in result.output
    assert "mcp" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output
