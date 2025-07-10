import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # GitHub API Configuration
    github_token: str
    github_api_url: str = "https://api.github.com"
    max_repositories: int = 50
    min_stars: int = 100
    
    # Email Configuration
    email_host: str
    email_port: int = 587
    email_user: str
    email_password: str
    email_use_tls: bool = True
    
    # Analysis Configuration
    contribution_indicators: list = [
        "CONTRIBUTING.md",
        "good-first-issue",
        "help-wanted",
        "beginner",
        "easy"
    ]
    
    # Rate Limiting
    api_rate_limit: int = 5000  # requests per hour
    cache_duration: int = 3600  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
