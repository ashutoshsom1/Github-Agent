"""
Model Context Protocol (MCP) Server for GitHub Agent AI.
Exposes autonomous repository analysis, issue mining, and PR planning tools
to Claude Desktop, Cursor, Antigravity, and any standard MCP client.
"""

import asyncio
import json
import logging
import sys
from typing import Any

from github_agent.ai_intelligence import AIIntelligenceEngine
from github_agent.analyzer import RepositoryAnalyzer
from github_agent.api_client import GitHubAPIClient

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("mcp_server")

TOOLS = [
    {
        "name": "search_repositories",
        "description": "Search top GitHub repositories by keyword and evaluate contribution viability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Search keyword or topic (e.g. 'machine learning', 'langgraph')",
                },
                "max_repos": {
                    "type": "integer",
                    "description": "Maximum number of repositories to return",
                    "default": 10,
                },
                "min_stars": {
                    "type": "integer",
                    "description": "Minimum repository stars",
                    "default": 100,
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "analyze_repository",
        "description": "Perform deep architectural analysis and compute contribution readiness score (0-100) for a specific repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner / organization"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "mine_contribution_issues",
        "description": "Mine beginner-friendly (good-first-issue, help-wanted) open issues and rank them by contribution opportunity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "limit": {
                    "type": "integer",
                    "description": "Maximum issues to return",
                    "default": 5,
                },
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "generate_pr_contribution_plan",
        "description": "Synthesize a concrete step-by-step PR contribution plan, target files, prerequisites, and testing strategy for a given issue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_title": {"type": "string", "description": "Title of the target issue"},
                "issue_body": {
                    "type": "string",
                    "description": "Description / body text of the issue",
                    "default": "",
                },
            },
            "required": ["owner", "repo", "issue_title"],
        },
    },
]


class GitHubMCPServer:
    def __init__(self):
        self.api_client = GitHubAPIClient()
        self.analyzer = RepositoryAnalyzer(api_client=self.api_client, enable_ai=True)
        self.ai_engine = AIIntelligenceEngine()

    async def run_stdio(self):
        """Standard JSON-RPC 2.0 event loop over STDIN / STDOUT."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while not reader.at_eof():
            try:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                request = json.loads(line_str)
                response = await self.handle_request(request)
                if response:
                    out = json.dumps(response) + "\n"
                    sys.stdout.write(out)
                    sys.stdout.flush()

            except Exception as e:
                logger.error(f"Error processing MCP message: {e}")

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "github-agent-ai-mcp", "version": "2.0.0"},
                    "capabilities": {"tools": {}},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                result_text = await self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result_text}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32603, "message": str(e)},
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method {method} not found"},
        }

    async def execute_tool(self, name: str, args: dict[str, Any]) -> str:
        if name == "search_repositories":
            keyword = args["keyword"]
            max_repos = args.get("max_repos", 10)
            min_stars = args.get("min_stars", 100)

            repos = await self.api_client.search_repositories(
                keyword, max_repos=max_repos, min_stars=min_stars
            )
            analyses = []
            for r in repos[:max_repos]:
                a = await self.analyzer.analyze_repository(r)
                analyses.append(a.model_dump(mode="json"))
            return json.dumps(analyses, indent=2)

        elif name == "analyze_repository":
            owner = args["owner"]
            repo_name = args["repo"]
            repo_data = await self.api_client.get_repository(owner, repo_name)
            if not repo_data or "name" not in repo_data:
                return json.dumps({"error": f"Repository {owner}/{repo_name} not found"})

            analysis = await self.analyzer.analyze_repository(repo_data)
            return json.dumps(analysis.model_dump(mode="json"), indent=2)

        elif name == "mine_contribution_issues":
            owner = args["owner"]
            repo_name = args["repo"]
            limit = args.get("limit", 5)
            issues = await self.api_client.get_issues(owner, repo_name, state="open", per_page=40)

            results = []
            for i in issues:
                labels = [l.get("name", "").lower() for l in i.get("labels", [])]
                if any(
                    k in l
                    for l in labels
                    for k in ["good", "first", "help", "beginner", "up-for-grabs"]
                ):
                    results.append(
                        {
                            "number": i["number"],
                            "title": i["title"],
                            "url": i["html_url"],
                            "labels": [l.get("name") for l in i.get("labels", [])],
                            "comments": i.get("comments", 0),
                        }
                    )
                if len(results) >= limit:
                    break
            return json.dumps(results, indent=2)

        elif name == "generate_pr_contribution_plan":
            owner = args["owner"]
            repo_name = args["repo"]
            issue_title = args["issue_title"]
            issue_body = args.get("issue_body", "")

            repo_data = await self.api_client.get_repository(owner, repo_name)
            language = repo_data.get("language", "Python") if repo_data else "Python"

            plan = await self.ai_engine.generate_pr_plan(
                repository=f"{owner}/{repo_name}",
                issue_title=issue_title,
                issue_body=issue_body,
                language=language,
            )
            return json.dumps(plan.model_dump(mode="json"), indent=2)

        raise ValueError(f"Unknown tool: {name}")


def main():
    server = GitHubMCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
