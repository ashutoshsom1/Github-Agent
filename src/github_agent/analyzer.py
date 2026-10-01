import logging
from datetime import UTC, datetime

from github_agent.ai_intelligence import AIIntelligenceEngine
from github_agent.api_client import GitHubAPIClient
from github_agent.models import (
    ContributionDifficulty,
    ContributionStatus,
    IssueOpportunity,
    RepositoryAnalysis,
)

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """
    Evaluates repository contribution readiness using multi-factor heuristics
    and AI-assisted architectural reasoning.
    """

    def __init__(self, api_client: GitHubAPIClient | None = None, enable_ai: bool = True):
        self.api_client = api_client or GitHubAPIClient()
        self.own_api_client = api_client is None
        self.ai_engine = AIIntelligenceEngine() if enable_ai else None

    async def analyze_repository(self, repo_data: dict) -> RepositoryAnalysis:
        """Analyze a repository dictionary for contribution readiness."""
        details = await self.api_client.get_repository_details(repo_data)
        repo = details["repo"]
        issues = details["issues"]
        commits = details["commits"]
        contributors = details["contributors"]
        community = details["community"]

        analysis = await self._perform_analysis(repo, issues, commits, contributors, community)
        return analysis

    async def _perform_analysis(
        self,
        repo: dict,
        issues: list[dict],
        commits: list[dict],
        contributors: list[dict],
        community: dict,
    ) -> RepositoryAnalysis:
        owner = repo["owner"]["login"]
        name = repo["name"]
        full_name = repo.get("full_name", f"{owner}/{name}")

        # Check documentation files
        community_files = community.get("files", {})
        has_contributing = bool(community_files.get("contributing"))
        has_coc = bool(community_files.get("code_of_conduct"))
        has_issue_template = bool(community_files.get("issue_template"))
        has_pull_template = bool(community_files.get("pull_request_template"))

        # Fallback to file checks if community profile was incomplete
        if not has_contributing:
            has_contributing = await self.api_client.check_file_exists(
                owner, name, "CONTRIBUTING.md"
            )
        if not has_coc:
            has_coc = await self.api_client.check_file_exists(owner, name, "CODE_OF_CONDUCT.md")

        # Parse dates
        pushed_at_str = (
            repo.get("pushed_at") or repo.get("updated_at") or datetime.now(UTC).isoformat()
        )
        try:
            last_activity = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
        except Exception:
            last_activity = datetime.now(UTC)

        # Activity calculations
        now = datetime.now(UTC)
        days_since_activity = (now - last_activity).days

        # Issue mining
        good_first_issues = []
        help_wanted_issues = []
        for issue in issues:
            label_names = [lbl.get("name", "").lower() for lbl in issue.get("labels", [])]
            if any("good" in l and "first" in l for l in label_names) or "beginner" in label_names:
                good_first_issues.append(issue)
            elif (
                any("help" in l and "wanted" in l for l in label_names)
                or "up-for-grabs" in label_names
            ):
                help_wanted_issues.append(issue)

        # Calculate multi-factor contribution score
        score = 0.0
        # 1. Community & Documentation Standards (Max 30)
        if has_contributing:
            score += 15.0
        if has_coc:
            score += 5.0
        if has_issue_template:
            score += 5.0
        if has_pull_template:
            score += 5.0

        # 2. Issue Landscape & Opportunity (Max 25)
        if good_first_issues:
            score += min(len(good_first_issues) * 4.0, 15.0)
        if help_wanted_issues:
            score += min(len(help_wanted_issues) * 2.5, 10.0)

        # 3. Maintainer Velocity & Commits (Max 25)
        recent_commits_count = len(commits)
        if days_since_activity <= 7:
            score += 12.0
        elif days_since_activity <= 30:
            score += 8.0
        elif days_since_activity <= 90:
            score += 4.0

        if recent_commits_count >= 15:
            score += 13.0
        elif recent_commits_count >= 5:
            score += 8.0
        elif recent_commits_count >= 1:
            score += 4.0

        # 4. Repo Health & License (Max 20)
        if repo.get("license") and repo["license"].get("spdx_id") not in ("NOASSERTION", None):
            score += 8.0
        if len(contributors) >= 5:
            score += 7.0
        if repo.get("open_issues_count", 0) > 0:
            score += 5.0

        score = max(0.0, min(100.0, round(score, 1)))

        # Status classification
        is_archived = repo.get("archived", False)
        if is_archived or days_since_activity > 180:
            status = ContributionStatus.ARCHIVED_INACTIVE
        elif score >= 70.0 and (has_contributing or good_first_issues):
            status = ContributionStatus.ACTIVELY_ACCEPTING
        elif score >= 45.0:
            status = ContributionStatus.LIMITED_SCOPE
        else:
            status = ContributionStatus.NOT_ACCEPTING

        # Maintainer response velocity
        if days_since_activity <= 3:
            response_time = "Within 24-48 hours"
            maintainer_activity = "Very High"
        elif days_since_activity <= 14:
            response_time = "Within 3-5 days"
            maintainer_activity = "High"
        elif days_since_activity <= 45:
            response_time = "Within 1-2 weeks"
            maintainer_activity = "Moderate"
        else:
            response_time = "Slow / Stale (> 1 month)"
            maintainer_activity = "Low"

        # Setup complexity estimation based on language and size
        lang = repo.get("language") or "General"
        size_kb = repo.get("size", 0)
        if size_kb > 200000 or lang in ("C++", "Rust", "Java"):
            setup_complexity = "Complex (Enterprise Monorepo)"
        elif size_kb > 40000 or lang in ("TypeScript", "Go", "Python"):
            setup_complexity = "Medium (Standard Dependencies)"
        else:
            setup_complexity = "Low (Quick Local Setup)"

        # Tech stack detection
        topics = repo.get("topics", [])
        tech_stack = [lang] if lang != "General" else []
        tech_stack.extend([t for t in topics if t.lower() not in [lang.lower()]])

        # Format mined issue opportunities
        opportunities = []
        for raw_issue in (good_first_issues + help_wanted_issues)[:5]:
            lbls = [l.get("name", "") for l in raw_issue.get("labels", [])]
            is_beginner = any("good" in l.lower() or "beginner" in l.lower() for l in lbls)
            diff = (
                ContributionDifficulty.BEGINNER
                if is_beginner
                else ContributionDifficulty.INTERMEDIATE
            )

            opp = IssueOpportunity(
                number=raw_issue["number"],
                title=raw_issue["title"],
                url=raw_issue["html_url"],
                labels=lbls,
                created_at=raw_issue.get("created_at", ""),
                comments_count=raw_issue.get("comments", 0),
                difficulty=diff,
            )
            opportunities.append(opp)

        analysis = RepositoryAnalysis(
            name=name,
            full_name=full_name,
            description=repo.get("description") or "No description provided",
            url=repo.get("html_url", f"https://github.com/{full_name}"),
            stars=repo.get("stargazers_count", 0),
            forks=repo.get("forks_count", 0),
            language=lang,
            license=repo.get("license", {}).get("spdx_id") if repo.get("license") else None,
            contribution_status=status,
            contribution_score=score,
            last_activity=last_activity,
            open_issues=repo.get("open_issues_count", 0),
            good_first_issues=len(good_first_issues),
            help_wanted_issues=len(help_wanted_issues),
            recent_commits=recent_commits_count,
            contributors_count=len(contributors),
            has_contributing_guide=has_contributing,
            has_code_of_conduct=has_coc,
            has_issue_templates=has_issue_template,
            has_pr_templates=has_pull_template,
            response_time_estimate=response_time,
            tech_stack=tech_stack[:8],
            setup_complexity=setup_complexity,
            maintainer_activity=maintainer_activity,
            opportunities=opportunities,
        )

        # AI Insights generation
        if self.ai_engine:
            try:
                analysis.ai_insights = await self.ai_engine.generate_repository_insights(analysis)
            except Exception as e:
                logger.warning(f"Failed to generate AI insights for {full_name}: {e}")

        return analysis
