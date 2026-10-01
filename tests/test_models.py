from datetime import UTC, datetime

from github_agent.models import (
    ContributionDifficulty,
    ContributionStatus,
    PRContributionPlan,
    RepositoryAnalysis,
)


def test_repository_analysis_model():
    repo = RepositoryAnalysis(
        name="test-repo",
        full_name="owner/test-repo",
        description="A great open source repo",
        url="https://github.com/owner/test-repo",
        stars=1500,
        forks=250,
        language="Python",
        contribution_status=ContributionStatus.ACTIVELY_ACCEPTING,
        contribution_score=85.5,
        last_activity=datetime.now(UTC),
        good_first_issues=4,
    )
    assert repo.stars == 1500
    assert repo.contribution_status == ContributionStatus.ACTIVELY_ACCEPTING
    assert repo.contribution_score == 85.5

    dumped = repo.model_dump(mode="json")
    assert dumped["name"] == "test-repo"
    assert dumped["contribution_status"] == "actively_accepting"


def test_pr_contribution_plan_model():
    plan = PRContributionPlan(
        repository="owner/repo",
        issue_number=42,
        issue_title="Fix memory leak in background worker",
        difficulty=ContributionDifficulty.INTERMEDIATE,
        prerequisites=["Python 3.11", "Docker"],
        implementation_steps=["Identify circular ref", "Patch weakref", "Run pytest"],
        files_to_modify=["src/worker.py"],
        testing_strategy=["Unit test with tracemalloc"],
        estimated_effort_hours=3.5,
    )
    assert plan.issue_number == 42
    assert plan.difficulty == ContributionDifficulty.INTERMEDIATE
    assert len(plan.implementation_steps) == 3
