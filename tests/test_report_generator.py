from datetime import UTC, datetime

from github_agent.models import ContributionStatus, RepositoryAnalysis
from github_agent.report_generator import ReportGenerator


def test_markdown_and_json_report_generation():
    generator = ReportGenerator()

    repo = RepositoryAnalysis(
        name="octo-agent",
        full_name="ashutoshsom1/octo-agent",
        description="Autonomous AI Agent",
        url="https://github.com/ashutoshsom1/octo-agent",
        stars=1200,
        forks=150,
        language="Python",
        contribution_status=ContributionStatus.ACTIVELY_ACCEPTING,
        contribution_score=88.0,
        last_activity=datetime.now(UTC),
        good_first_issues=3,
        tech_stack=["Python", "FastAPI", "Docker"],
    )

    analyses = [repo]

    reports = generator.generate_reports(analyses)
    assert reports["total_repositories"] == 1
    assert "summary" in reports

    md_report = generator.generate_markdown_report(analyses)
    assert "GitHub Agent AI" in md_report
    assert "octo-agent" in md_report
    assert "88.0/100" in md_report

    json_report = generator.generate_json_report(analyses)
    assert '"total_repositories": 1' in json_report
    assert '"full_name": "ashutoshsom1/octo-agent"' in json_report
