from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub API Configuration
    github_token: str | None = Field(default=None, description="GitHub Personal Access Token")
    github_api_url: str = Field(
        default="https://api.github.com", description="GitHub REST API Base URL"
    )
    max_repositories: int = Field(default=15, description="Default max repositories to analyze")
    min_stars: int = Field(default=100, description="Minimum repository stars filter")

    # AI / LLM Configuration
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API Key for Claude")
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    default_ai_provider: str = Field(
        default="auto", description="AI Provider: auto | anthropic | openai | heuristic"
    )
    ai_model: str = Field(default="claude-3-5-sonnet-20241022", description="Primary AI Model")

    # Email / Notification Configuration
    email_host: str | None = Field(default=None, description="SMTP Host")
    email_port: int = Field(default=587, description="SMTP Port")
    email_user: str | None = Field(default=None, description="SMTP User")
    email_password: str | None = Field(default=None, description="SMTP Password")
    email_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # Model Context Protocol (MCP) Configuration
    mcp_server_name: str = Field(default="github-agent-mcp", description="MCP Server Name")
    mcp_server_version: str = Field(default="2.0.0", description="MCP Server Version")

    # Analysis Configuration
    contribution_indicators: list[str] = Field(
        default_factory=lambda: [
            "CONTRIBUTING.md",
            "good-first-issue",
            "help-wanted",
            "beginner",
            "easy",
            "up-for-grabs",
        ]
    )

    # Rate Limiting & Network
    api_rate_limit: int = Field(default=5000, description="Requests per hour limit")
    request_timeout_seconds: int = Field(default=30, description="HTTP request timeout")
    cache_duration: int = Field(default=3600, description="Cache duration in seconds")


settings = Settings()
