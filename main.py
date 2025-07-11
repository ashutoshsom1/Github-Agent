#!/usr/bin/env python3
"""
GitHub Repository Analysis Agent
Main script to run the analysis
"""

import asyncio
import sys
import os
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from github_agent import GitHubAnalysisAgent

console = Console()

@click.command()
@click.option('--keyword', '-k', required=True, help='Keyword to search repositories')
@click.option('--email', '-e', required=True, help='Email address to send reports')
@click.option('--max-repos', '-m', default=20, help='Maximum number of repositories to analyze')
@click.option('--min-stars', '-s', default=100, help='Minimum stars for repositories')
def main(keyword: str, email: str, max_repos: int, min_stars: int):
    """
    GitHub Repository Analysis Agent
    
    Analyzes top repositories for contribution opportunities and generates detailed reports.
    """
    
    console.print(f"[bold blue]🔍 GitHub Repository Analysis Agent[/bold blue]")
    console.print(f"[yellow]Keyword:[/yellow] {keyword}")
    console.print(f"[yellow]Email:[/yellow] {email}")
    console.print(f"[yellow]Max Repositories:[/yellow] {max_repos}")
    console.print(f"[yellow]Min Stars:[/yellow] {min_stars}")
    console.print()
    
    # Check environment variables
    if not check_environment():
        return
    
    # Update settings
    from config.settings import settings
    settings.max_repositories = max_repos
    settings.min_stars = min_stars
    
    # Run analysis
    asyncio.run(run_analysis(keyword, email))

def check_environment() -> bool:
    """Check if required environment variables are set"""
    required_vars = [
        'GITHUB_TOKEN',
        'EMAIL_HOST',
        'EMAIL_USER',
        'EMAIL_PASSWORD'
    ]
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        console.print("[bold red]❌ .env file not found![/bold red]")
        console.print("[yellow]Please create a .env file based on .env.example[/yellow]")
        return False
    
    console.print("[green]✅ .env file found, checking variables...[/green]")
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show partial value for confirmation (mask sensitive data)
            if 'PASSWORD' in var or 'TOKEN' in var:
                masked_value = '*' * len(value) if len(value) > 4 else '****'
                console.print(f"[green]✅ {var}:[/green] {masked_value}")
            else:
                console.print(f"[green]✅ {var}:[/green] {value}")
    
    if missing_vars:
        console.print("[bold red]❌ Missing required environment variables:[/bold red]")
        for var in missing_vars:
            console.print(f"  • {var}")
        console.print("\n[yellow]Please update your .env file with these variables.[/yellow]")
        return False
    
    console.print("[green]✅ All environment variables found![/green]")
    return True

async def run_analysis(keyword: str, email: str):
    """Run the repository analysis"""
    agent = GitHubAnalysisAgent()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Start analysis
        task = progress.add_task("Analyzing repositories...", total=None)
        
        try:
            analyses = await agent.analyze_repositories(keyword, email)
            
            progress.update(task, description="Analysis complete!")
            
            # Display summary
            display_summary(analyses)
            
        except Exception as e:
            console.print(f"[bold red]❌ Analysis failed: {str(e)}[/bold red]")
            raise

def display_summary(analyses):
    """Display analysis summary"""
    console.print("\n[bold green]✅ Analysis Complete![/bold green]")
    
    # Create summary table
    table = Table(title="Repository Analysis Summary")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")
    
    # Count by status
    from github_agent.analyzer import ContributionStatus
    
    status_counts = {}
    for analysis in analyses:
        status = analysis.contribution_status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    total = len(analyses)
    
    for status in ContributionStatus:
        count = status_counts.get(status, 0)
        percentage = (count / total * 100) if total > 0 else 0
        status_name = status.value.replace("_", " ").title()
        table.add_row(status_name, str(count), f"{percentage:.1f}%")
    
    console.print(table)
    
    # Show top repositories
    console.print("\n[bold cyan]⭐ Top Repositories by Contribution Score:[/bold cyan]")
    
    top_repos = sorted(analyses, key=lambda x: x.contribution_score, reverse=True)[:5]
    
    for i, repo in enumerate(top_repos, 1):
        status_emoji = {
            ContributionStatus.ACTIVELY_ACCEPTING: "✅",
            ContributionStatus.LIMITED_SCOPE: "⚠️",
            ContributionStatus.NOT_ACCEPTING: "❌",
            ContributionStatus.ARCHIVED_INACTIVE: "🗄️"
        }
        
        emoji = status_emoji.get(repo.contribution_status, "❓")
        console.print(f"  {i}. {emoji} [bold]{repo.full_name}[/bold] - Score: {repo.contribution_score}/100")
        console.print(f"     ⭐ {repo.stars:,} stars • 🍴 {repo.forks:,} forks • 🎯 {repo.good_first_issues} good first issues")

if __name__ == "__main__":
    main()
