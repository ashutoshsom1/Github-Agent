import pytest

from github_agent.mcp_server import GitHubMCPServer


@pytest.mark.asyncio
async def test_mcp_server_initialize():
    server = GitHubMCPServer()
    init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    response = await server.handle_request(init_request)
    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == "github-agent-ai-mcp"
    assert "tools" in response["result"]["capabilities"]


@pytest.mark.asyncio
async def test_mcp_server_tools_list():
    server = GitHubMCPServer()
    list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = await server.handle_request(list_request)
    assert response["id"] == 2
    tools = response["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "search_repositories" in tool_names
    assert "analyze_repository" in tool_names
    assert "mine_contribution_issues" in tool_names
    assert "generate_pr_contribution_plan" in tool_names
