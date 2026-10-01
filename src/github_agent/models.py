from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContributionStatus(str, Enum):
    ACTIVELY_ACCEPTING = "actively_accepting"
    LIMITED_SCOPE = "limited_scope"
    NOT_ACCEPTING = "not_accepting"
    ARCHIVED_INACTIVE = "archived_inactive"


class ContributionDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class IssueOpportunity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int = Field(description="Issue number")
    title: str = Field(description="Issue title")
    url: str = Field(description="Direct HTML URL to issue")
    labels: list[str] = Field(default_factory=list, description="Labels on the issue")
    created_at: str = Field(description="Creation timestamp")
    comments_count: int = Field(default=0, description="Number of comments")
    difficulty: ContributionDifficulty = Field(
        default=ContributionDifficulty.BEGINNER, description="Estimated difficulty"
    )
    suggested_approach: str | None = Field(
        default=None, description="AI-generated PR implementation outline"
    )


class PRContributionPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repository: str = Field(description="Owner/Repo identifier")
    issue_number: int = Field(description="Target issue number")
    issue_title: str = Field(description="Issue title")
    difficulty: ContributionDifficulty = Field(default=ContributionDifficulty.BEGINNER)
    prerequisites: list[str] = Field(
        default_factory=list, description="Local environment and tooling requirements"
    )
    implementation_steps: list[str] = Field(
        default_factory=list, description="Step-by-step code change roadmap"
    )
    files_to_modify: list[str] = Field(
        default_factory=list, description="Likely target files and modules"
    )
    testing_strategy: list[str] = Field(
        default_factory=list, description="Unit and integration tests to add or run"
    )
    estimated_effort_hours: float = Field(default=2.0, description="Estimated hours to complete PR")


class RepositoryAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Repository name")
    full_name: str = Field(description="Owner and repository name")
    description: str | None = Field(default="", description="Repository description")
    url: str = Field(description="GitHub repository HTML URL")
    stars: int = Field(default=0, description="Star count")
    forks: int = Field(default=0, description="Forks count")
    language: str | None = Field(default="Unknown", description="Primary programming language")
    license: str | None = Field(default=None, description="License SPDX identifier")
    contribution_status: ContributionStatus = Field(
        description="Contribution status classification"
    )
    contribution_score: float = Field(
        ge=0.0, le=100.0, description="Contribution readiness score (0-100)"
    )
    last_activity: datetime = Field(description="Timestamp of last push or update")
    open_issues: int = Field(default=0, description="Total open issues")
    good_first_issues: int = Field(default=0, description="Count of good-first-issues")
    help_wanted_issues: int = Field(default=0, description="Count of help-wanted issues")
    recent_commits: int = Field(default=0, description="Commit count in last 30 days")
    contributors_count: int = Field(default=0, description="Active contributors count")
    has_contributing_guide: bool = Field(
        default=False, description="Whether CONTRIBUTING.md exists"
    )
    has_code_of_conduct: bool = Field(
        default=False, description="Whether CODE_OF_CONDUCT.md exists"
    )
    has_issue_templates: bool = Field(default=False, description="Whether issue templates exist")
    has_pr_templates: bool = Field(
        default=False, description="Whether pull request templates exist"
    )
    response_time_estimate: str = Field(
        default="Unknown", description="Maintainer response velocity estimate"
    )
    tech_stack: list[str] = Field(
        default_factory=list, description="Detected technology stack and frameworks"
    )
    setup_complexity: str = Field(
        default="Medium", description="Estimated development environment setup complexity"
    )
    maintainer_activity: str = Field(default="Moderate", description="Maintainer review velocity")
    ai_insights: str | None = Field(
        default=None, description="AI-generated architectural & contribution briefing"
    )
    opportunities: list[IssueOpportunity] = Field(
        default_factory=list, description="Mined beginner and help-wanted issues"
    )


class BatchAnalysisReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    keyword: str
    total_repositories: int
    generated_at: str
    summary: dict[str, Any]
    repositories: list[RepositoryAnalysis]
