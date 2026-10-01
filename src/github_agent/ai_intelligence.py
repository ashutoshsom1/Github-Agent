import logging
import os

from config.settings import settings
from github_agent.models import (
    ContributionDifficulty,
    PRContributionPlan,
    RepositoryAnalysis,
)

logger = logging.getLogger(__name__)


class AIIntelligenceEngine:
    """
    AI Intelligence Engine supporting Anthropic Claude, OpenAI, and Heuristic Fallbacks.
    Provides repository architectural assessment, issue difficulty scoring, and PR roadmap generation.
    """

    def __init__(self):
        self.provider = settings.default_ai_provider
        self.anthropic_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = settings.ai_model
        self._init_clients()

    def _init_clients(self):
        self.anthropic_client = None
        self.openai_client = None

        if self.anthropic_key:
            try:
                import anthropic

                self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
                if self.provider == "auto":
                    self.provider = "anthropic"
            except ImportError:
                logger.warning(
                    "anthropic package not installed. Run `pip install anthropic` to enable Claude AI reasoning."
                )

        if not self.anthropic_client and self.openai_key:
            try:
                import openai

                self.openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
                if self.provider == "auto":
                    self.provider = "openai"
            except ImportError:
                logger.warning(
                    "openai package not installed. Run `pip install openai` to enable OpenAI reasoning."
                )

        if not self.anthropic_client and not self.openai_client:
            self.provider = "heuristic"

    async def generate_repository_insights(self, repo: RepositoryAnalysis) -> str:
        """Generate high-signal architectural and contribution insights."""
        prompt = (
            f"You are a Senior Principal Open-Source Software Architect. "
            f"Analyze the following GitHub repository metadata and provide a crisp 3-4 sentence technical briefing on its architectural health, maintainer velocity, and suitability for open-source contributions:\n"
            f"- Repository: {repo.full_name}\n"
            f"- Stars: {repo.stars:,} | Forks: {repo.forks:,} | Open Issues: {repo.open_issues}\n"
            f"- Primary Language: {repo.language} | Tech Stack: {', '.join(repo.tech_stack) if repo.tech_stack else 'Standard'}\n"
            f"- Contribution Score: {repo.contribution_score}/100 ({repo.contribution_status.value})\n"
            f"- Recent Commits (30d): {repo.recent_commits} | Good First Issues: {repo.good_first_issues}\n"
            f"- Community Assets: CONTRIBUTING={repo.has_contributing_guide}, CodeOfConduct={repo.has_code_of_conduct}, IssueTemplates={repo.has_issue_templates}\n\n"
            f"Format with bullet points covering: Architecture & Health, Contribution Barrier, and Recommended Next Steps."
        )

        if self.provider == "anthropic" and self.anthropic_client:
            try:
                resp = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=400,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text
            except Exception as e:
                logger.warning(
                    f"Anthropic API call failed: {e}. Falling back to heuristic insights."
                )

        elif self.provider == "openai" and self.openai_client:
            try:
                resp = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=400,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Falling back to heuristic insights.")

        # Heuristic Fallback
        return self._heuristic_repository_insights(repo)

    def _heuristic_repository_insights(self, repo: RepositoryAnalysis) -> str:
        velocity = (
            "High"
            if repo.recent_commits > 15
            else "Moderate"
            if repo.recent_commits > 3
            else "Low/Stale"
        )
        readiness = (
            "Excellent"
            if repo.contribution_score >= 75
            else "Moderate"
            if repo.contribution_score >= 50
            else "High Barrier"
        )

        guidance = (
            f"• Architecture & Velocity: Maintained in {repo.language} with {velocity} commit velocity ({repo.recent_commits} commits/30d) and {repo.open_issues} active issues.\n"
            f"• Contribution Readiness: {readiness} ({repo.contribution_score}/100). "
        )
        if repo.has_contributing_guide and repo.good_first_issues > 0:
            guidance += f"Welcoming environment with {repo.good_first_issues} beginner-friendly issues and structured CONTRIBUTING guidelines.\n"
        elif repo.good_first_issues == 0:
            guidance += "Lacks explicit beginner labels; contributors should focus on documentation or reproduction of recent bug reports.\n"
        else:
            guidance += "Community templates are partially missing; engage directly via issue discussions before submitting large PRs.\n"

        guidance += f"• Recommended Action: Clone repo, inspect {repo.language} test suite, and check issues matching your technical stack."
        return guidance

    async def generate_pr_plan(
        self,
        repository: str,
        issue_title: str,
        issue_body: str | None = None,
        language: str = "Python",
    ) -> PRContributionPlan:
        """Synthesize a step-by-step PR contribution plan for a specific issue."""
        body_snippet = (issue_body or "")[:500]
        prompt = (
            f"You are a Staff Software Engineer. Formulate a technical PR implementation roadmap for:\n"
            f"Repository: {repository} ({language})\n"
            f"Issue: {issue_title}\n"
            f"Details: {body_snippet}\n\n"
            f"Provide: 1) Difficulty level (Beginner, Intermediate, Advanced), 2) Prerequisites, 3) 3-4 Implementation Steps, 4) Testing strategy."
        )

        if self.provider == "anthropic" and self.anthropic_client:
            try:
                resp = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = resp.content[0].text
                return self._parse_pr_plan_response(repository, issue_title, text)
            except Exception as e:
                logger.warning(f"Claude PR planning failed: {e}. Using deterministic plan.")

        return self._heuristic_pr_plan(repository, issue_title, language)

    def _heuristic_pr_plan(
        self, repository: str, issue_title: str, language: str
    ) -> PRContributionPlan:
        is_doc = any(
            k in issue_title.lower() for k in ["doc", "readme", "typo", "guide", "example"]
        )
        is_bug = any(
            k in issue_title.lower() for k in ["fix", "bug", "error", "fail", "crash", "issue"]
        )

        difficulty = (
            ContributionDifficulty.BEGINNER if is_doc else ContributionDifficulty.INTERMEDIATE
        )
        prerequisites = [
            "Git & GitHub CLI installed",
            f"{language} runtime & development environment configured",
            f"Fork of {repository} with dependencies installed locally",
        ]

        if is_doc:
            steps = [
                "Locate relevant markdown documentation in docs/ or README.md",
                "Verify formatting and markdown linting standards",
                "Verify all external and relative markdown links",
                "Submit clean PR referencing this issue",
            ]
            files = ["README.md", "docs/*.md"]
            testing = ["Run markdown linter or local documentation preview"]
            effort = 1.0
        elif is_bug:
            steps = [
                "Reproduce the bug locally with a minimal failing unit test",
                "Trace root cause in core source modules",
                "Implement patch ensuring backwards compatibility",
                "Verify test suite passes without regressions",
            ]
            files = ["src/*", "tests/test_*.py"]
            testing = ["Execute local pytest / test suite", "Add dedicated regression test case"]
            effort = 3.5
        else:
            steps = [
                "Read CONTRIBUTING.md and existing architecture documentation",
                "Set up local development branch `feature/issue-resolution`",
                "Implement feature/enhancement following repo code style",
                "Run test suite and format code with project linters",
            ]
            files = ["src/*", "tests/*"]
            testing = ["Unit tests covering happy and edge-case paths"]
            effort = 2.5

        return PRContributionPlan(
            repository=repository,
            issue_number=1,
            issue_title=issue_title,
            difficulty=difficulty,
            prerequisites=prerequisites,
            implementation_steps=steps,
            files_to_modify=files,
            testing_strategy=testing,
            estimated_effort_hours=effort,
        )

    def _parse_pr_plan_response(
        self, repository: str, issue_title: str, text: str
    ) -> PRContributionPlan:
        # Fallback to heuristic parser if needed
        return PRContributionPlan(
            repository=repository,
            issue_number=1,
            issue_title=issue_title,
            difficulty=ContributionDifficulty.INTERMEDIATE,
            prerequisites=[
                "Git & local runtime environment configured",
                "Repository dependencies synced",
            ],
            implementation_steps=[
                line.strip("-• ")
                for line in text.split("\n")
                if line.strip().startswith(("-", "•", "1", "2", "3", "4"))
            ][:4],
            files_to_modify=["src/*", "tests/*"],
            testing_strategy=["Run automated test suite", "Verify regression tests pass"],
            estimated_effort_hours=2.5,
        )
