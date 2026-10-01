"""
GitHub Agent AI (OctoAgent)
Autonomous Open-Source Intelligence & Contribution Agent.
"""

from github_agent.ai_intelligence import AIIntelligenceEngine
from github_agent.analyzer import RepositoryAnalyzer
from github_agent.api_client import GitHubAPIClient
from github_agent.email_sender import EmailSender
from github_agent.mcp_server import GitHubMCPServer
from github_agent.models import (
    BatchAnalysisReport,
    ContributionDifficulty,
    ContributionStatus,
    IssueOpportunity,
    PRContributionPlan,
    RepositoryAnalysis,
)
from github_agent.report_generator import ReportGenerator


class GitHubAnalysisAgent:
    """
    Main orchestrator for discovering repositories, analyzing contribution viability,
    mining issues, generating PR roadmaps, and producing multi-format reports.
    """

    def __init__(self, token: str | None = None, enable_ai: bool = True):
        self.api_client = GitHubAPIClient(token=token)
        self.analyzer = RepositoryAnalyzer(api_client=self.api_client, enable_ai=enable_ai)
        self.report_generator = ReportGenerator()
        self.email_sender = EmailSender()
        self.ai_engine = AIIntelligenceEngine() if enable_ai else None

    async def __aenter__(self):
        await self.api_client._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.api_client.close()

    async def analyze_repositories(
        self,
        keyword: str,
        recipient_email: str | None = None,
        max_repos: int | None = None,
        min_stars: int | None = None,
    ) -> list[RepositoryAnalysis]:
        """Analyze top repositories matching keyword and optionally distribute reports."""
        await self.api_client._ensure_session()
        try:
            repositories = await self.api_client.search_repositories(
                keyword=keyword, max_repos=max_repos, min_stars=min_stars
            )

            analyzed_repos: list[RepositoryAnalysis] = []
            for repo in repositories:
                analysis = await self.analyzer.analyze_repository(repo)
                analyzed_repos.append(analysis)

            reports = self.report_generator.generate_reports(analyzed_repos)

            # Send email only if recipient provided and configured
            if recipient_email:
                await self.email_sender.send_reports(reports, recipient_email)

            return analyzed_repos

        finally:
            await self.api_client.close()

    async def analyze_single_repository(self, owner: str, repo: str) -> RepositoryAnalysis | None:
        """Deep dive analysis on a single repository."""
        await self.api_client._ensure_session()
        try:
            repo_data = await self.api_client.get_repository(owner, repo)
            if not repo_data or "name" not in repo_data:
                return None
            return await self.analyzer.analyze_repository(repo_data)
        finally:
            await self.api_client.close()


__all__ = [
    "AIIntelligenceEngine",
    "BatchAnalysisReport",
    "ContributionDifficulty",
    "ContributionStatus",
    "EmailSender",
    "GitHubAPIClient",
    "GitHubAnalysisAgent",
    "GitHubMCPServer",
    "IssueOpportunity",
    "PRContributionPlan",
    "ReportGenerator",
    "RepositoryAnalysis",
    "RepositoryAnalyzer",
]
