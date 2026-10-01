import asyncio
import os
import sys

import click
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure environment variables are loaded
load_dotenv()

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from github_agent import (
    AIIntelligenceEngine,
    ContributionStatus,
    GitHubAnalysisAgent,
    GitHubMCPServer,
)

console = Console()


@click.group()
@click.version_option(version="2.0.0", prog_name="github-agent")
def cli():
    """
    GitHub Agent AI (OctoAgent)

    Autonomous Open-Source Intelligence & Contribution Agent.
    Evaluates repositories, mines issues, generates PR roadmaps, and runs as an MCP server.
    """


@cli.command("scan")
@click.option(
    "--keyword",
    "-k",
    required=True,
    help="Keyword or topic to search (e.g. 'machine learning', 'fastapi')",
)
@click.option("--max-repos", "-m", default=10, help="Maximum repositories to analyze (default: 10)")
@click.option("--min-stars", "-s", default=100, help="Minimum stars filter (default: 100)")
@click.option(
    "--email", "-e", default=None, help="Optional email address to send comprehensive HTML report"
)
@click.option(
    "--output", "-o", default=None, help="Save report to Markdown file path (e.g. report.md)"
)
@click.option(
    "--json-out", "-j", default=None, help="Save raw results to JSON file path (e.g. results.json)"
)
def scan(
    keyword: str,
    max_repos: int,
    min_stars: int,
    email: str | None,
    output: str | None,
    json_out: str | None,
):
    """Scan and analyze top repositories by keyword."""
    console.print(
        Panel.fit(
            f"[bold blue]🐙 GitHub Agent AI: Repository Scanner[/bold blue]\n"
            f"[cyan]Keyword:[/cyan] {keyword} | [cyan]Max Repos:[/cyan] {max_repos} | [cyan]Min Stars:[/cyan] {min_stars}",
            box=box.ROUNDED,
        )
    )

    async def _run():
        agent = GitHubAnalysisAgent()
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(
                f"Searching and evaluating repositories for '{keyword}'...", total=None
            )
            analyses = await agent.analyze_repositories(
                keyword=keyword, recipient_email=email, max_repos=max_repos, min_stars=min_stars
            )
            progress.update(task, completed=True)

        if not analyses:
            console.print("[yellow]⚠️ No repositories found matching the criteria.[/yellow]")
            return

        # Render Rich Table
        table = Table(
            title=f"Repository Contribution Analysis ({len(analyses)} evaluated)", box=box.ROUNDED
        )
        table.add_column("Rank", justify="center", style="dim")
        table.add_column("Repository", style="bold cyan")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Language", style="magenta")
        table.add_column("Score", justify="center")
        table.add_column("Status", style="bold")
        table.add_column("Good First Issues", justify="center")
        table.add_column("Maintainer Velocity")

        status_colors = {
            ContributionStatus.ACTIVELY_ACCEPTING: "[bold green]Actively Accepting[/bold green]",
            ContributionStatus.LIMITED_SCOPE: "[bold yellow]Limited Scope[/bold yellow]",
            ContributionStatus.NOT_ACCEPTING: "[bold red]Not Accepting[/bold red]",
            ContributionStatus.ARCHIVED_INACTIVE: "[dim]Archived/Stale[/dim]",
        }

        for idx, repo in enumerate(analyses, 1):
            score_color = (
                "green"
                if repo.contribution_score >= 70
                else "yellow"
                if repo.contribution_score >= 45
                else "red"
            )
            table.add_row(
                str(idx),
                repo.full_name,
                f"{repo.stars:,}",
                repo.language or "Unknown",
                f"[{score_color}]{repo.contribution_score}[/{score_color}]",
                status_colors.get(repo.contribution_status, repo.contribution_status.value),
                str(repo.good_first_issues),
                repo.maintainer_activity,
            )

        console.print(table)

        # File Exports
        reports = agent.report_generator.generate_reports(analyses)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(reports["markdown_summary"])
            console.print(f"[green]✅ Markdown report saved to {output}[/green]")

        if json_out:
            with open(json_out, "w", encoding="utf-8") as f:
                f.write(agent.report_generator.generate_json_report(analyses))
            console.print(f"[green]✅ JSON data exported to {json_out}[/green]")

        if email:
            console.print(f"[cyan]📧 Report dispatch to {email} completed.[/cyan]")

    asyncio.run(_run())


@cli.command("analyze")
@click.option(
    "--repo", "-r", required=True, help="Repository in 'owner/repo' format (e.g. 'astral-sh/uv')"
)
def analyze(repo: str):
    """Deep-dive architectural and contribution analysis on a single repository."""
    if "/" not in repo:
        console.print("[red]❌ Error: Repository must be in 'owner/repo' format.[/red]")
        return

    owner, repo_name = repo.split("/", 1)
    console.print(f"[bold blue]🔍 Performing deep inspection on {owner}/{repo_name}...[/bold blue]")

    async def _run():
        agent = GitHubAnalysisAgent()
        analysis = await agent.analyze_single_repository(owner, repo_name)
        if not analysis:
            console.print(f"[red]❌ Repository {repo} not found or inaccessible.[/red]")
            return

        console.print(
            Panel(
                f"[bold]{analysis.full_name}[/bold]\n"
                f"[dim]{analysis.description}[/dim]\n\n"
                f"⭐ Stars: {analysis.stars:,} | 🍴 Forks: {analysis.forks:,} | 💻 Language: {analysis.language}\n"
                f"📊 Contribution Score: [bold green]{analysis.contribution_score}/100[/bold green] ({analysis.contribution_status.value})\n"
                f"⏱️ Maintainer Response: {analysis.response_time_estimate} | Commits (30d): {analysis.recent_commits}\n"
                f"📝 Docs: CONTRIBUTING={analysis.has_contributing_guide} | CodeOfConduct={analysis.has_code_of_conduct}\n\n"
                f"[bold cyan]🤖 AI Architectural Insights:[/bold cyan]\n"
                f"{analysis.ai_insights or 'AI reasoning engine operating in deterministic mode.'}",
                title="Repository Diagnostic Profile",
                box=box.ROUNDED,
            )
        )

        if analysis.opportunities:
            console.print("\n[bold green]🎯 Mined Contribution Opportunities:[/bold green]")
            for opp in analysis.opportunities:
                console.print(
                    f"  • [yellow]#{opp.number}[/yellow] {opp.title} ([dim]{opp.difficulty.value}[/dim])"
                )
                console.print(f"    URL: {opp.url}")

    asyncio.run(_run())


@cli.command("plan-pr")
@click.option("--repo", "-r", required=True, help="Repository in 'owner/repo' format")
@click.option("--title", "-t", required=True, help="Issue title or description of bug/feature")
@click.option("--body", "-b", default="", help="Issue description / body snippet")
def plan_pr(repo: str, title: str, body: str):
    """Synthesize a step-by-step PR implementation plan for a specific issue."""
    console.print(f"[bold blue]🛠️ Formulating PR Implementation Roadmap for {repo}...[/bold blue]")

    async def _run():
        ai = AIIntelligenceEngine()
        plan = await ai.generate_pr_plan(repository=repo, issue_title=title, issue_body=body)

        console.print(
            Panel(
                f"[bold cyan]Target Issue:[/bold cyan] {plan.issue_title}\n"
                f"[cyan]Estimated Effort:[/cyan] {plan.estimated_effort_hours} hours | [cyan]Difficulty:[/cyan] {plan.difficulty.value.upper()}\n\n"
                f"[bold]Prerequisites:[/bold]\n"
                + "\n".join(f"  - {p}" for p in plan.prerequisites)
                + "\n\n"
                "[bold]Implementation Roadmap:[/bold]\n"
                + "\n".join(
                    f"  {idx}. {step}" for idx, step in enumerate(plan.implementation_steps, 1)
                )
                + "\n\n"
                "[bold]Testing Strategy:[/bold]\n"
                + "\n".join(f"  - {t}" for t in plan.testing_strategy),
                title="🚀 Pull Request Contribution Blueprint",
                box=box.ROUNDED,
            )
        )

    asyncio.run(_run())


@cli.command("mcp")
def mcp():
    """Launch the Model Context Protocol (MCP) server over standard I/O."""
    server = GitHubMCPServer()
    asyncio.run(server.run_stdio())


def main():
    cli()


if __name__ == "__main__":
    main()
