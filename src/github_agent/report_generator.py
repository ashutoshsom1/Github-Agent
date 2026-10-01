import json
from datetime import datetime

from jinja2 import Template

from github_agent.models import ContributionStatus, RepositoryAnalysis


class ReportGenerator:
    """
    Generates multi-format reports (HTML, Markdown, JSON)
    for analyzed repositories and contribution opportunities.
    """

    def __init__(self):
        self.template = self._get_report_template()

    def generate_reports(self, analyses: list[RepositoryAnalysis]) -> dict:
        """Generate comprehensive reports for all analyzed repositories."""
        categorized = self._categorize_repositories(analyses)
        summary_report = self._generate_summary_report(analyses, categorized)

        individual_reports = []
        for analysis in analyses:
            individual_report = self._generate_individual_report(analysis)
            individual_reports.append(individual_report)

        markdown_report = self.generate_markdown_report(analyses)

        return {
            "summary": summary_report,
            "individual_reports": individual_reports,
            "markdown_summary": markdown_report,
            "total_repositories": len(analyses),
            "generated_at": datetime.now().isoformat(),
        }

    def generate_markdown_report(self, analyses: list[RepositoryAnalysis]) -> str:
        """Generate a clean, high-signal Markdown report."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        total = len(analyses)
        categorized = self._categorize_repositories(analyses)

        active = len(categorized["actively_accepting"])
        limited = len(categorized["limited_scope"])
        stale = len(categorized["not_accepting"]) + len(categorized["archived_inactive"])

        md = [
            "# 🐙 GitHub Agent AI: Repository Intelligence & Contribution Report",
            f"**Generated:** {now} | **Total Evaluated:** {total}\n",
            "## 📊 Executive Overview",
            "| Contribution Status | Repositories | Distribution |",
            "|---|---|---|",
            f"| 🟢 **Actively Accepting** | {active} | {(active / total * 100) if total else 0:.1f}% |",
            f"| 🟡 **Limited Scope** | {limited} | {(limited / total * 100) if total else 0:.1f}% |",
            f"| 🔴 **Not Accepting / Stale** | {stale} | {(stale / total * 100) if total else 0:.1f}% |\n",
            "---",
            "## 🏆 Top Contribution Opportunities\n",
        ]

        # Top repos sorted by score
        top_repos = sorted(analyses, key=lambda x: x.contribution_score, reverse=True)
        for idx, repo in enumerate(top_repos, 1):
            badge = (
                "🟢"
                if repo.contribution_status == ContributionStatus.ACTIVELY_ACCEPTING
                else "🟡"
                if repo.contribution_status == ContributionStatus.LIMITED_SCOPE
                else "🔴"
            )
            md.append(f"### {idx}. [{repo.full_name}]({repo.url}) {badge}")
            md.append(
                f"**Score:** `{repo.contribution_score}/100` | **Status:** {repo.contribution_status.value.replace('_', ' ').title()} | **Stars:** ⭐ {repo.stars:,} | **Language:** `{repo.language}`"
            )
            md.append(f"> {repo.description}\n")

            if repo.ai_insights:
                md.append(f"**🤖 Architectural & Contribution Insights:**\n{repo.ai_insights}\n")

            if repo.opportunities:
                md.append("**🎯 Actionable Entrypoint Issues:**")
                for opp in repo.opportunities:
                    md.append(
                        f"- [#{opp.number} {opp.title}]({opp.url}) (`{opp.difficulty.value}`)"
                    )
                md.append("")

            md.append("**Setup & Maintainer Telemetry:**")
            md.append(
                f"- Maintainer Velocity: {repo.maintainer_activity} ({repo.response_time_estimate})"
            )
            md.append(f"- Commits (30d): {repo.recent_commits} | Open Issues: {repo.open_issues}")
            md.append(
                f"- Documentation: CONTRIBUTING={repo.has_contributing_guide}, CodeOfConduct={repo.has_code_of_conduct}"
            )
            md.append("\n---\n")

        return "\n".join(md)

    def generate_json_report(self, analyses: list[RepositoryAnalysis]) -> str:
        """Generate structured JSON report."""
        data = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "total_repositories": len(analyses),
            },
            "repositories": [a.model_dump(mode="json") for a in analyses],
        }
        return json.dumps(data, indent=2)

    def _categorize_repositories(self, analyses: list[RepositoryAnalysis]) -> dict:
        categorized = {
            "actively_accepting": [],
            "limited_scope": [],
            "not_accepting": [],
            "archived_inactive": [],
        }
        for analysis in analyses:
            status_key = analysis.contribution_status.value
            if status_key in categorized:
                categorized[status_key].append(analysis)
            else:
                categorized["not_accepting"].append(analysis)
        return categorized

    def _generate_summary_report(
        self, analyses: list[RepositoryAnalysis], categorized: dict
    ) -> str:
        total = len(analyses)
        actively_accepting = len(categorized["actively_accepting"])
        limited_scope = len(categorized["limited_scope"])
        not_accepting = len(categorized["not_accepting"])
        archived = len(categorized["archived_inactive"])

        top_repos = sorted(analyses, key=lambda x: x.contribution_score, reverse=True)[:10]

        languages = {}
        for analysis in analyses:
            lang = analysis.language
            languages[lang] = languages.get(lang, 0) + 1
        popular_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]

        summary_data = {
            "total_repositories": total,
            "actively_accepting": actively_accepting,
            "actively_accepting_pct": (actively_accepting / total * 100) if total > 0 else 0,
            "limited_scope": limited_scope,
            "limited_scope_pct": (limited_scope / total * 100) if total > 0 else 0,
            "not_accepting": not_accepting,
            "not_accepting_pct": (not_accepting / total * 100) if total > 0 else 0,
            "archived": archived,
            "archived_pct": (archived / total * 100) if total > 0 else 0,
            "top_repositories": top_repos,
            "popular_languages": popular_languages,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return self._render_summary_template(summary_data)

    def _generate_individual_report(self, analysis: RepositoryAnalysis) -> dict:
        recommendations = self._generate_recommendations(analysis)
        getting_started = self._generate_getting_started_guide(analysis)

        report_data = {
            "repository": analysis,
            "recommendations": recommendations,
            "getting_started": getting_started,
            "contribution_indicators": self._get_contribution_indicators(analysis),
            "technical_details": self._get_technical_details(analysis),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {
            "repository_name": analysis.full_name,
            "score": analysis.contribution_score,
            "status": analysis.contribution_status.value,
            "html_content": self.template.render(**report_data),
            "data": report_data,
        }

    def _generate_recommendations(self, analysis: RepositoryAnalysis) -> list[str]:
        recommendations = []
        if analysis.contribution_status == ContributionStatus.ACTIVELY_ACCEPTING:
            recommendations.append(
                "High-probability contribution opportunity. Check labeled good-first-issues."
            )
            if analysis.has_contributing_guide:
                recommendations.append(
                    "Follow the structured CONTRIBUTING.md guidelines carefully."
                )
            recommendations.append(
                f"Maintainers respond {analysis.response_time_estimate.lower()}. Submit small, focused PRs."
            )
        elif analysis.contribution_status == ContributionStatus.LIMITED_SCOPE:
            recommendations.append(
                "Moderate contribution barrier. Propose improvements in discussion threads first."
            )
            recommendations.append(
                "Look for documentation, typos, or minor bug fixes as an initial entrypoint."
            )
        else:
            recommendations.append(
                "Low contribution velocity. Project may be feature-complete or maintainer-constrained."
            )
            recommendations.append(
                "Avoid large unsolicited PRs; comment on existing open issues to test responsiveness."
            )
        return recommendations

    def _generate_getting_started_guide(self, analysis: RepositoryAnalysis) -> dict:
        return {
            "step_1": f"Fork and clone the repository: `git clone {analysis.url}.git`",
            "step_2": f"Set up local runtime ({analysis.language}) and install project dependencies.",
            "step_3": "Review open issue discussions and comment before claiming a task.",
            "step_4": "Create a scoped topic branch, write unit tests, and submit a PR referencing the issue.",
        }

    def _get_contribution_indicators(self, analysis: RepositoryAnalysis) -> dict:
        return {
            "has_contributing": analysis.has_contributing_guide,
            "has_coc": analysis.has_code_of_conduct,
            "has_issue_template": analysis.has_issue_templates,
            "has_pr_template": analysis.has_pr_templates,
            "good_first_issues": analysis.good_first_issues,
            "help_wanted_issues": analysis.help_wanted_issues,
        }

    def _get_technical_details(self, analysis: RepositoryAnalysis) -> dict:
        return {
            "language": analysis.language,
            "tech_stack": analysis.tech_stack,
            "stars": analysis.stars,
            "forks": analysis.forks,
            "open_issues": analysis.open_issues,
            "recent_commits": analysis.recent_commits,
            "setup_complexity": analysis.setup_complexity,
        }

    def _render_summary_template(self, data: dict) -> str:
        template_str = """
        <div class="summary-report">
            <h2>GitHub Repository Contribution Intelligence Summary</h2>
            <p><strong>Generated At:</strong> {{ generated_at }}</p>
            <p><strong>Total Repositories Evaluated:</strong> {{ total_repositories }}</p>
            
            <div class="metrics-grid" style="display: flex; gap: 15px; margin: 20px 0;">
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; flex: 1;">
                    <h3 style="color: #2e7d32; margin: 0;">Actively Accepting</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{{ actively_accepting }} ({{ "%.1f"|format(actively_accepting_pct) }}%)</p>
                </div>
                <div style="background: #fff8e1; padding: 15px; border-radius: 8px; flex: 1;">
                    <h3 style="color: #f57f17; margin: 0;">Limited Scope</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{{ limited_scope }} ({{ "%.1f"|format(limited_scope_pct) }}%)</p>
                </div>
                <div style="background: #ffebee; padding: 15px; border-radius: 8px; flex: 1;">
                    <h3 style="color: #c62828; margin: 0;">Not Accepting / Stale</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{{ not_accepting + archived }} ({{ "%.1f"|format(not_accepting_pct + archived_pct) }}%)</p>
                </div>
            </div>
        </div>
        """
        return Template(template_str).render(**data)

    def _get_report_template(self) -> Template:
        template_str = """
        <div class="repo-card" style="border: 1px solid #e1e4e8; border-radius: 8px; padding: 20px; margin-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0;"><a href="{{ repository.url }}" target="_blank" style="color: #0366d6; text-decoration: none;">{{ repository.full_name }}</a></h3>
                <span style="background: #24292e; color: #fff; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 14px;">Score: {{ repository.contribution_score }}/100</span>
            </div>
            <p style="color: #586069; margin: 10px 0;">{{ repository.description }}</p>
            <div style="margin: 15px 0; font-size: 14px;">
                <span>⭐ {{ repository.stars }} stars</span> | 
                <span>🍴 {{ repository.forks }} forks</span> | 
                <span>💻 {{ repository.language }}</span> | 
                <span>⏱️ Maintainer Velocity: {{ repository.maintainer_activity }}</span>
            </div>
            {% if repository.ai_insights %}
            <div style="background: #f6f8fa; border-left: 4px solid #0366d6; padding: 12px; border-radius: 4px; margin: 15px 0;">
                <strong>🤖 Architectural & Contribution Insights:</strong>
                <p style="white-space: pre-line; margin: 5px 0 0 0;">{{ repository.ai_insights }}</p>
            </div>
            {% endif %}
            <div style="margin-top: 15px;">
                <strong>Getting Started:</strong>
                <ol style="margin: 5px 0 0 20px; padding: 0;">
                    <li>{{ getting_started.step_1 }}</li>
                    <li>{{ getting_started.step_2 }}</li>
                    <li>{{ getting_started.step_3 }}</li>
                    <li>{{ getting_started.step_4 }}</li>
                </ol>
            </div>
        </div>
        """
        return Template(template_str)
